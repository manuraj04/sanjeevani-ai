"""
Custom PyTorch Dataset for medicinal plant leaf images.
Handles loading, preprocessing, and augmentation.
"""

import torch
from torch.utils.data import Dataset
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlantLeafDataset(Dataset):
    """PyTorch Dataset for medicinal plant leaves."""

    def __init__(self, split='train', transform=None):
        """
        Initialize dataset.

        Args:
            split: 'train', 'val', or 'test'
            transform: albumentations or torchvision transform
        """
        self.split = split
        self.transform = transform

        # Load metadata
        df = pd.read_csv('metadata/split_log.csv')
        self.metadata = df[df['split'] == split].reset_index(drop=True)

        if len(self.metadata) == 0:
            logger.error(f"No images found for split: {split}")
            raise ValueError(f"Empty dataset for split {split}")

        # Build species → class_id mapping
        self.species_list = sorted(self.metadata['species_name'].unique())
        self.species_to_id = {sp: i for i, sp in enumerate(self.species_list)}

        self.split_path = Path('processed') / split

        logger.info(f"\nPlantLeafDataset initialized")
        logger.info(f"  Split: {split}")
        logger.info(f"  Images: {len(self.metadata)}")
        logger.info(f"  Species: {len(self.species_list)}")

    def __len__(self):
        return len(self.metadata)

    def __getitem__(self, idx):
        """
        Get a single sample.

        Args:
            idx: Sample index

        Returns:
            Dictionary with 'image', 'label', 'species', 'filename'
        """
        row = self.metadata.iloc[idx]

        # Load image
        img_path = self.split_path / row['species_name'] / row['filename']

        try:
            image = Image.open(img_path).convert('RGB')
        except Exception as e:
            logger.error(f"Failed to load {img_path}: {e}")
            # Return a black image as fallback
            image = Image.new('RGB', (384, 384), color=(0, 0, 0))

        # Convert to numpy for albumentations
        image = np.array(image)

        # Apply augmentation/preprocessing
        if self.transform:
            augmented = self.transform(image=image)
            image = augmented['image']
        else:
            # Fallback: basic preprocessing
            image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0

        # Get label
        label = self.species_to_id[row['species_name']]

        return {
            'image': image,
            'label': torch.tensor(label, dtype=torch.long),
            'species': row['species_name'],
            'filename': row['filename']
        }

    def get_species_list(self):
        """Return sorted list of species."""
        return self.species_list

    def get_num_classes(self):
        """Return number of classes."""
        return len(self.species_list)


def test_dataset():
    """Test dataset loading."""
    try:
        import albumentations as A
        from albumentations.pytorch import ToTensorV2

        # Define a simple transform
        transform = A.Compose([
            A.Resize(384, 384),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2(),
        ])
    except ImportError:
        logger.warning("albumentations not available; using no transform")
        transform = None

    # Load dataset
    try:
        dataset = PlantLeafDataset(split='train', transform=transform)
    except ValueError as e:
        logger.error(f"Failed to load dataset: {e}")
        logger.info("Make sure processed/train/ exists and has images")
        return

    logger.info(f"\nDataset test:")
    logger.info(f"  Total samples: {len(dataset)}")
    logger.info(f"  Classes: {dataset.get_num_classes()}")
    logger.info(f"  Species: {dataset.get_species_list()}")

    # Get a sample
    sample = dataset[0]
    logger.info(f"\nSample 0:")
    logger.info(f"  Image shape: {sample['image'].shape}")
    logger.info(f"  Label: {sample['label']} ({sample['species']})")
    logger.info(f"  Filename: {sample['filename']}")

    # Test multiple samples
    logger.info(f"\nTesting 10 random samples...")
    import random
    for _ in range(10):
        idx = random.randint(0, len(dataset) - 1)
        sample = dataset[idx]
        assert sample['image'].shape == (3, 384, 384), f"Wrong shape: {sample['image'].shape}"
        assert isinstance(sample['label'], torch.Tensor), "Label not a tensor"
        assert 0 <= sample['label'].item() < dataset.get_num_classes(), "Label out of range"

    logger.info("All tests passed!")


if __name__ == "__main__":
    test_dataset()
