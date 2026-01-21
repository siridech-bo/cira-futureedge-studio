#!/usr/bin/env python3
"""Verify the newly recorded dataset has correct format"""

import cbor2
import sys

def verify_cbor_file(file_path):
    print(f"Verifying: {file_path}")
    print("=" * 60)

    with open(file_path, 'rb') as f:
        data = cbor2.load(f)

    # Check top-level structure
    print(f"Top-level keys: {list(data.keys())}")

    if 'samples' not in data:
        print("[FAIL] Missing 'samples' key")
        return False

    samples = data['samples']
    print(f"Total samples: {len(samples)}")

    # Check first sample structure
    if len(samples) > 0:
        first_sample = samples[0]
        print(f"\nFirst sample keys: {list(first_sample.keys())}")
        print(f"  class_id: {first_sample.get('class_id')}")
        print(f"  class_name: {first_sample.get('class_name')}")
        print(f"  timestamp: {first_sample.get('timestamp')}")

        if 'data' in first_sample:
            data_array = first_sample['data']
            print(f"  data length: {len(data_array)}")
            print(f"  data type: {type(data_array)}")
            print(f"  first 9 values: {data_array[:9]}")

            # Check if values repeat (old bug)
            if len(data_array) >= 6:
                if (abs(data_array[0] - data_array[1]) < 1e-6 and
                    abs(data_array[1] - data_array[2]) < 1e-6):
                    print("  [WARNING] Values appear to repeat!")
                else:
                    print("  [OK] Values are distinct (no repetition)")

    # Check if class_id is correct for sine
    correct_class_id = 1  # sine should be 1
    all_correct = True

    for i, sample in enumerate(samples[:5]):  # Check first 5 samples
        if sample.get('class_id') != correct_class_id:
            print(f"[FAIL] Sample {i}: class_id={sample.get('class_id')}, expected {correct_class_id}")
            all_correct = False

    if all_correct:
        print(f"\n[OK] All checked samples have correct class_id={correct_class_id}")

    # Check data array length
    if len(samples) > 0 and 'data' in samples[0]:
        data_len = len(samples[0]['data'])
        if data_len == 3:
            print(f"[OK] Data array has 3 values (channel-by-channel for 1 sample)")
        else:
            print(f"[WARNING] Data array has {data_len} values (expected 3)")

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    return True

if __name__ == "__main__":
    file_path = r"D:\CiRA FES\Dataset\StandardWave_new\sine.5.cbor.69707def.user-desktop.cbor"
    verify_cbor_file(file_path)
