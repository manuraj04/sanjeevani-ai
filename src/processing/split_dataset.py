"""
Stratified train/val/test split for Sanjeevani dataset.
Reads master_labels.csv, splits 70/15/15, copies files into processed/,
and writes split_log.csv.

Run ONLY after:
  1. build_master_csv.py
  2. check_balance.py confirms no CRITICAL species

Usage:
    python scripts/split_dataset.py
    python scripts/split_dataset.py --test-size 0.15 --val-size 0.15
    python scripts/split_dataset.py --dry-run    # stats only, no file copies
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import CRITICAL_THRESHOLD

LOG_DIR   = Path("logs")
META_DIR  = Path("metadata")
PROCESSED = Path("data/processed")
RAW_ROOT  = Path("data/raw")

# Source directories in the order we try to find files
RAW_SOURCES = [
    "kaggle_indian",
    "kaggle_medleaf",
    "kaggle_medleaf2",
    "kaggle_ayurvedic",
    "inat",
    "manual",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "split_dataset.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def resolve_source(row: pd.Series) -> Path | None:
    """Find the actual file on disk for a master_labels row."""
    # Primary: use rel_path if it exists
    if "rel_path" in row and pd.notna(row["rel_path"]):
        p = Path(row["rel_path"])
        if p.exists():
            return p

    # Fallback: try each raw source directory
    for src in RAW_SOURCES:
        candidate = RAW_ROOT / src / row["species_name"] / row["filename"]
        if candidate.exists():
            return candidate

    return None


def guard_min_per_class(df: pd.DataFrame, split_name: str, min_count: int = 5) -> None:
    counts = df.groupby("species_name").size()
    tiny   = counts[counts < min_count]
    if len(tiny):
        log.warning(f"  {split_name}: {len(tiny)} species with < {min_count} images: "
                    f"{list(tiny.index)}")


def main():
    LOG_DIR.mkdir(exist_ok=True)
    PROCESSED.mkdir(exist_ok=True)

    parser = argparse.ArgumentParser(description="Split dataset into train/val/test")
    parser.add_argument("--csv", default="metadata/master_labels.csv")
    parser.add_argument("--test-size",  type=float, default=0.15)
    parser.add_argument("--val-size",   type=float, default=0.15)
    parser.add_argument("--seed",       type=int,   default=42)
    parser.add_argument("--dry-run",    action="store_true",
                        help="Print split stats without copying files")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found. Run build_master_csv.py first.")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    df = df[df["verified"] == "yes"].reset_index(drop=True)

    # Guard: skip species below critical threshold
    counts = df.groupby("species_name").size()
    critical = counts[counts < CRITICAL_THRESHOLD]
    if len(critical):
        log.error(f"  {len(critical)} species below {CRITICAL_THRESHOLD} images. "
                  f"Collect more before splitting.")
        for sp, cnt in critical.items():
            log.error(f"    {sp:28s} {cnt}")
        print("\nERROR: Fix critical species first (see log). Aborting.")
        sys.exit(1)

    # ── Stratified 70 / 15 / 15 split ────────────────────────────────────────
    # First cut off test (15%)
    val_frac_of_trainval = args.val_size / (1.0 - args.test_size)

    train_val, test = train_test_split(
        df, test_size=args.test_size,
        stratify=df["species_name"], random_state=args.seed,
    )
    train, val = train_test_split(
        train_val, test_size=val_frac_of_trainval,
        stratify=train_val["species_name"], random_state=args.seed,
    )

    train = train.copy(); train["split"] = "train"
    val   = val.copy();   val["split"]   = "val"
    test  = test.copy();  test["split"]  = "test"

    guard_min_per_class(train, "train")
    guard_min_per_class(val,   "val")
    guard_min_per_class(test,  "test")

    split_df = pd.concat([train, val, test]).reset_index(drop=True)
    split_df.to_csv(META_DIR / "split_log.csv", index=False)

    total = len(split_df)
    print(f"\n-- Split Summary -----------------------------------------")
    print(f"  Total verified:  {total:,}")
    print(f"  Train:           {len(train):,}  ({100*len(train)/total:.1f}%)")
    print(f"  Val:             {len(val):,}  ({100*len(val)/total:.1f}%)")
    print(f"  Test:            {len(test):,}  ({100*len(test)/total:.1f}%)")
    for split_name, split_data in [("train", train), ("val", val), ("test", test)]:
        sp_counts = split_data.groupby("species_name").size()
        print(f"  {split_name} min/max per class: {sp_counts.min()} / {sp_counts.max()}")

    if args.dry_run:
        print("\n  [DRY RUN] No files copied.")
        return

    # ── Copy files into processed/ ────────────────────────────────────────────
    print("\n  Copying files into processed/ ...")
    copied = errors = 0

    for _, row in split_df.iterrows():
        src = resolve_source(row)
        if src is None:
            log.warning(f"  File not found: {row['species_name']}/{row['filename']}")
            errors += 1
            continue

        dst = PROCESSED / row["split"] / row["species_name"] / row["filename"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1

    print(f"  Copied: {copied:,}  |  Errors: {errors}")
    if errors:
        log.warning(f"  {errors} files could not be found — check split_dataset.log")

    print(f"\n  split_log.csv:   {META_DIR / 'split_log.csv'}")
    print(f"  processed/:      ready for training")
    print(f"\n  !  Test set is now SEALED — do not use processed/test/ until final evaluation.")


if __name__ == "__main__":
    main()
