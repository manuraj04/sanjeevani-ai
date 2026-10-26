"""
Web image collector for Sanjeevani dataset using Bing Image Search.
Downloads images for species that are marked as LOW or CRITICAL in the dataset.

Usage:
    python -m src.collection.collect_web
"""

import logging
import sys
import shutil
import pandas as pd
from pathlib import Path
from collections import Counter
from bing_image_downloader import downloader

from src.config import SPECIES_MAP, MIN_IMAGES

LOG_DIR  = Path("logs")
SAVE_DIR = Path("data/raw/bing")
META_CSV = Path("metadata/master_labels.csv")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "collect_web.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def main():
    LOG_DIR.mkdir(exist_ok=True)
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    if not META_CSV.exists():
        log.error(f"{META_CSV} not found! Run build_master_csv.py first.")
        sys.exit(1)

    df = pd.read_csv(META_CSV)
    counts = Counter(df["species_name"])
    
    # Identify missing species (0 images)
    found_species = set(df["species_name"].unique())
    all_species = set(SPECIES_MAP.keys())
    missing = all_species - found_species
    for sp in missing:
        counts[sp] = 0

    # We want to boost any species below MIN_IMAGES (150) up to roughly 200
    targets = []
    for sp, cnt in counts.items():
        if cnt < MIN_IMAGES:
            targets.append((sp, 200 - cnt))

    log.info(f"Identified {len(targets)} species needing web images.")

    for sp, needed in sorted(targets, key=lambda x: x[1], reverse=True):
        info = SPECIES_MAP.get(sp)
        if not info:
            continue
            
        botanical = info["botanical"]
        query = f"{botanical} leaf plant"
        log.info(f"Fetching {needed} images for {sp} (Query: '{query}')")
        
        try:
            downloader.download(
                query,
                limit=needed,
                output_dir=str(SAVE_DIR),
                adult_filter_off=True,
                force_replace=False,
                timeout=20,
                verbose=False
            )
            
            # Bing downloader creates a subfolder named after the query. 
            # We need to rename/move it to the standard species folder.
            query_folder = SAVE_DIR / query
            target_folder = SAVE_DIR / sp
            
            if query_folder.exists():
                target_folder.mkdir(exist_ok=True)
                # Move files
                for f in query_folder.iterdir():
                    if f.is_file():
                        # to avoid overwriting, generate unique name
                        dest = target_folder / f"bing_{f.name}"
                        f.rename(dest)
                
                # Remove empty query folder
                try:
                    query_folder.rmdir()
                except Exception:
                    pass
                
        except Exception as e:
            log.error(f"Failed to download for {sp}: {e}")

if __name__ == "__main__":
    main()
