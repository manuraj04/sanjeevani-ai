import os
import json
import sqlite3
import numpy as np
import tensorflow as tf
from PIL import Image

class SanjeevaniOfflineAPI:
    def __init__(self, model_path, db_path, class_names=None, confidence_threshold=0.70):
        self.model_path = model_path
        self.db_path = db_path
        self.confidence_threshold = confidence_threshold
        
        print("Loading TFLite interpreter...")
        self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
        self.interpreter.allocate_tensors()
        
        self.input_details = self.interpreter.get_input_details()[0]
        self.output_details = self.interpreter.get_output_details()[0]
        
        self.class_names = class_names
        # We assume the last class is Non_Plant if we have 67 classes (66 plants + 1 non_plant)
        self.non_plant_idx = len(class_names) - 1 if class_names else -1

    def preprocess(self, image_path):
        img = Image.open(image_path).convert('RGB')
        img = img.resize((256, 256), Image.BILINEAR)
        
        # Center crop
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

    def fetch_ayurvedic_info(self, species_name):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 1. Get basic plant info
            cursor.execute("SELECT * FROM plants WHERE species_name = ?", (species_name,))
            plant = cursor.fetchone()
            
            if not plant:
                return {"message": "No Ayurvedic data found for this species in the local DB."}
                
            plant_id = plant['plant_id']
            data = dict(plant)
            
            # 2. Get ayurvedic profile
            cursor.execute("SELECT * FROM ayurvedic_profile WHERE plant_id = ?", (plant_id,))
            profile = cursor.fetchone()
            if profile:
                data['ayurvedic_profile'] = dict(profile)
                
            # 3. Get therapeutic uses
            cursor.execute("SELECT condition, use_description FROM therapeutic_uses WHERE plant_id = ?", (plant_id,))
            uses = cursor.fetchall()
            data['therapeutic_uses'] = [dict(u) for u in uses]
            
            # 4. Get contraindications
            cursor.execute("SELECT condition, severity, notes FROM contraindications WHERE plant_id = ?", (plant_id,))
            contras = cursor.fetchall()
            data['contraindications'] = [dict(c) for c in contras]
            
            conn.close()
            return data
            
        except Exception as e:
            return {"error": str(e)}

    def predict(self, image_path):
        try:
            input_data = self.preprocess(image_path)
        except Exception as e:
            return {"status": "error", "message": f"Image processing failed: {e}"}
            
        self.interpreter.set_tensor(self.input_details['index'], input_data)
        self.interpreter.invoke()
        
        output_data = self.interpreter.get_tensor(self.output_details['index'])[0]
        
        # Output is logits or probabilities. Assuming softmax wasn't applied in TFLite:
        # Actually in EfficientNet it might just be logits. We apply softmax.
        def softmax(x):
            e_x = np.exp(x - np.max(x))
            return e_x / e_x.sum(axis=0)
            
        probs = softmax(output_data)
        pred_idx = int(np.argmax(probs))
        confidence = float(probs[pred_idx])
        
        # OOD Rejection
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
        
        # Fetch knowledge base data
        ayurvedic_data = self.fetch_ayurvedic_info(species_name)
        
        return {
            "status": "success",
            "prediction": species_name,
            "confidence": confidence,
            "ayurvedic_data": ayurvedic_data
        }

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_path = os.path.join(project_root, "data", "processed", "sanjeevani_quantized.tflite")
    db_path = os.path.join(project_root, "data", "processed", "sanjeevani_kb.db")
    test_dir = os.path.join(project_root, "data", "processed", "test")
    
    # Load class names from test directory folders
    if os.path.exists(test_dir):
        class_names = sorted(os.listdir(test_dir))
    else:
        print("Warning: Could not find test directory to infer class names.")
        class_names = None
        
    api = SanjeevaniOfflineAPI(model_path, db_path, class_names=class_names)
    
    # Run a quick test if we can find any image
    if class_names:
        first_class = class_names[0]
        class_dir = os.path.join(test_dir, first_class)
        images = os.listdir(class_dir)
        if images:
            test_img = os.path.join(class_dir, images[0])
            print(f"\nRunning test inference on: {test_img}")
            result = api.predict(test_img)
            print(json.dumps(result, indent=2))
