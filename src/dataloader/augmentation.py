"""
Data augmentation pipeline for medicinal plant leaf images.
Uses albumentations for efficient, realistic augmentations.
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_augmented_transforms(split='train'):
    """
    Returns augmentation transforms using albumentations.
    Tuned for plant leaf images (avoid over-distortion).

    Args:
        split: 'train', 'val', or 'test'

    Returns:
        albumentations.Compose object
    """
    try:
        import albumentations as A
        from albumentations.pytorch import ToTensorV2
    except ImportError:
        logger.error("albumentations not installed. Run: pip install albumentations")
        raise

    if split == 'train':
        # Training: apply augmentation
        return A.Compose([
            A.Resize(384, 384),

            # Geometric transforms (moderate - preserve leaf morphology)
            A.Rotate(limit=30, border_mode=1, p=0.5),  # Up to ±30 degrees
            A.HorizontalFlip(p=0.5),  # Plants are usually symmetric
            A.Perspective(scale=(0.05, 0.1), p=0.3),  # Slight perspective change

            # Color/brightness transforms (mimic varying photo conditions)
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.3),
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.2),  # Sensor noise
            A.Blur(blur_limit=3, p=0.2),  # Out-of-focus shots

            # Normalization and conversion to tensor
            A.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
            ToTensorV2(),
        ], bbox_params=None)

    else:  # val, test — no augmentation, only normalization
        return A.Compose([
            A.Resize(384, 384),
            A.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
            ToTensorV2(),
        ])


def test_augmentation():
    """Test augmentation pipeline on sample images."""
    import numpy as np
    from PIL import Image
    from pathlib import Path

    processed_path = Path('processed/train')
    sample_files = list(processed_path.rglob('*.png')) + list(processed_path.rglob('*.jpg'))

    if not sample_files:
        logger.error("No images found in processed/train/")
        return

    sample_img_path = sample_files[0]
    logger.info(f"Testing augmentation on: {sample_img_path.name}")

    # Load image as numpy array
    img_pil = Image.open(sample_img_path).convert('RGB')
    img_np = np.array(img_pil)

    logger.info(f"Original shape: {img_np.shape}")

    # Apply augmentation
    transform = get_augmented_transforms(split='train')
    augmented = transform(image=img_np)
    tensor = augmented['image']

    logger.info(f"Augmented tensor shape: {tensor.shape}")
    logger.info(f"Tensor dtype: {tensor.dtype}")
    logger.info(f"Min: {tensor.min():.3f}, Max: {tensor.max():.3f}")

    logger.info("\nAugmentation test PASSED")


if __name__ == "__main__":
    # First check if albumentations is installed
    try:
        import albumentations
        logger.info(f"Albumentations version: {albumentations.__version__}")
    except ImportError:
        logger.error("albumentations not installed")
        logger.info("Installing: pip install albumentations")
        import subprocess
        subprocess.run(['pip', 'install', 'albumentations', '-q'])
        logger.info("Installation complete. Re-run script.")
        exit(0)

    test_augmentation()
