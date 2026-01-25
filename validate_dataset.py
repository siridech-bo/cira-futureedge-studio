#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate CBOR dataset files for TimesNet training"""

import cbor2
import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def validate_cbor_file(filepath):
    """Validate a single CBOR dataset file"""
    print(f"\n{'='*70}")
    print(f"Validating: {Path(filepath).name}")
    print(f"{'='*70}")

    # Check file size
    file_size = os.path.getsize(filepath)
    print(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    # Parse CBOR
    try:
        with open(filepath, 'rb') as f:
            data = cbor2.load(f)
    except Exception as e:
        print(f"❌ ERROR: Failed to parse CBOR: {e}")
        return False

    # Check structure
    if not isinstance(data, dict):
        print(f"❌ ERROR: Root should be dict, got {type(data)}")
        return False

    print(f"✓ Valid CBOR structure")

    # Check metadata
    if 'metadata' in data:
        meta = data['metadata']
        print(f"\nMetadata:")
        print(f"  Device ID: {meta.get('device_id', 'N/A')}")
        print(f"  Timestamp: {meta.get('timestamp', 'N/A')}")
        print(f"  Class: {meta.get('class_name', 'N/A')} (ID: {meta.get('class_id', 'N/A')})")
        print(f"  Total samples: {meta.get('num_samples', 'N/A')}")
    else:
        print("⚠ Warning: No metadata found")

    # Check samples
    if 'samples' not in data:
        print("❌ ERROR: No 'samples' field found")
        return False

    samples = data['samples']
    if not isinstance(samples, list):
        print(f"❌ ERROR: samples should be list, got {type(samples)}")
        return False

    num_samples = len(samples)
    print(f"\n✓ Found {num_samples} samples")

    if num_samples == 0:
        print("❌ ERROR: No samples in dataset")
        return False

    # Validate first few samples
    print(f"\nValidating sample structure...")
    for i, sample in enumerate(samples[:3]):  # Check first 3 samples
        if not isinstance(sample, dict):
            print(f"❌ ERROR: Sample {i} is not a dict")
            return False

        required_fields = ['timestamp', 'class_name', 'class_id', 'data']
        for field in required_fields:
            if field not in sample:
                print(f"❌ ERROR: Sample {i} missing field '{field}'")
                return False

        data_array = sample['data']
        if not isinstance(data_array, list):
            print(f"❌ ERROR: Sample {i} data should be list, got {type(data_array)}")
            return False

        data_len = len(data_array)
        if i == 0:
            print(f"  Sample 0: {data_len} values, class='{sample['class_name']}', id={sample['class_id']}")
            expected_len = data_len
        elif data_len != expected_len:
            print(f"❌ ERROR: Sample {i} has {data_len} values, expected {expected_len}")
            return False

    # Check all samples have consistent length
    print(f"✓ First 3 samples validated")

    # Verify windowed format (should be 300 samples × 3 channels = 900 values)
    first_sample_len = len(samples[0]['data'])
    expected_windowed_len = 300 * 3  # 300 samples, 3 channels

    if first_sample_len == expected_windowed_len:
        print(f"✓ Correct windowed format: {first_sample_len} values (300 samples × 3 channels)")
    else:
        print(f"⚠ Warning: Expected {expected_windowed_len} values, got {first_sample_len}")

    # Check class consistency
    classes = set()
    for sample in samples:
        classes.add(sample['class_name'])

    if len(classes) == 1:
        print(f"✓ All samples have same class: '{list(classes)[0]}'")
    else:
        print(f"⚠ Warning: Multiple classes found: {classes}")

    # Summary
    print(f"\n{'='*70}")
    print(f"✓ VALIDATION PASSED")
    print(f"  Total windows: {num_samples}")
    print(f"  Values per window: {first_sample_len}")
    print(f"  Class: {samples[0]['class_name']} (ID: {samples[0]['class_id']})")
    print(f"{'='*70}")

    return True


def main():
    dataset_dir = Path("D:/CiRA FES/Dataset/StandardWave_new")

    if not dataset_dir.exists():
        print(f"Error: Directory not found: {dataset_dir}")
        sys.exit(1)

    # Find all CBOR files
    cbor_files = list(dataset_dir.glob("*.cbor"))

    if not cbor_files:
        print(f"Error: No .cbor files found in {dataset_dir}")
        sys.exit(1)

    print(f"Found {len(cbor_files)} CBOR files")

    # Validate each file
    results = {}
    for cbor_file in sorted(cbor_files):
        try:
            results[cbor_file.name] = validate_cbor_file(cbor_file)
        except Exception as e:
            print(f"\n❌ EXCEPTION while validating {cbor_file.name}: {e}")
            results[cbor_file.name] = False

    # Final summary
    print(f"\n\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")

    passed = sum(1 for v in results.values() if v)
    failed = len(results) - passed

    for filename, result in sorted(results.items()):
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {filename}")

    print(f"\nTotal: {passed}/{len(results)} passed")

    if failed > 0:
        print(f"\n❌ {failed} file(s) failed validation")
        sys.exit(1)
    else:
        print(f"\n✓ All files validated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
