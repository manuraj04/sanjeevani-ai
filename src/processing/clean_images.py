"""
Image cleaning pipeline for Sanjeevani dataset.
Processes every raw species folder and removes:
  1. Corrupt / unreadable files
  2. Too small (< 64px on either side)
  3. Extreme aspect ratio (> 6:1 or < 1:6)
  4. Overexposed / underexposed / near-blank images
  5. Perceptual hash duplicates (across the whole species, not just one source)

Keeps a cleaning_log.csv and cleaning_summary.csv in metadata/.

Usage:
    python scripts/clean_images.py                    # clean all raw/
    python scripts/clean_images.py --species Tulsi    # one species
    python scripts/clean_images.py --dry-run          # report without moving
"""

import argparse
import csv
import logging
import sys
from pathlib import Path

import imagehash
import pandas as pd
from PIL import Image, ImageStat
from tqdm import tqdm

from src.config import SPECIES_MAP

LOG_DIR  = Path("logs")
META_DIR = Path("metadata")
RAW_ROOT = Path("data/raw")
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "clean_images.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def brightness_stddev(img: Image.Image) -> tuple[float, float]:
    stat = ImageStat.Stat(img)
    brightness = sum(stat.mean) / 3
    stddev     = sum(stat.stddev) / 3
    return brightness, stddev


def clean_folder(folder_path: Path, species_name: str,
                 global_hashes: dict, dry_run: bool) -> tuple[int, int, list]:
    """Clean one species folder. Returns (kept, removed, log_rows)."""
    all_files = sorted(f for f in folder_path.iterdir() if f.suffix.lower() in IMG_EXTS)
    kept = removed = 0
    log_rows = []

    review_dir = RAW_ROOT / "review" / species_name

    with tqdm(all_files, desc=f"  {species_name:25s}", unit="img", leave=False) as pbar:
        for fpath in pbar:
            reason = None

            # ── 1. File integrity ─────────────────────────────────────
            try:
                img = Image.open(fpath)
                img.load()               # force full decode
                img = img.convert("RGB")
            except Exception as e:
                reason = f"corrupt:{e}"

            if reason is None:
                w, h = img.size

                # ── 2. Minimum resolution ─────────────────────────────
                if w < 64 or h < 64:
                    reason = f"too_small:{w}x{h}"

                # ── 3. Extreme aspect ratio ───────────────────────────
                elif max(w / h, h / w) > 6:
                    reason = f"bad_aspect:{w}x{h}"

                else:
                    # ── 4. Brightness / content check ─────────────────
                    brightness, stddev = brightness_stddev(img)
                    if brightness > 245:
                        reason = "overexposed"
                    elif brightness < 8:
                        reason = "underexposed"
                    elif stddev < 7:
                        reason = "near_blank"

                    # ── 5. Perceptual duplicate (cross-source) ────────
                    if reason is None:
                        ph = str(imagehash.phash(img, hash_size=16))
                        if ph in global_hashes:
                            reason = f"duplicate_of:{global_hashes[ph]}"
                        else:
                            global_hashes[ph] = f"{species_name}/{fpath.name}"

            if reason:
                if not dry_run:
                    review_dir.mkdir(parents=True, exist_ok=True)
                    fpath.rename(review_dir / fpath.name)
                log_rows.append({
                    "file":    str(fpath),
                    "species": species_name,
                    "action":  "moved_to_review" if not dry_run else "would_remove",
                    "reason":  reason,
                })
                removed += 1
            else:
                # ── Standardise to JPEG ───────────────────────────────
                if not dry_run and fpath.suffix.lower() != '.jpg':
                    new_path = fpath.with_suffix('.jpg')
                    img.save(new_path, "JPEG", quality=92)
                    fpath.unlink()
                kept += 1

    return kept, removed, log_rows


def main():
    LOG_DIR.mkdir(exist_ok=True)
    META_DIR.mkdir(exist_ok=True)

    parser = argparse.ArgumentParser(description="Clean raw image folders")
    parser.add_argument("--species", nargs="+", metavar="NAME",
                        help="Only clean these species (folder names)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would be removed without moving files")
    args = parser.parse_args()

    all_log  = []
    summary  = []

    for source_dir in sorted(RAW_ROOT.iterdir()):
        if not source_dir.is_dir() or source_dir.name in ("review",):
            continue

        for species_dir in sorted(source_dir.iterdir()):
            if not species_dir.is_dir():
                continue
            if args.species and species_dir.name not in args.species:
                continue

            species_name = species_dir.name
            if species_name not in SPECIES_MAP:
                log.warning(f"  {species_name} not in SPECIES_MAP — processing anyway")

            before = sum(1 for f in species_dir.iterdir() if f.suffix.lower() in IMG_EXTS)
            if before == 0:
                continue

            # Per-species hash table so duplicates across sources are caught together
            global_hashes: dict = {}
            kept, removed, rows = clean_folder(species_dir, species_name, global_hashes, args.dry_run)
            all_log.extend(rows)

            summary.append({
                "source":  source_dir.name,
                "species": species_name,
                "before":  before,
                "after":   kept,
                "removed": removed,
                "dry_run": args.dry_run,
            })
            log.info(f"  {species_name}: {before} → {kept}  (removed {removed})")

    prefix = "[DRY RUN] " if args.dry_run else ""
    log_path     = META_DIR / "cleaning_log.csv"
    summary_path = META_DIR / "cleaning_summary.csv"

    pd.DataFrame(all_log).to_csv(log_path, index=False)
    pd.DataFrame(summary).to_csv(summary_path, index=False)

    total_before = sum(r["before"]   for r in summary)
    total_after  = sum(r["after"]    for r in summary)
    total_removed = sum(r["removed"] for r in summary)

    print(f"\n{prefix}── Cleaning Summary ─────────────────────────────────")
    print(f"  Images before:  {total_before}")
    print(f"  Images after:   {total_after}")
    print(f"  Removed:        {total_removed}  ({100*total_removed/max(total_before,1):.1f}%)")
    print(f"  Species cleaned:{len(summary)}")
    print(f"\n  Log saved: {log_path}")
    print(f"  Summary:   {summary_path}")

    if args.dry_run:
        print("\n  [DRY RUN] No files were moved.")


if __name__ == "__main__":
    main()
