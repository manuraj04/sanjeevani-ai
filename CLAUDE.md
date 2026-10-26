# CLAUDE.md — System Context, Technical Audit & Engineering Roadmap
**Project:** Sanjeevani Scan: Deep Learning for Real-Time Identification of Indian Ayurvedic Medicinal Plants with Integrated Knowledge Retrieval  
**Current Date:** October 2026  
**Auditor / Architect:** Antigravity AI Engineering  
**Intended Audience:** Claude Code, GitHub Collaborators, IEEE Manuscript Reviewers & Developers  

---

## 1. EXECUTIVE SUMMARY & PROJECT BLUEPRINT

### 1.1 What is Sanjeevani Scan?
Sanjeevani Scan is an AI-driven ethno-medicinal plant identification and clinical Ayurvedic informatics system designed for:
1. **Botanical Computer Vision:** Classifying Indian Ayurvedic medicinal flora from leaf photographs across 66 botanical classes.
2. **Explainable AI (XAI):** Generating convolutional attention heatmaps via Grad-CAM to visually substantiate predictions along leaf margins and venation.
3. **Structured Ayurvedic Pharmacopoeia:** Querying an SQLite relational database mapping 63 species to classical properties (*Tridosha, Rasa, Guna, Virya, Vipaka, Prabhava*), 129 therapeutic indications, 76 bioactive phytochemicals, and 63 contraindications cross-referenced against the IMPPAT database.
4. **Reverse Semantic Symptom Search:** Utilizing Sentence-BERT (`all-MiniLM-L6-v2`) embeddings with a FAISS vector index (`IndexFlatIP`, Cosine Similarity) to match descriptive symptoms (e.g., *"joint pain and burning sensation"*) to ranked medicinal plants in under 10 ms.
5. **Cross-Platform Mobile Application:** A React Native Expo client localized into 6 Indian languages (English, Hindi, Kannada, Tamil, Telugu, Malayalam).

---

## 2. REPOSITORY INVENTORY & WHERE THINGS LIVE

```text
d:\Sanjeevani Scan AI\
├── data/
│   ├── raw/                           # 46,069 raw images (inat: 25,152, kaggle_medleaf: 20,509, bing: 329, gbif: 79)
│   │   ├── review/                    # 22 quarantined images (pHash duplicates / overexposed)
│   │   └── medicinal-plant-dataset-augmented.zip # 1.41 GB Kaggle pre-augmented archive
│   └── processed/                     # 45,530 processed images (45,280 plant + 250 non-plant)
│       ├── train/                     # 28,434 images across 67 folders (66 plants + Non_Plant)
│       ├── val/                       # 8,688 images across 67 folders (66 plants + Non_Plant)
│       ├── test/                      # 8,408 images across 66 plant folders (SEALED EVALUATION SET)
│       ├── best_model_final.pth       # Deployed PyTorch weights (66 classes, 80.47 MB, Top-1: 95.50%)
│       ├── sanjeevani.onnx            # Exported ONNX graph (79.50 MB, opset 13)
│       ├── sanjeevani_quantized.tflite# TFLite model with dynamic range quantization (21.57 MB, Top-1: 93.33%)
│       ├── sanjeevani_kb.db           # SQLite 3 Knowledge Base (63 species, 129 uses, 76 phytochemicals)
│       └── ayurvedic_knowledge.json   # Exported master JSON used by mobile offline library
│
├── metadata/
│   ├── master_labels.csv              # Single source of truth manifest (31,682 rows)
│   ├── split_log.csv                  # Stratified split manifest (31,682 rows: 22,176 train, 4,753 val, 4,753 test)
│   ├── class_weights.json / .csv      # Inverse frequency class weights for loss rebalancing
│   ├── imppat_species_map.csv         # 68 species verified against IMPPAT database
│   └── cleaning_summary.csv           # Cleaning log from perceptual hashing and quality filter
│
├── src/
│   ├── api/
│   │   ├── main.py                    # FastAPI gateway: /predict, /explain, /plant/{id}, /plants, /search
│   │   ├── explainability.py          # PyTorch GradCAM generator targeting EfficientNet features[-1]
│   │   ├── semantic_search.py         # FAISS vector similarity search (all-MiniLM-L6-v2)
│   │   └── offline_inference.py       # Standalone Python TFLite interpreter + local DB query
│   │
│   ├── db/
│   │   ├── schema.sql                 # SQLite schema with foreign keys and indexes
│   │   ├── expand_knowledge_base.py   # Populates database with 66-class encyclopedic details
│   │   ├── extract_imppat.py          # Botanical taxonomy extractor
│   │   └── audit_all_data.py          # Complete SQL verification and integrity check
│   │
│   ├── processing/
│   │   ├── clean_images.py            # Automated image filtering (pHash 16-bit, size, aspect, brightness)
│   │   ├── build_master_csv.py        # Assembles master_labels.csv from raw folders
│   │   └── split_dataset.py           # Stratified 70/15/15 train_test_split (seed=42)
│   │
│   ├── mobile/
│   │   ├── App.js                     # React Native Expo application (Scan, Library, Search, Glossary)
│   │   ├── services/plantService.js   # 3-tier fallback knowledge resolver and offline search
│   │   ├── constants/i18n.js          # 6-language UI localization and medical disclaimer
│   │   ├── constants/references.js    # Verified Wikimedia Commons reference photos for all 66 classes
│   │   └── assets/ayurvedic_knowledge.json # Bundled offline knowledge base for zero-network use
│   │
│   ├── train.py                       # 3-Phase Transfer Learning training loop (AdamW, CosineAnnealingLR)
│   ├── resume_train.py                # Resumes Phase 3 fine-tuning
│   ├── inference.py                   # PyTorch inference class with Out-Of-Distribution (OOD) rejection
│   └── convert_to_onnx.py             # PyTorch -> ONNX exporter
│
├── test_api.py                        # Endpoint verification script (predict & explain)
├── test_deep_run.py                   # Comprehensive API integration test suite
└── requirements.txt                   # Production Python dependencies
```

---

## 3. VERIFIED TECHNICAL AUDIT: IMPLEMENTED VS. CLAIMED

The following table distinguishes verified code reality from project report claims:

| Feature / Metric | Claimed in Report / Paper | Verified Reality in Codebase | Verification Status |
| :--- | :--- | :--- | :--- |
| **Model Backbone** | Multi-Scale Attention CNN | Stock `torchvision.models.efficientnet_v2_s` | **VERIFIED** (Stock EfficientNet) |
| **CBAM Attention** | Channel & Spatial Attention (CBAM) | **Zero lines of CBAM code exist.** Documented as "conceptually integrated". | **NOT IMPLEMENTED** |
| **Feature Fusion** | Multi-scale fusion of stages 3, 5, 7 | Only standard `AdaptiveAvgPool2d` global pooling | **NOT IMPLEMENTED** |
| **Model Head** | Dropout + Dense + GELU | `Dropout(0.4) -> Linear(1280, 512) -> GELU -> Dropout(0.3) -> Linear(512, 66)` | **VERIFIED** |
| **Total Parameters** | Not precisely reported | **20,867,218 parameters (20.87 M)** | **VERIFIED** |
| **Dataset Images** | 12,000–18,000 images | **45,530 processed images (45,280 plant images)**; 46,069 raw images | **VERIFIED** |
| **Plant Classes** | 60–80 species | **66 botanical visual classes mapped to 63 species** | **VERIFIED** |
| **PyTorch Top-1 Acc** | 89.4% (placeholder) | **95.50%** on 8,408 sealed test images | **VERIFIED (MEASURED)** |
| **PyTorch Top-5 Acc** | 98.2% (placeholder) | **98.80%** on 8,408 sealed test images | **VERIFIED (MEASURED)** |
| **Macro Average F1** | 0.881 | **0.9455** (Weighted F1: 0.9546) | **VERIFIED (MEASURED)** |
| **Grad-CAM** | Visual attention heatmaps | Implemented in `src/api/explainability.py` on `features[-1]` | **VERIFIED** (API only) |
| **TFLite Model Size** | < 20 MB (18.7 MB) | **21.57 MB (22,620,552 bytes)** | **CONTRADICTED** (> 20 MB) |
| **TFLite Accuracy** | < 0.8% degradation | **93.33% Top-1** (2.17% drop from PyTorch 95.50%) | **CONTRADICTED** |
| **Quantization** | Full INT8 Quantization | Post-training **dynamic range 8-bit weight quantization** | **PARTIALLY VERIFIED** |
| **Offline Mobile Scan** | 100% Offline Mobile AI Scan | Mobile app calls `POST http://<ip>:8000/predict`. Fails in airplane mode. | **CONTRADICTED** |
| **Offline Encyclopedia**| Offline SQLite on device | Bundled `assets/ayurvedic_knowledge.json` used by mobile app | **VERIFIED** |
| **Semantic Search** | Sentence-BERT + FAISS (<50ms) | `all-MiniLM-L6-v2` + FAISS `IndexFlatIP`. Measured latency: **7.24 ms**. | **VERIFIED (MEASURED)** |
| **Background Removal** | Segmented via `rembg` | Zero `rembg` imports or execution | **NOT IMPLEMENTED** |
| **Baselines** | ResNet50, MobileNetV3 | Zero baseline training scripts or checkpoints | **NOT IMPLEMENTED** |
| **User Study** | Validated with Ayurvedic Vaidyas | Marked as pending in `OBJ5_System_Integration_Evaluation.md:L85` | **NOT IMPLEMENTED** |

---

## 4. ROOT CAUSE ANALYSIS: WHY ARE THINGS STILL MISSING?

Why did the project objectives not match the code 100%? Here is the exact technical diagnosis:

1. **The Disconnect Between Theoretical Design and Rapid Prototyping:**
   The paper proposal and `methodology.txt` laid out an aspirational system including CBAM, multi-scale feature pyramids, `rembg` background segmentation, and full on-device mobile C++ TFLite execution. However, during execution, standard PyTorch `torchvision.models.efficientnet_v2_s` already delivered strong results (>95% accuracy) using ImageNet transfer learning. Consequently, custom CBAM blocks were deferred, leaving the note: *"CBAM blocks are conceptually integrated"*.

2. **Kaggle Pre-Augmentation & Data Leakage Blindspot:**
   One raw data source (`vishnuoum/medicinal-plant-dataset-augmented`) was ingested directly into `data/raw/kaggle_medleaf`. That archive already contained synthetic rotations of the same physical leaves (`__0_...`, `__100_...`). Because `split_dataset.py` split files by row index using `train_test_split(stratify=species)` without grouping by original leaf photograph ID, near-duplicate images leaked across train and test splits, artificially boosting test accuracy to 95.50%.

3. **Taxonomic Redundancy (Bringaraj vs. Bhringraj):**
   The vision dataset contains two separate classes: `Bringaraj` (*Eclipta alba*) and `Bhringraj` (*Eclipta prostrata*). In botanical and Ayurvedic taxonomy, these are synonyms for the exact same plant. Because they have identical morphology, the model suffered its worst error rate here (**Bringaraj F1 = 0.6364**; **Bhringraj F1 = 0.8862**) purely due to class label duplication.

4. **Mobile Client Architectural Trade-Off:**
   Embedding a custom C++ TFLite interpreter with TensorFlow Flex ops inside a React Native Expo managed workflow requires ejecting to bare React Native (`npx expo prebuild`) or custom native bridging (`react-native-fast-tflite`). To keep the mobile app portable across Expo Go on both iOS and Android, the developer wired `uploadAndAnalyze()` to send HTTP multipart requests to the FastAPI backend, postponing true on-device edge execution.

5. **Quantization Precision Gap:**
   Converting an EfficientNetV2 graph to full integer INT8 requires generating a representative calibration dataset in TensorFlow. The conversion script (`convert_tflite_quantized_static.py`) used `converter.optimizations = [tf.lite.Optimize.DEFAULT]`, which defaults to **dynamic range quantization** (weights quantized to 8 bits, activations computed in float32). This resulted in a **21.57 MB** model rather than <20 MB, and caused a **2.17 percentage-point drop** in accuracy.

---

## 5. PRIORITIZED ENGINEERING ROADMAP

Follow this sequence to finish the unimplemented objectives:

### Phase 1: Core Architecture Upgrade (P0 — Immediate)
- [ ] **Task 1.1: Implement CBAM Module in PyTorch (`src/models/cbam.py`)**  
  Implement the mathematically authentic Convolutional Block Attention Module:
  - Channel Attention: $M_c(F) = \sigma(\text{MLP}(\text{AvgPool}(F)) + \text{MLP}(\text{MaxPool}(F)))$
  - Spatial Attention: $M_s(F) = \sigma(f^{7\times 7}([\text{AvgPool}(F); \text{MaxPool}(F)]))$
- [ ] **Task 1.2: Build Multi-Scale Attention CNN Backbone (`src/models/cbam_efficientnet.py`)**  
  Integrate CBAM into EfficientNetV2-S at Stage 3 ($28\times 28$), Stage 5 ($14\times 14$), and Stage 7 ($7\times 7$), followed by multi-scale feature concatenation into the 512-dim classifier head.
- [ ] **Task 1.3: Taxonomic Reconciliation**  
  Merge `Bringaraj` and `Bhringraj` into a single class in the master manifest to resolve the 0.6364 F1 failure mode.

### Phase 2: Retraining & Baseline Benchmarks (P1 — Core ML)
- [ ] **Task 2.1: Leakage-Free Dataset Partitioning**  
  Group pre-augmented images by parent image ID before splitting so that transformed variants never cross between train and test sets.
- [ ] **Task 2.2: Retrain Upgraded CBAM Architecture**  
  Run training with AdamW, CosineAnnealingLR, label smoothing ($\varepsilon=0.1$), and log full epoch histories to CSV.
- [ ] **Task 2.3: Train Baseline Models for IEEE Comparisons**  
  Train stock ResNet50 and MobileNetV3 on the identical split to provide empirical baseline comparison tables for the research paper.
- [ ] **Task 2.4: Generate Formal Experimental Figures**  
  Save genuine PNG figures: Training/Validation Loss Curves, 66-class Confusion Matrix, and side-by-side Grad-CAM comparisons (EfficientNetV2 vs. CBAM).

### Phase 3: Edge Quantization & Mobile Offline Inference (P2 — Deployment)
- [ ] **Task 3.1: Full INT8 Quantization with Calibration**  
  Supply a representative dataset generator to `TFLiteConverter` to achieve true INT8 integer quantization and compress file size below **18 MB**.
- [ ] **Task 3.2: On-Device Mobile Vision Inference**  
  Integrate `react-native-fast-tflite` into the React Native app so `App.js` can classify camera frames in airplane mode without network requests.

---

## 6. QUICK START & RUNNING COMMANDS

### 6.1 Backend API & Semantic Search
```powershell
# Activate Python 3.11 Virtual Environment
.\.venv\Scripts\activate

# Run FastAPI Development Server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Execute End-to-End Test Suite
python test_deep_run.py
```

### 6.2 Mobile Application (Expo)
```powershell
cd src\mobile
npm install
npm start
# Press 'w' for Web preview, or scan QR code with Expo Go on Android/iOS
```

### 6.3 Evaluating PyTorch & TFLite Models
```powershell
# Test PyTorch FP32 on full sealed test set (8,408 images)
python scratch/eval_test.py

# Test TFLite Quantized model on test samples
.\.venv\Scripts\python.exe scratch/eval_tflite_sample.py

# Benchmark FAISS Semantic Retrieval Latency
.\.venv\Scripts\python.exe scratch/benchmark_search.py
```
