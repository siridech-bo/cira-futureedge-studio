#!/usr/bin/env python3
"""
Test script to verify CBOR loading works correctly end-to-end.
"""

import pickle
from pathlib import Path
from data_sources.cira_cbor_loader import CiraCBORDataSource

print("=" * 60)
print("CBOR LOADER TEST")
print("=" * 60)

# Test 1: Metadata detection
print("\n1. Testing metadata detection...")
loader = CiraCBORDataSource()
loader.file_path = Path("Dataset/StandardWave/training/sawtooth/sawtooth.1.cbor.6960fd9e.user-desktop.cbor")

if loader.connect():
    print(f"   ✓ Connected to CBOR file")
    print(f"   Window size: {loader.metadata.get('window_size', 'N/A')}")
    print(f"   Detected channels: {loader.metadata.get('num_channels', 'N/A')}")
    print(f"   Samples per channel: {loader.metadata.get('samples_per_channel', 'N/A')}")

    sensor_cols = loader.detect_sensor_columns()
    print(f"   Sensor columns: {sensor_cols}")

    if loader.metadata.get('num_channels') == 3:
        print("   ✓ PASS: Correctly detected 3 channels")
    else:
        print(f"   ✗ FAIL: Expected 3 channels, got {loader.metadata.get('num_channels')}")
else:
    print(f"   ✗ FAIL: Could not connect")

# Test 2: Pickle file structure
print("\n2. Testing pickle file structure...")
pickle_path = Path("output/StandardWave/data/train_data.pkl")
if pickle_path.exists():
    with open(pickle_path, 'rb') as f:
        df = pickle.load(f)

    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")

    sensor_cols = [col for col in df.columns
                   if col not in ['time', 'label', 'class_label', 'timestamp', '_source_file']]
    print(f"   Sensor columns: {sensor_cols}")

    if len(sensor_cols) == 3 and sensor_cols == ['ch0', 'ch1', 'ch2']:
        print("   ✓ PASS: Pickle has correct 3 channels")
    else:
        print(f"   ✗ FAIL: Expected ['ch0', 'ch1', 'ch2'], got {sensor_cols}")
else:
    print(f"   ⚠ SKIP: Pickle file not found (load data first)")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nNext step: Launch CiRA FES and load CBOR data.")
print("Expected result: Windowing tab should show 3 channels, not 300.")
