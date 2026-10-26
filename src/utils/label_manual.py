"""
CLI logger for manually photographed leaves.
Appends rows to metadata/master_labels.csv for images you photograph yourself.

Usage:
    python scripts/label_manual.py <image_folder> <species_name>

Examples:
    python scripts/label_manual.py raw/manual/Brahmi Brahmi
    python scripts/label_manual.py D:/my_photos/ashwagandha Ashwagandha

The script:
  1. Validates that <species_name> is in species_list.py
  2. Moves images to raw/manual/<species_name>/ if not already there
  3. Appends entries to metadata/master_labels.csv
"""

import argparse
import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path

from src.config import SPECIES_MAP

META_DIR = Path("metadata")
RAW_MANUAL = Path("raw/manual")
IMG_EXTS   = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.heic'}

FIELDNAMES = [
    "filename", "rel_path", "species_name", "botanical_name",
    "ayurvedic_name", "source", "split", "verified", "date_added",
]


def main():
    parser = argparse.ArgumentParser(
        description="Log manually photographed images into master_labels.csv"
    )
    parser.add_argument("image_folder", help="Folder containing your images")
    parser.add_argument("species_name", help="Species folder name (e.g. Brahmi)")
    parser.add_argument("--unverified", action="store_true",
                        help="Mark as unverified (not IMPPAT-checked yet)")
    args = parser.parse_args()

    img_dir      = Path(args.image_folder)
    species_name = args.species_name

    if not img_dir.exists():
        print(f"ERROR: Folder not found: {img_dir}")
        sys.exit(1)

    if species_name not in SPECIES_MAP:
        print(f"ERROR: '{species_name}' not in species_list.py")
        print(f"  Valid names: {sorted(SPECIES_MAP.keys())}")
        sys.exit(1)

    info    = SPECIES_MAP[species_name]
    today   = datetime.today().strftime("%Y-%m-%d")
    dest_dir = RAW_MANUAL / species_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)

    # Collect images
    images = [f for f in sorted(img_dir.iterdir()) if f.suffix.lower() in IMG_EXTS]
    if not images:
        print(f"ERROR: No image files found in {img_dir}")
        sys.exit(1)

    # Move/copy into raw/manual/
    moved_rows = []
    for fpath in images:
        dest = dest_dir / fpath.name
        if not dest.exists():
            shutil.copy2(fpath, dest)

        moved_rows.append({
            "filename":       dest.name,
            "rel_path":       str(dest).replace("\\", "/"),
            "species_name":   species_name,
            "botanical_name": info["botanical"],
            "ayurvedic_name": info["ayurvedic"],
            "source":         "manual",
            "split":          "unassigned",
            "verified":       "no" if args.unverified else "yes",
            "date_added":     today,
        })

    # Append to master CSV
    csv_path = META_DIR / "master_labels.csv"
    file_exists = csv_path.exists()

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(moved_rows)

    print(f"\n  Logged {len(moved_rows)} images for {species_name} ({info['botanical']})")
    print(f"  Copied to: {dest_dir}")
    print(f"  Appended to: {csv_path}")
    print(f"  Verified: {'no (--unverified)' if args.unverified else 'yes'}")


if __name__ == "__main__":
    main()
