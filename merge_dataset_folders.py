"""
Quick Dataset Merger - Batch load CBOR/JSON files from folders

Usage:
    python merge_dataset_folders.py

This will load all files from your motion dataset folders and create:
- motion_train.csv (training data with labels)
- motion_test.csv (test data with labels)
"""

import pandas as pd
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_sources.edgeimpulse_loader import EdgeImpulseLoader
from loguru import logger


def load_folder_batch(folder_path: Path, extract_labels=True):
    """
    Load all CBOR/JSON files from a folder and its subfolders.

    Args:
        folder_path: Path to folder containing CBOR/JSON files
        extract_labels: Whether to extract labels from filenames

    Returns:
        DataFrame with all loaded data
    """
    # Find all CBOR and JSON files recursively
    cbor_files = list(folder_path.glob("**/*.cbor"))
    json_files = list(folder_path.glob("**/*.json"))
    all_files = cbor_files + json_files

    logger.info(f"Found {len(all_files)} files in {folder_path}")

    data_list = []

    for file_path in all_files:
        try:
            loader = EdgeImpulseLoader()
            loader.file_path = file_path
            loader.extract_labels = extract_labels
            loader.label_pattern = "prefix"  # idle.1.cbor -> 'idle'
            loader.label_separator = "."

            df = loader.load_data()
            data_list.append(df)

            label = df['class_label'].iloc[0] if 'class_label' in df.columns else 'unlabeled'
            logger.info(f"  ✓ Loaded {file_path.name} ({len(df)} samples, label={label})")

        except Exception as e:
            logger.error(f"  ✗ Failed to load {file_path.name}: {e}")

    if not data_list:
        logger.warning(f"No data loaded from {folder_path}")
        return pd.DataFrame()

    # Concatenate all dataframes
    combined = pd.concat(data_list, ignore_index=True)
    logger.info(f"Combined {len(data_list)} files into {len(combined)} total samples")

    return combined


def main():
    """Main function to merge dataset folders."""

    # Define your dataset paths here
    dataset_base = Path(r"D:\CiRA FES\Dataset\Motion+Classification+-+Continuous+motion+recognition")

    # Correct folder names based on your dataset
    train_folder = dataset_base / "training"
    test_folder = dataset_base / "testing"

    logger.info("="*60)
    logger.info("CiRA FES Dataset Merger")
    logger.info("="*60)

    # Load training data
    if train_folder.exists():
        logger.info(f"\n📁 Loading TRAINING data from: {train_folder}")
        train_data = load_folder_batch(train_folder, extract_labels=True)

        if not train_data.empty:
            # Show class distribution
            if 'class_label' in train_data.columns:
                class_counts = train_data['class_label'].value_counts()
                logger.info("\n🎯 Training Class Distribution:")
                for class_name, count in class_counts.items():
                    logger.info(f"  {class_name}: {count} samples")

            # Save to CSV
            output_train = Path("motion_train.csv")
            train_data.to_csv(output_train, index=False)
            logger.info(f"\n✅ Saved training data to: {output_train}")
            logger.info(f"   Rows: {len(train_data)}, Columns: {len(train_data.columns)}")
    else:
        logger.warning(f"Training folder not found: {train_folder}")
        train_data = pd.DataFrame()

    # Load test data
    if test_folder and test_folder.exists():
        logger.info(f"\n📁 Loading TEST data from: {test_folder}")
        test_data = load_folder_batch(test_folder, extract_labels=True)

        if not test_data.empty:
            # Show class distribution
            if 'class_label' in test_data.columns:
                class_counts = test_data['class_label'].value_counts()
                logger.info("\n🎯 Test Class Distribution:")
                for class_name, count in class_counts.items():
                    logger.info(f"  {class_name}: {count} samples")

            # Save to CSV
            output_test = Path("motion_test.csv")
            test_data.to_csv(output_test, index=False)
            logger.info(f"\n✅ Saved test data to: {output_test}")
            logger.info(f"   Rows: {len(test_data)}, Columns: {len(test_data.columns)}")
    else:
        logger.info("\nNo test folder specified or found")
        test_data = pd.DataFrame()

    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Training samples: {len(train_data)}")
    logger.info(f"Test samples: {len(test_data)}")
    if 'class_label' in train_data.columns:
        logger.info(f"Classes: {sorted(train_data['class_label'].unique())}")
    logger.info("\n✨ Ready to load in CiRA FES!")
    logger.info("   1. Open CiRA FES")
    logger.info("   2. Select 'CSV File' data source")
    logger.info("   3. Load motion_train.csv")


if __name__ == "__main__":
    main()
