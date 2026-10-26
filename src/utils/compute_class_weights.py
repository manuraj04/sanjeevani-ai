"""
Compute class weights for handling imbalanced medicinal plant dataset.
Uses inverse frequency weighting to penalize minority class errors.
"""

import pandas as pd
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_class_weights(split='train'):
    """
    Compute inverse frequency weights for imbalanced classes.

    Formula: weight_i = total_samples / (num_classes * samples_i)

    Args:
        split: Which split to compute weights for ('train', 'val', 'test')

    Returns:
        Dictionary mapping species_name -> weight
    """
    df = pd.read_csv('metadata/split_log.csv')

    # Filter to specified split
    split_df = df[df['split'] == split]

    # Count samples per class
    class_counts = split_df['species_name'].value_counts()

    logger.info(f"\nClass distribution for {split.upper()} set:")
    logger.info(f"  Total samples: {len(split_df)}")
    logger.info(f"  Total classes: {len(class_counts)}")
    logger.info(f"  Min samples/class: {class_counts.min()}")
    logger.info(f"  Max samples/class: {class_counts.max()}")
    logger.info(f"  Mean samples/class: {class_counts.mean():.1f}")

    # Inverse frequency weighting
    total = class_counts.sum()
    num_classes = len(class_counts)
    weights = {}

    for species, count in class_counts.items():
        # Raw weight: total / (num_classes * count)
        weight = total / (num_classes * count)
        weights[species] = weight

    # Normalize so sum equals num_classes (optional, but helps with loss scaling)
    total_weight = sum(weights.values())
    weights = {k: v * num_classes / total_weight for k, v in weights.items()}

    # Print summary
    logger.info(f"\nClass weights (inverse frequency):")
    for species in sorted(weights.keys()):
        original_count = class_counts[species]
        weight = weights[species]
        logger.info(f"  {species:20s}: {original_count:5d} samples -> weight {weight:.4f}")

    # Find imbalance ratio
    min_weight = min(weights.values())
    max_weight = max(weights.values())
    logger.info(f"\nImbalance ratio: {max_weight / min_weight:.2f}x")

    return weights


def save_weights(weights, output_path='metadata/class_weights.json'):
    """Save class weights to JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(weights, f, indent=2)

    logger.info(f"\nWeights saved to: {output_path}")

    # Also save as CSV for easy inspection
    csv_path = output_path.replace('.json', '.csv')
    weights_df = pd.DataFrame(list(weights.items()), columns=['species', 'weight'])
    weights_df = weights_df.sort_values('weight', ascending=False)
    weights_df.to_csv(csv_path, index=False)
    logger.info(f"Weights also saved as: {csv_path}")


def load_weights(path='metadata/class_weights.json'):
    """Load class weights from JSON file."""
    with open(path, 'r') as f:
        weights = json.load(f)
    return weights


if __name__ == "__main__":
    # Compute weights for training set
    weights = compute_class_weights(split='train')

    # Save weights
    save_weights(weights, 'metadata/class_weights.json')

    logger.info("\n" + "=" * 60)
    logger.info("Class weights computed successfully!")
    logger.info("These weights will be used in the loss function during training")
    logger.info("to penalize errors on minority classes more heavily.")
