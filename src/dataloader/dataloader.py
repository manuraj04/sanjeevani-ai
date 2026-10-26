"""
PyTorch DataLoader factory for medicinal plant leaf dataset.
Handles weighted sampling for imbalanced classes.
"""

import torch
from torch.utils.data import DataLoader, WeightedRandomSampler
from plant_dataset import PlantLeafDataset
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_dataloaders(batch_size=32, num_workers=4, use_weighted_sampler=True, transform_factory=None):
    """
    Create train/val/test DataLoaders.

    Args:
        batch_size: Batch size for all loaders
        num_workers: Number of worker processes for data loading
        use_weighted_sampler: If True, use weighted sampling for training to handle class imbalance
        transform_factory: Function that returns transforms. If None, no transforms are applied.

    Returns:
        Tuple of (train_loader, val_loader, test_loader)
    """

    # Get transforms
    if transform_factory is None:
        logger.warning("No transform factory provided; using no augmentation")
        train_transform = None
        val_transform = None
        test_transform = None
    else:
        train_transform = transform_factory('train')
        val_transform = transform_factory('val')
        test_transform = transform_factory('test')

    # Create datasets
    logger.info("Creating datasets...")
    train_dataset = PlantLeafDataset('train', transform=train_transform)
    val_dataset = PlantLeafDataset('val', transform=val_transform)
    test_dataset = PlantLeafDataset('test', transform=test_transform)

    # Create train loader with optional weighted sampling
    logger.info("\nSetting up train loader...")
    if use_weighted_sampler:
        sampler = _create_weighted_sampler(train_dataset)
        if sampler is not None:
            train_loader = DataLoader(
                train_dataset,
                batch_size=batch_size,
                sampler=sampler,
                num_workers=num_workers,
                pin_memory=True
            )
            logger.info("  Using weighted random sampler for class imbalance")
        else:
            train_loader = DataLoader(
                train_dataset,
                batch_size=batch_size,
                shuffle=True,
                num_workers=num_workers,
                pin_memory=True
            )
            logger.info("  Using standard random sampler (no class weights)")
    else:
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=True
        )
        logger.info("  Using standard random sampler")

    # Create val and test loaders (no shuffling, no weighted sampling)
    logger.info("Setting up val/test loaders...")
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )

    # Print summary
    logger.info(f"\nDataLoader summary:")
    logger.info(f"  Train: {len(train_loader)} batches ({len(train_dataset)} images)")
    logger.info(f"  Val:   {len(val_loader)} batches ({len(val_dataset)} images)")
    logger.info(f"  Test:  {len(test_loader)} batches ({len(test_dataset)} images)")
    logger.info(f"  Batch size: {batch_size}")
    logger.info(f"  Num workers: {num_workers}")

    return train_loader, val_loader, test_loader


def _create_weighted_sampler(dataset):
    """
    Create weighted random sampler for imbalanced dataset.

    Args:
        dataset: PlantLeafDataset instance

    Returns:
        WeightedRandomSampler or None if weights not available
    """
    weights_path = Path('metadata/class_weights.json')

    if not weights_path.exists():
        logger.warning(f"Class weights not found at {weights_path}")
        logger.info("Run compute_class_weights.py first to create class weights")
        return None

    try:
        with open(weights_path, 'r') as f:
            class_weights = json.load(f)

        # Compute sample weights
        sample_weights = []
        for i in range(len(dataset)):
            species = dataset.metadata.iloc[i]['species_name']
            # Sample weight = 1 / class_weight (inverse of class weight)
            sample_weight = 1.0 / class_weights.get(species, 1.0)
            sample_weights.append(sample_weight)

        # Normalize
        total_weight = sum(sample_weights)
        sample_weights = [w / total_weight * len(sample_weights) for w in sample_weights]

        sampler = WeightedRandomSampler(
            weights=sample_weights,
            num_samples=len(sample_weights),
            replacement=True
        )

        logger.info(f"Weighted sampler created from {len(class_weights)} classes")
        return sampler

    except Exception as e:
        logger.error(f"Failed to create weighted sampler: {e}")
        return None


if __name__ == "__main__":
    # Test without transforms
    logger.info("Testing DataLoaders without augmentation...")
    try:
        train_loader, val_loader, test_loader = get_dataloaders(
            batch_size=32,
            num_workers=0,  # Use 0 for testing
            use_weighted_sampler=True,
            transform_factory=None
        )

        # Get a batch
        batch = next(iter(train_loader))
        logger.info(f"\nSample batch from train_loader:")
        logger.info(f"  Images shape: {batch['image'].shape if isinstance(batch['image'], torch.Tensor) else 'N/A'}")
        logger.info(f"  Labels shape: {batch['label'].shape}")
        logger.info(f"  Species: {batch['species'][:3]}")

        logger.info("\nDataLoader test PASSED")

    except Exception as e:
        logger.error(f"DataLoader test FAILED: {e}")
        import traceback
        traceback.print_exc()
