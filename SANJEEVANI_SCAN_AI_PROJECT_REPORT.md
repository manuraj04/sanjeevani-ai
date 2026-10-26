# 🌿 SANJEEVANI SCAN AI
## Deep Learning-Based Explainable Ayurvedic Botanical Scanner & Clinical Knowledge Engine
### Comprehensive Academic & Technical Project Report

---

**Project Title:** Sanjeevani Scan AI — Explainable Medicinal Plant Identification and Ayurvedic Pharmacopoeia System  
**Domain:** Artificial Intelligence, Deep Learning Computer Vision, Ethnobotany, Ayurvedic Clinical Informatics  
**Architecture:** Multi-Scale Attention CNN (EfficientNetV2-S / ResNet + CBAM), Grad-CAM XAI, FAISS Vector Search, SQLite, React Native (Expo)  
**Status:** Validated, Production-Ready, 100% Offline-Capable  
**Model Coverage:** 66 Botanical Classes | **Database Flora:** 63 Ayurvedic Species | **Therapeutic Vectors:** 129 Conditions | **Languages:** 6 Indian Languages  

---

## EXECUTIVE SUMMARY & ABSTRACT

India possesses one of the world's most ancient and comprehensive medicinal plant traditions, comprising over **8,000 documented species** recognized across classical Ayurvedic literature (Charaka Samhita, Sushruta Samhita, and Ashtanga Hridayam). Despite this heritage, the accurate identification of medicinal flora remains an acute bottleneck. Botanical taxonomic knowledge is concentrated among a diminishing number of senior *vaidyas* and field botanists. Misidentification of plant organs leads to therapeutic failure, toxic substitutions, and clinical hazards. While generic computer vision applications (such as Pl@ntNet and iNaturalist) exist, none are optimized for Indian Ayurvedic pharmacopoeia, none integrate classical Ayurvedic pharmacology (*Dosha, Rasa, Guna, Virya, Vipaka, Prabhava*), none provide reverse symptom-to-plant discovery, and virtually all fail in rural forests lacking cellular internet connectivity.

**Sanjeevani Scan AI** resolves this critical multi-disciplinary challenge by presenting an end-to-end, offline-first mobile and cloud ecosystem:
1. **Botanical Computer Vision:** A customized **Multi-Scale Attention CNN** built on an EfficientNetV2-S backbone with **Convolutional Block Attention Module (CBAM)** blocks, trained over **66 plant classes** with an Out-of-Distribution (OOD) rejection mechanism that prevents non-plant false positives.
2. **Explainable AI (XAI):** Embedded **Gradient-weighted Class Activation Mapping (Grad-CAM)** producing real-time attention heatmaps to visually verify that predictions stem from genuine leaf morphology (venation, margins, and trichomes) rather than background noise.
3. **Structured Ayurvedic Knowledge Engine:** A relational **SQLite database** and bundled offline JSON catalog cross-referenced against **IMPPAT** (Indian Medicinal Plants, Phytochemistry And Therapeutics) and **TKDL** (Traditional Knowledge Digital Library), detailing Tridosha balances, 76 bioactive phytochemicals, therapeutic indications, and 63 clinical contraindications.
4. **Reverse Semantic Symptom Search:** A **FAISS vector database** utilizing Sentence-BERT (`all-MiniLM-L6-v2`) embeddings over 129 clinical conditions, allowing users to describe symptoms (e.g., *"burning sensation and joint inflammation"*) and receive ranked botanical recommendations in <50ms.
5. **Offline-First Cross-Platform Mobile Client:** A **React Native (Expo)** client featuring 4 functional tabs (Scan, Library, Search, Glossary), a 3-tier fail-safe profile resolution engine, and complete multilingual localization across **6 Indian languages** (English, Hindi, Kannada, Tamil, Telugu, and Malayalam).

---

## 1. INTRODUCTION & PROBLEM DEFINITION

### 1.1 Background & Ethnomedicinal Heritage
Ayurveda is recognized globally as a comprehensive system of natural healthcare. The efficacy of Ayurvedic formulations (such as *Swarasa*, *Kwatha*, *Churna*, and *Taila*) depends fundamentally on the authenticity of the raw botanical ingredients. Traditional harvesting has always relied on phenotypic leaf, stem, and root recognition. However, rapid urbanization, habitat destruction, and the loss of oral transmission have caused a severe decline in botanical expertise.

### 1.2 The Misidentification Dilemma in Herbal Medicine
In commercial and domestic herbal preparation, phenotypic similarity between species frequently leads to dangerous substitution:
- *Tinospora cordifolia* (Giloy - immunomodulator) is easily confused with toxic wild climbers.
- *Bacopa monnieri* (Brahmi - cognitive enhancer) is substituted with *Centella asiatica* (Gotu Kola) or non-medicinal pennyworts.
- *Eclipta prostrata* (Bhringraj) and *Wedelia chinensis* share nearly identical leaf geometries.

Without scientific verification at the collection point, adulteration propagates through the supply chain, degrading medicinal efficacy and endangering patient health.

### 1.3 Key Problem Gaps in Existing Technology
1. **Absence of Indian Ayurvedic Specialization:** Global apps (Pl@ntNet, iNaturalist) are trained predominantly on European and North American flora. They misclassify Indian sub-species and lack Ayurvedic taxonomic mapping.
2. **Disconnected Knowledge Silos:** Existing classifiers only output a raw Latin binomial name. Practitioners must manually cross-reference heavy volumes of the Ayurvedic Pharmacopoeia of India (API) to obtain medicinal actions.
3. **Black-Box Decision Making:** Standard deep learning classifiers offer no explanation. For healthcare professionals, an unverified prediction is untrustworthy and clinically unacceptable.
4. **Network Dependence:** Commercial plant identification APIs require active 4G/5G connections. Rural collectors and tribal harvesters in deep forests operate with zero connectivity.
5. **No Reverse Clinical Discovery:** Traditional systems only answer *"What is this plant?"*, never *"What plant cures my symptom?"*.

### 1.4 Formal Problem Statement
> *"To design, implement, and validate an intelligent, explainable, and offline-deployable mobile computational system capable of classifying Indian Ayurvedic medicinal plant leaves across 60+ species, providing transparent visual attribution through Grad-CAM heatmaps, linking classifications instantly to structured pharmacopoeial profiles, and enabling reverse symptom-to-plant semantic discovery under zero-connectivity constraints."*

### 1.5 Five Core Research & Engineering Objectives
- **Objective 1 — Dataset Engineering:** Curate, verify, clean, and stratify a high-quality multi-source leaf image repository cross-referenced with IMPPAT records.
- **Objective 2 — Preprocessing & Augmentation:** Design an albumentations pipeline and class-rebalancing strategy to handle natural illumination and field variance.
- **Objective 3 — Model Architecture & Quantization:** Develop a Multi-Scale Attention CNN (EfficientNetV2-S + CBAM), train via two-phase transfer learning, and quantize to Int8 TFLite (<20MB) for mobile edge execution.
- **Objective 4 — Ayurvedic Knowledge Base & Semantic Search:** Construct a relational SQLite database (Tridosha, Rasa, Guna, Phytochemicals, Contraindications) and deploy FAISS vector search for reverse symptom lookup.
- **Objective 5 — System Integration & Field Evaluation:** Build a cross-platform React Native client with 6-language localization, 3-tier fallback resolution, and validate system latency and accuracy.

---

## 2. LITERATURE REVIEW & EXISTING SYSTEMS GAP ANALYSIS

A thorough review of both commercial applications and academic prototypes demonstrates clear functional deficiencies that Sanjeevani Scan AI directly overcomes:

### 2.1 Commercial & Public Applications
- **Pl@ntNet (INRIA / CIRAD):** Crowdsourced global herbarium app. While broad (30,000+ species), it exhibits high error rates on visually similar Indian medicinal plants, offers zero Ayurvedic context, requires continuous internet, and provides no explainability.
- **iNaturalist (CalAcademy / NatGeo):** Citizen science platform. Useful for biodiversity logging, but suggestions rely on asynchronous community review (taking hours or days). Purely taxonomic with no medicinal data or offline inference.
- **PictureThis (Glority Global):** Consumer gardening application. Operates behind an expensive subscription paywall ($30+/year), inaccessible to Indian students or rural vaidyas. Contains no classical Ayurvedic parameters (*Dosha/Rasa*) and operates as a closed black box.
- **LeafSnap (Smithsonian / Columbia):** Pioneer leaf-shape matcher. Discontinued and limited to North American trees on pristine white backgrounds; completely fails in natural forest environments.

### 2.2 Academic Research Prototypes
- **AyurLeaf (2019):** CNN classifier on 40 Ayurvedic species (96.76% accuracy). Limited strictly to model evaluation; lacked an application, knowledge base, or mobile deployment.
- **DeepHerb (2021):** Evaluated Xception and SVM on 40 species. Academic benchmark only; no explainability or clinical profile retrieval.
- **Ayur-PlantNet (2023):** 100 Indian species with hierarchical classification. Closest conceptual prototype, but released no deployable mobile client, no offline capability, and no reverse symptom search.
- **Kavitha et al. (2024):** High accuracy (98.3%) but limited to only 6 plant species—insufficient for real-world field utility.

### 2.3 Consolidated Comparative Gap Matrix

| Feature / Capability | Pl@ntNet | iNaturalist | PictureThis | Academic Prototypes | Sanjeevani Scan AI |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Indian Ayurvedic Species Specialization** | ❌ None | ❌ None | ❌ None | ⚠️ Partial (6–40) | **✅ 66 Classes / 63 Species** |
| **Ayurvedic Profile (*Dosha, Rasa, Guna*)** | ❌ None | ❌ None | ❌ None | ❌ None | **✅ Complete Relational DB** |
| **Explainable AI (Grad-CAM in UI)** | ❌ None | ❌ None | ❌ None | ❌ None | **✅ Real-Time Heatmap Overlay** |
| **Reverse Symptom-to-Plant Search** | ❌ None | ❌ None | ❌ None | ❌ None | **✅ FAISS Semantic Vector Search** |
| **100% Offline Mobile Inference** | ❌ No | ❌ No | ❌ No | ❌ No | **✅ Int8 Quantized TFLite (<20MB)** |
| **Multilingual Support (6 Indian Languages)** | ❌ No | ❌ No | ❌ No | ❌ No | **✅ EN, HI, KN, TA, TE, ML** |
| **Confidence-Aware Safety Re-Scan Warning** | ⚠️ Partial | ❌ No | ❌ No | ❌ No | **✅ <70% Warning / <20% OOD Reject** |
| **Cost & Open Accessibility** | ✅ Free | ✅ Free | ❌ Paywalled | ⚠️ Research Code | **✅ 100% Free / Open System** |

---

## 3. SYSTEM ARCHITECTURE & END-TO-END PIPELINE

The architecture of Sanjeevani Scan AI is organized into **four modular, decoupled tiers**, ensuring scalability, high throughput, and seamless offline failover:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER (Mobile)                      │
│   React Native (Expo) • Vision Camera • 4 Tabs: Scan/Library/Search/Glossary   │
│   Multilingual Engine (6 Languages) • Interactive Grad-CAM Heatmap Overlay  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼ (Online Mode)                         ▼ (Offline Mode)
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│           API GATEWAY LAYER          │  │       ON-DEVICE ENGINE       │
│  FastAPI (Uvicorn Async Gateway)     │  │  Quantized TFLite Model      │
│  Security Headers • OOD Filter       │  │  Bundled Offline JSON Assets │
│  Endpoints: /predict, /explain, ...  │  │  Local AsyncStorage Cache     │
└──────────────────┬───────────────────┘  └──────────────────────────────┘
                   │
    ┌──────────────┴──────────────┐
    ▼                             ▼
┌───────────────────────────┐  ┌────────────────────────────────────────┐
│     INTELLIGENCE LAYER    │  │             KNOWLEDGE LAYER            │
│  Multi-Scale Attention    │  │  SQLite Database (sanjeevani_kb.db)    │
│  CNN (EfficientNetV2-S)   │  │  63 Species • 129 Uses • 76 Phyto      │
│  Grad-CAM Module          │  │  FAISS Vector Index (all-MiniLM-L6-v2) │
└───────────────────────────┘  └────────────────────────────────────────┘
```

### 3.1 The 3-Tier Fail-Safe Profile Resolution Engine
A primary vulnerability of mobile field applications is "disappearing details" when operating in low-signal environments. Sanjeevani Scan AI implements a **3-tier hierarchical resolver**:
- **Tier 1 (Live Cloud API):** Queries the remote FastAPI server for live high-precision SQLite records and dynamic Grad-CAM heatmaps.
- **Tier 2 (Bundled Offline Knowledge Base):** If network latency exceeds 3000ms or connection fails, the app falls back to the embedded 63-species `ayurvedic_knowledge.json`, ensuring zero data loss.
- **Tier 3 (Synthetic Knowledge Synthesizer):** For uncataloged or exotic botanical varieties, an algorithmic fallback synthesizes general safety guidance and botanical classification properties.

---

## 4. OBJECTIVE 1: DATASET ENGINEERING & CURATION

Building a reliable clinical vision model requires pristine, diverse, and botanically authentic training data.

### 4.1 Data Sources
The dataset was curated from four complementary sources:
1. **Kaggle Indian Medicinal Leaves Image Dataset:** ~80 species, providing laboratory and semi-controlled leaf captures.
2. **MedLeaf Curated Herbarium Collection:** High-resolution verified specimens.
3. **iNaturalist Verified Field Observations:** Real-world observations featuring natural foliage, variable angles, and insect bites.
4. **Targeted Field Photography:** Direct manual photography for underrepresented species on neutral and field backgrounds.

### 4.2 Taxonomic Catalog (66 Classes / 63 Botanical Species)
The vision classifier recognizes **66 distinct visual classes**, mapped to **63 primary botanical species** (accounting for clinical variants and classical aliases):
- *Tulsi* (*Ocimum tenuiflorum*) and *Holy Basil Vana* (*Ocimum gratissimum*)
- *Giloy* / *Amruth* (*Tinospora cordifolia* / *T. sinensis*)
- *Bhringraj* / *Bringaraj* (*Eclipta prostrata* / *Eclipta alba*)
- *Neem* (*Azadirachta indica*), *Ashwagandha* (*Withania somnifera*), *Brahmi* (*Bacopa monnieri*)
- *Amla* (*Phyllanthus emblica*), *Haritaki* (*Terminalia chebula*), *Vibhitaki* (*Terminalia bellirica*)
- *Arjuna* (*Terminalia arjuna*), *Kalmegh* (*Andrographis paniculata*), *Shatavari* (*Asparagus racemosus*)

### 4.3 Rigorous IMPPAT Verification Protocol
Every collected class was cross-referenced against the **IMPPAT (Indian Medicinal Plants, Phytochemistry And Therapeutics)** database. Unverified submissions or disputed vernacular names were systematically purged.

### 4.4 Automated Data Cleaning Pipeline
Raw botanical data contains significant noise. An automated five-step Python pipeline processed all images:
1. **Integrity Check:** PIL bitstream decoding to eliminate truncated or corrupted JPEGs.
2. **Resolution Filtering:** Any image smaller than 64×64 pixels was discarded.
3. **Aspect Ratio Enforcement:** Extreme aspect ratios (>6:1 or <1:6) were pruned.
4. **Exposure & Contrast Thresholding:** Mean pixel brightness <10 (underexposed) or >245 (overexposed) and standard deviation <8 (blank scans) were quarantined.
5. **Perceptual Hashing (pHash):** 16-bit perceptual hashing (`imagehash.phash`) removed duplicate copies and augmented re-uploads across datasets, preventing data leakage between splits.

### 4.5 Stratified Dataset Splitting
Data was partitioned into a **70% Training / 15% Validation / 15% Test** split using stratified sampling (`random_state=42`). The test split was permanently locked to guarantee unbiased evaluation.

---

## 5. OBJECTIVE 2: PREPROCESSING, AUGMENTATION & CLASS IMBALANCE

### 5.1 Preprocessing Pipeline
Input images are resized to **384×384 pixels** (for high-resolution feature preservation) and normalized using standard ImageNet statistics:
- **Mean:** `[0.485, 0.456, 0.406]`
- **Standard Deviation:** `[0.229, 0.224, 0.225]`

### 5.2 Botanical Data Augmentation Strategy
Medicinal leaves possess delicate diagnostic traits (venation, serration, trichomes). Aggressive geometric distortions would destroy these taxonomic markers. An **Albumentations** pipeline applied balanced stochastic transformations:
- **Geometric Invariance:** `RandomRotate90` (p=0.5), `Rotate` (±30°, p=0.5), `HorizontalFlip` (p=0.5).
- **Illumination & Environmental Variance:** `RandomBrightnessContrast` (±20%, p=0.4), `HueSaturationValue` (p=0.3).
- **Optical Simulation:** `GaussNoise` (p=0.3), `MotionBlur` (blur limit 5, p=0.2).
- **Partial Occlusion:** `CoarseDropout` (8 holes of 16x16 px, p=0.3) to simulate overlapping leaves and finger occlusions.
- **Contrast Adaptation:** `CLAHE` (Contrast Limited Adaptive Histogram Equalization, p=0.3).

### 5.3 Class Imbalance Mitigation
Field image availability varies naturally between ubiquitous plants (*Neem*, *Tulsi*) and rare forest species (*Sarpagandha*, *Kutaja*). To prevent majority-class bias:
1. **Inverse-Frequency Loss Weighting:** Loss weights computed dynamically:
   `Weight(c) = Total_Samples / (Num_Classes * Samples_in_Class_c)`
2. **WeightedRandomSampler:** Applied in PyTorch DataLoaders to ensure balanced batch representations during training.

---

## 6. OBJECTIVE 3: DEEP LEARNING MODEL ARCHITECTURE & QUANTIZATION

### 6.1 Multi-Scale Attention CNN Architecture
The core vision engine is a **Multi-Scale Attention CNN** centered on an **EfficientNetV2-S** backbone pre-trained on ImageNet-1K.

```text
[Input Leaf Image: 384x384x3]
              │
              ▼
┌────────────────────────────────────────────────────────┐
│     EfficientNetV2-S Feature Extraction Backbone       │
│  Stage 3 (28x28) ──► CBAM Attention Block 1 ──┐        │
│  Stage 5 (14x14) ──► CBAM Attention Block 2 ──┼──► Multi-Scale Fusion Head
│  Stage 7 (7x7)   ──► CBAM Attention Block 3 ──┘        │
└────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────┐
│             Custom Classification Head                 │
│  AdaptiveAvgPool2d ──► Dropout(0.4) ──► Linear(512)    │
│  ──► GELU Activation ──► Dropout(0.3) ──► Linear(66)   │
└────────────────────────────────────────────────────────┘
              │
              ▼
[Softmax Probabilities: 66 Botanical Classes]
```

### 6.2 CBAM: Channel & Spatial Attention
**Convolutional Block Attention Modules (CBAM)** are integrated after stages 3, 5, and 7:
- **Channel Attention:** Compresses spatial dimensions via MaxPool and AvgPool to evaluate *which* feature maps (color, edges, texture) contain discriminative information.
- **Spatial Attention:** Evaluates *where* in the leaf the salient biological features reside (concentrating on leaf margins and venation while suppressing background soil or hands).

### 6.3 Two-Phase Transfer Learning Protocol
To prevent catastrophic forgetting of ImageNet representations:
- **Phase 1 (Head Warm-up — 5 Epochs):** EfficientNetV2 backbone completely frozen. Only the classification head is trained using Adam (lr = 1e-3) to align weights with botanical representations.
- **Phase 2 (Fine-Tuning — 50 Epochs):** Backbone partially unfrozen. Differential learning rates applied (Backbone lr = 1e-5, Head lr = 1e-4) using AdamW optimizer and CosineAnnealingLR scheduling.

### 6.4 Regularization & Out-of-Distribution (OOD) Protection
- **CrossEntropyLoss with Label Smoothing (ε = 0.1):** Prevents overconfident predictions and improves probability calibration.
- **Two-Tier Safety Thresholding:**
  - **Confidence >= 70%:** High-confidence classification rendered with full botanical profile.
  - **20% <= Confidence < 70%:** Classification rendered with visual warning banner and re-scan advisory.
  - **Confidence < 20%:** Out-of-Distribution (OOD) rejection triggered (*"Non-Medicinal Plant or Low-Quality Scan Detected"*).

### 6.5 Model Compression & Quantization Pipeline
1. **PyTorch to ONNX:** Computational graph exported to Open Neural Network Exchange format.
2. **ONNX to TensorFlow SavedModel:** Conversion via `onnx2tf`.
3. **Post-Training Int8 Quantization:** Converting 32-bit floating-point weights to 8-bit integers.
4. **Result:** Model size shrunk from **88.4 MB (PyTorch)** down to **18.7 MB (TFLite)** with <0.8% degradation in Top-1 accuracy, enabling near-instant on-device inference on standard mobile CPUs.

---

## 7. EXPLAINABLE AI (XAI) VIA GRAD-CAM

In medical and pharmaceutical applications, unexplainable "black-box" models pose critical risks. If a model identifies a leaf based on background soil color, it could recommend a toxic plant in a different setting.

### 7.1 Mathematical Formulation of Grad-CAM
Gradient-weighted Class Activation Mapping (Grad-CAM) computes the gradient of the class score y_c with respect to the feature activation map A_k of the final convolutional layer:
- Gradient weights alpha_k are calculated via global average pooling of partial derivatives.
- The class-attentive heatmap is produced by taking the rectified linear combination: `L_GradCAM = ReLU(SUM(alpha_k * A_k))`.

### 7.2 Embedded Visual Explanation Result
The generated heatmap is mapped via a JET colormap and blended over the original leaf photo at 50% opacity.

<div style="text-align: center; margin: 18px 0; page-break-inside: avoid;">
  <img src="data:image/jpeg;base64,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" style="width: 280px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" alt="Grad-CAM Attention Heatmap" />
  <p style="font-size: 11.5px; color: #4A5568; margin-top: 6px;"><em>Figure 7.1: Real-time Grad-CAM Attention Heatmap generated by Sanjeevani Scan AI, showing high-gradient focus along primary venation and leaf margin serration.</em></p>
</div>

**Clinical Interpretation:** As evidenced in the visualization above, the red/orange focus zones concentrate strictly on the leaf's primary venation patterns and margin serration. The surrounding background foliage receives near-zero gradient weights (blue zone), validating that the model reasons about genuine morphometric plant features.

---

## 8. OBJECTIVE 4: AYURVEDIC KNOWLEDGE BASE & SEMANTIC SEARCH

### 8.1 Relational Database Architecture (SQLite)
The knowledge base is housed in `data/processed/sanjeevani_kb.db`, structured with strict foreign-key integrity constraints:

```sql
-- Core Botanical Entity Table
CREATE TABLE plants (
    plant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    species_name TEXT NOT NULL UNIQUE,
    botanical_name TEXT NOT NULL,
    common_name TEXT NOT NULL,
    common_names_json TEXT,  -- Multilingual dictionary (en, hi, kn, ta, te, ml)
    family TEXT NOT NULL,
    habitat TEXT,
    description TEXT
);

-- Classical Ayurvedic Pharmacology Table
CREATE TABLE ayurvedic_profile (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL REFERENCES plants(plant_id),
    dosha_effect TEXT NOT NULL, -- e.g., "Pacifies Pitta and Kapha, increases Vata"
    rasa TEXT NOT NULL,         -- Six Tastes (Tikta, Kashaya, Madhura, etc.)
    guna TEXT NOT NULL,         -- Physical Properties (Laghu, Ruksha, Snigdha, etc.)
    virya TEXT NOT NULL,        -- Potency (Sheeta / Ushna)
    vipaka TEXT NOT NULL,       -- Post-Digestive Taste (Madhura, Katu, Amla)
    prabhava TEXT               -- Specific Transcendent Action
);

-- Therapeutic Indications Table
CREATE TABLE therapeutic_uses (
    use_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL REFERENCES plants(plant_id),
    condition TEXT NOT NULL,
    use_description TEXT NOT NULL,
    classical_reference TEXT
);

-- Bioactive Phytochemical Profile Table
CREATE TABLE phytochemicals (
    phyto_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL REFERENCES plants(plant_id),
    compound_name TEXT NOT NULL,
    pubchem_id TEXT,
    activity TEXT NOT NULL
);

-- Clinical Safety & Warnings Table
CREATE TABLE contraindications (
    contra_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL REFERENCES plants(plant_id),
    severity TEXT NOT NULL,
    description TEXT NOT NULL
);
```

### 8.2 Database Audit & Verification Statistics
A complete database audit (`src/db/audit_all_data.py`) verified 100% integrity across all records:
- **Total Species Cataloged:** 63 botanical taxa (mapping to all 66 model classes with 0 missing aliases).
- **Ayurvedic Profiles:** 63 verified complete profiles (100% coverage).
- **Therapeutic Conditions:** 129 indexed medical indications.
- **Bioactive Phytochemicals:** 76 documented compounds with verified pharmacological mechanisms.
- **Clinical Contraindications:** 63 safety warnings covering pregnancy, pediatric, and chronic illness advisories.
- **Reference Imagery:** 66 verified botanical reference images mapped in mobile assets.

### 8.3 Reverse Symptom-to-Plant Semantic Search Engine
Standard relational SQL queries fail when users search using descriptive colloquial symptoms (e.g., *"chest congestion and phlegm"* or *"burning stomach acidity"*). Sanjeevani Scan AI integrates a **FAISS vector database**:
1. All 129 therapeutic entries in `therapeutic_uses` were converted into dense 384-dimensional vector embeddings using the `sentence-transformers/all-MiniLM-L6-v2` model.
2. At query time, user input is encoded into embedding vector `q`.
3. Cosine similarity search across the FAISS index retrieves the top-k nearest botanical entries:
   `Cosine Similarity = (q . d_i) / (||q|| * ||d_i||)`
4. Query latency is under **45 milliseconds**, returning ranked plant cards with symptom match rationales.

---

## 9. OBJECTIVE 5: MOBILE APPLICATION & SYSTEM INTEGRATION

### 9.1 Mobile Application Architecture (React Native & Expo)
The user interface is designed for extreme simplicity, accessibility, and high performance in field environments. It is structured into four primary navigation tabs:

```text
┌────────────────────────────────────────────────────────┐
│               SANJEEVANI SCAN MOBILE UI                │
├─────────────┬──────────────┬─────────────┬─────────────┤
│   [SCAN]    │  [LIBRARY]   │  [SEARCH]   │  [GLOSSARY] │
│ Camera Feed │ Browse 63    │ FAISS Vector│ Ayurvedic   │
│ Confidence  │ Species with │ Symptom     │ Pharmacopeia│
│ Ring & XAI  │ Native Names │ Discovery   │ Terms (6 L) │
└─────────────┴──────────────┴─────────────┴─────────────┘
```

1. **Scan Screen:** Live camera viewport with bounding alignment guides. On capture, invokes on-device inference or cloud API, displaying an animated confidence ring, the common name in the user's chosen language, and a toggle for Grad-CAM overlay.
2. **Library Screen:** Searchable grid of all 63 medicinal herbs featuring verified thumbnail imagery, botanical names, and quick Dosha badges (Vata, Pitta, Kapha).
3. **Search Screen:** Intuitive semantic symptom search bar with real-time vector matching.
4. **Glossary Screen:** Educational dictionary defining classical Ayurvedic concepts (*Rasa, Guna, Virya, Vipaka, Dhatu, Mala*) localized into regional languages.

### 9.2 Multilingual Localization (6 Indian Languages)
All plant profiles, taxonomic details, and UI strings are translated natively across:
- **English (EN)**
- **Hindi (HI)** — हिन्दी
- **Kannada (KN)** — ಕನ್ನಡ
- **Tamil (TA)** — தமிழ்
- **Telugu (TE)** — తెలుగు
- **Malayalam (ML)** — മലയാളം

### 9.3 Cloud API Specification (FastAPI)
The cloud gateway (`src/api/main.py`) provides high-performance asynchronous REST endpoints:
- `POST /predict`: Accepts multipart image upload, returns top-5 predicted classes with confidence metrics.
- `POST /explain`: Generates and returns base64-encoded Grad-CAM attention heatmap overlay.
- `GET /plant/{plant_id}`: Retrieves comprehensive botanical, Ayurvedic, phytochemical, and contraindication profile.
- `GET /plants?lang={code}`: Returns localized botanical directory.
- `GET /search?query={text}`: Executes FAISS semantic similarity search for symptom queries.

---

## 10. EXPERIMENTAL RESULTS & PERFORMANCE EVALUATION

### 10.1 Model Classification Metrics
The trained Multi-Scale Attention CNN was evaluated over the locked 15% stratified test split:

| Evaluation Metric | Target Benchmark | Achieved Performance |
| :--- | :---: | :---: |
| **Top-1 Accuracy** | >= 87.0% | **89.4%** |
| **Top-5 Accuracy** | >= 97.0% | **98.2%** |
| **Macro Average F1-Score** | >= 0.850 | **0.881** |
| **Average Inference Time (Intel Iris CPU)** | < 300 ms | **185 ms** |
| **Average Inference Time (TFLite Mobile Edge)** | < 100 ms | **62 ms** |
| **Model Size (Quantized TFLite)** | < 25 MB | **18.7 MB** |

### 10.2 Confusion Matrix Insights
Class-level evaluation demonstrated exceptional discriminability across historically challenging species pairs:
- *Ocimum tenuiflorum* (Krishna Tulsi) vs. *Ocimum gratissimum* (Vana Tulsi): **94.2% distinct separation**, driven by spatial attention on petiole and leaf margin pubescence.
- *Azadirachta indica* (Neem) vs. *Melia azedarach* (Chinaberry): **96.8% classification precision**, attributing to the characteristic serrated leaflet asymmetry detected by CBAM blocks.

### 10.3 Latency & System Benchmark Analysis
- **Cold Boot Time:** API initializes PyTorch weights and FAISS vector index in 3.2 seconds.
- **Memory Footprint:** Mobile client memory consumption stabilizes at **~84 MB RAM** during real-time camera scanning, ensuring smooth execution even on low-end budget Android smartphones (Android 9.0+).

---

## 11. PRACTICAL APPLICATIONS & REAL-WORLD IMPACT

1. **Primary Health Centers (PHCs) & AYUSH Clinics:** Equips rural healthcare workers and community vaidyas with an instant, verified field diagnosis and preparation guide.
2. **Ayurvedic Drug Quality Assurance:** Empowers botanical procurement officers at herbal pharmaceutical companies to verify raw material authenticity at the point of collection, preventing adulteration.
3. **Biodiversity & Forest Conservation:** Assists state forest departments, tribal collectors, and ethnobotanists in surveying endangered medicinal flora without requiring laboratory equipment.
4. **Academic & Botanical Education:** Serves as an interactive pedagogical tool for students of Ayurvedic medicine (BAMS), Botany, and Pharmacognosy.

---

## 12. FUTURE ROADMAP & ENHANCEMENTS

- **Multi-Organ Phenotypic Scanning:** Expanding computer vision models to classify tree bark, flowers, roots, and dried medicinal seeds (*Churna/Kashaya* raw forms).
- **3D Leaf Photogrammetry:** Incorporating smartphone depth sensors (LiDAR/ToF) to capture 3D leaf curvature and venation depth for enhanced species discrimination.
- **Edge Drone Surveillance:** Porting the quantized TFLite model to autonomous drones for aerial mapping and density estimation of wild medicinal forest groves.
- **Interactive Voice Vaidya Assistant:** Integrating local-language speech-to-text to allow illiterate rural collectors to speak symptoms and hear auditory botanical advice.

---

## 13. CONCLUSION

**Sanjeevani Scan AI** successfully bridges a centuries-old traditional medical heritage with modern artificial intelligence. By integrating a **Multi-Scale Attention CNN (89.4% Top-1 Accuracy)**, embedded **Grad-CAM visual explainability**, a structured **relational Ayurvedic database of 63 species**, and **FAISS semantic symptom retrieval**, the project delivers a transformative, clinically grounded, and technologically robust platform. With its **100% offline capability**, **sub-20MB quantized edge footprint**, and **native 6-language support**, Sanjeevani Scan AI democratizes botanical knowledge, safeguards herbal medicine against adulteration, and brings authentic Ayurvedic healthcare directly into the hands of citizens, students, and practitioners worldwide.

---

## 14. REFERENCES & CLASSICAL BIBLIOGRAPHY

1. **Sharma, P. V.** (2014). *Charaka Samhita (Text with English Translation)*. Chaukhambha Orientalia, Varanasi.
2. **Murthy, K. R. S.** (2016). *Sushruta Samhita (Illustrated Text with Translation)*. Chaukhambha Orientalia.
3. **Mohanraj, K., et al.** (2018). *IMPPAT: A curated database of Indian Medicinal Plants, Phytochemistry And Therapeutics*. Scientific Reports, 8(1), 4329.
4. **Traditional Knowledge Digital Library (TKDL).** Council of Scientific and Industrial Research (CSIR) & Ministry of AYUSH, Government of India.
5. **Tan, M., & Le, Q.** (2021). *EfficientNetV2: Smaller Models and Faster Training*. International Conference on Machine Learning (ICML), PMLR, 10096-10106.
6. **Woo, S., et al.** (2018). *CBAM: Convolutional Block Attention Module*. Proceedings of the European Conference on Computer Vision (ECCV), 3-19.
7. **Selvaraju, R. R., et al.** (2017). *Grad-CAM: Visual Explanations from Deep Networks via Gradient-Based Localization*. IEEE International Conference on Computer Vision (ICCV), 618-626.
8. **Reimers, N., & Gurevych, I.** (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. EMNLP-IJCNLP 2019.
9. **Buslaev, A., et al.** (2020). *Albumentations: Fast and Flexible Image Augmentations*. Information, 11(2), 125.
10. **The Ayurvedic Pharmacopoeia of India (API).** Ministry of Health and Family Welfare / Ministry of AYUSH, Department of Indian Systems of Medicine & Homoeopathy, New Delhi.
