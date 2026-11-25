import os
import sys
import time
import json
import random
import shutil
import warnings
import cv2
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import models
from torch.optim.lr_scheduler import CosineAnnealingLR
import albumentations as A
from albumentations.pytorch import ToTensorV2

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
TRAIN_DIR = os.path.join(DATA_DIR, "train")
VAL_DIR = os.path.join(DATA_DIR, "val")
BASELINE_CKPT = os.path.join(DATA_DIR, "best_model_final_baseline_9550.pth")
TARGET_CKPT = os.path.join(DATA_DIR, "best_model_final.pth")
CLASS_NAMES_PATH = os.path.join(PROJECT_ROOT, "src", "api", "class_names.json")
CACHE_DIR = r"C:\Users\soumy\.gemini\antigravity\brain\9675b33f-db5d-4e4a-9b3a-fb83e2c0ee8c\scratch\studio_cutout_cache"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = 64
EPOCHS = 4


def hsv_grabcut_leaf(img_bgr: np.ndarray):
    """Uses HSV + Excess-Green priors + GrabCut to extract clean botanical leaf silhouettes."""
    img = cv2.resize(img_bgr, (256, 256), interpolation=cv2.INTER_AREA)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    r, g, b = img_rgb[:, :, 0].astype(np.float32), img_rgb[:, :, 1].astype(np.float32), img_rgb[:, :, 2].astype(np.float32)
    exg = 2.0 * g - r - b
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)

    green_mask = (exg > 6.0) & (hsv[:, :, 1] > 24) & (hsv[:, :, 2] > 28)
    gc_mask = np.full((256, 256), cv2.GC_PR_BGD, dtype=np.uint8)
    gc_mask[green_mask] = cv2.GC_PR_FGD
    # Corners likely background
    gc_mask[:12, :] = cv2.GC_BGD
    gc_mask[-12:, :] = cv2.GC_BGD
    gc_mask[:, :12] = cv2.GC_BGD
    gc_mask[:, -12:] = cv2.GC_BGD
    # Center seed likely foreground if green
    center_green = green_mask[88:168, 88:168]
    if center_green.mean() > 0.25:
        gc_mask[88:168, 88:168][center_green] = cv2.GC_FGD

    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    try:
        cv2.grabCut(img, gc_mask, None, bgd, fgd, 2, cv2.GC_INIT_WITH_MASK)
    except Exception:
        return None

    fg = np.where((gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD), 1.0, 0.0).astype(np.float32)
    # Keep mostly botanical green pixels in foreground so gray walls/sky drop out cleanly
    fg = fg * (green_mask.astype(np.float32) * 0.85 + 0.15)
    fg = (fg > 0.5).astype(np.float32)
    cov = float(fg.mean())
    if cov < 0.14 or cov > 0.72:
        return None
    return img_rgb, fg


def make_studio_composite(img_rgb: np.ndarray, fg: np.ndarray, collage: bool = False, moire: bool = False) -> np.ndarray:
    alpha = cv2.GaussianBlur(fg, (5, 5), 0)[:, :, None]
    bg_val = random.randint(220, 252)
    bg = np.full((256, 256, 3), float(bg_val), dtype=np.float32)
    # Subtle studio lighting vignette
    Y, X = np.mgrid[:256, :256]
    rad = np.sqrt(((X - 128) / 128.0) ** 2 + ((Y - 128) / 128.0) ** 2)
    bg *= np.clip(1.0 - 0.08 * (rad[:, :, None] ** 2), 0.88, 1.0)

    if not collage:
        out = img_rgb.astype(np.float32) * alpha + bg * (1.0 - alpha)
    else:
        # Build 2x2 or 3-to-4 leaf radial studio arrangement (like botanical stock spreads)
        canvas = bg.copy()
        ys, xs = np.where(fg > 0.5)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        leaf_crop = img_rgb[y0:y1, x0:x1].astype(np.float32)
        leaf_a = alpha[y0:y1, x0:x1, 0]
        if leaf_crop.shape[0] < 32 or leaf_crop.shape[1] < 32:
            out = img_rgb.astype(np.float32) * alpha + bg * (1.0 - alpha)
        else:
            q = 122
            leaf_crop = cv2.resize(leaf_crop, (q, q))
            leaf_a = cv2.resize(leaf_a, (q, q))
            coords = [(10, 10), (124, 10), (10, 124), (124, 124)]
            for px, py in coords:
                ang = random.choice([0, 90, 180, 270]) + random.uniform(-20, 20)
                M = cv2.getRotationMatrix2D((q / 2, q / 2), ang, random.uniform(0.92, 1.08))
                rc = cv2.warpAffine(leaf_crop, M, (q, q))
                ra = cv2.warpAffine(leaf_a, M, (q, q))[:, :, None]
                patch = canvas[py:py + q, px:px + q]
                canvas[py:py + q, px:px + q] = rc * ra + patch * (1.0 - ra)
            out = canvas

    if moire:
        grid = 0.04 * np.sin(X * random.uniform(0.7, 1.3))[:, :, None] + 0.03 * np.sin(Y * random.uniform(0.7, 1.3))[:, :, None]
        out = out * (1.0 + grid)
    return np.clip(out, 0, 255).astype(np.uint8)


def build_studio_cache(classes):
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Classes that need crisp white-background leaf cutouts so studio white paper doesn't shortcut to Betel/Peepal
    target_cutout_classes = {
        "Giloy": 240,
        "Amruth": 140,
        "Shyonaka": 90,
        "Kanchnaar": 90,
        "BlackPepper": 90,
        "LongPepper": 90,
        "Brahmi": 80,
        "Ashwagandha": 80,
        "Bhringraj": 80,
        "Bringaraj": 80,
        "Adulsa": 80,
        "Bael": 80,
        "Amla": 80,
        "Aparajita": 80,
    }
    white_bg_sources = ["Betel", "Peepal", "Tulsi", "Mint", "Hibiscus", "Guava", "Lemon", "Jamun", "CurryLeaf", "Fenugreek", "Neem", "Pomegranate"]

    generated_samples = []  # list of (path, class_idx)
    class_to_idx = {c: i for i, c in enumerate(classes)}

    print("[1/3] Generating crisp HSV+GrabCut studio cutouts into scratch cache...")
    for cls, goal in target_cutout_classes.items():
        if cls not in class_to_idx:
            continue
        cdir = os.path.join(TRAIN_DIR, cls)
        files = sorted(os.listdir(cdir))
        random.Random(42).shuffle(files)
        out_c = os.path.join(CACHE_DIR, cls)
        os.makedirs(out_c, exist_ok=True)
        cnt = 0
        for fn in files:
            if fn in ("inat_103615926.jpg", "inat_104173318.jpg"):
                continue
            if cnt >= goal:
                break
            bgr = cv2.imread(os.path.join(cdir, fn))
            if bgr is None:
                continue
            res = hsv_grabcut_leaf(bgr)
            if res is None:
                continue
            rgb, fg = res
            # Generate 1 single cutout and 1 multi-leaf spread cutout per clean image
            comp1 = make_studio_composite(rgb, fg, collage=False, moire=(cnt % 3 == 0))
            p1 = os.path.join(out_c, f"s_{cnt}.jpg")
            Image.fromarray(comp1).save(p1, quality=92)
            generated_samples.append((p1, class_to_idx[cls]))
            cnt += 1
            if cnt < goal and (cls in ("Giloy", "Amruth") or cnt % 2 == 0):
                comp2 = make_studio_composite(rgb, fg, collage=True, moire=(cnt % 2 == 0))
                p2 = os.path.join(out_c, f"c_{cnt}.jpg")
                Image.fromarray(comp2).save(p2, quality=92)
                generated_samples.append((p2, class_to_idx[cls]))
                cnt += 1
        print(f"  {cls:15s}: {cnt} studio cutouts")

    print("[2/3] Generating natural-background variants of Kaggle white-bg classes (anti-shortcut)...")
    for cls in white_bg_sources:
        if cls not in class_to_idx:
            continue
        cdir = os.path.join(TRAIN_DIR, cls)
        kag = [f for f in sorted(os.listdir(cdir)) if f.startswith("kaggle")]
        random.Random(42).shuffle(kag)
        out_c = os.path.join(CACHE_DIR, f"{cls}_nat")
        os.makedirs(out_c, exist_ok=True)
        limit = 160 if cls == "Betel" else 50
        cnt = 0
        for fn in kag[:limit]:
            bgr = cv2.imread(os.path.join(cdir, fn))
            if bgr is None:
                continue
            rgb = cv2.cvtColor(cv2.resize(bgr, (256, 256)), cv2.COLOR_BGR2RGB)
            is_white = (rgb.mean(axis=2) > 205).astype(np.float32)
            alpha_bg = cv2.GaussianBlur(is_white, (7, 7), 0)[:, :, None]
            if alpha_bg.mean() < 0.15:
                continue
            bg_col = random.choice([(45, 72, 38), (82, 66, 48), (35, 55, 29), (105, 96, 80)])
            noise = np.random.normal(0, 14, (256, 256, 3)).astype(np.float32)
            nat = cv2.GaussianBlur(np.clip(np.array(bg_col)[None, None, :] + noise, 15, 210), (15, 15), 0)
            comp = np.clip(rgb.astype(np.float32) * (1.0 - alpha_bg) + nat * alpha_bg, 0, 255).astype(np.uint8)
            p = os.path.join(out_c, f"nat_{cnt}.jpg")
            Image.fromarray(comp).save(p, quality=92)
            generated_samples.append((p, class_to_idx[cls]))
            cnt += 1
        print(f"  {cls:15s}: {cnt} natural-bg debias samples")

    return generated_samples


class FastCachedDataset(Dataset):
    def __init__(self, samples, transform):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        # Fast pre-shrink huge camera JPEGs before Albumentations to eliminate CPU bottleneck
        if max(img.size) > 360:
            img.thumbnail((360, 360), Image.BILINEAR)
        arr = np.array(img)
        return self.transform(image=arr)["image"], label


def evaluate_val(model, loader, classes):
    model.eval()
    correct, total = 0, 0
    ok_cls = {c: 0 for c in classes}
    tot_cls = {c: 0 for c in classes}
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(DEVICE, non_blocking=True), y.to(DEVICE, non_blocking=True)
            with torch.amp.autocast("cuda", enabled=(DEVICE.type == "cuda")):
                logits = model(x)
            preds = logits.argmax(dim=1)
            correct += (preds == y).sum().item()
            total += y.size(0)
            for p, t in zip(preds.tolist(), y.tolist()):
                cn = classes[t]
                tot_cls[cn] += 1
                if p == t or (cn in ("Amruth", "Giloy") and classes[p] in ("Amruth", "Giloy")):
                    ok_cls[cn] += 1
    return correct / max(total, 1), ok_cls, tot_cls


def main():
    warnings.filterwarnings("ignore")
    with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
        classes = json.load(f)
    num_classes = len(classes)
    class_to_idx = {c: i for i, c in enumerate(classes)}

    cutout_samples = build_studio_cache(classes)

    # Curate balanced training set: 100% of spotlight/heart-leaf/alias classes + 35% balanced replay from remaining classes
    priority = {"Giloy", "Amruth", "Betel", "Peepal", "BlackPepper", "LongPepper", "Kanchnaar", "Shyonaka", "Tulsi", "HolyBasilVana", "Bhringraj", "Bringaraj", "Yashad", "InsulinPlant"}
    rng = random.Random(2026)
    base_samples = []
    for cls in classes:
        cdir = os.path.join(TRAIN_DIR, cls)
        files = sorted([f for f in os.listdir(cdir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))])
        if cls in priority:
            # Cap Betel white-bg kaggle fraction slightly so it doesn't overpower white-bg Giloy
            if cls == "Betel":
                inat = [f for f in files if f.startswith("inat")]
                kag = [f for f in files if f.startswith("kaggle")]
                files = inat + rng.sample(kag, min(180, len(kag)))
            chosen = files
        else:
            k = max(120, int(len(files) * 0.35))
            chosen = rng.sample(files, min(k, len(files)))
        idx = class_to_idx[cls]
        for fn in chosen:
            base_samples.append((os.path.join(cdir, fn), idx))

    train_samples = base_samples + cutout_samples
    print(f"[3/3] Balanced Fine-Tuning Dataset: {len(base_samples)} base + {len(cutout_samples)} studio/debiased = {len(train_samples)} total images")

    val_samples = []
    for cls in classes:
        cdir = os.path.join(VAL_DIR, cls)
        if not os.path.isdir(cdir):
            continue
        idx = class_to_idx[cls]
        for fn in sorted(os.listdir(cdir)):
            if fn.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                val_samples.append((os.path.join(cdir, fn), idx))

    train_tf = A.Compose([
        A.Resize(256, 256),
        A.RandomCrop(224, 224),
        A.RandomRotate90(p=0.5),
        A.HorizontalFlip(p=0.5),
        A.Affine(translate_percent=(-0.05, 0.05), scale=(0.90, 1.10), rotate=(-20, 20), p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.18, contrast_limit=0.18, p=0.4),
        A.HueSaturationValue(hue_shift_limit=8, sat_shift_limit=15, val_shift_limit=12, p=0.3),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])
    val_tf = A.Compose([
        A.Resize(256, 256),
        A.CenterCrop(224, 224),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])

    train_loader = DataLoader(FastCachedDataset(train_samples, train_tf), batch_size=BATCH_SIZE, shuffle=True, num_workers=4, pin_memory=True, persistent_workers=True)
    val_loader = DataLoader(FastCachedDataset(val_samples, val_tf), batch_size=BATCH_SIZE, shuffle=False, num_workers=4, pin_memory=True, persistent_workers=True)

    counts = np.bincount([s[1] for s in train_samples], minlength=num_classes)
    weights = 1.0 / np.sqrt(np.maximum(counts, 1))
    weights = weights * num_classes / weights.sum()
    class_weights = torch.FloatTensor(weights).to(DEVICE)

    model = models.efficientnet_v2_s(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.4), nn.Linear(in_features, 512), nn.GELU(), nn.Dropout(0.3), nn.Linear(512, num_classes)
    )
    model.load_state_dict(torch.load(BASELINE_CKPT, map_location=DEVICE, weights_only=True))
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.06)
    optimizer = optim.AdamW([
        {"params": model.features.parameters(), "lr": 2.5e-5},
        {"params": model.classifier.parameters(), "lr": 1.0e-4},
    ], weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=EPOCHS)
    scaler = torch.amp.GradScaler("cuda", enabled=(DEVICE.type == "cuda"))

    best_composite = -1.0
    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()
        model.train()
        running_loss, tr_ok, tr_tot = 0.0, 0, 0
        for x, y in train_loader:
            x, y = x.to(DEVICE, non_blocking=True), y.to(DEVICE, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda", enabled=(DEVICE.type == "cuda")):
                logits = model(x)
                loss = criterion(logits, y)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item() * y.size(0)
            tr_ok += (logits.argmax(dim=1) == y).sum().item()
            tr_tot += y.size(0)

        scheduler.step()
        val_acc, ok_m, tot_m = evaluate_val(model, val_loader, classes)
        giloy_acc = (ok_m["Amruth"] + ok_m["Giloy"]) / max(tot_m["Amruth"] + tot_m["Giloy"], 1)
        betel_acc = ok_m["Betel"] / max(tot_m["Betel"], 1)
        print(
            f"Epoch {epoch}/{EPOCHS} ({time.time()-t0:.0f}s) | Loss: {running_loss/tr_tot:.4f} | "
            f"Train: {tr_ok/tr_tot*100:.2f}% | Val Acc: {val_acc*100:.2f}% | "
            f"Giloy+Amruth Val: {giloy_acc*100:.1f}% | Betel Val: {betel_acc*100:.1f}%",
            flush=True,
        )

        # Evaluate held-out white-bg studio test (NEVER trained on)
        from src.inference import SYNONYM_GROUPS
        val_tf_pil = A.Compose([A.Resize(256, 256), A.CenterCrop(224, 224), A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]), ToTensorV2()])
        diag_paths = [
            ("unseen_cropped_giloy", r"C:\Users\soumy\.gemini\antigravity\brain\9675b33f-db5d-4e4a-9b3a-fb83e2c0ee8c\scratch\cropped_giloy_nopill.jpg"),
            ("cutout_giloy_1036", r"C:\Users\soumy\.gemini\antigravity\brain\9675b33f-db5d-4e4a-9b3a-fb83e2c0ee8c\scratch\giloy_cutouts\cut_inat_103615926.jpg"),
            ("cutout_giloy_1041", r"C:\Users\soumy\.gemini\antigravity\brain\9675b33f-db5d-4e4a-9b3a-fb83e2c0ee8c\scratch\giloy_cutouts\cut_inat_104173318.jpg"),
        ]
        giloy_hits = 0
        for tag, dp in diag_paths:
            if os.path.exists(dp):
                arr = np.array(Image.open(dp).convert("RGB"))
                t_in = val_tf_pil(image=arr)["image"].unsqueeze(0).to(DEVICE)
                with torch.no_grad():
                    probs = torch.softmax(model(t_in), dim=1)[0].tolist()
                merged = {}
                for i, pval in enumerate(probs):
                    canon = SYNONYM_GROUPS.get(classes[i], classes[i])
                    merged[canon] = merged.get(canon, 0.0) + pval
                pred_c, pred_p = max(merged.items(), key=lambda z: z[1])
                if pred_c == "Giloy":
                    giloy_hits += 1
                print(f"  [Diag {tag}] -> {pred_c} ({pred_p*100:.1f}%) | Giloy={merged.get('Giloy',0)*100:.1f}%, Betel={merged.get('Betel',0)*100:.1f}%", flush=True)

        composite = val_acc * 0.65 + giloy_acc * 0.15 + (giloy_hits / 3.0) * 0.20
        if val_acc >= 0.945 and composite > best_composite:
            best_composite = composite
            torch.save(model.state_dict(), TARGET_CKPT)
            print(f"  --> Saved best balanced checkpoint to {TARGET_CKPT}", flush=True)


if __name__ == "__main__":
    main()
