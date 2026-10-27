import os
import sys
import time
import torch
import numpy as np
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from sklearn.metrics import f1_score

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.models.cbam_efficientnet import MultiScaleCBAMEfficientNet

def evaluate_cbam():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Evaluating CBAM model on device: {device} ({torch.cuda.get_device_name(0)})")
    
    test_dir = os.path.join(project_root, "data", "processed", "test")
    model_path = os.path.join(project_root, "data", "processed", "best_cbam_model.pth")
    
    test_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.CenterCrop((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    test_dataset = datasets.ImageFolder(test_dir, transform=test_transform)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False, num_workers=2, pin_memory=True)
    
    print(f"[*] Test images: {len(test_dataset)} across {len(test_dataset.classes)} classes")
    
    model = MultiScaleCBAMEfficientNet(num_classes=66, pretrained=False).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.eval()
    
    param_count = sum(p.numel() for p in model.parameters()) / 1e6
    print(f"[*] Total Parameters: {param_count:.2f} M")
    
    # Warmup GPU
    dummy_input = torch.randn(1, 3, 224, 224).to(device)
    for _ in range(50):
        with torch.no_grad():
            _ = model(dummy_input)
            
    # Measure Latency (batch=1)
    latencies = []
    for _ in range(200):
        t0 = time.time()
        with torch.no_grad():
            _ = model(dummy_input)
        torch.cuda.synchronize()
        latencies.append((time.time() - t0) * 1000)
    mean_latency = np.mean(latencies)
    print(f"[*] Mean Single-Image Forward Latency: {mean_latency:.2f} ms")
    
    all_preds = []
    all_targets = []
    top1_correct = 0
    top5_correct = 0
    total = 0
    
    print("[*] Running sealed test set evaluation...")
    with torch.no_grad():
        for inputs, targets in test_loader:
            inputs, targets = inputs.to(device, non_blocking=True), targets.to(device, non_blocking=True)
            with torch.amp.autocast('cuda'):
                outputs = model(inputs)
                
            _, pred_top1 = torch.max(outputs, 1)
            _, pred_top5 = outputs.topk(5, 1, True, True)
            
            top1_correct += (pred_top1 == targets).sum().item()
            for i in range(len(targets)):
                if targets[i] in pred_top5[i]:
                    top5_correct += 1
                    
            total += targets.size(0)
            all_preds.extend(pred_top1.cpu().numpy())
            all_targets.extend(targets.cpu().numpy())
            
    top1_acc = (top1_correct / total) * 100
    top5_acc = (top5_correct / total) * 100
    macro_f1 = f1_score(all_targets, all_preds, average='macro')
    weighted_f1 = f1_score(all_targets, all_preds, average='weighted')
    
    print("=" * 60)
    print(f" MULTI-SCALE CBAM EFFICIENTNETV2-S TEST BENCHMARK")
    print("=" * 60)
    print(f" Parameters:         {param_count:.2f} M")
    print(f" Top-1 Accuracy:     {top1_acc:.2f}%")
    print(f" Top-5 Accuracy:     {top5_acc:.2f}%")
    print(f" Macro F1-Score:     {macro_f1:.4f}")
    print(f" Weighted F1-Score:  {weighted_f1:.4f}")
    print(f" Inference Latency:  {mean_latency:.2f} ms")
    print("=" * 60)

if __name__ == "__main__":
    evaluate_cbam()

