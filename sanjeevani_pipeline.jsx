import { useState } from "react";

const phases = [
  {
    id: 1,
    phase: "Phase 1",
    title: "Data Collection",
    icon: "🌿",
    color: "#1a6b3c",
    bg: "#e8f5ee",
    border: "#2d9e5f",
    steps: [
      {
        step: "1.1",
        title: "Dataset Sources — Where to Get Images",
        tag: "SOURCE",
        tagColor: "#1a6b3c",
        content: `Combine these sources for maximum coverage:`,
        items: [
          { label: "Kaggle: Indian Medicinal Plants", detail: "~80 species, ~17,000 images — Primary source. Search: 'Indian Medicinal Leaves Dataset'" },
          { label: "Kaggle: MedLeaf Dataset", detail: "30 Indian species, 1800 clean images — Good quality baseline" },
          { label: "iNaturalist (filtered)", detail: "Field photos — Use API to pull by species name. Realistic, messy, essential for robustness" },
          { label: "PlantNet API", detail: "Open dataset — Use for cross-validation and edge-case images" },
          { label: "Manual Collection (optional)", detail: "If you have access to a garden, school, or AYUSH center — photograph 30–50 images per rare species" },
        ],
        note: "Target: 8,000–15,000 images across 60–80 species minimum. 100–300 images per species is workable."
      },
      {
        step: "1.2",
        title: "Folder Structure — Organize Before Anything Else",
        tag: "STRUCTURE",
        tagColor: "#0d5c8a",
        content: "Set up your directory like this from Day 1:",
        code: `sanjeevani_data/
├── raw/                   ← All downloaded images, untouched
│   ├── kaggle_indian/
│   ├── medleaf/
│   └── inat_collected/
├── processed/             ← After cleaning + augmentation
│   ├── train/
│   │   ├── Tulsi/
│   │   ├── Neem/
│   │   ├── Brahmi/
│   │   └── ... (one folder per species)
│   ├── val/
│   └── test/
├── metadata/              ← CSV files tracking labels & sources
│   ├── master_labels.csv
│   └── split_log.csv
└── logs/                  ← Training logs, confusion matrices`,
        note: "Never mix raw and processed. If you mess up processing, you can always restart from raw."
      }
    ]
  },
  {
    id: 2,
    phase: "Phase 2",
    title: "Data Labelling",
    icon: "🏷️",
    color: "#7b3f00",
    bg: "#fdf0e0",
    border: "#e07b20",
    steps: [
      {
        step: "2.1",
        title: "Verify Existing Labels — Don't Trust Kaggle Blindly",
        tag: "CRITICAL",
        tagColor: "#c0392b",
        content: "Many Kaggle datasets have mislabelled or mixed images. Do this first:",
        items: [
          { label: "Cross-check with IMPPAT", detail: "Look up the plant's official botanical name and match it with what the folder says" },
          { label: "Google Image Search check", detail: "Search 10 random images from each folder — if something looks wrong, flag the folder" },
          { label: "Wikipedia cross-reference", detail: "Compare leaf shape, color, margin with the Wikipedia image for that species" },
          { label: "Mark uncertain images", detail: "Don't delete yet — move to a 'review/' folder. You'll verify or remove them later" },
        ],
        note: "Mislabelled data is the #1 silent killer of accuracy. A 5% label error can drop accuracy by 10–15%."
      },
      {
        step: "2.2",
        title: "Labelling Tool — If You're Adding New Images",
        tag: "TOOL",
        tagColor: "#1a6b3c",
        content: "For any manually collected images, use one of these:",
        items: [
          { label: "LabelImg (free, offline)", detail: "Best for beginners. Saves labels as XML. Install: pip install labelImg" },
          { label: "Label Studio (free, web)", detail: "More powerful, supports multi-class, custom attributes. Good if your team is 2+ people" },
          { label: "Roboflow (free tier)", detail: "Cloud-based, auto-splits train/val/test, exports to multiple formats including YOLO and TFRecord" },
          { label: "Simple folder naming", detail: "If just doing species classification (no bounding boxes needed), just putting images in named folders IS the label" },
        ],
        note: "For leaf classification, you don't need bounding boxes. Folder = class label. Keep it simple."
      },
      {
        step: "2.3",
        title: "Master CSV — Track Everything",
        tag: "DATA",
        tagColor: "#0d5c8a",
        content: "Create a master_labels.csv with these columns:",
        code: `filename,           species_name,    botanical_name,        source,       split,  verified
neem_001.jpg,       Neem,            Azadirachta indica,    kaggle,       train,  yes
tulsi_042.jpg,      Tulsi,           Ocimum tenuiflorum,    inat,         val,    yes
brahmi_017.jpg,     Brahmi,          Bacopa monnieri,       manual,       train,  yes
unknown_009.jpg,    Ashwagandha,     Withania somnifera,    kaggle,       REVIEW, no`,
        note: "This CSV is your source of truth. Every image in your dataset should have a row here."
      }
    ]
  },
  {
    id: 3,
    phase: "Phase 3",
    title: "Image Cleaning",
    icon: "🧹",
    color: "#1a3a6b",
    bg: "#e8edf5",
    border: "#2e5ba8",
    steps: [
      {
        step: "3.1",
        title: "Remove Unusable Images",
        tag: "FILTER",
        tagColor: "#7b3f00",
        content: "Write a Python script to auto-flag or delete these categories:",
        items: [
          { label: "Corrupt/unreadable files", detail: "try: PIL.Image.open(f) — catch exceptions, log and remove" },
          { label: "Wrong format images", detail: "Keep only .jpg, .jpeg, .png — convert .webp and .bmp with PIL" },
          { label: "Too small (< 64×64 px)", detail: "Useless for CNN. Filter: if img.size[0] < 64 or img.size[1] < 64: remove" },
          { label: "Extreme aspect ratios", detail: "If width/height > 5 or < 0.2, it's likely a panoramic or strip — remove" },
          { label: "Duplicate detection", detail: "Use imagehash library. Perceptual hash (pHash) finds near-duplicates even with slight edits" },
          { label: "Non-leaf images", detail: "Manually scan each folder's worst 20 images — remove fruits, roots, trees, people" },
        ],
        code: `import os
from PIL import Image
import imagehash

def clean_images(folder):
    hashes = {}
    removed = []
    for fname in os.listdir(folder):
        fpath = os.path.join(folder, fname)
        try:
            img = Image.open(fpath).convert("RGB")
            w, h = img.size
            # Size check
            if w < 64 or h < 64:
                os.remove(fpath); removed.append(fname); continue
            # Duplicate check (pHash)
            ph = str(imagehash.phash(img))
            if ph in hashes:
                os.remove(fpath); removed.append(fname); continue
            hashes[ph] = fname
        except Exception:
            os.remove(fpath); removed.append(fname)
    print(f"Removed {len(removed)} images from {folder}")`,
        note: "Run this per-class folder. Log everything removed — you may want to review before permanent deletion."
      },
      {
        step: "3.2",
        title: "Background Removal — Optional but Powerful",
        tag: "PROCESSING",
        tagColor: "#1a6b3c",
        content: "For cleaner feature learning, remove noisy backgrounds using rembg:",
        code: `# Install: pip install rembg
from rembg import remove
from PIL import Image
import io

def remove_background(input_path, output_path):
    with open(input_path, "rb") as f:
        input_data = f.read()
    output_data = remove(input_data)
    img = Image.open(io.BytesIO(output_data)).convert("RGBA")
    # White background for clean leaf on white
    background = Image.new("RGBA", img.size, (255, 255, 255, 255))
    combined = Image.alpha_composite(background, img).convert("RGB")
    combined.save(output_path)`,
        note: "Background removal improves accuracy by 3–7% on clean datasets. Essential if using field-collected images. Optional for already-clean Kaggle images."
      }
    ]
  },
  {
    id: 4,
    phase: "Phase 4",
    title: "Image Preprocessing",
    icon: "⚙️",
    color: "#4a1080",
    bg: "#f3e8f8",
    border: "#8e3bb5",
    steps: [
      {
        step: "4.1",
        title: "Standardize All Images",
        tag: "NORMALIZE",
        tagColor: "#4a1080",
        content: "Every image must be the same size and format before entering the model:",
        code: `from PIL import Image
import numpy as np

def preprocess_image(path, target_size=(224, 224)):
    img = Image.open(path).convert("RGB")
    
    # Step 1: Resize (maintain aspect ratio, then center crop)
    img.thumbnail((256, 256), Image.LANCZOS)   # Resize longest side to 256
    w, h = img.size
    left = (w - 224) // 2
    top  = (h - 224) // 2
    img  = img.crop((left, top, left+224, top+224))  # Center crop to 224x224
    
    # Step 2: Convert to numpy array
    arr = np.array(img, dtype=np.float32)
    
    # Step 3: Normalize to ImageNet mean/std (required for transfer learning)
    mean = np.array([0.485, 0.456, 0.406]) * 255
    std  = np.array([0.229, 0.224, 0.225]) * 255
    arr  = (arr - mean) / std
    
    return arr`,
        note: "Always use 224×224 for EfficientNet/ResNet/MobileNet. Use 299×299 for InceptionV3 and Xception. ImageNet normalization is mandatory for transfer learning."
      },
      {
        step: "4.2",
        title: "Data Augmentation — Multiply Your Dataset",
        tag: "AUGMENT",
        tagColor: "#1a6b3c",
        content: "Augmentation artificially expands your dataset. Use Albumentations — it's faster than torchvision/tf.image:",
        code: `import albumentations as A
from albumentations.pytorch import ToTensorV2

# Training augmentation pipeline
train_transform = A.Compose([
    A.RandomRotate90(p=0.5),
    A.Flip(p=0.5),
    A.Rotate(limit=30, p=0.5),
    A.RandomBrightnessContrast(0.2, 0.2, p=0.4),
    A.HueSaturationValue(10, 20, 10, p=0.3),
    A.GaussNoise(var_limit=(10, 50), p=0.3),
    A.MotionBlur(blur_limit=5, p=0.2),
    A.CoarseDropout(max_holes=8, max_height=16, max_width=16, p=0.3),  # Simulate occlusions
    A.CLAHE(clip_limit=2.0, p=0.3),   # Enhance contrast adaptively
    A.Resize(224, 224),
    A.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    ToTensorV2()
])

# Validation/Test — NO augmentation, just resize + normalize
val_transform = A.Compose([
    A.Resize(224, 224),
    A.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    ToTensorV2()
])`,
        note: "Do NOT augment validation or test sets — that would corrupt your accuracy metrics. Augmentation is only for training."
      },
      {
        step: "4.3",
        title: "Handle Class Imbalance",
        tag: "BALANCE",
        tagColor: "#c0392b",
        content: "If some species have 500 images and others only 80, the model will learn to predict majority classes. Fix with:",
        items: [
          { label: "Oversampling minorities", detail: "Use WeightedRandomSampler in PyTorch to give rare classes more training appearances per epoch" },
          { label: "Weighted loss function", detail: "class_weights = total_images / (n_classes * count_per_class) — pass to CrossEntropyLoss" },
          { label: "Augment minority classes more", detail: "Apply 5–8 augmentations per image for species with < 150 images to bring them up" },
          { label: "Target: 200+ per class minimum", detail: "Below 100 images per class, even transfer learning struggles significantly" },
        ],
        code: `import torch
from torch.utils.data import WeightedRandomSampler

# Calculate sample weights per image
class_counts = [count_per_class[c] for c in dataset.targets]
weights = [1.0 / class_counts[i] for i in range(len(dataset))]
sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)

# Use sampler in DataLoader — ensures balanced batches
loader = DataLoader(dataset, batch_size=32, sampler=sampler)`
      }
    ]
  },
  {
    id: 5,
    phase: "Phase 5",
    title: "Dataset Splitting",
    icon: "✂️",
    color: "#0d5c8a",
    bg: "#e3f0fa",
    border: "#1a86c8",
    steps: [
      {
        step: "5.1",
        title: "Train / Validation / Test Split",
        tag: "SPLIT",
        tagColor: "#0d5c8a",
        content: "Use stratified splitting so every class is proportionally represented in each split:",
        code: `from sklearn.model_selection import train_test_split
import pandas as pd

df = pd.read_csv("metadata/master_labels.csv")
df = df[df["verified"] == "yes"]   # Only verified images

# Step 1: Split off test set (15%)
train_val, test = train_test_split(
    df, test_size=0.15, stratify=df["species_name"], random_state=42
)

# Step 2: Split train into train + val (15% of original = ~17.6% of train_val)
train, val = train_test_split(
    train_val, test_size=0.176, stratify=train_val["species_name"], random_state=42
)

# Result: ~70% train / 15% val / 15% test
print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

# Save splits back to CSV
train["split"] = "train"; val["split"] = "val"; test["split"] = "test"
pd.concat([train, val, test]).to_csv("metadata/split_log.csv", index=False)`,
        note: "LOCK your test set after this step. Never look at test set results during training. It is used ONLY for final evaluation."
      },
      {
        step: "5.2",
        title: "Copy Files Into Split Folders",
        tag: "ORGANIZE",
        tagColor: "#1a6b3c",
        code: `import shutil, os
import pandas as pd

df = pd.read_csv("metadata/split_log.csv")

for _, row in df.iterrows():
    src = f"raw/{row['source']}/{row['filename']}"
    dst_dir = f"processed/{row['split']}/{row['species_name']}"
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(src, dst_dir)

print("All files organized into train/val/test folders.")`,
        note: "After this step, your folder structure is ready to directly feed into PyTorch ImageFolder or TensorFlow ImageDataGenerator."
      }
    ]
  },
  {
    id: 6,
    phase: "Phase 6",
    title: "Model Training",
    icon: "🧠",
    color: "#1a3a6b",
    bg: "#e8edf5",
    border: "#2e5ba8",
    steps: [
      {
        step: "6.1",
        title: "Load Dataset with PyTorch",
        tag: "PYTORCH",
        tagColor: "#4a1080",
        code: `from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader

train_dataset = ImageFolder("processed/train", transform=train_transform)
val_dataset   = ImageFolder("processed/val",   transform=val_transform)
test_dataset  = ImageFolder("processed/test",  transform=val_transform)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True,  num_workers=4, pin_memory=True)
val_loader   = DataLoader(val_dataset,   batch_size=32, shuffle=False, num_workers=4)
test_loader  = DataLoader(test_dataset,  batch_size=32, shuffle=False, num_workers=4)

print(f"Classes: {train_dataset.classes}")
print(f"Train: {len(train_dataset)} | Val: {len(val_dataset)} | Test: {len(test_dataset)}")`
      },
      {
        step: "6.2",
        title: "Transfer Learning — Start with EfficientNetV2",
        tag: "MODEL",
        tagColor: "#c0392b",
        code: `import torch
import torch.nn as nn
import torchvision.models as models

num_classes = 80  # your number of species

# Load pretrained EfficientNetV2-S
model = models.efficientnet_v2_s(weights="IMAGENET1K_V1")

# Freeze all layers first (feature extraction mode)
for param in model.parameters():
    param.requires_grad = False

# Replace classifier head for your classes
in_features = model.classifier[1].in_features
model.classifier = nn.Sequential(
    nn.Dropout(0.4),
    nn.Linear(in_features, 512),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(512, num_classes)
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)`,
        note: "Train only the classifier head for 5 epochs first (frozen backbone). Then unfreeze the last 2 blocks and train with a much lower LR (fine-tuning)."
      },
      {
        step: "6.3",
        title: "Training Loop — Full Setup",
        tag: "TRAIN",
        tagColor: "#1a6b3c",
        code: `import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR

criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))

# Phase 1: Train head only (frozen backbone)
optimizer = optim.Adam(model.classifier.parameters(), lr=1e-3)
scheduler = CosineAnnealingLR(optimizer, T_max=5)

def train_epoch(model, loader, optimizer, criterion):
    model.train()
    total_loss, correct, total = 0, 0, 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        correct += (outputs.argmax(1) == labels).sum().item()
        total += labels.size(0)
    return total_loss / len(loader), 100 * correct / total

def eval_epoch(model, loader, criterion):
    model.eval()
    total_loss, correct, total = 0, 0, 0
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            total_loss += loss.item()
            correct += (outputs.argmax(1) == labels).sum().item()
            total += labels.size(0)
    return total_loss / len(loader), 100 * correct / total

best_val_acc = 0
for epoch in range(1, 6):    # Phase 1: 5 epochs
    train_loss, train_acc = train_epoch(model, train_loader, optimizer, criterion)
    val_loss, val_acc     = eval_epoch(model, val_loader, criterion)
    scheduler.step()
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), "best_model_phase1.pth")
    print(f"Epoch {epoch} | Train: {train_acc:.2f}% | Val: {val_acc:.2f}%")`,
        note: "After Phase 1 (head training), unfreeze the last 2 blocks and re-run with LR=1e-4 for 10–15 more epochs (fine-tuning phase)."
      },
      {
        step: "6.4",
        title: "Fine-Tuning — Unfreeze and Improve",
        tag: "FINETUNE",
        tagColor: "#7b3f00",
        code: `# Phase 2: Fine-tune — unfreeze last 2 blocks
# EfficientNetV2-S has 7 feature blocks; unfreeze blocks 5 and 6
blocks_to_unfreeze = list(model.features.children())[-2:]  
for block in blocks_to_unfreeze:
    for param in block.parameters():
        param.requires_grad = True

# Also unfreeze classifier (already trainable)
for param in model.classifier.parameters():
    param.requires_grad = True

# Fine-tune with much lower learning rate
optimizer_ft = optim.Adam([
    {"params": blocks_to_unfreeze[0].parameters(), "lr": 1e-5},
    {"params": blocks_to_unfreeze[1].parameters(), "lr": 1e-5},
    {"params": model.classifier.parameters(),       "lr": 1e-4},
])
scheduler_ft = CosineAnnealingLR(optimizer_ft, T_max=15)

for epoch in range(1, 16):   # Phase 2: 15 epochs
    train_loss, train_acc = train_epoch(model, train_loader, optimizer_ft, criterion)
    val_loss, val_acc     = eval_epoch(model, val_loader, criterion)
    scheduler_ft.step()
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), "best_model_final.pth")
    print(f"Epoch {epoch} | Train: {train_acc:.2f}% | Val: {val_acc:.2f}%")`
      }
    ]
  },
  {
    id: 7,
    phase: "Phase 7",
    title: "Evaluation & Explainability",
    icon: "📊",
    color: "#1a6b3c",
    bg: "#e8f5ee",
    border: "#2d9e5f",
    steps: [
      {
        step: "7.1",
        title: "Evaluation Metrics — What to Measure",
        tag: "METRICS",
        tagColor: "#1a6b3c",
        content: "Run on the locked test set ONLY ONCE at the very end:",
        items: [
          { label: "Top-1 Accuracy", detail: "% of images where the top prediction is correct. Target: ≥ 87%" },
          { label: "Top-5 Accuracy", detail: "% where correct class is in top 5 predictions. Target: ≥ 97%" },
          { label: "Per-class F1 Score", detail: "Harmonic mean of precision + recall per species. Exposes weak classes" },
          { label: "Confusion Matrix", detail: "Shows which species are confused with which — critical for Ayurvedic safety" },
          { label: "Confidence Calibration", detail: "Is a 90% confidence prediction actually right 90% of the time? Use reliability diagrams" },
        ],
        code: `from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

all_preds, all_labels = [], []
model.load_state_dict(torch.load("best_model_final.pth"))
model.eval()
with torch.no_grad():
    for images, labels in test_loader:
        outputs = model(images.to(device))
        preds = outputs.argmax(1).cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(labels.numpy())

print(classification_report(all_labels, all_preds, target_names=train_dataset.classes))

# Confusion matrix
cm = confusion_matrix(all_labels, all_preds)
plt.figure(figsize=(20,16))
sns.heatmap(cm, xticklabels=train_dataset.classes, yticklabels=train_dataset.classes, 
            annot=True, fmt="d", cmap="YlGn")
plt.savefig("confusion_matrix.png", bbox_inches="tight")`
      },
      {
        step: "7.2",
        title: "Grad-CAM — Make the Model Explainable",
        tag: "XAI",
        tagColor: "#4a1080",
        content: "Grad-CAM shows which parts of the leaf triggered the prediction. Essential for user trust and validation:",
        code: `# pip install grad-cam
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
import numpy as np
from PIL import Image
import torchvision.transforms.functional as TF

# Target the last conv layer of EfficientNetV2
target_layer = model.features[-1]

cam = GradCAM(model=model, target_layers=[target_layer])

def get_gradcam(image_path):
    img_pil = Image.open(image_path).convert("RGB").resize((224,224))
    img_arr = np.array(img_pil) / 255.0
    input_tensor = val_transform(image=np.array(img_pil))["image"].unsqueeze(0)
    
    grayscale_cam = cam(input_tensor=input_tensor)[0]
    visualization = show_cam_on_image(img_arr, grayscale_cam, use_rgb=True)
    return visualization   # Returns overlay image — display or save this

# Save Grad-CAM overlay
result = get_gradcam("test_leaf.jpg")
Image.fromarray(result).save("gradcam_output.jpg")`
      }
    ]
  },
  {
    id: 8,
    phase: "Phase 8",
    title: "Export & Deploy",
    icon: "🚀",
    color: "#7b3f00",
    bg: "#fdf0e0",
    border: "#e07b20",
    steps: [
      {
        step: "8.1",
        title: "Export to ONNX and TFLite",
        tag: "EXPORT",
        tagColor: "#7b3f00",
        code: `# Export to ONNX (universal format)
import torch.onnx
dummy_input = torch.randn(1, 3, 224, 224).to(device)
torch.onnx.export(model, dummy_input, "sanjeevani_model.onnx",
                  input_names=["image"], output_names=["predictions"],
                  dynamic_axes={"image": {0: "batch"}})

# Convert ONNX to TFLite (for mobile)
# pip install onnx-tf tensorflow
import onnx
from onnx_tf.backend import prepare
import tensorflow as tf

onnx_model = onnx.load("sanjeevani_model.onnx")
tf_rep = prepare(onnx_model)
tf_rep.export_graph("sanjeevani_tf_model")

# Quantize for mobile (reduces size ~4x)
converter = tf.lite.TFLiteConverter.from_saved_model("sanjeevani_tf_model")
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()
with open("sanjeevani_model.tflite", "wb") as f:
    f.write(tflite_model)
print(f"TFLite model size: {len(tflite_model)/1024/1024:.2f} MB")`,
        note: "Target model size after quantization: < 20 MB for smooth mobile performance."
      },
      {
        step: "8.2",
        title: "FastAPI Backend — Serve the Model",
        tag: "BACKEND",
        tagColor: "#1a3a6b",
        code: `# pip install fastapi uvicorn pillow torch
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import torch, io
from PIL import Image
import numpy as np

app = FastAPI()
model.load_state_dict(torch.load("best_model_final.pth", map_location="cpu"))
model.eval()
class_names = train_dataset.classes   # Load from saved file

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    img_bytes = await file.read()
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    tensor = val_transform(image=np.array(img))["image"].unsqueeze(0)
    
    with torch.no_grad():
        output = model(tensor)
        probs = torch.softmax(output, dim=1)[0]
        top5_probs, top5_idx = probs.topk(5)
    
    predictions = [
        {"species": class_names[idx.item()], "confidence": round(prob.item()*100, 2)}
        for prob, idx in zip(top5_probs, top5_idx)
    ]
    return JSONResponse({
        "top_prediction": predictions[0],
        "top5": predictions,
        "low_confidence": predictions[0]["confidence"] < 70
    })

# Run: uvicorn api:app --host 0.0.0.0 --port 8000`
      }
    ]
  }
];

const toolsData = [
  { tool: "Python 3.10+", purpose: "Core language", install: "Already installed" },
  { tool: "PyTorch 2.x", purpose: "Model training", install: "pip install torch torchvision" },
  { tool: "Albumentations", purpose: "Fast augmentation", install: "pip install albumentations" },
  { tool: "timm", purpose: "Model zoo", install: "pip install timm" },
  { tool: "grad-cam", purpose: "Explainability", install: "pip install grad-cam" },
  { tool: "rembg", purpose: "Background removal", install: "pip install rembg" },
  { tool: "imagehash", purpose: "Duplicate detection", install: "pip install imagehash" },
  { tool: "Albumentations", purpose: "Augmentation pipeline", install: "pip install albumentations" },
  { tool: "scikit-learn", purpose: "Metrics + splitting", install: "pip install scikit-learn" },
  { tool: "FastAPI", purpose: "Backend API", install: "pip install fastapi uvicorn" },
  { tool: "Label Studio", purpose: "Manual labelling", install: "pip install label-studio" },
  { tool: "Roboflow", purpose: "Cloud labelling + split", install: "Web app (free tier)" },
];

export default function SanjeevaniPipeline() {
  const [activePhase, setActivePhase] = useState(1);
  const [activeStep, setActiveStep] = useState(null);
  const [showTools, setShowTools] = useState(false);

  const currentPhase = phases.find(p => p.id === activePhase);

  return (
    <div style={{
      fontFamily: "'Segoe UI', system-ui, sans-serif",
      background: "linear-gradient(135deg, #0a1628 0%, #0d2137 50%, #0a1628 100%)",
      minHeight: "100vh",
      color: "#e8edf5",
      padding: "0"
    }}>
      {/* Header */}
      <div style={{
        background: "linear-gradient(90deg, #0d3d2a 0%, #0a2540 50%, #1a0d3d 100%)",
        borderBottom: "1px solid #2d5a3d",
        padding: "20px 32px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 12
      }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: 28 }}>🌿</span>
            <span style={{ fontSize: 22, fontWeight: 800, letterSpacing: 1, color: "#5dd68c" }}>SANJEEVANI SCAN</span>
          </div>
          <div style={{ fontSize: 12, color: "#8fa8b8", marginTop: 2, letterSpacing: 2 }}>
            MODEL TRAINING PIPELINE — STEP BY STEP GUIDE
          </div>
        </div>
        <button
          onClick={() => setShowTools(!showTools)}
          style={{
            background: showTools ? "#2d9e5f" : "transparent",
            border: "1px solid #2d9e5f",
            color: showTools ? "#fff" : "#5dd68c",
            padding: "8px 18px",
            borderRadius: 6,
            cursor: "pointer",
            fontSize: 13,
            fontWeight: 600
          }}
        >
          🛠 {showTools ? "Hide" : "Show"} All Tools
        </button>
      </div>

      {/* Tools Panel */}
      {showTools && (
        <div style={{ background: "#0a1e14", borderBottom: "1px solid #1a4d30", padding: "20px 32px" }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: "#5dd68c", marginBottom: 14, letterSpacing: 1 }}>
            🛠 COMPLETE TOOLKIT FOR THIS PROJECT
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 10 }}>
            {toolsData.map((t, i) => (
              <div key={i} style={{
                background: "#0f2d1e",
                border: "1px solid #1a4d30",
                borderRadius: 8,
                padding: "10px 14px",
                display: "flex",
                flexDirection: "column",
                gap: 2
              }}>
                <span style={{ fontWeight: 700, color: "#5dd68c", fontSize: 13 }}>{t.tool}</span>
                <span style={{ color: "#8fa8b8", fontSize: 12 }}>{t.purpose}</span>
                <span style={{ color: "#4a90a4", fontSize: 11, fontFamily: "monospace", marginTop: 2 }}>{t.install}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Phase Nav */}
      <div style={{
        padding: "16px 32px",
        background: "#0b1e2d",
        borderBottom: "1px solid #1a3a4d",
        display: "flex",
        gap: 8,
        overflowX: "auto",
        flexWrap: "wrap"
      }}>
        {phases.map(p => (
          <button
            key={p.id}
            onClick={() => { setActivePhase(p.id); setActiveStep(null); }}
            style={{
              padding: "8px 16px",
              borderRadius: 8,
              border: activePhase === p.id ? `2px solid ${p.border}` : "2px solid transparent",
              background: activePhase === p.id ? p.bg + "33" : "#0d2137",
              color: activePhase === p.id ? p.border : "#7a9ab5",
              cursor: "pointer",
              fontSize: 12,
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              gap: 6,
              whiteSpace: "nowrap",
              transition: "all 0.2s"
            }}
          >
            <span>{p.icon}</span>
            <span>{p.phase}</span>
            <span style={{ fontWeight: 400 }}>— {p.title}</span>
          </button>
        ))}
      </div>

      {/* Main Content */}
      <div style={{ maxWidth: 960, margin: "0 auto", padding: "28px 24px" }}>
        {/* Phase Header */}
        <div style={{
          background: `linear-gradient(135deg, ${currentPhase.color}22, ${currentPhase.color}11)`,
          border: `1px solid ${currentPhase.border}`,
          borderRadius: 14,
          padding: "22px 28px",
          marginBottom: 28,
          display: "flex",
          alignItems: "center",
          gap: 16
        }}>
          <span style={{ fontSize: 44 }}>{currentPhase.icon}</span>
          <div>
            <div style={{ fontSize: 12, color: currentPhase.border, fontWeight: 700, letterSpacing: 2 }}>
              {currentPhase.phase}
            </div>
            <div style={{ fontSize: 26, fontWeight: 800, color: "#e8edf5" }}>{currentPhase.title}</div>
            <div style={{ fontSize: 13, color: "#8fa8b8", marginTop: 4 }}>
              {currentPhase.steps.length} step{currentPhase.steps.length !== 1 ? "s" : ""} in this phase
            </div>
          </div>
        </div>

        {/* Steps */}
        {currentPhase.steps.map((step, si) => {
          const stepKey = `${activePhase}-${si}`;
          const isOpen = activeStep === stepKey;
          return (
            <div key={si} style={{
              background: "#0b1e2d",
              border: `1px solid ${isOpen ? currentPhase.border : "#1a3a4d"}`,
              borderRadius: 12,
              marginBottom: 14,
              overflow: "hidden",
              transition: "border-color 0.2s"
            }}>
              {/* Step Header */}
              <div
                onClick={() => setActiveStep(isOpen ? null : stepKey)}
                style={{
                  padding: "16px 20px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  background: isOpen ? `${currentPhase.color}18` : "transparent"
                }}
              >
                <div style={{
                  background: currentPhase.border,
                  color: "#fff",
                  borderRadius: 6,
                  padding: "4px 10px",
                  fontSize: 12,
                  fontWeight: 800,
                  fontFamily: "monospace",
                  flexShrink: 0
                }}>
                  {step.step}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 15, color: "#e8edf5" }}>{step.title}</div>
                </div>
                <span style={{
                  background: step.tagColor + "33",
                  color: step.tagColor,
                  border: `1px solid ${step.tagColor}66`,
                  borderRadius: 4,
                  padding: "2px 8px",
                  fontSize: 10,
                  fontWeight: 800,
                  letterSpacing: 1
                }}>
                  {step.tag}
                </span>
                <span style={{ color: currentPhase.border, fontSize: 18, flexShrink: 0 }}>
                  {isOpen ? "▲" : "▼"}
                </span>
              </div>

              {/* Step Body */}
              {isOpen && (
                <div style={{ padding: "0 20px 20px 20px", borderTop: `1px solid ${currentPhase.border}44` }}>
                  {step.content && (
                    <p style={{ color: "#a8c0d6", fontSize: 14, marginTop: 16, marginBottom: 12 }}>
                      {step.content}
                    </p>
                  )}
                  {step.items && (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 14 }}>
                      {step.items.map((item, ii) => (
                        <div key={ii} style={{
                          background: "#0d2137",
                          border: "1px solid #1a3a4d",
                          borderRadius: 8,
                          padding: "10px 14px",
                          display: "flex",
                          gap: 12,
                          alignItems: "flex-start"
                        }}>
                          <span style={{ color: currentPhase.border, fontSize: 16, flexShrink: 0, marginTop: 1 }}>▸</span>
                          <div>
                            <span style={{ fontWeight: 700, color: "#c8dde8", fontSize: 13 }}>{item.label}</span>
                            <span style={{ color: "#7a9ab5", fontSize: 13 }}> — {item.detail}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {step.code && (
                    <div style={{
                      background: "#060f18",
                      border: "1px solid #1a3a4d",
                      borderRadius: 10,
                      padding: "16px 18px",
                      overflowX: "auto",
                      marginBottom: step.note ? 12 : 0
                    }}>
                      <pre style={{
                        fontFamily: "'Courier New', Consolas, monospace",
                        fontSize: 12,
                        color: "#a8d8a8",
                        margin: 0,
                        lineHeight: 1.7,
                        whiteSpace: "pre"
                      }}>
                        {step.code.trim()}
                      </pre>
                    </div>
                  )}
                  {step.note && (
                    <div style={{
                      background: "#1a2d0a",
                      border: `1px solid ${currentPhase.border}66`,
                      borderLeft: `4px solid ${currentPhase.border}`,
                      borderRadius: "0 8px 8px 0",
                      padding: "10px 14px",
                      marginTop: 10
                    }}>
                      <span style={{ color: "#5dd68c", fontWeight: 700, fontSize: 12 }}>💡 NOTE:  </span>
                      <span style={{ color: "#a8c8a8", fontSize: 13 }}>{step.note}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Progress Footer */}
      <div style={{
        background: "#060f18",
        borderTop: "1px solid #1a3a4d",
        padding: "14px 32px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: 10
      }}>
        <div style={{ fontSize: 12, color: "#4a7090" }}>
          Total Steps Across All Phases: {phases.reduce((s, p) => s + p.steps.length, 0)}
        </div>
        <div style={{ display: "flex", gap: 16 }}>
          {phases.map(p => (
            <div key={p.id} style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <div style={{
                width: 8, height: 8, borderRadius: "50%",
                background: activePhase === p.id ? p.border : "#1a3a4d"
              }} />
              <span style={{ fontSize: 11, color: activePhase === p.id ? p.border : "#4a7090" }}>
                {p.phase}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
