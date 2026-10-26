# 🌿 Sanjeevani Scan AI — System Architecture & Antigravity Setup Guide

> **Notice for Antigravity / AI Agents & Developers:**  
> This document is the single source of truth for understanding, booting, maintaining, and developing the **Sanjeevani Scan AI** system. Follow this guide when setting up the workspace on a new machine (including laptops with integrated Intel Iris graphics / no dedicated GPU).

---

## 1. Project Overview & Identity

**Sanjeevani Scan AI** is an offline-capable Ayurvedic botanical scanner and clinical knowledge engine. It bridges modern computer vision with classical Ayurvedic pharmacopoeia.

### Key Capabilities
1. **Botanical Computer Vision:** ResNet-based deep learning classifier trained on **66 plant classes** with Out-Of-Distribution (OOD) non-plant rejection.
2. **Visual Explainability (Grad-CAM):** Generates convolutional attention heatmaps showing which leaf veins, margins, and textures influenced the classification.
3. **Ayurvedic Knowledge Base:** Curated database of **63 botanical species** (covering all 66 model classes and taxonomic aliases) with complete taxonomy, Rasa, Guna, Virya, Vipaka, Prabhava, therapeutic indications, bioactive phytochemicals, and contraindications.
4. **Semantic Symptom Search:** FAISS vector database powered by `sentence-transformers/all-MiniLM-L6-v2` indexing 129 therapeutic conditions.
5. **Multilingual Localization:** Native translations across **6 Indian languages** (English, Hindi, Kannada, Tamil, Telugu, Malayalam).
6. **Offline-First Mobile Client:** React Native Expo app that functions completely offline for library exploration, symptom search, and glossary lookup, falling back to local storage seamlessly.

---

## 2. Directory Structure & Key Files

```text
d:\Sanjeevani Scan AI\
├── data/
│   └── processed/
│       ├── sanjeevani_kb.db          # SQLite master database (63 species, 129 uses, 76 phytochemicals)
│       ├── ayurvedic_knowledge.json  # Master JSON export of all 63 botanical profiles
│       ├── sanjeevani.onnx           # Exported ONNX model (CPU / Intel Iris optimized)
│       ├── sanjeevani_quantized.tflite # Int8 quantized TensorFlow Lite model for edge mobile
│       └── best_model_final.pth      # PyTorch model weights (66 classes)
│
├── src/
│   ├── api/
│   │   ├── main.py                   # FastAPI server, endpoints, and CORS config
│   │   ├── classifier.py             # Inference pipeline & confidence scoring (Torch CPU/CUDA auto-detect)
│   │   ├── gradcam.py                # Grad-CAM heatmap generation engine
│   │   ├── semantic_search.py        # FAISS vector similarity search engine
│   │   └── offline_inference.py      # Standalone local inference utilities
│   │
│   ├── db/
│   │   ├── schema.sql                # SQLite relational schema
│   │   ├── populate_db.py            # Database build & populator script
│   │   ├── expand_knowledge_base.py  # 66-herb knowledge base expansion tool
│   │   └── audit_all_data.py         # Complete verification & integrity test suite
│   │
│   └── mobile/
│       ├── App.js                    # Main React Native Expo application (4 tabs: Scan, Library, Search, Glossary)
│       ├── app.json                  # Expo configuration
│       ├── package.json              # Mobile client dependencies
│       ├── assets/
│       │   └── ayurvedic_knowledge.json # Bundled offline knowledge base for zero-network usage
│       ├── constants/
│       │   ├── i18n.js               # 6-language UI dictionary and glossary terms
│       │   └── references.js         # Verified reference botanical imagery for all 66 classes
│       └── services/
│           └── plantService.js       # 3-tier profile resolution, search, and fallback synthesizers
│
├── requirements.txt                  # Python dependencies (Torch, FastAPI, OpenCV, FAISS, etc.)
├── PRODUCTION_DEPLOYMENT_GUIDE.pdf   # Print-ready 4-page production deployment manual
└── ANTIGRAVITY_SYSTEM_GUIDE.md       # This file
```

---

## 3. Hardware & Runtime Compatibility

- **Dedicated GPU (Nvidia CUDA):** Supported automatically if available.
- **Integrated GPU / CPU (Intel Iris / AMD / Apple Silicon):** 100% supported.
  - The model loader in `src/api/classifier.py` checks `torch.cuda.is_available()`. If no CUDA GPU is detected, it automatically loads onto the CPU.
  - Inference latency on Intel Iris / modern Core i5/i7 CPU is **~150–250 ms**, which is near-instantaneous for mobile camera scans.

---

## 4. Step-by-Step Environment Bootstrap

### Step 4.1: Python Backend Setup (Terminal 1)

1. Open PowerShell or Command Prompt in the repository root:
   ```powershell
   # 1. Create a virtual environment
   python -m venv .venv

   # 2. Activate the virtual environment
   .\.venv\Scripts\activate

   # 3. Upgrade pip
   python -m pip install --upgrade pip

   # 4. Install required dependencies
   pip install -r requirements.txt
   ```

2. Run the database and data integrity audit:
   ```powershell
   python src/db/audit_all_data.py
   ```
   *(Expected output: 63 plants in DB, 0 missing mappings, 0 missing classes, 0 missing reference images).*

3. Start the FastAPI server:
   ```powershell
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   ```
   *(The server will initialize the PyTorch model, build the FAISS index with 129 vectors, and listen on port 8000).*

---

### Step 4.2: React Native Mobile Setup (Terminal 2)

1. Open a second PowerShell window and enter the mobile folder:
   ```powershell
   cd src\mobile
   ```

2. Install Node dependencies:
   ```powershell
   npm install
   ```

3. Launch the Expo bundler:
   ```powershell
   npx expo start
   ```

4. Connect your phone:
   - Ensure your mobile device is on the **same Wi-Fi network** or **mobile hotspot** as the laptop.
   - Open **Expo Go** on Android (or Camera app on iOS) and scan the QR code displayed in the terminal.
   - `App.js` automatically resolves the backend URL using `Constants.expoConfig?.hostUri` to dynamically target the host laptop IP on port `8000`.

---

## 5. Core Architectural Concepts

### 5.1 Three-Tier Profile Resolution
In `src/mobile/App.js` and `src/mobile/services/plantService.js`, the app uses a **3-tier fail-safe resolver** to ensure that scanned plant details **never vanish**:

```text
[Scan Photo Uploaded]
         │
         ▼
[Tier 1: Live API Database] ──(Found?)──► Render Complete Profile
         │ (Fails / Offline / plant_id null)
         ▼
[Tier 2: Bundled Offline JSON] ──(Found?)──► Render Normalized Profile
         │ (Exotic / Unindexed Species)
         ▼
[Tier 3: Synthetic Fallback Engine] ─────► Render Synthesized Profile
```

### 5.2 Model Classes vs. Database Species
- The deep learning model recognizes **66 classes**.
- The botanical database contains **63 distinct species** because:
  - `HolyBasilVana` is mapped to `Tulsi` (*Ocimum tenuiflorum*).
  - `Amruth` is mapped to `Giloy` (*Tinospora cordifolia*).
  - `Bringaraj` is mapped to `Bhringraj` (*Eclipta prostrata*).
- `CLASS_TO_SPECIES` in `src/api/main.py` maps all 66 classes cleanly, and the database query uses:
  ```sql
  SELECT plant_id, common_name, common_names_json 
  FROM plants 
  WHERE species_name = ? OR common_name = ? OR common_name LIKE ?
  ```

### 5.3 Semantic Search & Vector Embeddings
- `src/api/semantic_search.py` builds an in-memory **FAISS** vector index at API startup.
- It encodes descriptions from the `therapeutic_uses` table using `all-MiniLM-L6-v2`.
- Queries like *"burning urination"*, *"joint swelling"*, or *"insomnia"* perform cosine similarity search over embeddings to return the most clinically relevant medicinal herbs.

---

## 6. API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Health check & welcome message. |
| `POST` | `/predict` | Multipart upload (`file`). Returns `{ status, prediction, confidence, plant_id, common_name }`. |
| `POST` | `/explain` | Multipart upload (`file`). Returns `{ status, heatmap_base64 }` for Grad-CAM overlay. |
| `GET` | `/plant/{plant_id}` | Returns full botanical & Ayurvedic knowledge profile for a specific plant ID. |
| `GET` | `/plants?lang={code}` | Returns list of all flora in the database, localized into the selected language. |
| `GET` | `/search?query={text}` | Semantic vector search across therapeutic conditions and symptoms. |

---

## 7. Troubleshooting & Operational Guide

### Issue: "Port 8000 is already in use"
**Fix:**
```powershell
netstat -ano | findstr :8000
taskkill /F /PID <PID>
```

### Issue: "Cannot connect to Expo CLI" / Network Timeout on Mobile
**Fix:**
1. Check that both the phone and laptop are on the same Wi-Fi network.
2. In Windows Defender Firewall, allow port `8000` and port `8081`:
   ```powershell
   New-NetFirewallRule -DisplayName "Sanjeevani API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
   ```
3. Restart Expo with cache cleared:
   ```powershell
   npx expo start -c
   ```

### Issue: Rebuilding the Database Fresh
If you ever edit botanical data or add new herbs:
```powershell
# 1. Update/expand knowledge
python src/db/expand_knowledge_base.py

# 2. Rebuild SQLite database
python src/db/populate_db.py

# 3. Verify complete coverage
python src/db/audit_all_data.py
```

---

*Authored for the Sanjeevani Scan AI Development Team & Antigravity IDE.*
