"""
Kaggle dataset downloader for Sanjeevani dataset.
Downloads and extracts the four medicinal plant Kaggle datasets,
then maps their folder names to our standard species names.

Prerequisites:
    - kaggle.json in ~/.kaggle/ (or KAGGLE_USERNAME + KAGGLE_KEY env vars)
    - pip install kaggle

Usage:
    python scripts/collect_kaggle.py
    python scripts/collect_kaggle.py --dataset aryashah2k/indian-medicinal-leaves-image-datasets
"""

import argparse
import json
import logging
import os
import shutil
import sys
import zipfile
from pathlib import Path

from src.config import SPECIES_MAP

LOG_DIR = Path("logs")
RAW_DIR = Path("data/raw")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "collect_kaggle.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# Each entry: (kaggle_slug, local_target_dir)
DATASETS = [
    ("aryashah2k/indian-medicinal-leaves-image-datasets", "kaggle_indian"),
    ("vishnuoum/medicinal-plant-dataset-augmented",       "kaggle_medleaf"),
    ("pushpankar/medleaf",                                "kaggle_medleaf2"),
    ("noumanali1122/medicinal-plants",                    "kaggle_ayurvedic"),
]

# Fuzzy name mapping: map common Kaggle folder spellings → our standard folder names
# Extend this as you discover what folder names each dataset actually uses.
KAGGLE_NAME_MAP = {
    # aryashah2k dataset typical names
    "tulsi":                    "Tulsi",
    "neem":                     "Neem",
    "brahmi":                   "Brahmi",
    "ashwagandha":              "Ashwagandha",
    "aloe vera":                "AloeVera",
    "aloe_vera":                "AloeVera",
    "aloevera":                 "AloeVera",
    "turmeric":                 "Turmeric",
    "ginger":                   "Ginger",
    "moringa":                  "Moringa",
    "curry leaf":               "CurryLeaf",
    "curry_leaf":               "CurryLeaf",
    "curryleaf":                "CurryLeaf",
    "betel":                    "Betel",
    "mint":                     "Mint",
    "lemongrass":               "Lemongrass",
    "amla":                     "Amla",
    "bael":                     "Bael",
    "giloy":                    "Giloy",
    "shatavari":                "Shatavari",
    "gotu kola":                "GotoKola",
    "gotukola":                 "GotoKola",
    "centella":                 "GotoKola",
    "kalmegh":                  "Kalmegh",
    "andrographis":             "Kalmegh",
    "adulsa":                   "Adulsa",
    "justicia adhatoda":        "Adulsa",
    "haritaki":                 "Haritaki",
    "gudmar":                   "Gudmar",
    "gymnema":                  "Gudmar",
    "nirgundi":                 "Nirgundi",
    "vitex":                    "Nirgundi",
    "black pepper":             "BlackPepper",
    "blackpepper":              "BlackPepper",
    "long pepper":              "LongPepper",
    "longpepper":               "LongPepper",
    "pippali":                  "LongPepper",
    "indian gooseberry":        "IndianGooseberry",
    "emblica":                  "IndianGooseberry",
    "guava":                    "Guava",
    "papaya":                   "Papaya",
    "bhringraj":                "Bhringraj",
    "eclipta":                  "Bhringraj",
    "punarnava":                "Punarnava",
    "boerhavia":                "Punarnava",
    "karela":                   "Karela",
    "bittergourd":              "Karela",
    "bitter gourd":             "Karela",
    "jamun":                    "Jamun",
    "syzygium cumini":          "Jamun",
    "hibiscus":                 "Hibiscus",
    "castor":                   "Castor",
    "mulethi":                  "Mulethi",
    "licorice":                 "Mulethi",
    "karpuravalli":             "Karpuravalli",
    "insulin plant":            "InsulinPlant",
    "insulinplant":             "InsulinPlant",
    "peepal":                   "Peepal",
    "ficus religiosa":          "Peepal",
    "banyan":                   "Banyan",
    "ficus benghalensis":       "Banyan",
    "aparajita":                "Aparajita",
    "clitoria":                 "Aparajita",
    "patharchatta":             "Patharchatta",
    "bryophyllum":              "Patharchatta",
    "palash":                   "Palash",
    "butea":                    "Palash",
    "vibhitaki":                "Vibhitaki",
    "arjuna":                   "Arjuna",
    "terminalia arjuna":        "Arjuna",
    "sarpagandha":              "Sarpagandha",
    "rauvolfia":                "Sarpagandha",
    "vacha":                    "Vacha",
    "acorus":                   "Vacha",
    "chitraka":                 "Chitraka",
    "plumbago":                 "Chitraka",
    "kutaja":                   "Kutaja",
    "holarrhena":               "Kutaja",
    "kanchnaar":                "Kanchnaar",
    "bauhinia":                 "Kanchnaar",
    "agathi":                   "Agathi",
    "sesbania":                 "Agathi",
    "pomegranate":              "Pomegranate",
    "punica":                   "Pomegranate",
    "fenugreek":                "Fenugreek",
    "methi":                    "Fenugreek",
    "clove":                    "Clove",
    "syzygium aromaticum":      "Clove",
    "vetiver":                  "Vetiver",
    "snake plant":              "SnakePlant",
    "lemon":                    "Lemon",
    "chamomile":                "Chamomile",
    "sesame":                   "Sesame",
    "coriander":                "Coriander",
    "betel nut":                "BetelNut",
    "arecanut":                 "BetelNut",
}


def normalize(name: str) -> str:
    return name.strip().lower().replace("-", " ").replace("_", " ")


def map_folder_name(raw_name: str) -> str | None:
    key = normalize(raw_name)
    if key in KAGGLE_NAME_MAP:
        return KAGGLE_NAME_MAP[key]
    # Try partial match for safety
    for k, v in KAGGLE_NAME_MAP.items():
        if k in key or key in k:
            return v
    return None


def download_dataset(slug: str, target_dir: str) -> Path:
    try:
        import kaggle  # noqa: F401 — just checking it's installed
    except ImportError:
        log.error("kaggle package not installed. Run: pip install kaggle")
        sys.exit(1)

    out_path = RAW_DIR / target_dir
    out_path.mkdir(parents=True, exist_ok=True)

    zip_name = slug.split("/")[1] + ".zip"
    zip_path = RAW_DIR / zip_name

    if zip_path.exists():
        log.info(f"  {zip_name} already downloaded — skipping")
    else:
        log.info(f"  Downloading {slug} ...")
        os.system(f'kaggle datasets download -d {slug} -p "{RAW_DIR}"')

    if not zip_path.exists():
        log.error(f"  Download failed — {zip_path} not found")
        return out_path

    log.info(f"  Extracting {zip_name} → {out_path}")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(out_path)

    return out_path


def reorganize(source_root: Path, target_base: str) -> dict:
    """Walk source_root, detect image folders, map names, copy to raw/<target_base>/<StandardName>/."""
    stats = {"mapped": 0, "unmapped": [], "images_copied": 0}

    for dirpath, dirnames, filenames in os.walk(source_root):
        images = [f for f in filenames if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        if not images:
            continue

        folder_name = Path(dirpath).name
        std_name = map_folder_name(folder_name)

        if std_name is None:
            stats["unmapped"].append(folder_name)
            log.warning(f"  UNMAPPED folder: '{folder_name}' — add to KAGGLE_NAME_MAP")
            continue

        dest_dir = RAW_DIR / target_base / std_name
        dest_dir.mkdir(parents=True, exist_ok=True)

        for img in images:
            src = Path(dirpath) / img
            # Prefix with source dir name to avoid filename collisions
            dest_fname = f"{target_base}_{img}"
            dest = dest_dir / dest_fname
            if not dest.exists():
                shutil.copy2(src, dest)
                stats["images_copied"] += 1

        stats["mapped"] += 1
        log.info(f"  {folder_name:30s} → {std_name}  ({len(images)} images)")

    return stats


def main():
    LOG_DIR.mkdir(exist_ok=True)
    RAW_DIR.mkdir(exist_ok=True)

    parser = argparse.ArgumentParser(description="Download Kaggle medicinal plant datasets")
    parser.add_argument("--dataset", help="Single Kaggle slug to download (optional)")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip download, only reorganize already-extracted folders")
    args = parser.parse_args()

    datasets = DATASETS if not args.dataset else [(args.dataset, args.dataset.split("/")[1])]

    for slug, target_dir in datasets:
        log.info(f"\n── {slug} ──────────────────────────────")
        source_root = RAW_DIR / target_dir

        if not args.skip_download:
            source_root = download_dataset(slug, target_dir)

        if not source_root.exists():
            log.warning(f"  Source folder not found: {source_root}")
            continue

        stats = reorganize(source_root, target_dir)
        log.info(f"  Mapped: {stats['mapped']} folders, {stats['images_copied']} images copied")
        if stats["unmapped"]:
            log.warning(f"  Unmapped folders ({len(stats['unmapped'])}): {stats['unmapped']}")

    print("\nKaggle collection done. Check logs/collect_kaggle.log for unmapped folders.")
    print("Add any unmapped folder names to KAGGLE_NAME_MAP in this script, then re-run with --skip-download.")


if __name__ == "__main__":
    main()
