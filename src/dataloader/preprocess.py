"""
Image preprocessing module for medicinal plant leaf images.
Handles normalization, resizing, and base transforms.
"""

import torch
import torchvision.transforms as T
from PIL import Image
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ImageNet normalization (for models pre-trained on ImageNet)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

RESIZE_SIZE = 384
CROP_SIZE = 384


def get_base_transforms(split='train'):
    """
    Returns base preprocessing transforms (no augmentation).
    Used for validation and test sets.

    Args:
        split: 'train', 'val', or 'test'

    Returns:
        torchvision.transforms.Compose object
    """
    return T.Compose([
        T.Resize((RESIZE_SIZE, RESIZE_SIZE)),
        T.ToTensor(),
        T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def preprocess_image(image_path, split='train'):
    """
    Load and preprocess a single image.

    Args:
        image_path: Path to image file
        split: 'train', 'val', or 'test'

    Returns:
        torch.Tensor of shape (3, 384, 384)
    """
    try:
        img = Image.open(image_path).convert('RGB')
        transform = get_base_transforms(split)
        tensor = transform(img)
        return tensor
    except Exception as e:
        logger.error(f"Failed to preprocess {image_path}: {e}")
        return None


def test_preprocessing():
    """Test preprocessing on a sample image."""
    processed_path = Path('processed/train')

    # Find a sample image
    sample_files = list(processed_path.rglob('*.png')) + list(processed_path.rglob('*.jpg'))

    if not sample_files:
        logger.error("No images found in processed/train/")
        return

    sample_img_path = sample_files[0]
    logger.info(f"Testing preprocessing on: {sample_img_path.name}")

    # Load original image
    orig_img = Image.open(sample_img_path).convert('RGB')
    logger.info(f"  Original size: {orig_img.size}")

    # Preprocess
    tensor = preprocess_image(sample_img_path, split='train')

    if tensor is None:
        return

    logger.info(f"  Tensor shape: {tensor.shape}")
    logger.info(f"  Min: {tensor.min():.3f}, Max: {tensor.max():.3f}")
    logger.info(f"  Mean: {tensor.mean():.3f}, Std: {tensor.std():.3f}")

    # Verify normalization
    expected_mean = torch.tensor(IMAGENET_MEAN).view(3, 1, 1)
    expected_std = torch.tensor(IMAGENET_STD).view(3, 1, 1)

    actual_mean = tensor.mean(dim=(1, 2))
    actual_std = tensor.std(dim=(1, 2))

    logger.info(f"\nNormalization check:")
    logger.info(f"  Expected mean: {expected_mean.squeeze()}")
    logger.info(f"  Actual mean:   {actual_mean}")
    logger.info(f"  Expected std:  {expected_std.squeeze()}")
    logger.info(f"  Actual std:    {actual_std}")

    logger.info("\nPreprocessing test PASSED")


if __name__ == "__main__":
    test_preprocessing()
