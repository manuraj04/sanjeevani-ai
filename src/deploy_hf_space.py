"""
Packages and deploys the Sanjeevani Scan AI FastAPI + PyTorch + Grad-CAM + IMPPAT DB
backend directly to a public Hugging Face Docker Space (16GB RAM Free Tier).
"""
import os
import sys
import shutil
import argparse
from huggingface_hub import HfApi

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGE_DIR = r"C:\Users\soumy\.gemini\antigravity\brain\9675b33f-db5d-4e4a-9b3a-fb83e2c0ee8c\scratch\hf_space_bundle"

HF_SPACE_README = """---
title: Sanjeevani Scan AI API
emoji: 🌿
colorFrom: green
colorTo: emerald
sdk: docker
app_port: 7860
pinned: false
---

# Sanjeevani Scan AI — Cloud Vision & Ayurvedic Knowledge API

Production FastAPI backend serving EfficientNetV2-S (95.74% Test / 96.18% Canonical Taxon accuracy across 66 classes), Grad-CAM explainability heatmaps, FAISS semantic symptom search, and the IMPPAT 2.0 63-species Ayurvedic relational database.
"""


def stage_bundle():
    if os.path.exists(STAGE_DIR):
        shutil.rmtree(STAGE_DIR)
    os.makedirs(STAGE_DIR, exist_ok=True)

    # Space README with Docker SDK metadata
    with open(os.path.join(STAGE_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(HF_SPACE_README)

    # Core Docker & Python files
    for fname in ["Dockerfile", "requirements.txt", ".dockerignore"]:
        src_f = os.path.join(PROJECT_ROOT, fname)
        if os.path.exists(src_f):
            shutil.copy2(src_f, os.path.join(STAGE_DIR, fname))

    # Required src modules
    os.makedirs(os.path.join(STAGE_DIR, "src", "api"), exist_ok=True)
    for rel in ["src/__init__.py", "src/config.py", "src/inference.py"]:
        shutil.copy2(os.path.join(PROJECT_ROOT, rel), os.path.join(STAGE_DIR, rel))

    for fn in os.listdir(os.path.join(PROJECT_ROOT, "src", "api")):
        if fn == "__pycache__":
            continue
        src_p = os.path.join(PROJECT_ROOT, "src", "api", fn)
        if os.path.isfile(src_p):
            shutil.copy2(src_p, os.path.join(STAGE_DIR, "src", "api", fn))

    # Required database & PyTorch model weights
    os.makedirs(os.path.join(STAGE_DIR, "data", "processed"), exist_ok=True)
    for rel in ["data/processed/sanjeevani_kb.db", "data/processed/best_model_final.pth"]:
        shutil.copy2(os.path.join(PROJECT_ROOT, rel), os.path.join(STAGE_DIR, rel))

    print(f"Staged clean Docker Space bundle at: {STAGE_DIR}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--space-name", default="sanjeevani-scan-ai-api")
    parser.add_argument("--token", default=os.environ.get("HF_TOKEN"))
    args = parser.parse_args()

    api = HfApi(token=args.token)
    try:
        me = api.whoami()
    except Exception as e:
        print(f"AUTH_REQUIRED: Not signed in to Hugging Face Hub ({e}). Run `hf auth login` first.")
        sys.exit(2)

    username = me["name"]
    repo_id = f"{username}/{args.space_name}"
    print(f"Authenticated as: {username} | Target Space: {repo_id}")

    stage_bundle()

    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk="docker",
        private=False,
        exist_ok=True,
    )
    print(f"Uploading bundle to Hugging Face Space https://huggingface.co/spaces/{repo_id} ...")
    api.upload_folder(
        folder_path=STAGE_DIR,
        repo_id=repo_id,
        repo_type="space",
        commit_message="Deploy Sanjeevani Scan AI v2.0 FastAPI + EfficientNetV2-S + Grad-CAM + IMPPAT KB",
    )
    space_host = f"https://{username.replace('_', '-').lower()}-{args.space_name.replace('_', '-').lower()}.hf.space"
    print("=" * 70)
    print(f"DEPLOYED SUCCESSFULLY!")
    print(f"Space Page:  https://huggingface.co/spaces/{repo_id}")
    print(f"Public API:  {space_host}")
    print("=" * 70)


if __name__ == "__main__":
    main()
