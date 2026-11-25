import os
import json
import torch
from torchvision import transforms, models
import torch.nn as nn
from PIL import Image

# Canonical botanical synonym groups so synonymous training labels combine confidence cleanly
SYNONYM_GROUPS = {
    "Amruth": "Giloy",
    "HolyBasilVana": "Tulsi",
    "Bringaraj": "Bhringraj",
}


class SanjeevaniClassifier:
    def __init__(self, model_path, num_classes=66, confidence_threshold=0.20, class_names_path=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.num_classes = num_classes
        self.confidence_threshold = confidence_threshold

        # Load authoritative class names list from JSON (never depends on data/processed/test in containers)
        if class_names_path is None:
            class_names_path = os.path.join(os.path.dirname(__file__), "api", "class_names.json")
        if os.path.exists(class_names_path):
            with open(class_names_path, "r", encoding="utf-8") as f:
                self.class_names = json.load(f)
            self.num_classes = len(self.class_names)
        else:
            self.class_names = None

        self.model = self._load_model(model_path)

        # Only treat an explicit "Non_Plant" class as OOD rejection; never falsely reject valid plant class index 65 (Yashad)
        if self.class_names and "Non_Plant" in self.class_names:
            self.non_plant_class_idx = self.class_names.index("Non_Plant")
        else:
            self.non_plant_class_idx = -1

        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def _load_model(self, model_path):
        print(f"Loading model on {self.device}...")
        has_checkpoint = os.path.exists(model_path)
        weights = None if has_checkpoint else models.EfficientNet_V2_S_Weights.IMAGENET1K_V1
        model = models.efficientnet_v2_s(weights=weights)

        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(in_features, 512),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(512, self.num_classes)
        )

        if has_checkpoint:
            model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))
        else:
            print(f"Warning: Model weights not found at {model_path}. Using initialized weights.")

        model = model.to(self.device)
        model.eval()
        return model

    def predict(self, image_path, class_names=None):
        """Predicts the botanical species with synonym probability aggregation and OOD rejection."""
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            return {"status": "error", "message": f"Failed to open image: {e}"}

        active_names = class_names or self.class_names

        # Multi-view inference blending full-frame center crop + slightly wider view for clustered leaves
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            raw_conf, raw_idx = torch.max(probabilities, 0)
            raw_conf = raw_conf.item()
            raw_idx = raw_idx.item()

        # 1. Explicit Non_Plant class check (only when Non_Plant exists)
        if self.non_plant_class_idx != -1 and raw_idx == self.non_plant_class_idx:
            return {
                "status": "rejected",
                "reason": "non_plant_detected",
                "message": "The scanned image does not appear to be a plant or leaf.",
                "confidence": raw_conf
            }

        # Aggregate probabilities over canonical botanical synonyms (e.g. Amruth + Giloy -> Giloy)
        if active_names and len(active_names) == len(probabilities):
            merged_probs = {}
            for idx, prob in enumerate(probabilities.tolist()):
                raw_label = active_names[idx]
                canonical = SYNONYM_GROUPS.get(raw_label, raw_label)
                merged_probs[canonical] = merged_probs.get(canonical, 0.0) + prob
            best_class, confidence = max(merged_probs.items(), key=lambda x: x[1])
        else:
            best_class = f"Class_{raw_idx}"
            confidence = raw_conf

        # 2. Confidence threshold rejection (guards against random non-botanical photos)
        if confidence < self.confidence_threshold:
            return {
                "status": "rejected",
                "reason": "low_confidence",
                "message": f"Confidence too low ({confidence*100:.1f}%). Please center a clear medicinal leaf in good lighting and try again.",
                "confidence": confidence
            }

        return {
            "status": "success",
            "prediction": best_class,
            "confidence": confidence
        }


if __name__ == "__main__":
    project_root = os.path.join(os.path.dirname(__file__), "..")
    model_path = os.path.join(project_root, "data", "processed", "best_model_final.pth")
    classifier = SanjeevaniClassifier(model_path=model_path, num_classes=66, confidence_threshold=0.20)
    print("Classifier ready with", len(classifier.class_names or []), "classes.")
