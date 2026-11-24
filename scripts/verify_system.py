import os
import sys
import json
import sqlite3
import torch
from PIL import Image

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from src.inference import SanjeevaniClassifier
from src.api.explainability import GradCamGenerator
from src.api.offline_inference import SanjeevaniOfflineAPI

def audit_database():
    db_path = os.path.join(project_root, "data", "processed", "sanjeevani_kb.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM plants")
    plant_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM ayurvedic_profile")
    profile_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM therapeutic_uses")
    uses_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM phytochemicals")
    phyto_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM contraindications")
    contra_count = c.fetchone()[0]
    
    c.execute("SELECT plant_id, species_name, botanical_name, family FROM plants LIMIT 5")
    sample_plants = c.fetchall()
    
    conn.close()
    return {
        "plant_count": plant_count,
        "profile_count": profile_count,
        "uses_count": uses_count,
        "phyto_count": phyto_count,
        "contra_count": contra_count,
        "sample_plants": sample_plants
    }

def audit_offline_catalog():
    catalog_path = os.path.join(project_root, "src", "mobile", "assets", "ayurvedic_knowledge.json")
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "catalog_count": len(data),
        "sample_entries": [d.get("species_name") for d in data[:5]]
    }

def run_live_test_evaluations():
    model_path = os.path.join(project_root, "data", "processed", "best_model_final.pth")
    output_dir = os.path.join(project_root, "docs", "presentation_assets")
    os.makedirs(output_dir, exist_ok=True)
    
    classifier = SanjeevaniClassifier(model_path=model_path, num_classes=66, confidence_threshold=0.20)
    grad_cam = GradCamGenerator(model=classifier.model)
    
    target_herbs = ["Tulsi", "Neem", "Ashwagandha", "Moringa", "Amla", "Giloy", "Brahmi"]
    test_base = os.path.join(project_root, "data", "processed", "test")
    
    # Map common herb name to folder name in test
    folder_mapping = {
        "Tulsi": "Tulsi",
        "Neem": "Neem",
        "Ashwagandha": "Ashwagandha",
        "Moringa": "Drumstick",
        "Amla": "Amla",
        "Giloy": "Amruth",
        "Brahmi": "Brahmi"
    }
    
    eval_results = []
    
    for herb in target_herbs:
        folder = folder_mapping.get(herb, herb)
        folder_path = os.path.join(test_base, folder)
        if not os.path.exists(folder_path):
            continue
        
        files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not files:
            continue
            
        test_img_path = os.path.join(folder_path, files[0])
        
        # Save a copy to presentation_assets for markdown and PDF inclusion
        saved_leaf_path = os.path.join(output_dir, f"{herb.lower()}_test_leaf.jpg")
        with Image.open(test_img_path) as img:
            img.convert("RGB").resize((400, 400)).save(saved_leaf_path, "JPEG", quality=90)
            
        # Run classification
        pred = classifier.predict(test_img_path)
        
        # Generate heatmap
        heatmap_path = os.path.join(output_dir, f"{herb.lower()}_gradcam_heatmap.jpg")
        b64 = grad_cam.generate_heatmap_base64(test_img_path)
        if b64:
            import base64
            with open(heatmap_path, "wb") as hf:
                hf.write(base64.b64decode(b64))
        
        eval_results.append({
            "target": herb,
            "folder": folder,
            "image_file": files[0],
            "prediction": pred.get("prediction"),
            "confidence": pred.get("confidence"),
            "is_ood": pred.get("is_ood"),
            "leaf_img_rel": f"presentation_assets/{herb.lower()}_test_leaf.jpg",
            "heatmap_rel": f"presentation_assets/{herb.lower()}_gradcam_heatmap.jpg"
        })
        
    return eval_results

if __name__ == "__main__":
    db_audit = audit_database()
    print("=== DATABASE AUDIT ===")
    print(json.dumps(db_audit, indent=2))
    
    cat_audit = audit_offline_catalog()
    print("\n=== OFFLINE CATALOG AUDIT ===")
    print(json.dumps(cat_audit, indent=2))
    
    eval_results = run_live_test_evaluations()
    print("\n=== LIVE TEST EVALUATION RESULTS ===")
    print(json.dumps(eval_results, indent=2))
    
    summary_path = os.path.join(project_root, "docs", "presentation_assets", "audit_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "database": db_audit,
            "catalog": cat_audit,
            "evaluations": eval_results
        }, f, indent=2)
    print(f"\nSaved complete audit summary to: {summary_path}")
