"""
Fix class IDs in CBOR dataset files to match the expected mapping.

Current (wrong) class IDs in dataset:
- sine: 0
- sawtooth: 2
- square: 4
- triangular: 3

Expected class IDs:
- sawtooth: 0
- sine: 1
- square: 2
- triangular: 3
"""

import cbor2
import os
from pathlib import Path

# Mapping from current wrong IDs to correct IDs
CLASS_ID_MAPPING = {
    0: 1,  # sine: 0 -> 1
    2: 0,  # sawtooth: 2 -> 0
    4: 2,  # square: 4 -> 2
    3: 3,  # triangular: 3 -> 3 (already correct)
}

def fix_cbor_file(file_path):
    """Fix class IDs in a single CBOR file."""
    print(f"Processing: {file_path}")

    # Read the CBOR file
    with open(file_path, 'rb') as f:
        data = cbor2.load(f)

    # Check if it has samples
    if 'samples' not in data:
        print(f"  WARNING: No 'samples' key found, skipping")
        return False

    # Track if any changes were made
    changed = False
    original_class_id = None

    # Fix class_id in all samples
    for sample in data['samples']:
        if 'class_id' in sample:
            old_id = sample['class_id']
            if original_class_id is None:
                original_class_id = old_id

            if old_id in CLASS_ID_MAPPING:
                new_id = CLASS_ID_MAPPING[old_id]
                sample['class_id'] = new_id
                changed = True

    if changed:
        # Backup original file
        backup_path = str(file_path) + '.backup'
        if not os.path.exists(backup_path):
            os.rename(file_path, backup_path)
            print(f"  Created backup: {backup_path}")

        # Write fixed data
        with open(file_path, 'wb') as f:
            cbor2.dump(data, f)

        new_id = CLASS_ID_MAPPING.get(original_class_id, original_class_id)
        print(f"  [OK] Fixed: class_id {original_class_id} -> {new_id}")
        return True
    else:
        print(f"  No changes needed")
        return False

def fix_dataset_directory(dir_path):
    """Fix all CBOR files in a directory."""
    dir_path = Path(dir_path)
    if not dir_path.exists():
        print(f"ERROR: Directory not found: {dir_path}")
        return

    print(f"\n{'='*60}")
    print(f"Fixing dataset in: {dir_path}")
    print(f"{'='*60}")

    cbor_files = list(dir_path.glob("*.cbor"))
    print(f"Found {len(cbor_files)} CBOR files\n")

    fixed_count = 0
    for cbor_file in cbor_files:
        if fix_cbor_file(cbor_file):
            fixed_count += 1

    print(f"\n{'='*60}")
    print(f"Fixed {fixed_count} / {len(cbor_files)} files")
    print(f"{'='*60}\n")

def verify_fixes(dir_path):
    """Verify that class IDs are now correct."""
    dir_path = Path(dir_path)
    print(f"\nVerifying fixes in: {dir_path}")

    cbor_files = list(dir_path.glob("*.cbor"))

    for cbor_file in cbor_files[:4]:  # Check first 4 files
        with open(cbor_file, 'rb') as f:
            data = cbor2.load(f)

        if 'samples' in data and len(data['samples']) > 0:
            class_name = data['samples'][0]['class_name']
            class_id = data['samples'][0]['class_id']
            print(f"  {cbor_file.name[:30]:30s} -> class_name=\"{class_name}\", class_id={class_id}")

if __name__ == "__main__":
    # Fix training dataset
    train_dir = "D:/CiRA FES/Dataset/StandardWave/train"
    fix_dataset_directory(train_dir)
    verify_fixes(train_dir)

    # Fix test dataset
    test_dir = "D:/CiRA FES/Dataset/StandardWave/test"
    fix_dataset_directory(test_dir)
    verify_fixes(test_dir)

    print("\n" + "="*60)
    print("IMPORTANT: You must now RETRAIN the model!")
    print("The dataset has been fixed, but the current model was")
    print("trained with wrong labels and needs to be retrained.")
    print("="*60)
