import os
import sqlite3
import json

import sys
sys.path.insert(0, os.path.abspath("."))

def audit():
    test_dir = os.path.join("data", "processed", "test")
    classes = sorted(os.listdir(test_dir)) if os.path.exists(test_dir) else []
    print(f"=== AUDIT: Total Model Classes ({len(classes)}) ===")

    db_path = os.path.join("data", "processed", "sanjeevani_kb.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as c FROM plants")
    plant_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM ayurvedic_profile")
    prof_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM therapeutic_uses")
    uses_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM phytochemicals")
    phyto_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM contraindications")
    contra_count = cur.fetchone()["c"]

    print(f"Plants in DB: {plant_count}")
    print(f"Ayurvedic Profiles in DB: {prof_count}")
    print(f"Therapeutic Uses in DB: {uses_count}")
    print(f"Phytochemicals in DB: {phyto_count}")
    print(f"Contraindications in DB: {contra_count}")

    # Read CLASS_TO_SPECIES from main.py via regex/ast or import
    from src.api.main import CLASS_TO_SPECIES

    missing_mapping = []
    missing_in_db = []
    missing_profile = []
    missing_uses = []
    missing_phyto = []
    missing_contra = []
    missing_langs = []

    languages = ['en', 'hi', 'kn', 'ta', 'te', 'ml']

    for c in classes:
        if c not in CLASS_TO_SPECIES:
            missing_mapping.append(c)
        species = CLASS_TO_SPECIES.get(c, c)
        cur.execute("SELECT plant_id, species_name, common_name, common_names_json FROM plants WHERE species_name = ? OR common_name = ?", (species, c))
        row = cur.fetchone()
        if not row:
            missing_in_db.append(c)
            continue
        
        pid = row["plant_id"]
        # Check langs
        cnames = {}
        if row["common_names_json"]:
            try:
                cnames = json.loads(row["common_names_json"])
            except:
                pass
        for l in languages:
            if l not in cnames:
                missing_langs.append((c, l))

        # Check profile
        cur.execute("SELECT * FROM ayurvedic_profile WHERE plant_id = ?", (pid,))
        if not cur.fetchone():
            missing_profile.append((c, pid))

        # Check uses
        cur.execute("SELECT * FROM therapeutic_uses WHERE plant_id = ?", (pid,))
        if not cur.fetchall():
            missing_uses.append((c, pid))

        # Check phyto
        cur.execute("SELECT * FROM phytochemicals WHERE plant_id = ?", (pid,))
        if not cur.fetchall():
            missing_phyto.append((c, pid))

        # Check contra
        cur.execute("SELECT * FROM contraindications WHERE plant_id = ?", (pid,))
        if not cur.fetchall():
            missing_contra.append((c, pid))

    print(f"\nMissing from CLASS_TO_SPECIES ({len(missing_mapping)}): {missing_mapping}")
    print(f"Missing from DB plants ({len(missing_in_db)}): {missing_in_db}")
    print(f"Missing Ayurvedic Profile ({len(missing_profile)}): {missing_profile}")
    print(f"Missing Therapeutic Uses ({len(missing_uses)}): {missing_uses}")
    print(f"Missing Phytochemicals ({len(missing_phyto)}): {missing_phyto}")
    print(f"Missing Contraindications ({len(missing_contra)}): {missing_contra}")
    print(f"Missing Language Translations ({len(missing_langs)}): {missing_langs[:10]}...")

    # Check Mobile Offline Knowledge JSON
    json_path = os.path.join("src", "mobile", "assets", "ayurvedic_knowledge.json")
    with open(json_path, "r", encoding="utf-8") as f:
        offline_data = json.load(f)
    print(f"\nOffline JSON Entries: {len(offline_data)}")

    # Check Reference Images
    ref_path = os.path.join("src", "mobile", "constants", "references.js")
    with open(ref_path, "r", encoding="utf-8") as f:
        ref_text = f.read()
    missing_refs = [c for c in classes if f'"{c}"' not in ref_text]
    print(f"Classes Missing Reference Image ({len(missing_refs)}): {missing_refs}")

if __name__ == "__main__":
    audit()
