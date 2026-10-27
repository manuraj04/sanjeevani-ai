import os
import json
import sqlite3
import numpy as np
import tensorflow as tf
from PIL import Image
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import SPECIES_MAP

class SanjeevaniOfflineAPI:
    def __init__(self, model_path=None, db_path=None, class_names=None, confidence_threshold=0.20):
        if model_path is None:
            model_path = os.path.join(project_root, "data", "processed", "sanjeevani_quantized.tflite")
        if db_path is None:
            db_path = os.path.join(project_root, "data", "processed", "sanjeevani_kb.db")

        self.model_path = model_path
        self.db_path = db_path
        self.confidence_threshold = confidence_threshold
        
        print("Loading Quantized TFLite interpreter for offline edge inference...")
        self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
        self.interpreter.allocate_tensors()
        
        self.input_details = self.interpreter.get_input_details()[0]
        self.output_details = self.interpreter.get_output_details()[0]
        
        if class_names is None:
            test_dir = os.path.join(project_root, "data", "processed", "test")
            if os.path.exists(test_dir):
                self.class_names = sorted(os.listdir(test_dir))
            else:
                self.class_names = [s[0] for s in SPECIES_MAP.items()]
        else:
            self.class_names = class_names

        self.non_plant_idx = len(self.class_names) - 1 if "Non_Plant" in self.class_names else -1

    def preprocess(self, image_input):
        if isinstance(image_input, str):
            img = Image.open(image_input).convert('RGB')
        else:
            img = Image.open(image_input).convert('RGB')

        img = img.resize((256, 256), Image.BILINEAR)
        
        # Center crop to 224x224
        width, height = img.size
        left = (width - 224) / 2
        top = (height - 224) / 2
        right = (width + 224) / 2
        bottom = (height + 224) / 2
        img = img.crop((left, top, right, bottom))
        
        # Convert to float32 and scale
        img_array = np.array(img).astype(np.float32) / 255.0
        
        # Normalize
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_array = (img_array - mean) / std
        
        return np.expand_dims(img_array, axis=0)

    def fetch_ayurvedic_info(self, class_name):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Resolve botanical name if available
            botanical = SPECIES_MAP.get(class_name, {}).get("botanical", class_name)

            cursor.execute(
                "SELECT * FROM plants WHERE species_name = ? OR botanical_name = ? OR common_name = ? OR common_name LIKE ? OR species_name LIKE ?",
                (botanical, botanical, class_name, f"%{class_name}%", f"%{botanical}%")
            )
            plant = cursor.fetchone()
            
            if not plant:
                conn.close()
                return {"message": "No Ayurvedic data found for this species in the local DB."}
                
            plant_id = plant['plant_id']
            data = dict(plant)
            if data.get("common_names_json"):
                try:
                    data["common_names"] = json.loads(data["common_names_json"])
                except:
                    data["common_names"] = {}
            
            # Ayurvedic profile
            cursor.execute("SELECT * FROM ayurvedic_profile WHERE plant_id = ?", (plant_id,))
            profile = cursor.fetchone()
            if profile:
                data['ayurvedic_profile'] = dict(profile)
                data['profile'] = dict(profile)
                
            # Therapeutic uses
            cursor.execute("SELECT condition, use_description, classical_reference FROM therapeutic_uses WHERE plant_id = ?", (plant_id,))
            uses = cursor.fetchall()
            data['therapeutic_uses'] = [dict(u) for u in uses]
            
            # Phytochemicals
            cursor.execute("SELECT compound_name, activity FROM phytochemicals WHERE plant_id = ?", (plant_id,))
            phytochemicals = cursor.fetchall()
            data['phytochemicals'] = [dict(p) for p in phytochemicals]

            # Contraindications
            cursor.execute("SELECT condition, severity, notes FROM contraindications WHERE plant_id = ?", (plant_id,))
            contras = cursor.fetchall()
            data['contraindications'] = [dict(c) for c in contras]
            
            conn.close()
            return data
            
        except Exception as e:
            return {"error": str(e)}

    def predict(self, image_input):
        try:
            input_data = self.preprocess(image_input)
        except Exception as e:
            return {"status": "error", "message": f"Image processing failed: {e}"}
            
        self.interpreter.set_tensor(self.input_details['index'], input_data)
        self.interpreter.invoke()
        
        output_data = self.interpreter.get_tensor(self.output_details['index'])[0]
        
        def softmax(x):
            e_x = np.exp(x - np.max(x))
            return e_x / e_x.sum(axis=0)
            
        probs = softmax(output_data)
        pred_idx = int(np.argmax(probs))
        confidence = float(probs[pred_idx])
        
        # OOD Rejection check
        if self.non_plant_idx != -1 and pred_idx == self.non_plant_idx:
            return {
                "status": "rejected",
                "reason": "non_plant_detected",
                "message": "The scanned image does not appear to be a plant.",
                "confidence": confidence
            }
            
        if confidence < self.confidence_threshold:
            return {
                "status": "rejected",
                "reason": "low_confidence",
                "message": f"Confidence too low ({confidence*100:.1f}%). Please rescan clearly.",
                "confidence": confidence
            }
            
        species_name = self.class_names[pred_idx] if self.class_names else f"Class_{pred_idx}"
        ayurvedic_data = self.fetch_ayurvedic_info(species_name)
        
        return {
            "status": "success",
            "prediction": species_name,
            "confidence": round(confidence * 100, 2),
            "confidence_ratio": float(confidence),
            "engine": "TensorFlow_Lite_Quantized_INT8",
            "is_offline_edge": True,
            "ayurvedic_data": ayurvedic_data
        }

# Optional FastAPI edge microservice
try:
    from fastapi import FastAPI, UploadFile, File
    from fastapi.middleware.cors import CORSMiddleware
    import io

    app = FastAPI(
        title="Sanjeevani Offline Edge API",
        version="2.0.0",
        description="Zero-Cloud Offline Edge Inference Server using TFLite Quantized Engine"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    offline_engine = None

    @app.on_event("startup")
    async def init_engine():
        global offline_engine
        offline_engine = SanjeevaniOfflineAPI()

    @app.get("/health")
    def health():
        return {"status": "online", "mode": "standalone_offline_edge", "engine": "TFLite"}

    @app.post("/predict")
    async def predict_edge(file: UploadFile = File(...)):
        contents = await file.read()
        res = offline_engine.predict(io.BytesIO(contents))
        return res

except ImportError:
    app = None

if __name__ == "__main__":
    api = SanjeevaniOfflineAPI()
    test_dir = os.path.join(project_root, "data", "processed", "test")
    test_img = os.path.join(test_dir, "Adulsa", "inat_103049127.jpg")
    if os.path.exists(test_img):
        print(f"\nRunning test inference on: {test_img}")
        res = api.predict(test_img)
        print(json.dumps(res, indent=2))
