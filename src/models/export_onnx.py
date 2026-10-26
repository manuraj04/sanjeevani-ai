import torch
import torchvision.models as models
import torch.nn as nn
import os

def export_to_onnx():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    model_path = os.path.join(project_root, "data", "processed", "best_model_final.pth")
    onnx_path = os.path.join(project_root, "data", "processed", "sanjeevani_model.onnx")
    
    num_classes = 66
    device = torch.device("cpu") # Export on CPU
    
    print("Initializing model architecture...")
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
    
    print(f"Loading weights from {model_path}...")
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.eval()
    
    # Dummy input for tracing (Batch Size 1, 3 Channels, 224x224)
    dummy_input = torch.randn(1, 3, 224, 224, device=device)
    
    print(f"Exporting to ONNX at {onnx_path}...")
    torch.onnx.export(
        model, 
        dummy_input, 
        onnx_path,
        export_params=True,
        opset_version=11,          # Opset 11 is stable for most mobile conversions
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    
    print("✅ ONNX Export Successful! You can now convert this ONNX file to TFLite using tensorflow-onnx (tf2onnx).")

if __name__ == "__main__":
    export_to_onnx()
