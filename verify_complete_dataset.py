#!/usr/bin/env python3
"""Verify complete StandardWave_new dataset"""

import cbor2
import os
import glob

def verify_dataset(dataset_dir):
    print("=" * 70)
    print(f"VERIFYING DATASET: {dataset_dir}")
    print("=" * 70)
    print()

    # Expected class mapping
    class_mapping = {
        'sawtooth': 0,
        'sine': 1,
        'square': 2,
        'triangular': 3
    }

    # Find all CBOR files
    cbor_files = glob.glob(os.path.join(dataset_dir, "*.cbor"))

    if not cbor_files:
        print("[ERROR] No CBOR files found in directory!")
        return False

    print(f"Found {len(cbor_files)} CBOR files\n")

    # Organize by class
    files_by_class = {}
    for filepath in cbor_files:
        filename = os.path.basename(filepath)
        # Extract class name from filename (e.g., "sine.1.cbor...")
        class_name = filename.split('.')[0]
        if class_name not in files_by_class:
            files_by_class[class_name] = []
        files_by_class[class_name].append(filepath)

    # Check each class
    all_ok = True
    for class_name in sorted(class_mapping.keys()):
        expected_id = class_mapping[class_name]

        if class_name not in files_by_class:
            print(f"[MISSING] {class_name.upper()}: No files found!")
            all_ok = False
            continue

        files = files_by_class[class_name]
        print(f"\n{class_name.upper()} (expected class_id={expected_id}):")
        print(f"  Files: {len(files)}")

        for filepath in sorted(files):
            filename = os.path.basename(filepath)

            # Read and verify
            try:
                with open(filepath, 'rb') as f:
                    data = cbor2.load(f)

                samples = data.get('samples', [])
                if not samples:
                    print(f"    [{filename}] [FAIL] No samples!")
                    all_ok = False
                    continue

                # Check first sample
                first_sample = samples[0]
                class_id = first_sample.get('class_id')
                class_name_in_data = first_sample.get('class_name')
                data_vals = first_sample.get('data', [])

                errors = []

                # Verify class_id
                if class_id != expected_id:
                    errors.append(f"class_id={class_id} (expected {expected_id})")
                    all_ok = False

                # Verify class_name
                if class_name_in_data != class_name:
                    errors.append(f"class_name='{class_name_in_data}' (expected '{class_name}')")
                    all_ok = False

                # Verify multi-channel data
                if len(data_vals) != 3:
                    errors.append(f"data has {len(data_vals)} channels (expected 3)")
                    all_ok = False
                elif abs(data_vals[0] - data_vals[1]) < 1e-6 and abs(data_vals[1] - data_vals[2]) < 1e-6:
                    errors.append("all channels identical")
                    all_ok = False

                if errors:
                    print(f"    [{filename}] [FAIL] {', '.join(errors)}")
                else:
                    print(f"    [{filename}] [OK] {len(samples)} samples")

            except Exception as e:
                print(f"    [{filename}] [ERROR] {str(e)}")
                all_ok = False

    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("=" * 70)

    for class_name in sorted(class_mapping.keys()):
        count = len(files_by_class.get(class_name, []))
        status = "[OK]" if count >= 3 else "[NEED MORE]" if count > 0 else "[MISSING]"
        print(f"{status} {class_name}: {count} files (recommend 3-5)")

    print()
    if all_ok and len(files_by_class) == 4:
        print("[SUCCESS] Dataset is complete and valid!")
        return True
    else:
        print("[INCOMPLETE] Dataset has issues - see above")
        return False

if __name__ == "__main__":
    dataset_dir = r"D:\CiRA FES\Dataset\StandardWave_new"
    verify_dataset(dataset_dir)
