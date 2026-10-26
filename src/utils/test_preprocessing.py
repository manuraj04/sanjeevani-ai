"""
Test preprocessing, augmentation, and DataLoaders.
Visualizes sample batches to verify correctness.
"""

import torch
import matplotlib.pyplot as plt
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_with_augmentation():
    """Test DataLoader with proper augmentation transforms."""
    from augmentation import get_augmented_transforms
    from dataloader import get_dataloaders

    logger.info("Testing DataLoaders with augmentation...\n")

    # Create DataLoaders with augmentation
    transform_factory = get_augmented_transforms
    train_loader, val_loader, test_loader = get_dataloaders(
        batch_size=32,
        num_workers=0,
        use_weighted_sampler=True,
        transform_factory=transform_factory
    )

    # Get a batch from train loader
    logger.info("\nGetting batch from train loader...")
    batch = next(iter(train_loader))

    logger.info(f"Batch keys: {batch.keys()}")
    logger.info(f"  Images shape: {batch['image'].shape}")
    logger.info(f"  Labels shape: {batch['label'].shape}")
    logger.info(f"  Batch size: {len(batch['label'])}")
    logger.info(f"  Image dtype: {batch['image'].dtype}")
    logger.info(f"  Image range: [{batch['image'].min():.3f}, {batch['image'].max():.3f}]")

    # Verify all images are same size (shape is [batch, channels, height, width])
    assert batch['image'].shape == (32, 3, 384, 384), f"Unexpected shape: {batch['image'].shape}"
    logger.info(f"\n  All images are 384x384 - PASSED")

    # Test a few batches from each split
    logger.info("\nTesting multiple batches...")
    for split_name, loader in [('train', train_loader), ('val', val_loader), ('test', test_loader)]:
        for i, batch in enumerate(loader):
            if i >= 2:  # Test first 2 batches
                break
            assert batch['image'].shape[0] == 32, f"Wrong batch size in {split_name}"
            assert batch['image'].shape[1:] == (3, 384, 384), f"Wrong image shape in {split_name}"
            logger.info(f"  {split_name} batch {i}: OK")

    logger.info("\nAll DataLoader tests PASSED!")
    return batch


def visualize_batch(batch, num_images=12, output_path='reports/preprocessing_sample.png'):
    """Visualize a batch of preprocessed images."""
    logger.info(f"\nVisualizing batch ({num_images} images)...")

    # Denormalize for visualization
    IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406]).reshape(3, 1, 1)
    IMAGENET_STD = torch.tensor([0.229, 0.224, 0.225]).reshape(3, 1, 1)

    images = batch['image'][:num_images].clone()
    images = images * IMAGENET_STD + IMAGENET_MEAN
    images = torch.clamp(images, 0, 1)

    # Create figure
    fig, axes = plt.subplots(3, 4, figsize=(14, 10))
    fig.suptitle('Sample Preprocessed Leaf Images', fontsize=14, fontweight='bold')

    for i, ax in enumerate(axes.flat):
        if i < len(images):
            img = images[i].permute(1, 2, 0).numpy()
            ax.imshow(img)
            species = batch['species'][i]
            filename = batch['filename'][i]
            ax.set_title(f"{species}\n{filename[:20]}...", fontsize=9)
        ax.axis('off')

    plt.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=120, bbox_inches='tight')
    logger.info(f"  Visualization saved: {output_path}")
    plt.close()


def main():
    """Run all tests."""
    logger.info("="*70)
    logger.info("OBJECTIVE 2 - PREPROCESSING TEST SUITE")
    logger.info("="*70)

    try:
        # Test DataLoaders with augmentation
        batch = test_with_augmentation()

        # Visualize batch
        visualize_batch(batch, num_images=12)

        logger.info("\n" + "="*70)
        logger.info("SUCCESS - Preprocessing pipeline is ready for training!")
        logger.info("="*70)
        logger.info("\nNext steps:")
        logger.info("  1. Review visualization: reports/preprocessing_sample.png")
        logger.info("  2. Verify augmentations look natural")
        logger.info("  3. Proceed to Objective 3: Model Training")

        return 0

    except Exception as e:
        logger.error(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
