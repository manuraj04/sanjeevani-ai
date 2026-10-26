"""
GBIF Image Collector for Sanjeevani dataset.
Downloads research-grade images for species that have fewer than 250 images.

Usage:
    python -m src.collection.collect_gbif
"""

import logging
import sys
import os
import requests
import pandas as pd
from pathlib import Path
from collections import Counter
from tqdm import tqdm
import time
import urllib.request

from src.config import SPECIES_MAP

LOG_DIR  = Path("logs")
SAVE_DIR = Path("data/raw/gbif")
META_CSV = Path("metadata/master_labels.csv")

# We want all species to have at least 250 images
TARGET_IMAGES = 250

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "collect_gbif.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

def search_gbif(scientific_name, limit=300):
    """
    Search GBIF for occurrences of the given species that have images.
    Returns a list of image URLs.
    """
    # First, we need to get the GBIF taxon key for the scientific name
    species_url = f"https://api.gbif.org/v1/species/match?name={scientific_name}"
    try:
        resp = requests.get(species_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("matchType") == "NONE" or "usageKey" not in data:
            log.warning(f"  GBIF: No taxon match found for {scientific_name}")
            return []
        
        taxon_key = data["usageKey"]
    except Exception as e:
        log.error(f"  GBIF taxon lookup failed for {scientific_name}: {e}")
        return []

    # Now search occurrences for this taxon that have media
    occurrences_url = "https://api.gbif.org/v1/occurrence/search"
    params = {
        "taxonKey": taxon_key,
        "mediaType": "StillImage",
        "limit": limit
    }
    
    image_urls = []
    try:
        resp = requests.get(occurrences_url, params=params, timeout=15)
        resp.raise_for_status()
        occ_data = resp.json()
        
        for record in occ_data.get("results", []):
            media = record.get("media", [])
            for m in media:
                if m.get("type") == "StillImage" and "identifier" in m:
                    url = m["identifier"]
                    # Skip herbarium sheets if possible (though hard to filter perfectly via API)
                    image_urls.append(url)
                    break # just take the first image of the occurrence
    except Exception as e:
        log.error(f"  GBIF occurrence search failed for {scientific_name}: {e}")
    
    return image_urls

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

    targets = []
    for sp, cnt in counts.items():
        if cnt < TARGET_IMAGES:
            targets.append((sp, TARGET_IMAGES - cnt))

    log.info(f"Identified {len(targets)} species needing images from GBIF.")

    for sp, needed in sorted(targets, key=lambda x: x[1], reverse=True):
        info = SPECIES_MAP.get(sp)
        if not info:
            continue
            
        botanical = info["botanical"]
        log.info(f"Fetching up to {needed} images for {sp} ({botanical})...")
        
        image_urls = search_gbif(botanical, limit=max(needed + 50, 300))
        
        if not image_urls:
            log.warning(f"  No images found on GBIF for {botanical}")
            continue
            
        target_folder = SAVE_DIR / sp
        target_folder.mkdir(exist_ok=True)
        
        downloaded = 0
        for i, url in enumerate(image_urls):
            if downloaded >= needed:
                break
                
            file_ext = url.split('.')[-1].lower()
            if len(file_ext) > 4 or file_ext not in ['jpg', 'jpeg', 'png']:
                file_ext = "jpg" # default fallback
                
            filename = target_folder / f"gbif_{int(time.time())}_{i}.{file_ext}"
            
            try:
                img_data = requests.get(url, timeout=5).content
                with open(filename, 'wb') as handler:
                    handler.write(img_data)
                downloaded += 1
            except Exception as e:
                pass # silently skip failed downloads
                
        log.info(f"  Successfully downloaded {downloaded} images for {sp}.")

if __name__ == "__main__":
    main()
