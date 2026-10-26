import os
import torch
import numpy as np
from PIL import Image
import base64
from io import BytesIO
import cv2
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from torchvision import transforms

class GradCamGenerator:
    def __init__(self, model):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model.to(self.device)
        self.model.eval()
        
        # In EfficientNetV2-S, the last convolutional layer is in features[-1]
        try:
            self.target_layers = [self.model.features[-1]]
        except AttributeError:
            print("Warning: Could not automatically determine target layer. Grad-CAM may fail.")
            self.target_layers = []

        self.cam = GradCAM(model=self.model, target_layers=self.target_layers)

        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def generate_heatmap_base64(self, image_path, target_category=None):
        """Generates a Grad-CAM heatmap and returns it as a base64 encoded image string."""
        if not self.target_layers:
            return None
            
        try:
            original_image = Image.open(image_path).convert("RGB")
        except Exception as e:
            print(f"Error opening image: {e}")
            return None

        # Prepare input tensor
        input_tensor = self.transform(original_image).unsqueeze(0).to(self.device)

        # Generate CAM mask
        # target_category=None will automatically use the highest scoring category
        targets = None
        if target_category is not None:
            # Custom targeting is available in pytorch-grad-cam via ClassifierOutputTarget
            from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
            targets = [ClassifierOutputTarget(target_category)]

        grayscale_cam = self.cam(input_tensor=input_tensor, targets=targets)
        grayscale_cam = grayscale_cam[0, :]

        # Prepare the original image for overlay
        # Resize to match tensor size (224x224)
        rgb_img = original_image.resize((224, 224))
        rgb_img = np.float32(rgb_img) / 255
        
        # Apply the colormap (Jet)
        visualization = show_cam_on_image(rgb_img, grayscale_cam, use_rgb=True)
        
        # Convert back to PIL to save as Bytes/Base64
        vis_pil = Image.fromarray(visualization)
        
        buffered = BytesIO()
        vis_pil.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return img_str
