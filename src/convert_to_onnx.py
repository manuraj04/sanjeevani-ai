import os
import torch
import torch.nn as nn
from torchvision import models

def get_model(num_classes):
    print("Loading model architecture...")
    weights = models.EfficientNet_V2_S_Weights.IMAGENET1K_V1
    model = models.efficientnet_v2_s(weights=weights)
    
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.4), 
        nn.Linear(in_features, 512), 
        nn.SiLU(), 
        nn.Dropout(0.3), 
        nn.Linear(512, num_classes)
    )
    return model

def main():
    model_path = r"d:\Sanjeevani Scan AI\data\processed\best_model_final.pth"
    onnx_path = r"d:\Sanjeevani Scan AI\data\processed\sanjeevani.onnx"
    
    print(f"Loading weights from {model_path}")
    state_dict = torch.load(model_path, map_location=torch.device('cpu'))
    
    num_classes = state_dict['classifier.4.weight'].shape[0]
    print(f"Detected {num_classes} classes from the checkpoint.")
    
    model = get_model(num_classes)
    model.load_state_dict(state_dict)
    model.eval()
    
    print(f"Exporting PyTorch model to ONNX: {onnx_path}")
    dummy_input = torch.randn(1, 3, 224, 224)
    # Removing dynamic_axes to force a static batch size of 1 for easier TFLite conversion
    torch.onnx.export(
        model, 
        dummy_input, 
        onnx_path, 
        export_params=True,
        opset_version=13,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output']
    )
    print("ONNX export completed successfully.")
    
if __name__ == "__main__":
    main()
