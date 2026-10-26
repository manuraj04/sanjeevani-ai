# Objective 1 — Dataset Engineering
## Sanjeevani Scan | Medicinal Plant Identification System

> **Goal:** Curate a clean, verified, balanced dataset of **12,000–18,000 leaf images** across **60–80 Indian Ayurvedic medicinal species**, with every label cross-checked against IMPPAT botanical records.

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Target Species List](#2-target-species-list)
3. [Data Collection](#3-data-collection)
4. [Folder Structure](#4-folder-structure)
5. [Label Verification Against IMPPAT](#5-label-verification-against-imppat)
6. [Image Cleaning Pipeline](#6-image-cleaning-pipeline)
7. [Master CSV — Source of Truth](#7-master-csv--source-of-truth)
8. [Class Balance Check](#8-class-balance-check)
9. [Dataset Split](#9-dataset-split)
10. [Final Validation Checklist](#10-final-validation-checklist)
11. [Progress Tracker](#11-progress-tracker)

---

## 1. Environment Setup

```bash
# Create a dedicated conda environment
conda create -n sanjeevani python=3.10 -y
conda activate sanjeevani

# Core libraries
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install albumentations opencv-python pillow imagehash pandas numpy scikit-learn
pip install rembg requests tqdm kaggle
```

**Kaggle API setup** (one-time):
```bash
# Place your kaggle.json in ~/.kaggle/
mkdir -p ~/.kaggle
cp kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

---

## 2. Target Species List

These 70 species are the core targets. Each must have ≥150 verified images before training.  
Priority tier tells you where to focus collection effort first.

| # | Common Name | Botanical Name | Ayurvedic Name | Priority |
|---|-------------|----------------|----------------|----------|
| 1 | Tulsi | *Ocimum tenuiflorum* | Tulasi | HIGH |
| 2 | Neem | *Azadirachta indica* | Nimba | HIGH |
| 3 | Brahmi | *Bacopa monnieri* | Brahmi | HIGH |
| 4 | Ashwagandha | *Withania somnifera* | Ashwagandha | HIGH |
| 5 | Aloe Vera | *Aloe barbadensis* | Kumari | HIGH |
| 6 | Turmeric | *Curcuma longa* | Haridra | HIGH |
| 7 | Ginger | *Zingiber officinale* | Shunti | HIGH |
| 8 | Moringa | *Moringa oleifera* | Shigru | HIGH |
| 9 | Curry Leaf | *Murraya koenigii* | Surabhi | HIGH |
| 10 | Betel | *Piper betle* | Nagavalli | HIGH |
| 11 | Mint | *Mentha spicata* | Pudina | HIGH |
| 12 | Lemongrass | *Cymbopogon citratus* | Bhustrina | HIGH |
| 13 | Indian Beech | *Millettia pinnata* | Karanja | HIGH |
| 14 | Guava | *Psidium guajava* | Amrud | MEDIUM |
| 15 | Papaya | *Carica papaya* | Erandakarkati | MEDIUM |
| 16 | Amla | *Phyllanthus emblica* | Amalaki | HIGH |
| 17 | Bael | *Aegle marmelos* | Bilva | HIGH |
| 18 | Giloy | *Tinospora cordifolia* | Guduchi | HIGH |
| 19 | Shatavari | *Asparagus racemosus* | Shatavari | HIGH |
| 20 | Bhringraj | *Eclipta prostrata* | Bhringaraja | MEDIUM |
| 21 | Punarnava | *Boerhavia diffusa* | Punarnava | MEDIUM |
| 22 | Gotu Kola | *Centella asiatica* | Mandukaparni | HIGH |
| 23 | Karela | *Momordica charantia* | Karavella | MEDIUM |
| 24 | Jamun | *Syzygium cumini* | Jambu | MEDIUM |
| 25 | Hibiscus | *Hibiscus rosa-sinensis* | Japa | MEDIUM |
| 26 | Drumstick | *Moringa oleifera* (leaf) | Shigru Patra | HIGH |
| 27 | Indian Pennywort | *Hydrocotyle asiatica* | Brahma Manduki | MEDIUM |
| 28 | Kalmegh | *Andrographis paniculata* | Kalamegh | HIGH |
| 29 | Castor | *Ricinus communis* | Eranda | MEDIUM |
| 30 | Mulethi | *Glycyrrhiza glabra* | Yastimadhu | MEDIUM |
| 31 | Karpuravalli | *Coleus aromaticus* | Karpuravalli | MEDIUM |
| 32 | Insulin Plant | *Costus igneus* | Keukand | MEDIUM |
| 33 | Snake Plant | *Sansevieria trifasciata* | — | LOW |
| 34 | Peepal | *Ficus religiosa* | Ashvattha | MEDIUM |
| 35 | Banyan | *Ficus benghalensis* | Vata | MEDIUM |
| 36 | Aparajita | *Clitoria ternatea* | Aparajita | MEDIUM |
| 37 | Patharchatta | *Bryophyllum pinnatum* | Parnabeeja | MEDIUM |
| 38 | Adulsa | *Justicia adhatoda* | Vasa | HIGH |
| 39 | Bringaraj | *Eclipta alba* | Bhringaraja | MEDIUM |
| 40 | Holy Basil (Vana) | *Ocimum gratissimum* | Vana Tulasi | MEDIUM |
| 41 | Lemon | *Citrus limon* | Nimbuka | LOW |
| 42 | Amruth | *Tinospora sinensis* | Amruth | MEDIUM |
| 43 | Chamomile | *Matricaria chamomilla* | Babunah | LOW |
| 44 | Palash | *Butea monosperma* | Palasha | MEDIUM |
| 45 | Haritaki | *Terminalia chebula* | Haritaki | HIGH |
| 46 | Vibhitaki | *Terminalia bellirica* | Vibhitaka | MEDIUM |
| 47 | Arjuna | *Terminalia arjuna* | Arjuna | MEDIUM |
| 48 | Gudmar | *Gymnema sylvestre* | Madhunashini | HIGH |
| 49 | Sarpagandha | *Rauvolfia serpentina* | Sarpagandha | MEDIUM |
| 50 | Vacha | *Acorus calamus* | Vacha | MEDIUM |
| 51 | Chitraka | *Plumbago zeylanica* | Chitraka | MEDIUM |
| 52 | Kutaja | *Holarrhena pubescens* | Kutaja | MEDIUM |
| 53 | Devadaru | *Cedrus deodara* | Devadaru | LOW |
| 54 | Yashad | *Withania coagulans* | Paneer Doda | LOW |
| 55 | Kanchnaar | *Bauhinia variegata* | Kanchanara | MEDIUM |
| 56 | Shyonaka | *Oroxylum indicum* | Shyonaka | LOW |
| 57 | Agathi | *Sesbania grandiflora* | Agasthya | MEDIUM |
| 58 | Indian Gooseberry | *Emblica officinalis* | Dhatri | HIGH |
| 59 | Betel Nut | *Areca catechu* | Puga | MEDIUM |
| 60 | Black Pepper | *Piper nigrum* | Maricha | HIGH |
| 61 | Long Pepper | *Piper longum* | Pippali | HIGH |
| 62 | Vetiver | *Chrysopogon zizanioides* | Ushira | MEDIUM |
| 63 | Sesame | *Sesamum indicum* | Tila | LOW |
| 64 | Pomegranate | *Punica granatum* | Dadima | MEDIUM |
| 65 | Coriander | *Coriandrum sativum* | Dhanyaka | LOW |
| 66 | Fenugreek | *Trigonella foenum-graecum* | Methi | MEDIUM |
| 67 | Malabar Nut | *Justicia adhatoda* | Vasaka | HIGH |
| 68 | Indian Sarsaparilla | *Hemidesmus indicus* | Anantamul | MEDIUM |
| 69 | Nirgundi | *Vitex negundo* | Nirgundi | HIGH |
| 70 | Clove | *Syzygium aromaticum* | Lavanga | MEDIUM |

> **Note:** Start with all **HIGH** priority species first (28 species). Once each has 200+ images, move to MEDIUM. LOW-priority species are optional — include only if data is easily available.

---

## 3. Data Collection

### 3.1 Source 1 — Kaggle Datasets

Download these datasets directly:

```bash
# Dataset 1: Indian Medicinal Leaves Image Datasets
kaggle datasets download -d aryashah2k/indian-medicinal-leaves-image-datasets
unzip indian-medicinal-leaves-image-datasets.zip -d raw/kaggle_indian/

# Dataset 2: Medicinal Plant Dataset
kaggle datasets download -d vishnuoum/medicinal-plant-dataset-augmented
unzip medicinal-plant-dataset-augmented.zip -d raw/kaggle_medleaf/

# Dataset 3: MedLeaf
kaggle datasets download -d pushpankar/medleaf
unzip medleaf.zip -d raw/kaggle_medleaf2/

# Dataset 4: Ayurvedic Plants
kaggle datasets download -d noumanali1122/medicinal-plants
unzip medicinal-plants.zip -d raw/kaggle_ayurvedic/
```

After extraction, inspect what species are available:
```bash
ls raw/kaggle_indian/
ls raw/kaggle_medleaf/
```

---

### 3.2 Source 2 — iNaturalist API

Pull field-collected images per species. These are messy/real-world — exactly what we need for robustness.

```python
# scripts/collect_inat.py
import requests, os, time
from pathlib import Path

SPECIES_LIST = [
    ("Ocimum tenuiflorum",  "Tulsi"),
    ("Azadirachta indica",  "Neem"),
    ("Bacopa monnieri",     "Brahmi"),
    ("Withania somnifera",  "Ashwagandha"),
    ("Tinospora cordifolia","Giloy"),
    ("Centella asiatica",   "GotoKola"),
    ("Terminalia chebula",  "Haritaki"),
    ("Andrographis paniculata", "Kalmegh"),
    # ... add all 70 species
]

BASE_URL = "https://api.inaturalist.org/v1/observations"
SAVE_DIR = Path("raw/inat")

def fetch_species(taxon_name, folder_name, max_results=200):
    save_path = SAVE_DIR / folder_name
    save_path.mkdir(parents=True, exist_ok=True)

    params = {
        "taxon_name": taxon_name,
        "quality_grade": "research",   # community-verified only
        "photos": "true",
        "per_page": 30,
        "page": 1,
        "order_by": "votes"
    }

    downloaded = 0
    while downloaded < max_results:
        r = requests.get(BASE_URL, params=params, timeout=30)
        if r.status_code != 200:
            print(f"API error for {taxon_name}: {r.status_code}")
            break

        data = r.json()
        results = data.get("results", [])
        if not results:
            break

        for obs in results:
            if downloaded >= max_results:
                break
            photos = obs.get("photos", [])
            for photo in photos[:1]:  # one photo per observation
                url = photo.get("url", "").replace("square", "large")
                if not url:
                    continue
                fname = save_path / f"inat_{obs['id']}.jpg"
                if fname.exists():
                    downloaded += 1
                    continue
                try:
                    img_data = requests.get(url, timeout=15).content
                    with open(fname, "wb") as f:
                        f.write(img_data)
                    downloaded += 1
                    time.sleep(0.3)  # be polite to API
                except Exception as e:
                    print(f"  Download error: {e}")

        params["page"] += 1
        if params["page"] > 10:
            break

    print(f"  {folder_name}: {downloaded} images")

if __name__ == "__main__":
    for botanical, common in SPECIES_LIST:
        print(f"Fetching {common} ({botanical})...")
        fetch_species(botanical, common)
```

```bash
python scripts/collect_inat.py
```

---

### 3.3 Source 3 — PlantNet API (supplementary)

For species where iNaturalist gives < 100 images:

```python
# scripts/collect_plantnet.py
import requests, os

API_KEY   = "YOUR_PLANTNET_API_KEY"   # free at my.plantnet.org
SPECIES_Q = "Bacopa monnieri"
URL       = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}"
# PlantNet is primarily for identification — use their open dataset download
# https://zenodo.org/record/5578578  (PlantNet-300K dataset, 306,146 images)
```

> **Tip:** The PlantNet-300K dataset on Zenodo is open-access. Download it and filter by the botanical names in your species list.

---

### 3.4 Manual Collection (For Rare Species)

For species that have < 80 images across all sources:

- Photograph leaves yourself (30+ images per species minimum)
- Use a plain white/neutral background for at least 50% of shots
- Vary: lighting conditions, angle (top, angled 45°), zoom level, wet/dry leaf, old/young leaf
- Use `scripts/label_manual.py` to log them into the master CSV immediately

```python
# scripts/label_manual.py — quick CLI logger for manual photos
import csv, os, sys
from datetime import datetime

IMG_DIR = sys.argv[1]          # folder of new photos
SPECIES  = sys.argv[2]         # e.g. "Brahmi"
BOTANICAL = sys.argv[3]        # e.g. "Bacopa monnieri"
CSV_FILE = "metadata/master_labels.csv"

rows = []
for f in os.listdir(IMG_DIR):
    if f.lower().endswith(('.jpg','.jpeg','.png')):
        rows.append({
            "filename": f,
            "species_name": SPECIES,
            "botanical_name": BOTANICAL,
            "source": "manual",
            "split": "unassigned",
            "verified": "yes",
            "date_added": datetime.today().strftime('%Y-%m-%d')
        })

with open(CSV_FILE, 'a', newline='') as out:
    writer = csv.DictWriter(out, fieldnames=rows[0].keys())
    writer.writerows(rows)

print(f"Logged {len(rows)} images for {SPECIES}")
```

---

## 4. Folder Structure

Set this up **before** you start downloading anything. Every file must go into the right place from day one.

```
sanjeevani_dataset/
│
├── raw/                          ← Original downloads, NEVER modified
│   ├── kaggle_indian/
│   ├── kaggle_medleaf/
│   ├── kaggle_medleaf2/
│   ├── kaggle_ayurvedic/
│   ├── inat/
│   │   ├── Tulsi/
│   │   ├── Neem/
│   │   └── ...
│   └── manual/
│       ├── Brahmi/
│       └── ...
│
├── processed/                    ← Output of cleaning pipeline
│   ├── train/
│   │   ├── Tulsi/
│   │   ├── Neem/
│   │   └── ...
│   ├── val/
│   │   ├── Tulsi/
│   │   └── ...
│   └── test/
│       ├── Tulsi/
│       └── ...
│
├── metadata/
│   ├── master_labels.csv         ← Single source of truth for all images
│   ├── split_log.csv             ← After train/val/test assignment
│   ├── imppat_species_map.csv    ← IMPPAT verification records
│   └── cleaning_log.csv          ← What was removed and why
│
├── scripts/
│   ├── collect_inat.py
│   ├── collect_plantnet.py
│   ├── label_manual.py
│   ├── clean_images.py
│   ├── verify_labels.py
│   ├── build_master_csv.py
│   └── split_dataset.py
│
└── reports/
    ├── class_distribution.png
    ├── sample_grid.png
    └── dataset_summary.txt
```

Create structure now:
```bash
mkdir -p sanjeevani_dataset/{raw,processed/{train,val,test},metadata,scripts,reports}
cd sanjeevani_dataset
```

---

## 5. Label Verification Against IMPPAT

This is the most important and most skipped step. Kaggle datasets frequently have wrong labels.

### 5.1 Download IMPPAT Reference

```python
# scripts/build_imppat_map.py
# IMPPAT is available at: https://cb.imsc.res.in/imppat/
# Download the "Plants" CSV from their download section
# OR use their API: https://cb.imsc.res.in/imppat/api/

import pandas as pd

# After downloading IMPPAT plant CSV:
imppat = pd.read_csv("metadata/IMPPAT_plants.csv")

# Our target species list
our_species = pd.DataFrame([
    {"common_name": "Tulsi",      "botanical_name": "Ocimum tenuiflorum"},
    {"common_name": "Neem",       "botanical_name": "Azadirachta indica"},
    {"common_name": "Brahmi",     "botanical_name": "Bacopa monnieri"},
    # ... all 70 species
])

# Match against IMPPAT
verified = our_species.merge(
    imppat[["Plant_name", "Botanical_name", "Family"]],
    left_on="botanical_name",
    right_on="Botanical_name",
    how="left"
)
verified["imppat_verified"] = verified["Plant_name"].notna()
verified.to_csv("metadata/imppat_species_map.csv", index=False)

print(f"Verified: {verified['imppat_verified'].sum()} / {len(verified)}")
print("NOT in IMPPAT:")
print(verified[~verified["imppat_verified"]][["common_name","botanical_name"]])
```

### 5.2 Per-Folder Verification Script

For each species folder in your raw downloads, run a visual spot-check:

```python
# scripts/verify_labels.py
import os, random
from PIL import Image
import matplotlib.pyplot as plt

def spot_check(species_folder, species_name, n=16):
    """Show a grid of n random images from this folder for manual verification."""
    all_files = [f for f in os.listdir(species_folder)
                 if f.lower().endswith(('.jpg','.jpeg','.png'))]
    sample = random.sample(all_files, min(n, len(all_files)))

    fig, axes = plt.subplots(4, 4, figsize=(12, 12))
    fig.suptitle(f"Spot Check: {species_name} — {len(all_files)} total images", fontsize=14)
    for ax, fname in zip(axes.flat, sample):
        img = Image.open(os.path.join(species_folder, fname)).convert("RGB")
        ax.imshow(img)
        ax.set_title(fname[:20], fontsize=7)
        ax.axis("off")
    plt.tight_layout()
    plt.savefig(f"reports/spotcheck_{species_name}.png", dpi=80)
    plt.close()
    print(f"Spot check saved: reports/spotcheck_{species_name}.png")

# Run for every species
RAW_DIRS = ["raw/kaggle_indian", "raw/kaggle_medleaf", "raw/inat"]
for raw_dir in RAW_DIRS:
    if not os.path.exists(raw_dir):
        continue
    for species_folder in os.listdir(raw_dir):
        full_path = os.path.join(raw_dir, species_folder)
        if os.path.isdir(full_path):
            spot_check(full_path, species_folder)
```

```bash
python scripts/verify_labels.py
# Open reports/ folder and visually confirm each grid looks correct
```

**What to look for in spot checks:**
- Are all images actually leaves of that species?
- Are there flowers, seeds, full trees, or text labels (cross those out)?
- Are there images from a completely different plant?
- Are images from the same 10-photo batch repeated too many times?

**Action on bad images:** Move to `raw/review/SPECIES_NAME/` — do NOT delete immediately.

---

## 6. Image Cleaning Pipeline

Run this on each raw species folder after spot-checking and labelling.

```python
# scripts/clean_images.py
import os, re
from PIL import Image, ImageStat
import imagehash
import pandas as pd
from pathlib import Path

def clean_folder(folder_path: str, species_name: str, log: list) -> int:
    """
    Cleans one species folder in-place.
    Returns count of images kept.
    """
    folder = Path(folder_path)
    hashes = {}
    kept = 0

    for fpath in sorted(folder.iterdir()):
        if fpath.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp', '.bmp'):
            continue

        reason = None

        # ── Step 1: File integrity ─────────────────────────────────────
        try:
            img = Image.open(fpath).convert("RGB")
        except Exception as e:
            reason = f"corrupt: {e}"

        if reason is None:
            w, h = img.size

            # ── Step 2: Minimum size ───────────────────────────────────
            if w < 64 or h < 64:
                reason = f"too_small: {w}x{h}"

            # ── Step 3: Extreme aspect ratio ───────────────────────────
            elif (w / h) > 6 or (h / w) > 6:
                reason = f"bad_aspect: {w}x{h}"

            # ── Step 4: Nearly blank / overexposed ────────────────────
            else:
                stat = ImageStat.Stat(img)
                mean_brightness = sum(stat.mean) / 3
                std_dev = sum(stat.stddev) / 3
                if mean_brightness > 245:
                    reason = "overexposed"
                elif mean_brightness < 10:
                    reason = "underexposed"
                elif std_dev < 8:
                    reason = "near_blank"

            # ── Step 5: Perceptual duplicate ──────────────────────────
            if reason is None:
                ph = str(imagehash.phash(img, hash_size=16))
                if ph in hashes:
                    reason = f"duplicate_of:{hashes[ph]}"
                else:
                    hashes[ph] = fpath.name

        if reason:
            review_dir = folder.parent.parent / "review" / species_name
            review_dir.mkdir(parents=True, exist_ok=True)
            fpath.rename(review_dir / fpath.name)
            log.append({"file": str(fpath), "species": species_name,
                         "action": "moved_to_review", "reason": reason})
        else:
            # Standardise format to JPEG
            if fpath.suffix.lower() != '.jpg':
                new_path = fpath.with_suffix('.jpg')
                img.save(new_path, "JPEG", quality=92)
                fpath.unlink()
            kept += 1

    return kept


if __name__ == "__main__":
    RAW_ROOT = "raw"
    log = []
    summary = []

    for source_dir in Path(RAW_ROOT).iterdir():
        if not source_dir.is_dir() or source_dir.name == "review":
            continue
        for species_dir in source_dir.iterdir():
            if not species_dir.is_dir():
                continue
            before = sum(1 for f in species_dir.iterdir()
                         if f.suffix.lower() in ('.jpg','.jpeg','.png','.webp','.bmp'))
            after = clean_folder(str(species_dir), species_dir.name, log)
            summary.append({
                "source": source_dir.name,
                "species": species_dir.name,
                "before": before,
                "after": after,
                "removed": before - after
            })
            print(f"  {species_dir.name}: {before} → {after} ({before-after} removed)")

    pd.DataFrame(log).to_csv("metadata/cleaning_log.csv", index=False)
    pd.DataFrame(summary).to_csv("metadata/cleaning_summary.csv", index=False)
    print("\nCleaning complete. Logs saved.")
```

```bash
pip install imagehash
python scripts/clean_images.py
```

---

## 7. Master CSV — Source of Truth

After cleaning, build a single CSV that tracks **every image** in the dataset.

```python
# scripts/build_master_csv.py
import os, csv
from pathlib import Path
from datetime import datetime

# Map folder names → verified species info
# Fill this in based on your spot-checks + IMPPAT verification
SPECIES_MAP = {
    "Tulsi":        {"botanical": "Ocimum tenuiflorum",    "imppat_id": "IMPPAT_P_001234"},
    "Neem":         {"botanical": "Azadirachta indica",    "imppat_id": "IMPPAT_P_000345"},
    "Brahmi":       {"botanical": "Bacopa monnieri",       "imppat_id": "IMPPAT_P_000123"},
    "Ashwagandha":  {"botanical": "Withania somnifera",    "imppat_id": "IMPPAT_P_001456"},
    "Giloy":        {"botanical": "Tinospora cordifolia",  "imppat_id": "IMPPAT_P_000789"},
    # ... add all 70 species
}

FIELDNAMES = [
    "filename", "species_name", "botanical_name", "imppat_id",
    "source", "split", "verified", "date_added"
]

RAW_ROOT = Path("raw")
rows = []

for source_dir in RAW_ROOT.iterdir():
    if not source_dir.is_dir() or source_dir.name == "review":
        continue
    for species_dir in source_dir.iterdir():
        if not species_dir.is_dir():
            continue

        species_key = species_dir.name
        info = SPECIES_MAP.get(species_key)
        if info is None:
            print(f"WARNING: {species_key} not in SPECIES_MAP — skipping")
            continue

        for fpath in species_dir.iterdir():
            if fpath.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
                continue
            rows.append({
                "filename":      fpath.name,
                "species_name":  species_key,
                "botanical_name": info["botanical"],
                "imppat_id":     info["imppat_id"],
                "source":        source_dir.name,
                "split":         "unassigned",
                "verified":      "yes",
                "date_added":    datetime.today().strftime('%Y-%m-%d')
            })

os.makedirs("metadata", exist_ok=True)
with open("metadata/master_labels.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nmaster_labels.csv written: {len(rows)} total images")

# Quick summary
from collections import Counter
counts = Counter(r["species_name"] for r in rows)
print("\nPer-species count:")
for sp, cnt in sorted(counts.items(), key=lambda x: -x[1]):
    status = "OK" if cnt >= 150 else ("LOW" if cnt >= 80 else "CRITICAL")
    print(f"  {sp:30s} {cnt:5d}  [{status}]")
```

```bash
python scripts/build_master_csv.py
```

**Expected output:**
```
master_labels.csv written: 14,320 total images

Per-species count:
  Tulsi                          312  [OK]
  Neem                           287  [OK]
  Brahmi                         143  [LOW]   ← needs more images
  Ashwagandha                     61  [CRITICAL] ← collect more
  ...
```

For any `CRITICAL` species (< 80 images): go back to Step 3 and collect more from iNaturalist or manually.

---

## 8. Class Balance Check

```python
# scripts/check_balance.py
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

df = pd.read_csv("metadata/master_labels.csv")
counts = df.groupby("species_name").size().sort_values(ascending=False)

# Print summary
print(f"\nTotal images:    {len(df)}")
print(f"Total species:   {df['species_name'].nunique()}")
print(f"Mean per class:  {counts.mean():.0f}")
print(f"Min per class:   {counts.min()} ({counts.idxmin()})")
print(f"Max per class:   {counts.max()} ({counts.idxmax()})")
print(f"Classes < 150:   {(counts < 150).sum()}")
print(f"Classes >= 150:  {(counts >= 150).sum()}")

# Plot distribution
fig, ax = plt.subplots(figsize=(16, 6))
colors = ['#d32f2f' if c < 80 else '#f9a825' if c < 150 else '#388e3c'
          for c in counts.values]
counts.plot(kind='bar', ax=ax, color=colors, edgecolor='white', linewidth=0.4)
ax.axhline(150, color='black', linestyle='--', linewidth=1, label='Min threshold (150)')
ax.set_title("Image Count per Species", fontsize=14, fontweight='bold')
ax.set_xlabel("Species")
ax.set_ylabel("Image Count")
ax.legend()
plt.tight_layout()
plt.savefig("reports/class_distribution.png", dpi=120)
print("\nDistribution chart saved: reports/class_distribution.png")
```

```bash
python scripts/check_balance.py
```

**Red bar** = CRITICAL (< 80) — must collect more before proceeding  
**Yellow bar** = LOW (80–149) — acceptable but augmentation will compensate  
**Green bar** = OK (≥ 150) — ready

---

## 9. Dataset Split

Only run this **after** every species has at least 80 images and the master CSV is complete.

```python
# scripts/split_dataset.py
import os, shutil, pandas as pd
from sklearn.model_selection import train_test_split
from pathlib import Path

df = pd.read_csv("metadata/master_labels.csv")
df = df[df["verified"] == "yes"].reset_index(drop=True)

# Step 1: Stratified split — test set (15%)
train_val, test = train_test_split(
    df, test_size=0.15,
    stratify=df["species_name"],
    random_state=42
)

# Step 2: Validation set from remaining (15% of total ≈ 17.6% of train_val)
train, val = train_test_split(
    train_val, test_size=0.176,
    stratify=train_val["species_name"],
    random_state=42
)

train = train.copy(); train["split"] = "train"
val   = val.copy();   val["split"]   = "val"
test  = test.copy();  test["split"]  = "test"

split_df = pd.concat([train, val, test]).reset_index(drop=True)
split_df.to_csv("metadata/split_log.csv", index=False)

print(f"Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")
print(f"Total: {len(split_df)}")

# Verify minimum per-class counts in each split
for split_name, split_data in [("train", train), ("val", val), ("test", test)]:
    min_count = split_data.groupby("species_name").size().min()
    print(f"  {split_name} — min per class: {min_count}")

# Step 3: Copy files into processed/ folder structure
RAW_SOURCE_MAP = {
    "kaggle_indian":  "raw/kaggle_indian",
    "kaggle_medleaf": "raw/kaggle_medleaf",
    "kaggle_medleaf2":"raw/kaggle_medleaf2",
    "kaggle_ayurvedic":"raw/kaggle_ayurvedic",
    "inat":           "raw/inat",
    "manual":         "raw/manual",
}

copied = 0
errors = 0

for _, row in split_df.iterrows():
    src_dir = RAW_SOURCE_MAP.get(row["source"])
    if src_dir is None:
        errors += 1
        continue

    src = Path(src_dir) / row["species_name"] / row["filename"]
    dst = Path("processed") / row["split"] / row["species_name"] / row["filename"]
    dst.parent.mkdir(parents=True, exist_ok=True)

    if src.exists():
        shutil.copy2(src, dst)
        copied += 1
    else:
        errors += 1

print(f"\nCopied: {copied} | Errors: {errors}")
print("processed/ folder is ready for training.")
```

```bash
python scripts/split_dataset.py
```

> **IMPORTANT:** After this step, lock the test split. Never use it for any model decision until final evaluation. Treat `processed/test/` as sealed.

---

## 10. Final Validation Checklist

Run through every item before starting Objective 2 (preprocessing).

```python
# scripts/final_check.py
import os, pandas as pd
from pathlib import Path

print("=" * 50)
print("OBJECTIVE 1 — FINAL VALIDATION CHECKLIST")
print("=" * 50)

CHECKS = []

# ── Check 1: master_labels.csv exists ─────────────────
if Path("metadata/master_labels.csv").exists():
    df = pd.read_csv("metadata/master_labels.csv")
    CHECKS.append(("master_labels.csv exists", True, f"{len(df)} rows"))
else:
    CHECKS.append(("master_labels.csv exists", False, "FILE MISSING"))
    df = pd.DataFrame()

# ── Check 2: Total image count ────────────────────────
total = len(df)
CHECKS.append((
    "Total images ≥ 12,000",
    total >= 12000,
    f"{total} images"
))

# ── Check 3: Species count ─────────────────────────────
n_species = df["species_name"].nunique() if len(df) else 0
CHECKS.append((
    "Species count 60–80",
    60 <= n_species <= 80,
    f"{n_species} species"
))

# ── Check 4: No class below 80 images ─────────────────
if len(df):
    counts = df.groupby("species_name").size()
    critical = (counts < 80).sum()
    CHECKS.append((
        "No class below 80 images",
        critical == 0,
        f"{critical} classes below threshold"
    ))

# ── Check 5: All labels IMPPAT-verified ───────────────
if Path("metadata/imppat_species_map.csv").exists():
    imap = pd.read_csv("metadata/imppat_species_map.csv")
    unverified = imap[~imap.get("imppat_verified", pd.Series([True]*len(imap)))].shape[0]
    CHECKS.append((
        "All species IMPPAT-verified",
        unverified == 0,
        f"{unverified} unverified"
    ))

# ── Check 6: processed/ split folders exist ───────────
for split in ["train", "val", "test"]:
    split_path = Path("processed") / split
    exists = split_path.exists() and len(list(split_path.iterdir())) > 0
    CHECKS.append((
        f"processed/{split}/ populated",
        exists,
        "OK" if exists else "MISSING"
    ))

# ── Check 7: split_log.csv exists ─────────────────────
if Path("metadata/split_log.csv").exists():
    sdf = pd.read_csv("metadata/split_log.csv")
    counts_by_split = sdf["split"].value_counts()
    CHECKS.append(("split_log.csv exists", True, str(counts_by_split.to_dict())))
else:
    CHECKS.append(("split_log.csv exists", False, "MISSING"))

# ── Check 8: cleaning_log.csv exists ──────────────────
CHECKS.append((
    "cleaning_log.csv exists",
    Path("metadata/cleaning_log.csv").exists(),
    "OK" if Path("metadata/cleaning_log.csv").exists() else "MISSING"
))

# ── Print results ──────────────────────────────────────
all_pass = True
for name, passed, detail in CHECKS:
    icon = "✅" if passed else "❌"
    if not passed:
        all_pass = False
    print(f"  {icon}  {name}")
    print(f"       → {detail}")

print()
if all_pass:
    print("✅ ALL CHECKS PASSED — Ready for Objective 2")
else:
    print("❌ SOME CHECKS FAILED — Fix above issues before proceeding")
```

```bash
python scripts/final_check.py
```

---

## 11. Progress Tracker

Update this table manually as you work through the objective.

| Task | Status | Notes |
|------|--------|-------|
| Environment setup | ☐ | |
| Kaggle datasets downloaded | ☐ | |
| iNaturalist collection script run | ☐ | |
| Manual collection for critical species | ☐ | |
| Folder structure created | ☐ | |
| Spot-check all species folders | ☐ | |
| IMPPAT species map built | ☐ | |
| Cleaning pipeline run | ☐ | |
| master_labels.csv built | ☐ | |
| Class balance chart reviewed | ☐ | |
| Critical species topped up (≥ 80 imgs) | ☐ | |
| Dataset split completed | ☐ | |
| Final checklist all green | ☐ | |
| **Objective 1 COMPLETE** | ☐ | |

---

## Definitions

| Term | Meaning |
|------|---------|
| **IMPPAT** | Indian Medicinal Plants, Phytochemistry and Therapeutics database — used to verify botanical names |
| **pHash** | Perceptual hash — fingerprint of an image's visual content, used to detect near-duplicates |
| **Stratified split** | Splitting data such that each class has the same proportion in train/val/test |
| **Research-grade** (iNaturalist) | Observations confirmed by ≥2 community identifications |
| **CLAHE** | Contrast Limited Adaptive Histogram Equalisation — used in Objective 2 augmentation |

---

*Next: [Objective 2 — Preprocessing & Augmentation](./OBJ2_Preprocessing_Augmentation.md)*
