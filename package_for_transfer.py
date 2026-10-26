import os
import zipfile
import time

def create_transfer_package():
    start_time = time.time()
    zip_filename = "Sanjeevani_App_Transfer.zip"
    
    print(f"Packaging Sanjeevani Scan AI for deployment to second laptop...")
    print(f"Skipping unnecessary 40GB+ of raw training data and virtual environment...\n")

    # Files to include directly from root
    root_files = [
        "requirements.txt",
        "test_deep_run.py",
        "convert_md_to_pdf.py",
        "PRODUCTION_DEPLOYMENT_GUIDE.md",
        "PRODUCTION_DEPLOYMENT_GUIDE.pdf",
        "Presentation_Explanation.md"
    ]

    # Crucial data files needed for app & inference
    crucial_data_files = [
        os.path.join("data", "processed", "best_model_final.pth"),
        os.path.join("data", "processed", "sanjeevani_kb.db"),
        os.path.join("data", "processed", "ayurvedic_knowledge.json")
    ]

    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. Add root files
        for f in root_files:
            if os.path.exists(f):
                zipf.write(f, f)
                print(f"Added: {f}")

        # 2. Add crucial data files
        for f in crucial_data_files:
            if os.path.exists(f):
                zipf.write(f, f)
                print(f"Added: {f}")

        # 3. Add src/ code (excluding node_modules or cache)
        for root, dirs, files in os.walk("src"):
            # Skip node_modules, .expo, __pycache__
            if "node_modules" in root or ".expo" in root or "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(('.pyc', '.pyo')):
                    continue
                filepath = os.path.join(root, f)
                zipf.write(filepath, filepath)

        # 4. Add test image samples so test_deep_run.py can run
        test_dir = os.path.join("data", "processed", "test")
        if os.path.exists(test_dir):
            count = 0
            for root, dirs, files in os.walk(test_dir):
                for f in files:
                    if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                        filepath = os.path.join(root, f)
                        zipf.write(filepath, filepath)
                        count += 1
                        if count >= 30: # Include a few samples across classes for testing
                            break
                if count >= 30:
                    break
            print(f"Added {count} test sample leaf images for verification.")

        # 5. Add a 1-step Quickstart guide inside the zip
        readme_content = """===============================================================
SANJEEVANI SCAN AI — QUICKSTART ON INTEL IRIS / CPU LAPTOP
===============================================================

Prerequisites:
- Python 3.10 or 3.11 installed
- Node.js (v18 or v20 LTS) installed

Step 1: Open Terminal / PowerShell in this folder:
   python -m venv .venv
   .venv\\Scripts\\pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   .venv\\Scripts\\pip install -r requirements.txt

Step 2: Install Mobile dependencies:
   cd src/mobile
   npm install
   cd ../..

Step 3: Run the API (CPU mode works automatically with Intel Iris):
   .venv\\Scripts\\python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

Step 4: Start Expo Mobile App:
   cd src/mobile
   npx expo start
"""
        zipf.writestr("QUICKSTART_SECOND_LAPTOP.txt", readme_content)
        print("Added: QUICKSTART_SECOND_LAPTOP.txt")

    elapsed = round(time.time() - start_time, 2)
    zip_size_mb = round(os.path.getsize(zip_filename) / (1024 * 1024), 2)
    print(f"\nSUCCESS! Package created: {zip_filename}")
    print(f"Total Size: {zip_size_mb} MB (compressed from 40GB+ down to only what's needed!)")
    print(f"Completed in {elapsed} seconds.")

if __name__ == "__main__":
    create_transfer_package()
