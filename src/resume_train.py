import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets, models
from torch.optim.lr_scheduler import CosineAnnealingLR
import albumentations as A
from albumentations.pytorch import ToTensorV2
from PIL import Image
import numpy as np
import time
import warnings
from tqdm import tqdm

# ==========================================
# 1. Configuration & Hyperparameters
# ==========================================
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed')
TRAIN_DIR = os.path.join(DATA_DIR, 'train')
VAL_DIR = os.path.join(DATA_DIR, 'val')

BATCH_SIZE = 32
# Calculate dynamically based on subdirectories in TRAIN_DIR, fallback to 67
try:
    NUM_CLASSES = len([d for d in os.listdir(TRAIN_DIR) if os.path.isdir(os.path.join(TRAIN_DIR, d))])
except FileNotFoundError:
    NUM_CLASSES = 67
    
START_EPOCH = 3 # Continuing Phase 3 from epoch 3
TOTAL_EPOCHS = 30
NUM_EPOCHS_REMAINING = TOTAL_EPOCHS - START_EPOCH + 1
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ==========================================
# 2. Albumentations Dataset Wrapper
# ==========================================
class AlbumentationsDataset(Dataset):
    def __init__(self, image_folder_dataset, transform=None):
        self.dataset = image_folder_dataset
        self.transform = transform

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        image, label = self.dataset[idx]
        image_np = np.array(image.convert("RGB"))
        if self.transform:
            augmented = self.transform(image=image_np)
            image = augmented["image"]
        return image, label

def train_epoch(model, dataloader, criterion, optimizer):
    model.train()
    running_loss, correct, total = 0.0, 0, 0
    pbar = tqdm(dataloader, desc="  Training", leave=False)
    for inputs, labels in pbar:
        inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * inputs.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels.data)
        total += labels.size(0)
        pbar.set_postfix({'loss': running_loss/total, 'acc': (correct.double()/total).item()})
    return running_loss / total, (correct.double() / total).item()

def evaluate(model, dataloader, criterion):
    model.eval()
    running_loss, correct, total = 0.0, 0, 0
    pbar = tqdm(dataloader, desc="  Validating", leave=False)
    with torch.no_grad():
        for inputs, labels in pbar:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data)
            total += labels.size(0)
            pbar.set_postfix({'loss': running_loss/total, 'acc': (correct.double()/total).item()})
    return running_loss / total, (correct.double() / total).item()

def main():
    warnings.filterwarnings("ignore")
    print(f"Device set to: {DEVICE}")
    
    train_transform = A.Compose([
        A.Resize(256, 256), A.RandomCrop(224, 224), A.RandomRotate90(p=0.5), A.HorizontalFlip(p=0.5),
        A.Affine(translate_percent=(-0.05, 0.05), scale=(0.95, 1.05), rotate=(-15, 15), p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.4),
        A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=10, p=0.3),
        A.CoarseDropout(num_holes_range=(1, 8), hole_height_range=(1, 16), hole_width_range=(1, 16), p=0.3),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]), ToTensorV2()
    ])
    val_transform = A.Compose([
        A.Resize(256, 256), A.CenterCrop(224, 224),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]), ToTensorV2()
    ])

    train_base = datasets.ImageFolder(TRAIN_DIR)
    val_base = datasets.ImageFolder(VAL_DIR)
    train_dataset = AlbumentationsDataset(train_base, transform=train_transform)
    val_dataset = AlbumentationsDataset(val_base, transform=val_transform)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0, pin_memory=True)

    weights = models.EfficientNet_V2_S_Weights.IMAGENET1K_V1
    model = models.efficientnet_v2_s(weights=weights)
    for param in model.parameters():
        param.requires_grad = False
    
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.4), nn.Linear(in_features, 512), nn.GELU(), nn.Dropout(0.3), nn.Linear(512, NUM_CLASSES)
    )

    model_path = os.path.join(DATA_DIR, 'best_model_final.pth')
    print(f"Loading weights from {model_path}")
    model.load_state_dict(torch.load(model_path, weights_only=True))
    model = model.to(DEVICE)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    print("\n" + "="*50)
    print(f"RESUMING PHASE 3: Full Network Fine-Tuning from epoch {START_EPOCH} to {TOTAL_EPOCHS}")
    print("="*50)

    for param in model.parameters():
        param.requires_grad = True

    optimizer_all = optim.AdamW(model.parameters(), lr=1e-6, weight_decay=1e-4)
    scheduler_all = CosineAnnealingLR(optimizer_all, T_max=TOTAL_EPOCHS)
    
    # Step scheduler to match the current epoch learning rate
    for _ in range(START_EPOCH - 1):
        scheduler_all.step()

    # Evaluate once to get best_val_acc
    print("Evaluating initial model...")
    _, best_val_acc = evaluate(model, val_loader, criterion)
    print(f"Initial Val Acc (from epoch {START_EPOCH-1}): {best_val_acc*100:.2f}%")

    for epoch in range(START_EPOCH, TOTAL_EPOCHS + 1):
        start_time = time.time()
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer_all)
        val_loss, val_acc = evaluate(model, val_loader, criterion)
        scheduler_all.step()

        print(f"Epoch {epoch}/{TOTAL_EPOCHS} | Time: {time.time()-start_time:.0f}s")
        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc*100:.2f}%")
        print(f"  Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc*100:.2f}%")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), os.path.join(DATA_DIR, 'best_model_final.pth'))
            print("  --> Saved new best model!")

    print("\nTraining Complete!")
    print(f"Best Validation Accuracy: {best_val_acc*100:.2f}%")

if __name__ == '__main__':
    main()
