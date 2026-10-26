"""
Class balance visualizer for Sanjeevani dataset.
Reads master_labels.csv and produces:
  - Console summary (totals, min/max, counts)
  - reports/class_distribution.png (bar chart, colour-coded)
  - reports/sample_grid.png (one random image per species)

Usage:
    python scripts/check_balance.py
    python scripts/check_balance.py --csv metadata/master_labels.csv
"""

import argparse
import logging
import random
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
from PIL import Image

from src.config import MIN_IMAGES, CRITICAL_THRESHOLD

LOG_DIR = Path("logs")
REPORTS = Path("reports")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "check_balance.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# Colour thresholds
RED    = "#c0392b"   # critical  < 80
YELLOW = "#f39c12"   # low       80–149
GREEN  = "#27ae60"   # ok        ≥ 150


def bar_chart(counts: pd.Series, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(max(18, len(counts) * 0.38), 6))

    colors = [
        RED    if c < CRITICAL_THRESHOLD else
        YELLOW if c < MIN_IMAGES         else
        GREEN
        for c in counts.values
    ]

    bars = counts.plot(kind="bar", ax=ax, color=colors, edgecolor="white", linewidth=0.4)
    ax.axhline(MIN_IMAGES,        color="black", linestyle="--", linewidth=1.2,
               label=f"Min target ({MIN_IMAGES})")
    ax.axhline(CRITICAL_THRESHOLD, color="red",  linestyle=":",  linewidth=1.0,
               label=f"Critical floor ({CRITICAL_THRESHOLD})")

    # Value labels on each bar
    for bar, val in zip(ax.patches, counts.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 3,
            str(val), ha="center", va="bottom", fontsize=5.5, rotation=90,
        )

    ax.set_title("Sanjeevani Dataset — Image Count per Species", fontsize=14, fontweight="bold")
    ax.set_xlabel("Species", fontsize=10)
    ax.set_ylabel("Image Count", fontsize=10)
    ax.tick_params(axis="x", labelsize=7, rotation=60)

    legend_patches = [
        mpatches.Patch(color=GREEN,  label=f"OK  (≥ {MIN_IMAGES})"),
        mpatches.Patch(color=YELLOW, label=f"Low ({CRITICAL_THRESHOLD}–{MIN_IMAGES-1})"),
        mpatches.Patch(color=RED,    label=f"Critical (< {CRITICAL_THRESHOLD})"),
    ]
    ax.legend(handles=legend_patches + ax.get_legend_handles_labels()[0][:2],
              loc="upper right", fontsize=8)

    plt.tight_layout()
    plt.savefig(out_path, dpi=130)
    plt.close(fig)
    log.info(f"  Bar chart saved: {out_path}")


def sample_grid(df: pd.DataFrame, out_path: Path) -> None:
    """One random image per species in a grid."""
    species = df["species_name"].unique()
    n = len(species)
    cols = 8
    rows = (n + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2, rows * 2.2))
    axes_flat  = [ax for row in axes for ax in row] if rows > 1 else list(axes)

    for ax in axes_flat:
        ax.axis("off")

    for ax, sp in zip(axes_flat, sorted(species)):
        subset = df[df["species_name"] == sp]
        row    = subset.sample(1).iloc[0]
        fpath  = Path(row["rel_path"])
        if not fpath.exists():
            ax.set_title(sp[:14], fontsize=6)
            continue
        try:
            img = Image.open(fpath).convert("RGB")
            ax.imshow(img)
        except Exception:
            pass
        ax.set_title(sp[:14], fontsize=5.5)
        ax.axis("off")

    fig.suptitle("Sanjeevani — One Sample per Species", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  Sample grid saved: {out_path}")


def main():
    LOG_DIR.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)

    parser = argparse.ArgumentParser(description="Check class balance")
    parser.add_argument("--csv", default="metadata/master_labels.csv")
    parser.add_argument("--no-grid", action="store_true",
                        help="Skip sample_grid.png (faster when many images)")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found. Run build_master_csv.py first.")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    counts = df.groupby("species_name").size().sort_values(ascending=False)

    ok       = (counts >= MIN_IMAGES).sum()
    low      = ((counts >= CRITICAL_THRESHOLD) & (counts < MIN_IMAGES)).sum()
    critical = (counts < CRITICAL_THRESHOLD).sum()

    print(f"\n── Class Balance Report ──────────────────────────────────")
    print(f"  Total images:    {len(df):,}")
    print(f"  Total species:   {df['species_name'].nunique()}")
    print(f"  Mean per class:  {counts.mean():.0f}")
    print(f"  Median:          {counts.median():.0f}")
    print(f"  Min:             {counts.min()}  ({counts.idxmin()})")
    print(f"  Max:             {counts.max()}  ({counts.idxmax()})")
    print(f"\n  OK  (≥ {MIN_IMAGES}):           {ok}")
    print(f"  Low ({CRITICAL_THRESHOLD}–{MIN_IMAGES-1}):         {low}")
    print(f"  Critical (< {CRITICAL_THRESHOLD}):    {critical}")

    if critical:
        print(f"\n  CRITICAL species:")
        for sp, cnt in counts[counts < CRITICAL_THRESHOLD].items():
            print(f"    {sp:28s} {cnt:4d}")

    bar_chart(counts, REPORTS / "class_distribution.png")
    if not args.no_grid:
        sample_grid(df, REPORTS / "sample_grid.png")

    # Write text summary
    summary_path = REPORTS / "dataset_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("Sanjeevani Dataset — Balance Summary\n")
        f.write("=" * 50 + "\n")
        f.write(f"Total images:  {len(df):,}\n")
        f.write(f"Species:       {df['species_name'].nunique()}\n")
        f.write(f"OK classes:    {ok}\n")
        f.write(f"Low classes:   {low}\n")
        f.write(f"Critical:      {critical}\n\n")
        f.write("Per-species counts:\n")
        for sp, cnt in counts.items():
            f.write(f"  {sp:30s} {cnt:5d}\n")
    print(f"\n  Summary text: {summary_path}")
    print(f"  Bar chart:    {REPORTS / 'class_distribution.png'}")


if __name__ == "__main__":
    main()
