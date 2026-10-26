# Objective 5 — System Integration & Final Evaluation
## Sanjeevani Scan | Medicinal Plant Identification System

> **Goal:** Integrate the deep learning model and Ayurvedic knowledge base into a cohesive, user-friendly mobile application and backend API, followed by rigorous evaluation of the entire system.

---

## Table of Contents

1. [Overview](#1-overview)
2. [API Backend (FastAPI)](#2-api-backend-fastapi)
3. [Mobile Application (React Native)](#3-mobile-application-react-native)
4. [Explainable AI (Grad-CAM) Integration](#4-explainable-ai-grad-cam-integration)
5. [System Evaluation & Validation](#5-system-evaluation--validation)
6. [Progress Tracker](#6-progress-tracker)

---

## 1. Overview

With the model trained and quantized (Objective 3) and the offline Ayurvedic SQLite database constructed (Objective 4), Objective 5 focuses on **Deployment and Validation**. 

We need to bring these isolated components together into a working product. The architecture supports two modes:
1. **Online Mode:** A cloud-hosted FastAPI backend for high-performance inference and updates.
2. **Offline Mode:** A React Native mobile app with a bundled TFLite model and SQLite database for deep-forest/rural use.

---

## 2. API Backend (FastAPI)

For online usage and web-based integrations, we developed a high-performance REST API using **FastAPI**.

### Core Endpoints:
- `POST /predict`: Accepts a multipart image upload. Runs the PyTorch/ONNX model and returns the Top-5 predicted plant species with confidence scores.
- `POST /explain`: Accepts an image and returns a Grad-CAM heatmap overlay showing exactly which parts of the leaf triggered the prediction.
- `GET /plant/{id}`: Queries the backend knowledge base to return the full Ayurvedic profile for a specific plant.
- `GET /search?query=...`: Accepts a symptom string (e.g., "headache") and uses Sentence-Transformer semantic search to return ranked plant recommendations.

---

## 3. Mobile Application (React Native)

The primary user interface is a cross-platform mobile app built with **React Native**, designed around a minimal, 4-screen flow:

1. **Home Screen**: Quick actions ("Scan Leaf" or "Search Symptom").
2. **Camera / Scan Screen**: Live camera feed with bounding boxes. Runs offline inference using the bundled `sanjeevani_quantized.tflite` model.
3. **Result Screen**: Displays the predicted species. If confidence is `< 70%`, a warning banner prompts the user to re-scan. It features swipeable tabs pulling offline data from `sanjeevani_kb.db`:
   - Overview
   - Ayurvedic Profile (Doshas, Guna, Rasa)
   - Uses & Remedies
   - Phytochemicals
   - Precautions
4. **Search Screen**: Reverse-lookup semantic search.

---

## 4. Explainable AI (Grad-CAM) Integration

Trust is paramount in medicinal applications. We integrated **Grad-CAM** (Gradient-weighted Class Activation Mapping) directly into the UI. 

When a user views a prediction, they are shown a heatmap overlaid on their original photograph. If the AI highlights the jagged edge of a Neem leaf, the user (especially botanists or Ayurvedic practitioners) can visually verify that the model is making decisions based on actual botanical features, not background noise.

---

## 5. System Evaluation & Validation

Before final deployment, the entire system undergoes rigorous evaluation (Stage 5 of the Methodology).

### Metrics Tracked:
- **Top-1 and Top-5 Accuracy**: Tested on the locked 15% Test Split.
- **Confusion Matrix Analysis**: To identify if the model struggles to differentiate between highly similar species within the same genus.
- **Calibration Analysis**: Ensuring that when the model says it is "90% confident", it is actually correct 90% of the time (critical for the `< 70%` re-scan warning threshold).
- **Inference Speed (Latency)**: Measured on low-end Android devices using the TFLite model.

---

## 6. Progress Tracker

- [x] Design API architecture and endpoints
- [x] Integrate Grad-CAM explanation generation
- [ ] Build FastAPI Backend Implementation (Code Pending)
- [ ] Develop React Native Mobile App UI (Code Pending)
- [ ] Bundle TFLite and SQLite DB into Mobile App
- [ ] Execute final Test Set Evaluation & Confusion Matrix
- [ ] Conduct User Testing with Practitioners

**Conclusion:** Once these steps are implemented, the Sanjeevani Scan project will be fully realized—solving the critical gap in accessible, offline, and explainable Ayurvedic plant identification.
