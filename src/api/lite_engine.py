"""
Ultra-lightweight Cloud Inference, Analytical Grad-CAM & Semantic Symptom Search Engine.
Engineered to fit cleanly under 120 MB RSS RAM on 512 MB Free Tier cloud containers
while preserving exact 66-class accuracy and analytical Grad-CAM explainability.
"""
import os
import re
import math
import json
import base64
import sqlite3
import threading
from io import BytesIO
from collections import Counter

import cv2
import numpy as np
from PIL import Image

try:
    import ai_edge_litert.interpreter as litert
except ImportError:
    import tensorflow.lite as litert

SYNONYM_GROUPS = {
    "Amruth": "Giloy",
    "HolyBasilVana": "Tulsi",
    "Bringaraj": "Bhringraj",
}

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

SYNONYM_EXPANSIONS = {
    "fever": "febrile pyrexia dengue temperature antipyretic",
    "cold": "cough bronchitis congestion asthma respiratory mucus",
    "cough": "cold bronchitis asthma throat respiratory expectorant",
    "skin": "rash eczema wound ulcer itching acne inflammation dermatitis",
    "diabetes": "glucose insulin blood sugar metabolic glycemic",
    "sugar": "diabetes glucose insulin glycemic",
    "stomach": "digestion acidity ulcer constipation bloating appetite",
    "digestion": "stomach gastric carminative bloating constipation",
    "hair": "alopecia scalp dandruff hairfall growth",
    "stress": "anxiety sleep insomnia memory adaptogen nervous calm",
    "immunity": "immune antioxidant infection platelet defense",
    "pain": "inflammation joint arthritis analgesic swelling",
    "heart": "cardiac cholesterol blood pressure hypertension",
}


class LiteClassifier:
    def __init__(self, model_path: str, class_names_path: str, confidence_threshold: float = 0.20):
        self.confidence_threshold = confidence_threshold
        with open(class_names_path, "r", encoding="utf-8") as f:
            self.class_names = json.load(f)
        self.num_classes = len(self.class_names)
        self.non_plant_class_idx = self.class_names.index("Non_Plant") if "Non_Plant" in self.class_names else -1

        self.interpreter = litert.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()[0]
        self.output_details = self.interpreter.get_output_details()
        self._lock = threading.Lock()

    @staticmethod
    def preprocess(image_path: str) -> tuple[np.ndarray, Image.Image]:
        image = Image.open(image_path).convert("RGB")
        resized = image.resize((256, 256), Image.BILINEAR)
        cropped = resized.crop((16, 16, 240, 240))
        arr = (np.array(cropped, dtype=np.float32) / 255.0 - IMAGENET_MEAN) / IMAGENET_STD
        return np.expand_dims(arr, axis=0), cropped

    def _run_raw(self, image_path: str):
        inp, cropped = self.preprocess(image_path)
        with self._lock:
            self.interpreter.set_tensor(self.input_details["index"], inp)
            self.interpreter.invoke()
            tensors = [self.interpreter.get_tensor(o["index"])[0].copy() for o in self.output_details]

        logits = None
        feat = None
        for t in tensors:
            if t.ndim == 1 and t.shape[0] == self.num_classes:
                logits = t
            elif t.ndim == 3:
                feat = t
        if feat is not None and feat.shape == (1280, 7, 7):
            feat = np.transpose(feat, (1, 2, 0))
        return logits, feat, cropped

    def predict(self, image_path: str, class_names=None):
        try:
            logits, _, _ = self._run_raw(image_path)
        except Exception as e:
            return {"status": "error", "message": f"Failed to process image: {e}"}

        active_names = class_names or self.class_names
        e = np.exp(logits - np.max(logits))
        probs = e / np.sum(e)

        raw_idx = int(np.argmax(probs))
        raw_conf = float(probs[raw_idx])

        if self.non_plant_class_idx != -1 and raw_idx == self.non_plant_class_idx:
            return {
                "status": "rejected",
                "reason": "non_plant_detected",
                "message": "The scanned image does not appear to be a plant or leaf.",
                "confidence": raw_conf,
            }

        merged = {}
        for idx, pval in enumerate(probs.tolist()):
            canon = SYNONYM_GROUPS.get(active_names[idx], active_names[idx])
            merged[canon] = merged.get(canon, 0.0) + pval

        best_class, confidence = max(merged.items(), key=lambda x: x[1])
        if confidence < self.confidence_threshold:
            return {
                "status": "rejected",
                "reason": "low_confidence",
                "message": f"Confidence too low ({confidence*100:.1f}%). Please center a clear medicinal leaf in good lighting and try again.",
                "confidence": confidence,
            }

        return {"status": "success", "prediction": best_class, "confidence": float(confidence)}


class LiteGradCamGenerator:
    """Computes exact analytical Grad-CAM from the last conv feature map (7x7x1280) and dense head weights."""

    def __init__(self, lite_classifier: LiteClassifier, head_weights_path: str):
        self.classifier = lite_classifier
        head = np.load(head_weights_path)
        self.W1 = head["W1"].astype(np.float32)  # (512, 1280)
        self.b1 = head["b1"].astype(np.float32)  # (512,)
        self.W2 = head["W2"].astype(np.float32)  # (66, 512)

    @staticmethod
    def _gelu_tanh_grad(z: np.ndarray) -> np.ndarray:
        s = math.sqrt(2.0 / math.pi)
        u = s * (z + 0.044715 * (z ** 3))
        th = np.tanh(u)
        sech2 = 1.0 - th * th
        return 0.5 * (1.0 + th) + 0.5 * z * sech2 * s * (1.0 + 3.0 * 0.044715 * (z ** 2))

    def generate_heatmap_base64(self, image_path: str, target_category: int = None):
        logits, feat, cropped = self.classifier._run_raw(image_path)
        if logits is None or feat is None:
            return None

        cls_idx = int(np.argmax(logits)) if target_category is None else int(target_category)
        pooled = feat.mean(axis=(0, 1))
        h1 = self.W1 @ pooled + self.b1
        alpha_k = (self.W2[cls_idx] * self._gelu_tanh_grad(h1)) @ self.W1

        cam = np.maximum(0.0, np.tensordot(feat, alpha_k, axes=([2], [0])))
        if cam.max() > 1e-8:
            cam = cam / cam.max()

        cam_resized = cv2.resize(cam.astype(np.float32), (224, 224), interpolation=cv2.INTER_CUBIC)
        cam_resized = np.clip(cam_resized, 0.0, 1.0)
        heatmap_bgr = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
        heatmap_rgb = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

        orig_float = np.array(cropped, dtype=np.float32) / 255.0
        overlay = np.clip(0.50 * heatmap_rgb + 0.50 * orig_float, 0.0, 1.0)
        vis_pil = Image.fromarray(np.uint8(255 * overlay))

        buf = BytesIO()
        vis_pil.save(buf, format="JPEG", quality=90)
        return base64.b64encode(buf.getvalue()).decode("utf-8")


class LiteSymptomSearch:
    """Zero-footprint TF-IDF + Medical Synonym Search over SQLite therapeutic uses (< 1 MB RAM)."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.docs = []
        self.idf = {}
        self._build_index()

    @staticmethod
    def _tokenize(text: str):
        tokens = re.findall(r"[a-z]{2,}", text.lower())
        expanded = list(tokens)
        for tok in tokens:
            if tok in SYNONYM_EXPANSIONS:
                expanded.extend(SYNONYM_EXPANSIONS[tok].split())
        # Add character/word bigrams for clinical phrasing precision
        bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
        return expanded + bigrams

    def _build_index(self):
        if not os.path.exists(self.db_path):
            return
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.plant_id, p.species_name, p.common_name, t.condition, t.use_description
            FROM plants p
            JOIN therapeutic_uses t ON p.plant_id = t.plant_id
            """
        )
        rows = cur.fetchall()
        conn.close()

        df = Counter()
        raw_tfs = []
        for row in rows:
            txt = f"{row['condition']} {row['use_description']} {row['common_name']} {row['species_name']}"
            toks = self._tokenize(txt)
            tf = Counter(toks)
            for t in tf:
                df[t] += 1
            raw_tfs.append((row, tf, len(toks) or 1))

        n_docs = max(len(raw_tfs), 1)
        self.idf = {t: math.log((n_docs + 1.0) / (c + 1.0)) + 1.0 for t, c in df.items()}

        self.docs = []
        for row, tf, length in raw_tfs:
            vec = {t: (cnt / length) * self.idf[t] for t, cnt in tf.items()}
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            self.docs.append({
                "plant_id": row["plant_id"],
                "species_name": row["species_name"],
                "condition_matched": row["condition"],
                "vec": vec,
                "norm": norm,
            })

    def search(self, query: str, top_k: int = 5):
        if not self.docs or not query:
            return []
        q_toks = self._tokenize(query)
        q_tf = Counter(q_toks)
        q_len = len(q_toks) or 1
        q_vec = {t: (cnt / q_len) * self.idf.get(t, 1.0) for t, cnt in q_tf.items()}
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0

        scored = []
        for d in self.docs:
            dot = sum(qv * d["vec"].get(t, 0.0) for t, qv in q_vec.items())
            if dot > 0:
                sim = dot / (q_norm * d["norm"])
                scored.append((sim, d))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "plant_id": d["plant_id"],
                "species_name": d["species_name"],
                "condition_matched": d["condition_matched"],
                "similarity_score": round(float(sim), 4),
            }
            for sim, d in scored[:top_k]
        ]
