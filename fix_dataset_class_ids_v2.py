"""
Fix class IDs in CBOR dataset files based on class_name.

Expected class IDs:
- sawtooth: 0
- sine: 1
- square: 2
- triangular: 3
"""

import cbor2
import os
from pathlib import Path

# Mapping from class_name to correct class_id
CLASS_NAME_TO_ID = {
    'sawtooth': 0,
    'sine': 1,
    'square': 2,
    'triangular': 3,
}

def fix_cbor_file(file_path):
    """Fix class IDs in a single CBOR file based on class_name."""
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
    stats = {}

    # Fix class_id based on class_name in all samples
    for sample in data['samples']:
        if 'class_name' in sample and 'class_id' in sample:
            class_name = sample['class_name']
            old_id = sample['class_id']

            if class_name in CLASS_NAME_TO_ID:
                correct_id = CLASS_NAME_TO_ID[class_name]

                if old_id != correct_id:
                    sample['class_id'] = correct_id
                    changed = True

                    # Track changes
                    key = f"{class_name}: {old_id} -> {correct_id}"
                    stats[key] = stats.get(key, 0) + 1

    if changed:
        # Backup original file (restore from backup if it exists)
        backup_path = str(file_path) + '.backup'
        if not os.path.exists(backup_path):
            import shutil
            shutil.copy2(file_path, backup_path)
            print(f"  Created backup: {backup_path}")

        # Write fixed data
        with open(file_path, 'wb') as f:
            cbor2.dump(data, f)

        for change, count in stats.items():
            print(f"  [OK] Fixed {count} samples: {change}")
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
    # Exclude backup files
    cbor_files = [f for f in cbor_files if not str(f).endswith('.backup')]

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
    print(f"{'='*60}")

    cbor_files = sorted(dir_path.glob("*.cbor"))
    cbor_files = [f for f in cbor_files if not str(f).endswith('.backup')]

    errors = []
    for cbor_file in cbor_files:
        with open(cbor_file, 'rb') as f:
            data = cbor2.load(f)

        if 'samples' in data and len(data['samples']) > 0:
            class_name = data['samples'][0]['class_name']
            class_id = data['samples'][0]['class_id']
            expected_id = CLASS_NAME_TO_ID.get(class_name, -1)

            status = "[OK]" if class_id == expected_id else "[ERROR]"
            print(f"  {status} {cbor_file.name[:40]:40s} class_name=\"{class_name}\", class_id={class_id} (expected {expected_id})")

            if class_id != expected_id:
                errors.append(cbor_file.name)

    print(f"{'='*60}")
    if errors:
        print(f"ERROR: {len(errors)} files still have wrong class IDs!")
        print("Files with errors:", errors)
    else:
        print(f"SUCCESS: All {len(cbor_files)} files have correct class IDs!")
    print(f"{'='*60}\n")

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
    print("DATASET FIXED!")
    print("="*60)
    print("Next step: RETRAIN the model in CiRA Studio")
    print("  1. Open StandardWave1 project")
    print("  2. Go to Training tab")
    print("  3. Click 'Train Model' button")
    print("  4. After training, re-deploy to Jetson")
    print("="*60)
