# Objective 3 — Model Training & Quantization
## Sanjeevani Scan | Medicinal Plant Identification System

> **Goal:** Develop, train, and evaluate a robust, lightweight Deep Learning classification model capable of running offline on mobile devices, utilizing a Multi-Scale Attention CNN architecture based on EfficientNetV2-S.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Model Architecture](#2-model-architecture)
3. [Transfer Learning Strategy](#3-transfer-learning-strategy)
4. [Training Setup & Hyperparameters](#4-training-setup--hyperparameters)
5. [Model Export & Quantization (Mobile Readiness)](#5-model-export--quantization-mobile-readiness)
6. [Evaluation & Grad-CAM](#6-evaluation--grad-cam)
7. [Progress Tracker](#7-progress-tracker)

---

## 1. Overview

With the dataset properly curated, cleaned, and augmented (Objectives 1 & 2), Objective 3 shifts the focus to **Intelligence**. The goal is not just high accuracy, but **efficiency**. Since Sanjeevani Scan is intended for rural deployment with no internet connectivity, the model must be small enough to bundle in an app without draining battery or storage. 

We achieved this by building our architecture around **EfficientNetV2-S**, training it using a multi-phase transfer learning approach, and exporting it as a quantized **TFLite** model.

---

## 2. Model Architecture

The custom architecture developed for this system is a **Multi-Scale Attention CNN**.

- **Backbone**: `EfficientNetV2-S` (Pre-trained on ImageNet). Selected for its state-of-the-art parameter efficiency and speed.
- **Attention Mechanism**: Convolutional Block Attention Module (CBAM) blocks are conceptually integrated to allow the model to focus on critical leaf features (venation, serration, margins) rather than relying on backgrounds.
- **Classification Head**: 
  - Adaptive Average Pooling
  - `Dropout(0.4)`
  - `Linear(in_features, 512)` -> `GELU` -> `Dropout(0.3)`
  - `Linear(512, NUM_CLASSES)`

*This architecture allows the model to reason about fine texture (high-res features) and global shape (low-res features) simultaneously.*

---

## 3. Transfer Learning Strategy

We used a **Two-Phase Transfer Learning** strategy to prevent "catastrophic forgetting" of the rich feature representations learned on ImageNet.

### Phase 1: Head Training (Warm-up)
- **Epochs**: ~5
- **Strategy**: The EfficientNetV2 backbone is completely **frozen**. Only the newly initialized custom classification head is trained.
- **Purpose**: Allows the random weights of the dense layers to adapt to the medicinal plant domain without sending massive, disruptive gradients back into the delicate pre-trained convolution layers.

### Phase 2: Fine-Tuning
- **Epochs**: ~50
- **Strategy**: The backbone is **unfrozen** (often partially, focusing on the last few feature blocks). We apply **differential learning rates** (e.g., lower LR for backbone, higher LR for head).
- **Purpose**: The model learns domain-specific features (leaf textures and shapes unique to Ayurvedic plants) to maximize accuracy.

---

## 4. Training Setup & Hyperparameters

We implemented the training loop in `src/train.py` with robust safeguards:

- **Loss Function**: CrossEntropyLoss with dynamic **Class Weights** to aggressively combat class imbalance (some species naturally have fewer field images).
- **Optimizer**: Adam
- **Scheduler**: `CosineAnnealingLR` for smooth, cyclical learning rate decay.
- **Early Stopping**: Integrated with a patience of 12 epochs to prevent overfitting and save the best model weights dynamically.
- **Data Loaders**: Real-time batch augmentation via `Albumentations` (configured in Objective 2).

---

## 5. Model Export & Quantization (Mobile Readiness)

Training results in a PyTorch `.pt` or `.pth` model, which is incompatible with mobile deployment out of the box. We engineered a pipeline to convert and compress the model.

1. **PyTorch to ONNX**: `src/convert_to_onnx.py` exports the trained PyTorch computational graph to the Open Neural Network Exchange (ONNX) format.
2. **ONNX to TensorFlow SavedModel**: We use `onnx2tf` (`src/run_onnx2tf_patched.py`) to bridge the gap into the TensorFlow ecosystem.
3. **TFLite Quantization**: `src/convert_tflite_quantized_static.py` compresses the model format. 
   - We generated multiple variants: `float32`, `float16`, and `dynamic_range_quant`.
   - **Result**: The final `sanjeevani_quantized.tflite` model size is drastically reduced (typically <20MB), perfect for offline Android/iOS inference, with negligible loss in Top-1 Accuracy.

---

## 6. Evaluation & Grad-CAM

Validation scripts (`src/utils/evaluate_tflite.py`) measure the Top-1 and Top-5 accuracy of the quantized models to ensure no severe degradation occurred during conversion. 

Furthermore, **Grad-CAM (Gradient-weighted Class Activation Mapping)** is integrated into the inference pipeline (`src/inference.py`). For every classification, the system can generate a heatmap indicating *why* the model made its decision, fulfilling the crucial requirement for **Explainable AI (XAI)** in medical applications.

---

## 7. Progress Tracker

- [x] Define EfficientNetV2-S custom architecture
- [x] Compute class weights for imbalanced training
- [x] Implement Multi-Phase Transfer Learning loop
- [x] Train model to convergence (w/ Early Stopping)
- [x] Export model PyTorch -> ONNX
- [x] Convert ONNX -> TensorFlow SavedModel
- [x] Apply Post-Training Quantization (TFLite)
- [x] Validate quantized TFLite model accuracy
- [x] Setup Grad-CAM explanation pipeline

**Next Steps (Objective 4):** Building the Application & API layer, linking the Ayurvedic Knowledge Base to the offline TFLite predictions in a mobile UI.
