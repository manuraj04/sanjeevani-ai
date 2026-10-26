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
    
NUM_EPOCHS_PHASE1 = 5
NUM_EPOCHS_PHASE2 = 50
NUM_EPOCHS_PHASE3 = 30
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

# ==========================================
# 3. Early Stopping Utility
# ==========================================
class EarlyStopping:
    def __init__(self, patience=12, min_delta=0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def __call__(self, val_loss):
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0

# ==========================================
# 4. Training Functions
# ==========================================
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

# ==========================================
# 5. Main Execution Block
# ==========================================
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

    print("Loading datasets...")
    train_base = datasets.ImageFolder(TRAIN_DIR)
    val_base = datasets.ImageFolder(VAL_DIR)

    # Compute class weights manually
    print("Computing class weights for imbalanced dataset...")
    targets = np.array(train_base.targets)
    class_sample_count = np.bincount(targets)
    weight = 1. / class_sample_count
    # Normalize weights so they sum up to num_classes
    weight = weight * NUM_CLASSES / np.sum(weight)
    class_weights = torch.FloatTensor(weight).to(DEVICE)
    print(f"Class weights computed. Min weight: {weight.min():.4f}, Max weight: {weight.max():.4f}")

    train_dataset = AlbumentationsDataset(train_base, transform=train_transform)
    val_dataset = AlbumentationsDataset(val_base, transform=val_transform)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0, pin_memory=True)

    print(f"Initializing EfficientNetV2-S on {DEVICE}...")
    weights = models.EfficientNet_V2_S_Weights.IMAGENET1K_V1
    model = models.efficientnet_v2_s(weights=weights)

    for param in model.parameters():
        param.requires_grad = False
    
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.4), nn.Linear(in_features, 512), nn.GELU(), nn.Dropout(0.3), nn.Linear(512, NUM_CLASSES)
    )

    model = model.to(DEVICE)
    # Apply class weights to criterion
    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.1)

    best_val_acc = 0.0

    # ---------------------------------------------------------
    # PHASE 1: Train Classifier Head
    # ---------------------------------------------------------
    print("\n" + "="*50)
    print("PHASE 1: Training Classifier Head (Frozen Backbone)")
    print("="*50)
    optimizer = optim.AdamW(model.classifier.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS_PHASE1)

    for epoch in range(NUM_EPOCHS_PHASE1):
        start_time = time.time()
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_acc = evaluate(model, val_loader, criterion)
        scheduler.step()
        print(f"Epoch {epoch+1}/{NUM_EPOCHS_PHASE1} | Time: {time.time()-start_time:.0f}s")
        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc*100:.2f}%")
        print(f"  Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc*100:.2f}%")
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), os.path.join(DATA_DIR, 'best_model_phase1.pth'))

    # ---------------------------------------------------------
    # PHASE 2: Unfreeze last 4 blocks
    # ---------------------------------------------------------
    print("\n" + "="*50)
    print("PHASE 2: Fine-Tuning (Unfreezing last 4 blocks)")
    print("="*50)
    model.load_state_dict(torch.load(os.path.join(DATA_DIR, 'best_model_phase1.pth'), weights_only=True))
    blocks_to_unfreeze = list(model.features.children())[-4:]
    for block in blocks_to_unfreeze:
        for param in block.parameters():
            param.requires_grad = True

    optimizer_ft = optim.AdamW([
        {"params": blocks_to_unfreeze[0].parameters(), "lr": 1e-5},
        {"params": blocks_to_unfreeze[1].parameters(), "lr": 1e-5},
        {"params": blocks_to_unfreeze[2].parameters(), "lr": 2e-5},
        {"params": blocks_to_unfreeze[3].parameters(), "lr": 2e-5},
        {"params": model.classifier.parameters(),      "lr": 1e-4},
    ], weight_decay=1e-4)
    scheduler_ft = CosineAnnealingLR(optimizer_ft, T_max=NUM_EPOCHS_PHASE2)
    early_stopping = EarlyStopping(patience=12)

    for epoch in range(NUM_EPOCHS_PHASE2):
        start_time = time.time()
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer_ft)
        val_loss, val_acc = evaluate(model, val_loader, criterion)
        scheduler_ft.step()
        print(f"Epoch {epoch+1}/{NUM_EPOCHS_PHASE2} | Time: {time.time()-start_time:.0f}s")
        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc*100:.2f}%")
        print(f"  Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc*100:.2f}%")
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), os.path.join(DATA_DIR, 'best_model_phase2.pth'))
            print("  --> Saved new best model!")
        
        early_stopping(val_loss)
        if early_stopping.early_stop:
            print("Early stopping triggered in Phase 2.")
            break

    # ---------------------------------------------------------
    # PHASE 3: Unfreeze ALL blocks
    # ---------------------------------------------------------
    print("\n" + "="*50)
    print("PHASE 3: Full Network Fine-Tuning")
    print("="*50)
    if os.path.exists(os.path.join(DATA_DIR, 'best_model_phase2.pth')):
        model.load_state_dict(torch.load(os.path.join(DATA_DIR, 'best_model_phase2.pth'), weights_only=True))
    
    for param in model.parameters():
        param.requires_grad = True

    optimizer_all = optim.AdamW(model.parameters(), lr=1e-6, weight_decay=1e-4)
    scheduler_all = CosineAnnealingLR(optimizer_all, T_max=NUM_EPOCHS_PHASE3)
    early_stopping_all = EarlyStopping(patience=12)

    for epoch in range(NUM_EPOCHS_PHASE3):
        start_time = time.time()
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer_all)
        val_loss, val_acc = evaluate(model, val_loader, criterion)
        scheduler_all.step()
        print(f"Epoch {epoch+1}/{NUM_EPOCHS_PHASE3} | Time: {time.time()-start_time:.0f}s")
        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc*100:.2f}%")
        print(f"  Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc*100:.2f}%")
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), os.path.join(DATA_DIR, 'best_model_final.pth'))
            print("  --> Saved new best final model!")
        
        early_stopping_all(val_loss)
        if early_stopping_all.early_stop:
            print("Early stopping triggered in Phase 3.")
            break

    print("\nTraining Complete!")
    print(f"Best Validation Accuracy: {best_val_acc*100:.2f}%")

if __name__ == '__main__':
    main()
