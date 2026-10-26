"""
iNaturalist image collector for Sanjeevani dataset.
Fetches research-grade leaf observations for all 70 species.

Usage:
    python scripts/collect_inat.py                     # all species
    python scripts/collect_inat.py --priority HIGH     # HIGH priority only
    python scripts/collect_inat.py --species Tulsi Neem
    python scripts/collect_inat.py --max 300           # override max per species
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import requests
from tqdm import tqdm

from src.config import SPECIES, SPECIES_MAP

BASE_URL = "https://api.inaturalist.org/v1/observations"
SAVE_DIR = Path("data/raw/inat")
LOG_DIR  = Path("logs")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "collect_inat.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def fetch_species(taxon_name: str, folder_name: str, max_results: int = 250) -> int:
    save_path = SAVE_DIR / folder_name
    save_path.mkdir(parents=True, exist_ok=True)

    # Skip if already have enough
    existing = [f for f in save_path.iterdir() if f.suffix.lower() in ('.jpg', '.jpeg', '.png')]
    if len(existing) >= max_results:
        log.info(f"  {folder_name}: already {len(existing)} images — skipping")
        return len(existing)

    params = {
        "taxon_name":    taxon_name,
        "photos":        "true",
        "per_page":      50,
        "page":          1,
        "order_by":      "votes",
    }

    downloaded = len(existing)
    seen_ids   = {f.stem.replace("inat_", "") for f in existing}

    with tqdm(total=max_results, initial=downloaded,
              desc=f"  {folder_name:22s}", unit="img", leave=False) as pbar:
        for page in range(1, 15):
            params["page"] = page
            try:
                r = requests.get(BASE_URL, params=params, timeout=30)
                r.raise_for_status()
            except requests.RequestException as e:
                log.warning(f"  {folder_name} page {page}: {e}")
                time.sleep(5)
                break

            results = r.json().get("results", [])
            if not results:
                break

            for obs in results:
                if downloaded >= max_results:
                    break
                obs_id = str(obs["id"])
                if obs_id in seen_ids:
                    continue
                photos = obs.get("photos", [])
                if not photos:
                    continue
                url = photos[0].get("url", "").replace("square", "large")
                if not url:
                    continue

                fname = save_path / f"inat_{obs_id}.jpg"
                try:
                    img_resp = requests.get(url, timeout=20)
                    img_resp.raise_for_status()
                    # Skip tiny responses (likely missing images)
                    if len(img_resp.content) < 5000:
                        continue
                    fname.write_bytes(img_resp.content)
                    seen_ids.add(obs_id)
                    downloaded += 1
                    pbar.update(1)
                    time.sleep(0.25)
                except Exception as e:
                    log.debug(f"    download error {url}: {e}")

            if downloaded >= max_results:
                break
            time.sleep(0.5)

    log.info(f"  {folder_name}: {downloaded} images total")
    return downloaded


def main():
    LOG_DIR.mkdir(exist_ok=True)
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser(description="Collect iNaturalist images")
    parser.add_argument("--priority", choices=["HIGH", "MEDIUM", "LOW", "ALL"],
                        default="ALL", help="Which priority tier to fetch")
    parser.add_argument("--species", nargs="+", metavar="NAME",
                        help="Specific species folder names (e.g. Tulsi Neem)")
    parser.add_argument("--max", type=int, default=250,
                        help="Max images per species (default: 250)")
    args = parser.parse_args()

    if args.species:
        targets = [(n, b, a, p) for (n, b, a, p) in SPECIES if n in args.species]
        missing = set(args.species) - {n for n, *_ in targets}
        if missing:
            log.warning(f"Unknown species names: {missing}")
    elif args.priority == "ALL":
        targets = SPECIES
    else:
        targets = [(n, b, a, p) for (n, b, a, p) in SPECIES if p == args.priority]

    log.info(f"Collecting {len(targets)} species from iNaturalist (max {args.max} each)")

    summary = []
    for folder_name, botanical, _, priority in targets:
        log.info(f"[{priority}] {folder_name} ({botanical})")
        count = fetch_species(botanical, folder_name, max_results=args.max)
        summary.append((folder_name, count))

    print("\n── iNaturalist Collection Summary ──────────────────")
    for name, cnt in sorted(summary, key=lambda x: x[1]):
        status = "OK" if cnt >= 150 else ("LOW" if cnt >= 80 else "CRITICAL")
        bar    = "█" * min(cnt // 10, 40)
        print(f"  {name:25s} {cnt:4d}  [{status:8s}]  {bar}")
    print(f"\n  Total species fetched: {len(summary)}")
    print(f"  Total images:          {sum(c for _, c in summary)}")


if __name__ == "__main__":
    main()
