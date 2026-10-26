"""
Multi-Scale Attention CNN with EfficientNetV2-S Backbone and CBAM Modules.
Implements the genuine architecture proposed in the Sanjeevani Scan IEEE manuscript.

Architecture:
    Input: (B, 3, 224, 224)
      │
      ▼
    EfficientNetV2-S Stages:
      ├─ Stage 3 (features[0:4]): Output shape (B, 64, 28, 28)
      │    └─► CBAM Block 1 ──► AdaptiveAvgPool2d(1) ──► (B, 64)
      ├─ Stage 5 (features[4:6]): Output shape (B, 160, 14, 14)
      │    └─► CBAM Block 2 ──► AdaptiveAvgPool2d(1) ──► (B, 160)
      └─ Stage 7 (features[6:8]): Output shape (B, 1280, 7, 7)
           └─► CBAM Block 3 ──► AdaptiveAvgPool2d(1) ──► (B, 1280)
      │
      ▼
    Multi-Scale Feature Fusion:
      Concatenate [F3, F5, F7] ──► (B, 1504)
      │
      ▼
    Classification Head:
      Dropout(0.4) ──► Linear(1504, 512) ──► GELU() ──► Dropout(0.3) ──► Linear(512, num_classes)
"""

import torch
import torch.nn as nn
from torchvision import models
from .cbam import CBAM


class MultiScaleCBAMEfficientNet(nn.Module):
    def __init__(self, num_classes: int = 66, pretrained: bool = True):
        super(MultiScaleCBAMEfficientNet, self).__init__()

        # Load pretrained EfficientNetV2-S backbone
        weights = models.EfficientNet_V2_S_Weights.IMAGENET1K_V1 if pretrained else None
        base_model = models.efficientnet_v2_s(weights=weights)

        # Slice backbone into 3 distinct functional stages
        # Stage 3 covers input up to block 3: output is 64 channels at 28x28
        self.stage3 = nn.Sequential(*base_model.features[0:4])
        # Stage 5 covers blocks 4 and 5: output is 160 channels at 14x14
        self.stage5 = nn.Sequential(*base_model.features[4:6])
        # Stage 7 covers blocks 6 and 7: output is 1280 channels at 7x7
        self.stage7 = nn.Sequential(*base_model.features[6:8])

        # CBAM Attention Modules inserted at each multi-scale stage
        self.cbam_stage3 = CBAM(in_planes=64, reduction_ratio=16, kernel_size=7)
        self.cbam_stage5 = CBAM(in_planes=160, reduction_ratio=16, kernel_size=7)
        self.cbam_stage7 = CBAM(in_planes=1280, reduction_ratio=16, kernel_size=7)

        # Global pooling per scale
        self.pool = nn.AdaptiveAvgPool2d(1)

        # Multi-scale fusion dimensionality: 64 + 160 + 1280 = 1504
        self.fusion_dim = 64 + 160 + 1280

        # Classification Head
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.Linear(self.fusion_dim, 512),
            nn.GELU(),
            nn.Dropout(p=0.3),
            nn.Linear(512, num_classes)
        )

    def extract_features(self, x: torch.Tensor):
        """Returns intermediate attended feature maps and pooled vectors."""
        # Forward through Stage 3
        f3 = self.stage3(x)           # (B, 64, 28, 28)
        f3_att = self.cbam_stage3(f3)  # Attended texture & margin features

        # Forward through Stage 5
        f5 = self.stage5(f3)          # (B, 160, 14, 14)
        f5_att = self.cbam_stage5(f5)  # Attended shape & venation features

        # Forward through Stage 7
        f7 = self.stage7(f5)          # (B, 1280, 7, 7)
        f7_att = self.cbam_stage7(f7)  # Attended high-level semantic features

        # Spatial pooling
        p3 = torch.flatten(self.pool(f3_att), 1)  # (B, 64)
        p5 = torch.flatten(self.pool(f5_att), 1)  # (B, 160)
        p7 = torch.flatten(self.pool(f7_att), 1)  # (B, 1280)

        # Multi-scale feature concatenation
        fused = torch.cat([p3, p5, p7], dim=1)    # (B, 1504)

        return fused, f7_att

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        fused, _ = self.extract_features(x)
        logits = self.classifier(fused)
        return logits


if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MultiScaleCBAMEfficientNet(num_classes=66, pretrained=False).to(device)
    dummy_input = torch.randn(2, 3, 224, 224).to(device)

    out = model(dummy_input)
    assert out.shape == (2, 66), f"Output shape mismatch: {out.shape}"

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"MultiScaleCBAMEfficientNet verification PASSED!")
    print(f"  Input: {dummy_input.shape} -> Logits: {out.shape}")
    print(f"  Total Parameters: {total_params:,} ({total_params/1e6:.2f} M)")
    print(f"  Trainable Parameters: {trainable_params:,} ({trainable_params/1e6:.2f} M)")
