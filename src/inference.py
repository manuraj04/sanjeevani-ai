import os
import torch
from torchvision import transforms, models
import torch.nn as nn
from PIL import Image
import json

class SanjeevaniClassifier:
    def __init__(self, model_path, num_classes=67, confidence_threshold=0.70):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.num_classes = num_classes
        self.confidence_threshold = confidence_threshold
        self.model = self._load_model(model_path)
        
        # In a real scenario, this would load from a class mapping JSON.
        # We assume the last class is 'Non_Plant'
        self.non_plant_class_idx = num_classes - 1 

        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def _load_model(self, model_path):
        print(f"Loading model on {self.device}...")
        weights = models.EfficientNet_V2_S_Weights.IMAGENET1K_V1
        model = models.efficientnet_v2_s(weights=weights)
        
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(0.4), 
            nn.Linear(in_features, 512), 
            nn.GELU(), 
            nn.Dropout(0.3), 
            nn.Linear(512, self.num_classes)
        )
        
        if os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))
        else:
            print(f"Warning: Model weights not found at {model_path}. Using initialized weights.")
            
        model = model.to(self.device)
        model.eval()
        return model

    def predict(self, image_path, class_names=None):
        """Predicts the class of an image with OOD rejection."""
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            return {"status": "error", "message": f"Failed to open image: {e}"}

        input_tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            
            confidence, predicted_idx = torch.max(probabilities, 0)
            confidence = confidence.item()
            predicted_idx = predicted_idx.item()

        # OOD Rejection Logic
        
        # 1. Did it explicitly predict the Non-Plant class?
        if predicted_idx == self.non_plant_class_idx:
            return {
                "status": "rejected",
                "reason": "non_plant_detected",
                "message": "The scanned image does not appear to be a plant or leaf.",
                "confidence": confidence
            }
            
        # 2. Is the confidence too low? (Thresholding)
        if confidence < self.confidence_threshold:
            return {
                "status": "rejected",
                "reason": "low_confidence",
                "message": f"Confidence too low ({confidence*100:.1f}%). Please rescan clearly.",
                "confidence": confidence
            }

        # Valid Plant Detected
        class_name = class_names[predicted_idx] if class_names else f"Class_{predicted_idx}"
        return {
            "status": "success",
            "prediction": class_name,
            "confidence": confidence
        }

if __name__ == "__main__":
    project_root = os.path.join(os.path.dirname(__file__), "..")
    model_path = os.path.join(project_root, "data", "processed", "best_model_final.pth")
    
    # Initialize the classifier (assumes 67 classes where 66 is Non_Plant)
    classifier = SanjeevaniClassifier(model_path=model_path, num_classes=67, confidence_threshold=0.70)
    
    print("Classifier ready. You can import this module to run inference with OOD rejection.")
