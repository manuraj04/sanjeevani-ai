# Objective 2 — Preprocessing & Augmentation
## Sanjeevani Scan | Medicinal Plant Identification System

> **Goal:** Prepare the dataset for training by implementing robust preprocessing pipelines and data augmentation strategies to boost model robustness and handle class imbalance.

---

## Table of Contents

1. [Overview](#1- overview)
2. [Image Preprocessing](#2-image-preprocessing)
3. [Data Augmentation Strategy](#3-data-augmentation-strategy)
4. [Class Imbalance Handling](#4-class-imbalance-handling)
5. [PyTorch DataLoader Setup](#5-pytorch-dataloader-setup)
6. [Preprocessing Validation](#6-preprocessing-validation)
7. [Progress Tracker](#7-progress-tracker)

---

## 1. Overview

The dataset from Objective 1 (10,162 images, 28 species) is now ready for preprocessing. This objective covers:

- **Normalization**: Standardize pixel values using ImageNet statistics
- **Augmentation**: Apply realistic transformations (rotation, brightness, blur, etc.)
- **Class rebalancing**: Oversample minority classes to reduce class imbalance
- **PyTorch integration**: Create efficient DataLoaders for training

**Note:** Do NOT start training yet. Objective 2 prepares data; Objective 3 builds and trains the model.

---

## 2. Image Preprocessing

### 2.1 Normalization & Resizing

All images will be resized to **384×384** (standard for ViT models) and normalized using ImageNet statistics.

```python
# scripts/preprocess.py
import torch
import torchvision.transforms as T
from PIL import Image
import os
from pathlib import Path

# ImageNet normalization (for models pre-trained on ImageNet)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

RESIZE_SIZE = 384
CROP_SIZE = 384

def get_base_transforms(split='train'):
    """
    Returns base preprocessing transforms (no augmentation).
    Used as a foundation; augmentation is added on top.
    """
    if split == 'train':
        return T.Compose([
            T.Resize((RESIZE_SIZE, RESIZE_SIZE)),
            T.ToTensor(),
            T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ])
    else:  # val, test
        return T.Compose([
            T.Resize((RESIZE_SIZE, RESIZE_SIZE)),
            T.ToTensor(),
            T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ])

if __name__ == "__main__":
    # Test: Load and preprocess a sample image
    sample_img = Image.open('processed/train/Tulsi/sample.png').convert('RGB')
    transform = get_base_transforms('train')
    tensor = transform(sample_img)
    print(f"Input shape: {sample_img.size}")
    print(f"Tensor shape: {tensor.shape}")
    print(f"Min: {tensor.min():.3f}, Max: {tensor.max():.3f}, Mean: {tensor.mean():.3f}")
```

### 2.2 Handling Corrupted Images

Run a validation script to catch any remaining corrupted/invalid images:

```python
# scripts/validate_images.py
import os
from PIL import Image
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_dataset(split='train'):
    """Check all images in split for corruption."""
    split_path = Path('processed') / split
    errors = []
    
    for species_dir in split_path.iterdir():
        if not species_dir.is_dir():
            continue
        
        for img_file in species_dir.iterdir():
            if img_file.suffix.lower() not in ['.jpg', '.png', '.jpeg']:
                continue
            
            try:
                img = Image.open(img_file).convert('RGB')
                if img.size[0] < 32 or img.size[1] < 32:
                    errors.append((str(img_file), 'too_small'))
            except Exception as e:
                errors.append((str(img_file), str(e)))
    
    if errors:
        logger.warning(f"Found {len(errors)} problematic images:")
        for fpath, reason in errors[:10]:
            logger.warning(f"  {fpath}: {reason}")
        return False
    else:
        logger.info(f"All images in {split}/ are valid")
        return True

if __name__ == "__main__":
    for split in ['train', 'val', 'test']:
        validate_dataset(split)
```

---

## 3. Data Augmentation Strategy

### 3.1 Augmentation Techniques

Apply light augmentation to avoid over-distorting medicinal plant leaves:

```python
# scripts/augmentation.py
import albumentations as A
from albumentations.pytorch import ToTensorV2

def get_augmented_transforms(split='train'):
    """
    Returns augmentation transforms.
    Tuned for plant leaf images (avoid aggressive distortion).
    """
    if split == 'train':
        return A.Compose([
            A.Resize(384, 384),
            
            # Geometric transforms (moderate)
            A.Rotate(limit=30, p=0.5),
            A.HorizontalFlip(p=0.5),
            A.Perspective(scale=(0.05, 0.1), p=0.3),
            
            # Color/brightness transforms
            A.RandomBrightnessContrast(p=0.3),
            A.GaussNoise(p=0.2),
            A.Blur(blur_limit=3, p=0.2),
            
            # Normalization
            A.Normalize(mean=[0.485, 0.456, 0.406],
                       std=[0.229, 0.224, 0.225]),
            ToTensorV2(),
        ], bbox_params=None)
    else:  # val, test — no augmentation
        return A.Compose([
            A.Resize(384, 384),
            A.Normalize(mean=[0.485, 0.456, 0.406],
                       std=[0.229, 0.224, 0.225]),
            ToTensorV2(),
        ])
```

**Why these augmentations?**
- **Rotation ±30°**: Leaves can be photographed at different angles
- **Horizontal flip**: Plants are naturally symmetric (usually)
- **Brightness/contrast**: Lighting varies in field photos
- **Slight blur**: Mimics out-of-focus shots
- **Avoid aggressive**: Don't use extreme distortions (>60° rotation, severe shear) — medicinal leaf identification depends on fine morphological details

---

## 4. Class Imbalance Handling

### 4.1 Compute Class Weights

Classes are imbalanced (83–1,004 images per species). Use class weights to penalize the model more for minority class errors:

```python
# scripts/compute_class_weights.py
import pandas as pd
import numpy as np
from pathlib import Path

def compute_class_weights():
    """Compute inverse frequency weights for imbalanced classes."""
    df = pd.read_csv('metadata/split_log.csv')
    
    # Count training samples per class
    train_df = df[df['split'] == 'train']
    class_counts = train_df['species_name'].value_counts()
    
    # Inverse frequency weighting
    total = class_counts.sum()
    weights = {}
    for species, count in class_counts.items():
        weight = total / (len(class_counts) * count)
        weights[species] = weight
    
    # Normalize to sum to num_classes
    total_weight = sum(weights.values())
    weights = {k: v * len(weights) / total_weight for k, v in weights.items()}
    
    print(f"Class weights for {len(weights)} species:")
    for species in sorted(weights.keys()):
        print(f"  {species:20s}: {weights[species]:.3f}")
    
    # Save for use in training
    import json
    with open('metadata/class_weights.json', 'w') as f:
        json.dump(weights, f, indent=2)
    
    return weights

if __name__ == "__main__":
    compute_class_weights()
```

### 4.2 Oversampling (Optional)

For stronger class balancing, oversample minority classes in the DataLoader:

```python
# In PyTorch DataLoader setup
from torch.utils.data import WeightedRandomSampler

# Compute sample weights (weight = 1 / class_weight)
sample_weights = [class_weights[label] for label in labels]

sampler = WeightedRandomSampler(
    weights=sample_weights,
    num_samples=len(sample_weights),
    replacement=True
)

train_loader = DataLoader(
    train_dataset,
    batch_size=32,
    sampler=sampler,
    num_workers=4
)
```

---

## 5. PyTorch DataLoader Setup

### 5.1 Custom Dataset Class

```python
# scripts/plant_dataset.py
import torch
from torch.utils.data import Dataset
from pathlib import Path
import pandas as pd
from PIL import Image
import albumentations as A
from albumentations.pytorch import ToTensorV2

class PlantLeafDataset(Dataset):
    """PyTorch Dataset for medicinal plant leaves."""
    
    def __init__(self, split='train', transform=None):
        """
        Args:
            split: 'train', 'val', or 'test'
            transform: albumentations transform
        """
        self.split = split
        self.transform = transform
        
        # Load metadata
        df = pd.read_csv('metadata/split_log.csv')
        self.metadata = df[df['split'] == split].reset_index(drop=True)
        
        # Build species → class_id mapping
        self.species_list = sorted(self.metadata['species_name'].unique())
        self.species_to_id = {sp: i for i, sp in enumerate(self.species_list)}
        
        self.split_path = Path('processed') / split
    
    def __len__(self):
        return len(self.metadata)
    
    def __getitem__(self, idx):
        row = self.metadata.iloc[idx]
        
        # Load image
        img_path = self.split_path / row['species_name'] / row['filename']
        image = Image.open(img_path).convert('RGB')
        
        # Convert to numpy for albumentations
        image = np.array(image)
        
        # Apply augmentation
        if self.transform:
            augmented = self.transform(image=image)
            image = augmented['image']
        
        # Get label
        label = self.species_to_id[row['species_name']]
        
        return {
            'image': image,
            'label': torch.tensor(label, dtype=torch.long),
            'species': row['species_name'],
            'filename': row['filename']
        }

if __name__ == "__main__":
    from augmentation import get_augmented_transforms
    
    # Test dataset
    transform = get_augmented_transforms(split='train')
    dataset = PlantLeafDataset(split='train', transform=transform)
    
    print(f"Dataset size: {len(dataset)}")
    print(f"Species: {len(dataset.species_list)}")
    
    sample = dataset[0]
    print(f"Sample image shape: {sample['image'].shape}")
    print(f"Sample label: {sample['label']} ({sample['species']})")
```

### 5.2 DataLoader Factory

```python
# scripts/dataloader.py
import torch
from torch.utils.data import DataLoader, WeightedRandomSampler
from plant_dataset import PlantLeafDataset
from augmentation import get_augmented_transforms
import json

def get_dataloaders(batch_size=32, num_workers=4, use_weighted_sampler=True):
    """Create train/val/test DataLoaders."""
    
    # Transforms
    train_transform = get_augmented_transforms('train')
    val_transform = get_augmented_transforms('val')
    test_transform = get_augmented_transforms('test')
    
    # Datasets
    train_dataset = PlantLeafDataset('train', transform=train_transform)
    val_dataset = PlantLeafDataset('val', transform=val_transform)
    test_dataset = PlantLeafDataset('test', transform=test_transform)
    
    # Train loader with optional weighted sampling
    if use_weighted_sampler:
        try:
            with open('metadata/class_weights.json', 'r') as f:
                class_weights = json.load(f)
            
            # Compute sample weights
            sample_weights = [
                1.0 / class_weights.get(train_dataset.metadata.iloc[i]['species_name'], 1.0)
                for i in range(len(train_dataset))
            ]
            
            sampler = WeightedRandomSampler(
                weights=sample_weights,
                num_samples=len(sample_weights),
                replacement=True
            )
            
            train_loader = DataLoader(
                train_dataset,
                batch_size=batch_size,
                sampler=sampler,
                num_workers=num_workers,
                pin_memory=True
            )
        except FileNotFoundError:
            print("Class weights not found; using standard DataLoader")
            train_loader = DataLoader(
                train_dataset,
                batch_size=batch_size,
                shuffle=True,
                num_workers=num_workers,
                pin_memory=True
            )
    else:
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=True
        )
    
    # Val & test loaders (no shuffling, no weighted sampling)
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    return train_loader, val_loader, test_loader

if __name__ == "__main__":
    train_loader, val_loader, test_loader = get_dataloaders()
    
    print(f"Train batches: {len(train_loader)}")
    print(f"Val batches: {len(val_loader)}")
    print(f"Test batches: {len(test_loader)}")
    
    # Test a batch
    batch = next(iter(train_loader))
    print(f"\nBatch size: {batch['image'].shape[0]}")
    print(f"Image shape: {batch['image'].shape}")
    print(f"Labels: {batch['label'].shape}")
```

---

## 6. Preprocessing Validation

Run validation to ensure preprocessing works correctly:

```python
# scripts/test_preprocessing.py
import torch
import matplotlib.pyplot as plt
from dataloader import get_dataloaders

def visualize_batch(loader, num_images=12):
    """Visualize a batch of preprocessed images."""
    batch = next(iter(loader))
    
    # Denormalize for visualization
    IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406]).reshape(3, 1, 1)
    IMAGENET_STD = torch.tensor([0.229, 0.224, 0.225]).reshape(3, 1, 1)
    
    images = batch['image'][:num_images]
    images = images * IMAGENET_STD + IMAGENET_MEAN
    images = torch.clamp(images, 0, 1)
    
    fig, axes = plt.subplots(3, 4, figsize=(12, 9))
    for i, ax in enumerate(axes.flat):
        if i < len(images):
            img = images[i].permute(1, 2, 0).numpy()
            ax.imshow(img)
            ax.set_title(batch['species'][i], fontsize=10)
        ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('reports/preprocessing_sample.png', dpi=150)
    print("Visualization saved: reports/preprocessing_sample.png")

if __name__ == "__main__":
    train_loader, _, _ = get_dataloaders(batch_size=12)
    visualize_batch(train_loader, num_images=12)
```

---

## 7. Progress Tracker

| Task | Status | Notes |
|------|--------|-------|
| Image normalization & resizing | ☐ | Target: 384×384, ImageNet stats |
| Validate remaining images | ☐ | Catch any remaining corrupted files |
| Implement augmentation pipeline | ☐ | Albumentations, moderate settings |
| Compute class weights | ☐ | Handle class imbalance |
| Build PlantLeafDataset class | ☐ | PyTorch Dataset |
| Create DataLoader factory | ☐ | Train/val/test with sampling |
| Test preprocessing & DataLoaders | ☐ | Visualize batch, check shapes |
| **Objective 2 COMPLETE** | ☐ | Ready for Objective 3 (model training) |

---

## Next Steps

Once Objective 2 is complete:
1. All images are preprocessed and augmented
2. PyTorch DataLoaders are ready
3. Class imbalance is handled
4. Proceed to **Objective 3 — Model Training** (build and train ViT/ResNet classifier)

---

*Previous: [Objective 1 — Dataset Engineering](./OBJ1_Dataset_Engineering.md)*
