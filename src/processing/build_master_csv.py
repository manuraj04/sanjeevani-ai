"""
Builds metadata/master_labels.csv — the single source of truth for every
image in the dataset, combining all sources (Kaggle, iNat, manual).

Run AFTER clean_images.py and verify_labels.py.

Usage:
    python scripts/build_master_csv.py
    python scripts/build_master_csv.py --raw-root path/to/raw
"""

import argparse
import csv
import logging
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from src.config import SPECIES_MAP, MIN_IMAGES, CRITICAL_THRESHOLD

LOG_DIR  = Path("logs")
META_DIR = Path("metadata")
RAW_ROOT = Path("data/raw")
IMG_EXTS = {'.jpg', '.jpeg', '.png'}

FIELDNAMES = [
    "filename", "rel_path", "species_name", "botanical_name",
    "ayurvedic_name", "source", "split", "verified", "date_added",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "build_master_csv.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def collect_rows(raw_root: Path, today: str) -> list[dict]:
    rows = []
    skipped_dirs = []

    for source_dir in sorted(raw_root.iterdir()):
        if not source_dir.is_dir() or source_dir.name == "review":
            continue
        source_name = source_dir.name

        for species_dir in sorted(source_dir.iterdir()):
            if not species_dir.is_dir():
                continue

            species_key = species_dir.name
            info = SPECIES_MAP.get(species_key)
            if info is None:
                skipped_dirs.append(str(species_dir))
                log.warning(f"  Skipping '{species_key}' — not in SPECIES_MAP")
                continue

            for fpath in sorted(species_dir.iterdir()):
                if fpath.suffix.lower() not in IMG_EXTS:
                    continue
                rows.append({
                    "filename":      fpath.name,
                    "rel_path":      str(fpath.relative_to(raw_root.parent)).replace("\\", "/"),
                    "species_name":  species_key,
                    "botanical_name": info["botanical"],
                    "ayurvedic_name": info["ayurvedic"],
                    "source":        source_name,
                    "split":         "unassigned",
                    "verified":      "yes",
                    "date_added":    today,
                })

    if skipped_dirs:
        log.warning(f"  {len(skipped_dirs)} unknown directories skipped. "
                    f"Add them to species_list.py if valid.")

    return rows


def print_status_table(counts: Counter) -> None:
    print("\n  Per-species image count:")
    print(f"  {'Species':28s} {'Count':>6}  Status")
    print("  " + "-" * 50)
    for sp, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        if cnt >= MIN_IMAGES:
            status = "OK"
        elif cnt >= CRITICAL_THRESHOLD:
            status = "LOW — needs augmentation"
        else:
            status = "CRITICAL — collect more"
        flag = "" if cnt >= MIN_IMAGES else "! " if cnt >= CRITICAL_THRESHOLD else "X "
        print(f"  {flag}{sp:26s} {cnt:6d}  {status}")


def main():
    LOG_DIR.mkdir(exist_ok=True)
    META_DIR.mkdir(exist_ok=True)

    parser = argparse.ArgumentParser(description="Build master_labels.csv")
    parser.add_argument("--raw-root", default="data/raw",
                        help="Root directory of raw images (default: data/raw)")
    args = parser.parse_args()

    raw_root = Path(args.raw_root)
    today    = datetime.today().strftime("%Y-%m-%d")

    log.info("Scanning raw/ for images ...")
    rows = collect_rows(raw_root, today)

    out_path = META_DIR / "master_labels.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    counts  = Counter(r["species_name"] for r in rows)
    ok      = sum(1 for c in counts.values() if c >= MIN_IMAGES)
    low     = sum(1 for c in counts.values() if CRITICAL_THRESHOLD <= c < MIN_IMAGES)
    critical = sum(1 for c in counts.values() if c < CRITICAL_THRESHOLD)

    print(f"\n  master_labels.csv written: {len(rows):,} total images")
    print(f"  Species: {len(counts)}  |  OK: {ok}  |  LOW: {low}  |  CRITICAL: {critical}")
    print_status_table(counts)

    if critical:
        print(f"\n  ACTION NEEDED: {critical} species below {CRITICAL_THRESHOLD} images.")
        print("  Run collect_inat.py --priority HIGH (or manually photograph) before splitting.")

    print(f"\n  Saved: {out_path}")


if __name__ == "__main__":
    main()
