"""
Convolutional Block Attention Module (CBAM) implementation in PyTorch.
Reference:
    Woo, S., Park, J., Lee, J. Y., & Kweon, I. S. (2018).
    CBAM: Convolutional block attention module.
    Proceedings of the European Conference on Computer Vision (ECCV), pp. 3-19.
"""

import torch
import torch.nn as nn


class ChannelAttention(nn.Module):
    """
    Channel Attention Module.
    Aggregates spatial information via Average Pooling and Max Pooling,
    routes through a shared Multi-Layer Perceptron (MLP), and applies a sigmoid gate.
    """
    def __init__(self, in_planes: int, reduction_ratio: int = 16):
        super(ChannelAttention, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)

        # Ensure reduction doesn't collapse to 0 for small channel counts
        reduced_planes = max(in_planes // reduction_ratio, 4)

        self.mlp = nn.Sequential(
            nn.Flatten(),
            nn.Linear(in_planes, reduced_planes, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(reduced_planes, in_planes, bias=False)
        )
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        avg_out = self.mlp(self.avg_pool(x))
        max_out = self.mlp(self.max_pool(x))
        channel_weights = self.sigmoid(avg_out + max_out).unsqueeze(2).unsqueeze(3)
        return x * channel_weights


class SpatialAttention(nn.Module):
    """
    Spatial Attention Module.
    Aggregates channel information via Average and Max pooling along the channel axis,
    concatenates both 1-channel feature maps (yielding 2 channels),
    and applies a 7x7 convolution followed by a sigmoid gate.
    """
    def __init__(self, kernel_size: int = 7):
        super(SpatialAttention, self).__init__()
        assert kernel_size in (3, 7), "Kernel size must be 3 or 7"
        padding = 3 if kernel_size == 7 else 1

        self.conv = nn.Conv2d(2, 1, kernel_size=kernel_size, padding=padding, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        combined = torch.cat([avg_out, max_out], dim=1)
        spatial_weights = self.sigmoid(self.conv(combined))
        return x * spatial_weights


class CBAM(nn.Module):
    """
    Complete Convolutional Block Attention Module (CBAM).
    Sequentially applies Channel Attention and Spatial Attention:
        F' = M_c(F) * F
        F'' = M_s(F') * F'
    """
    def __init__(self, in_planes: int, reduction_ratio: int = 16, kernel_size: int = 7):
        super(CBAM, self).__init__()
        self.channel_att = ChannelAttention(in_planes, reduction_ratio=reduction_ratio)
        self.spatial_att = SpatialAttention(kernel_size=kernel_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x_out = self.channel_att(x)
        x_out = self.spatial_att(x_out)
        return x_out


if __name__ == "__main__":
    # Sanity check
    dummy = torch.randn(2, 64, 28, 28)
    cbam = CBAM(in_planes=64)
    out = cbam(dummy)
    assert out.shape == dummy.shape, f"Shape mismatch: {out.shape} vs {dummy.shape}"
    print(f"CBAM Unit Test PASSED: input {dummy.shape} -> output {out.shape}")
