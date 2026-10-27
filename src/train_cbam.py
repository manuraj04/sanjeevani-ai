"""
================================================================================
SANJEEVANI AI: MULTI-SCALE CBAM EFFICIENTNETV2-S TRAINING PIPELINE
================================================================================
Trains the novel multi-scale attention network with genuine CBAM blocks across
stages 3, 5, and 7 on the 66 Indian Ayurvedic botanical classes.
Uses PyTorch Mixed Precision (AMP) on NVIDIA RTX 4050 GPU.
================================================================================
"""

import os
import sys
import time
import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets
from torch.optim.lr_scheduler import CosineAnnealingLR
import albumentations as A
from albumentations.pytorch import ToTensorV2
from PIL import Image

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.models.cbam_efficientnet import MultiScaleCBAMEfficientNet

# 1. Hyperparameters & Settings
DATA_DIR = os.path.join(project_root, "data", "processed")
TRAIN_DIR = os.path.join(DATA_DIR, "train")
VAL_DIR = os.path.join(DATA_DIR, "val")
TEST_DIR = os.path.join(DATA_DIR, "test")

BATCH_SIZE = 32
NUM_CLASSES = 66
PHASE1_EPOCHS = 3
PHASE2_EPOCHS = 5
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 2. Filtered Dataset Loader (ignoring Non_Plant to ensure strictly 66 botanical classes)
class BotanicalOnlyDataset(datasets.ImageFolder):
    def find_classes(self, directory):
        classes, _ = super().find_classes(directory)
        classes = [c for c in classes if c != "Non_Plant"]
        classes.sort()
        class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}
        return classes, class_to_idx

class AlbumentationsDataset(Dataset):
    def __init__(self, image_folder, transform=None):
        self.dataset = image_folder
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

def load_pretrained_features_into_cbam(model, weights_path):
    """Transfers the 780 pre-trained backbone weights from best_model_final.pth into MultiScaleCBAM stages."""
    if not os.path.exists(weights_path):
        print(f"[!] Historical weights not found at {weights_path}, starting from ImageNet weights.")
        return model

    print(f"[*] Transferring proven botanical backbone weights from: {weights_path}")
    state = torch.load(weights_path, map_location="cpu", weights_only=False)
    new_state = {}
    for k, v in state.items():
        if not k.startswith("features."):
            continue
        parts = k.split(".")
        block_idx = int(parts[1])
        rest = ".".join(parts[2:])
        if block_idx < 4:
            new_k = f"stage3.{block_idx}.{rest}"
        elif block_idx < 6:
            new_k = f"stage5.{block_idx - 4}.{rest}"
        else:
            new_k = f"stage7.{block_idx - 6}.{rest}"
        new_state[new_k] = v

    missing, unexpected = model.load_state_dict(new_state, strict=False)
    print(f"[+] Loaded backbone successfully. Missing keys for CBAM attention gates + head: {len(missing)}")
    return model

def train_one_epoch(model, dataloader, criterion, optimizer, scaler):
    model.train()
    running_loss, correct, total = 0.0, 0, 0
    t0 = time.time()
    
    for i, (inputs, labels) in enumerate(dataloader):
        inputs, labels = inputs.to(DEVICE, non_blocking=True), labels.to(DEVICE, non_blocking=True)
        optimizer.zero_grad()

        with torch.amp.autocast("cuda"):
            outputs = model(inputs)
            loss = criterion(outputs, labels)

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        running_loss += loss.item() * inputs.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels.data).item()
        total += labels.size(0)

        if (i + 1) % 200 == 0 or (i + 1) == len(dataloader):
            current_acc = (correct / total) * 100
            current_loss = running_loss / total
            elapsed = time.time() - t0
            print(f"    Step [{i+1:3d}/{len(dataloader):3d}] | Loss: {current_loss:.4f} | Acc: {current_acc:.2f}% | Elapsed: {elapsed:.1f}s")

    return running_loss / total, (correct / total) * 100

def evaluate_model(model, dataloader, criterion):
    model.eval()
    running_loss, correct, total = 0.0, 0, 0
    
    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs, labels = inputs.to(DEVICE, non_blocking=True), labels.to(DEVICE, non_blocking=True)
            with torch.amp.autocast("cuda"):
                outputs = model(inputs)
                loss = criterion(outputs, labels)

            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += labels.size(0)

    val_loss = running_loss / total
    val_acc = (correct / total) * 100
    return val_loss, val_acc

def run_training():
    print("=" * 70)
    print(" SANJEEVANI AI: CBAM MULTI-SCALE ATTENTION TRAINING")
    print(f" Target Device: {DEVICE} ({torch.cuda.get_device_name(0)})")
    print("=" * 70)

    # Albumentations transforms
    train_transform = A.Compose([
        A.Resize(256, 256),
        A.RandomCrop(224, 224),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.2),
        A.RandomRotate90(p=0.5),
        A.Affine(scale=(0.95, 1.05), rotate=(-15, 15), p=0.4),
        A.RandomBrightnessContrast(brightness_limit=0.15, contrast_limit=0.15, p=0.4),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2()
    ])

    val_transform = A.Compose([
        A.Resize(256, 256),
        A.CenterCrop(224, 224),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2()
    ])

    print("[*] Indexing datasets...")
    train_raw = BotanicalOnlyDataset(TRAIN_DIR)
    val_raw = BotanicalOnlyDataset(VAL_DIR)

    print(f"[+] Total Training Samples:   {len(train_raw)} across {len(train_raw.classes)} botanical classes")
    print(f"[+] Total Validation Samples: {len(val_raw)} across {len(val_raw.classes)} botanical classes")

    # Compute inverse frequency class weights
    targets = np.array(train_raw.targets)
    class_counts = np.bincount(targets)
    weights = 1.0 / np.maximum(class_counts, 1)
    weights = weights * NUM_CLASSES / np.sum(weights)
    class_weights = torch.FloatTensor(weights).to(DEVICE)
    print(f"[+] Class Weights Computed (Min: {weights.min():.3f}, Max: {weights.max():.3f})")

    train_dataset = AlbumentationsDataset(train_raw, transform=train_transform)
    val_dataset = AlbumentationsDataset(val_raw, transform=val_transform)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2, pin_memory=True)

    # Initialize CBAM Multi-Scale Model
    print("[*] Instantiating MultiScaleCBAMEfficientNet...")
    model = MultiScaleCBAMEfficientNet(num_classes=NUM_CLASSES, pretrained=True).to(DEVICE)
    
    # Load proven weights
    historical_weights = os.path.join(DATA_DIR, "best_model_final.pth")
    model = load_pretrained_features_into_cbam(model, historical_weights)

    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.08)
    scaler = torch.amp.GradScaler("cuda")
    best_save_path = os.path.join(DATA_DIR, "best_cbam_model.pth")
    best_val_acc = 0.0

    # -------------------------------------------------------------
    # PHASE 1: Warmup Attention Gates & Classification Head
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(" PHASE 1: TRAINING CBAM ATTENTION BLOCKS & MULTI-SCALE HEAD")
    print(" (Backbone frozen to isolate attention convergence)")
    print("=" * 70)

    # Freeze stages
    for param in model.stage3.parameters():
        param.requires_grad = False
    for param in model.stage5.parameters():
        param.requires_grad = False
    for param in model.stage7.parameters():
        param.requires_grad = False

    # Trainable: CBAM blocks + classifier
    trainable_params = [
        {"params": model.cbam_stage3.parameters(), "lr": 8e-4},
        {"params": model.cbam_stage5.parameters(), "lr": 8e-4},
        {"params": model.cbam_stage7.parameters(), "lr": 8e-4},
        {"params": model.classifier.parameters(), "lr": 1e-3}
    ]
    optimizer = optim.AdamW(trainable_params, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=PHASE1_EPOCHS, eta_min=1e-5)

    for epoch in range(1, PHASE1_EPOCHS + 1):
        t_start = time.time()
        print(f"\n--- Phase 1 | Epoch {epoch}/{PHASE1_EPOCHS} ---")
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, scaler)
        val_loss, val_acc = evaluate_model(model, val_loader, criterion)
        scheduler.step()
        duration = time.time() - t_start

        print(f"Results Epoch {epoch}: Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | Time: {duration:.1f}s")
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            print(f"[*] New Best Validation Accuracy ({val_acc:.2f}%). Saving checkpoint...")
            torch.save(model.state_dict(), best_save_path)

    # -------------------------------------------------------------
    # PHASE 2: End-to-End Fine-Tuning with Deep Stages Unfrozen
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(" PHASE 2: END-TO-END FINE-TUNING (Unfreezing Deep Stages)")
    print("=" * 70)

    # Unfreeze stage5 and stage7 for fine-grained venation co-adaptation
    for param in model.stage5.parameters():
        param.requires_grad = True
    for param in model.stage7.parameters():
        param.requires_grad = True

    finetune_params = [
        {"params": model.stage5.parameters(), "lr": 5e-5},
        {"params": model.stage7.parameters(), "lr": 5e-5},
        {"params": model.cbam_stage3.parameters(), "lr": 2e-4},
        {"params": model.cbam_stage5.parameters(), "lr": 2e-4},
        {"params": model.cbam_stage7.parameters(), "lr": 2e-4},
        {"params": model.classifier.parameters(), "lr": 3e-4}
    ]
    optimizer = optim.AdamW(finetune_params, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=PHASE2_EPOCHS, eta_min=1e-6)

    for epoch in range(1, PHASE2_EPOCHS + 1):
        t_start = time.time()
        print(f"\n--- Phase 2 | Epoch {epoch}/{PHASE2_EPOCHS} ---")
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, scaler)
        val_loss, val_acc = evaluate_model(model, val_loader, criterion)
        scheduler.step()
        duration = time.time() - t_start

        print(f"Results Epoch {epoch}: Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | Time: {duration:.1f}s")
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            print(f"[*] New Best Validation Accuracy ({val_acc:.2f}%). Saving checkpoint...")
            torch.save(model.state_dict(), best_save_path)

    print("\n" + "=" * 70)
    print(f" TRAINING COMPLETE! Best Validation Accuracy: {best_val_acc:.2f}%")
    print(f" Checkpoint saved to: {best_save_path}")
    print("=" * 70)

if __name__ == "__main__":
    run_training()

