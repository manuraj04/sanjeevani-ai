import torch
import torch.nn as nn
from torchvision import models
import ai_edge_torch

def get_model(num_classes):
    print("Loading model architecture...")
    weights = models.EfficientNet_V2_S_Weights.IMAGENET1K_V1
    model = models.efficientnet_v2_s(weights=weights)
    
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.4), 
        nn.Linear(in_features, 512), 
        nn.GELU(), 
        nn.Dropout(0.3), 
        nn.Linear(512, num_classes)
    )
    return model

def main():
    model_path = r"d:\Sanjeevani Scan AI\data\processed\best_model_final.pth"
    tflite_path = r"d:\Sanjeevani Scan AI\data\processed\sanjeevani_quantized.tflite"
    
    print(f"Loading weights from {model_path}")
    state_dict = torch.load(model_path, map_location=torch.device('cpu'))
    
    num_classes = state_dict['classifier.4.weight'].shape[0]
    print(f"Detected {num_classes} classes from the checkpoint.")
    
    model = get_model(num_classes)
    model.load_state_dict(state_dict)
    model.eval()
    
    print("Converting PyTorch model directly to TFLite with ai_edge_torch...")
    dummy_input = (torch.randn(1, 3, 224, 224),)
    
    # Use dynamic range quantization for < 20MB
    import ai_edge_quantizer
    from ai_edge_quantizer import quantize, pt2e_quantizer
    # Wait, ai_edge_quantizer API is changing. Let's just do a normal convert first,
    # then if it's too big, we can use the ai_edge_quantizer or standard TF post-training quantizer.
    edge_model = ai_edge_torch.convert(model, dummy_input)
    edge_model.export(tflite_path)
    print(f"TFLite export completed successfully: {tflite_path}")
    
if __name__ == "__main__":
    main()
