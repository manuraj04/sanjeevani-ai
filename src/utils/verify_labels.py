"""
Label verification for Sanjeevani dataset.

Two modes:
  1. IMPPAT cross-check — matches our 70 species against the IMPPAT CSV
     and writes metadata/imppat_species_map.csv
  2. Visual spot-check — renders a 4x4 grid of random images per species
     and saves it to reports/ for manual review

Usage:
    python scripts/verify_labels.py --mode imppat
    python scripts/verify_labels.py --mode spotcheck
    python scripts/verify_labels.py --mode all           # both
    python scripts/verify_labels.py --mode spotcheck --species Tulsi Neem
"""

import argparse
import logging
import os
import random
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

from src.config import SPECIES, SPECIES_MAP

LOG_DIR  = Path("logs")
META_DIR = Path("metadata")
RAW_ROOT = Path("data/raw")
REPORTS  = Path("reports")
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "verify_labels.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ─── IMPPAT cross-check ──────────────────────────────────────────────────────

def verify_imppat(imppat_csv: Path) -> pd.DataFrame:
    """
    Match our 70 species against IMPPAT and write imppat_species_map.csv.
    If IMPPAT CSV is missing, creates a stub with imppat_verified=False.
    """
    our_df = pd.DataFrame([
        {"common_name": name, "botanical_name": info["botanical"],
         "ayurvedic_name": info["ayurvedic"], "priority": info["priority"]}
        for name, info in SPECIES_MAP.items()
    ])

    if imppat_csv.exists():
        log.info(f"  Loading IMPPAT: {imppat_csv}")
        imppat = pd.read_csv(imppat_csv)

        # Try common IMPPAT column names
        bot_col = next(
            (c for c in imppat.columns
             if "botanical" in c.lower() or "plant_name" in c.lower() or "species" in c.lower()),
            None
        )
        if bot_col is None:
            log.error(f"  Cannot find botanical name column in {imppat_csv.name}. "
                      f"Columns: {list(imppat.columns)}")
            our_df["imppat_verified"] = False
        else:
            imppat_names = set(imppat[bot_col].str.strip().str.lower())
            our_df["imppat_verified"] = our_df["botanical_name"].str.lower().isin(imppat_names)
    else:
        log.warning(f"  IMPPAT CSV not found at {imppat_csv}")
        log.warning("  Download from https://cb.imsc.res.in/imppat/ → Plants CSV")
        log.warning("  Save to metadata/IMPPAT_plants.csv and re-run")
        our_df["imppat_verified"] = False

    out_path = META_DIR / "imppat_species_map.csv"
    our_df.to_csv(out_path, index=False)

    verified   = our_df["imppat_verified"].sum()
    unverified = (~our_df["imppat_verified"]).sum()
    log.info(f"  IMPPAT verified:   {verified}/{len(our_df)}")
    if unverified:
        log.warning(f"  NOT in IMPPAT ({unverified}):")
        for _, row in our_df[~our_df["imppat_verified"]].iterrows():
            log.warning(f"    {row['common_name']:25s}  {row['botanical_name']}")

    print(f"\n  imppat_species_map.csv written ({len(our_df)} species)")
    print(f"  Verified: {verified}   Unverified: {unverified}")
    return our_df


# ─── Visual spot-check ───────────────────────────────────────────────────────

def spot_check(species_folder: Path, species_name: str, n: int = 16) -> None:
    all_files = [f for f in species_folder.iterdir() if f.suffix.lower() in IMG_EXTS]
    if not all_files:
        log.warning(f"  {species_name}: no images found in {species_folder}")
        return

    sample = random.sample(all_files, min(n, len(all_files)))
    cols   = 4
    rows   = max(1, (len(sample) + cols - 1) // cols)

    fig, axes = plt.subplots(rows, cols, figsize=(14, 3.5 * rows))
    axes_flat = axes.flat if rows > 1 or cols > 1 else [axes]

    fig.suptitle(
        f"{species_name}  —  {SPECIES_MAP.get(species_name, {}).get('botanical', '')}\n"
        f"{len(all_files)} images in folder",
        fontsize=12, fontweight="bold", y=1.01,
    )

    for ax in axes_flat:
        ax.axis("off")

    for ax, fpath in zip(axes_flat, sample):
        try:
            img = Image.open(fpath).convert("RGB")
            ax.imshow(img)
            ax.set_title(fpath.name[:22], fontsize=6)
        except Exception as e:
            ax.set_title(f"ERROR\n{e}", fontsize=6, color="red")
        ax.axis("off")

    plt.tight_layout()
    out = REPORTS / f"spotcheck_{species_name}.png"
    plt.savefig(out, dpi=80, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  Spot-check saved: {out}")


def run_spotchecks(target_species: list[str] | None = None) -> None:
    REPORTS.mkdir(exist_ok=True)
    found = set()

    for source_dir in sorted(RAW_ROOT.iterdir()):
        if not source_dir.is_dir() or source_dir.name == "review":
            continue
        for species_dir in sorted(source_dir.iterdir()):
            if not species_dir.is_dir():
                continue
            name = species_dir.name
            if target_species and name not in target_species:
                continue
            if name in found:
                continue        # only check first occurrence per species
            found.add(name)
            spot_check(species_dir, name)

    print(f"\n  Spot-check images saved to: {REPORTS}/")
    print(f"  Open each spotcheck_*.png and confirm the images look correct.")


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    LOG_DIR.mkdir(exist_ok=True)
    META_DIR.mkdir(exist_ok=True)

    parser = argparse.ArgumentParser(description="Verify dataset labels")
    parser.add_argument("--mode", choices=["imppat", "spotcheck", "all"],
                        default="all", help="Which checks to run")
    parser.add_argument("--imppat-csv", default="metadata/IMPPAT_plants.csv",
                        help="Path to IMPPAT plants CSV download")
    parser.add_argument("--species", nargs="+", metavar="NAME",
                        help="Limit spot-checks to these species")
    args = parser.parse_args()

    if args.mode in ("imppat", "all"):
        log.info("── Running IMPPAT verification ──────────────────────")
        verify_imppat(Path(args.imppat_csv))

    if args.mode in ("spotcheck", "all"):
        log.info("── Running visual spot-checks ───────────────────────")
        run_spotchecks(args.species)


if __name__ == "__main__":
    main()
