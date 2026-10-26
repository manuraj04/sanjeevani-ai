"""
Image validation script to catch corrupted/invalid images.
Runs on train/val/test splits.
"""

import os
from PIL import Image
from pathlib import Path
import logging
import csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_dataset(split='train', move_bad=False):
    """
    Check all images in split for corruption and validity.

    Args:
        split: 'train', 'val', or 'test'
        move_bad: If True, move corrupted images to review/ folder

    Returns:
        List of (filepath, error_reason) tuples
    """
    split_path = Path('processed') / split
    errors = []

    if not split_path.exists():
        logger.error(f"Split path not found: {split_path}")
        return errors

    total_files = 0
    valid_files = 0

    for species_dir in sorted(split_path.iterdir()):
        if not species_dir.is_dir():
            continue

        for img_file in sorted(species_dir.iterdir()):
            if img_file.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.webp']:
                continue

            total_files += 1

            try:
                # Try to open and convert
                img = Image.open(img_file).convert('RGB')
                w, h = img.size

                # Check dimensions
                if w < 32 or h < 32:
                    reason = f"too_small: {w}x{h}"
                    errors.append((img_file, reason))
                elif (w / h) > 8 or (h / w) > 8:
                    reason = f"bad_aspect: {w}x{h}"
                    errors.append((img_file, reason))
                else:
                    valid_files += 1

            except Exception as e:
                reason = f"corrupt: {str(e)[:50]}"
                errors.append((img_file, reason))

    # Log summary
    logger.info(f"\n{split.upper()} SET VALIDATION")
    logger.info(f"  Total files: {total_files}")
    logger.info(f"  Valid files: {valid_files}")
    logger.info(f"  Errors: {len(errors)}")

    if errors:
        logger.warning(f"\nProblematic images ({len(errors)}):")
        for fpath, reason in errors[:20]:
            logger.warning(f"  {fpath.name}: {reason}")

        if len(errors) > 20:
            logger.warning(f"  ... and {len(errors) - 20} more")

        # Optionally move bad files
        if move_bad:
            review_path = Path('raw/review')
            for fpath, reason in errors:
                try:
                    review_subdir = review_path / fpath.parent.name
                    review_subdir.mkdir(parents=True, exist_ok=True)
                    fpath.rename(review_subdir / fpath.name)
                    logger.info(f"Moved: {fpath.name}")
                except Exception as e:
                    logger.error(f"Failed to move {fpath}: {e}")

    return errors


def run_validation(move_bad=False):
    """Validate all splits."""
    all_errors = {}

    for split in ['train', 'val', 'test']:
        logger.info(f"\nValidating {split}...")
        errors = validate_dataset(split, move_bad=move_bad)
        all_errors[split] = errors

    # Summary
    total_errors = sum(len(e) for e in all_errors.values())
    logger.info(f"\n{'='*60}")
    logger.info(f"VALIDATION COMPLETE")
    logger.info(f"Total errors across all splits: {total_errors}")

    if total_errors == 0:
        logger.info("All images validated successfully!")
    else:
        logger.warning(f"Found {total_errors} problematic images")

    # Save error log
    with open('logs/validation_errors.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['split', 'filename', 'error_reason'])
        for split, errors in all_errors.items():
            for fpath, reason in errors:
                writer.writerow([split, fpath.name, reason])

    logger.info(f"Error log saved: logs/validation_errors.csv")

    return all_errors


if __name__ == "__main__":
    import sys

    move_bad = '--move-bad' in sys.argv
    all_errors = run_validation(move_bad=move_bad)

    exit_code = 0 if sum(len(e) for e in all_errors.values()) == 0 else 1
    exit(exit_code)
