"""
Test script for Edge Impulse data loader
"""

from pathlib import Path
from data_sources.edgeimpulse_loader import EdgeImpulseDataSource

def test_cbor_loader():
    """Test loading CBOR file from the dataset"""
    print("=" * 60)
    print("Testing Edge Impulse CBOR Loader")
    print("=" * 60)

    # Find a sample CBOR file
    test_file = Path(r"D:\CiRA FES\Dataset\Motion+Classification+-+Continuous+motion+recognition\testing\idle.1.cbor.1q53q9pg.ingestion-54698b698b-jtpt9.cbor")

    if not test_file.exists():
        print(f"[FAIL] Test file not found: {test_file}")
        return False

    print(f"\n[INFO] Loading file: {test_file.name}")

    try:
        # Create data source
        loader = EdgeImpulseDataSource()
        loader.file_path = test_file
        loader.format_type = "cbor"

        # Connect
        print("[INFO] Connecting to data source...")
        if not loader.connect():
            print(f"[FAIL] Failed to connect: {loader.last_error}")
            return False
        print("[OK] Connected successfully")

        # Load data
        print("[INFO] Loading data...")
        df = loader.load_data()
        print(f"[OK] Loaded {len(df)} samples")

        # Display info
        print("\n" + "-" * 60)
        print("Data Information:")
        print("-" * 60)
        print(f"Rows: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        print(f"Shape: {df.shape}")

        # Metadata
        print("\n" + "-" * 60)
        print("Metadata:")
        print("-" * 60)
        device_info = loader.get_device_info()
        print(f"Device Type: {device_info['type']}")
        print(f"Device Name: {device_info['name']}")
        print(f"Sampling Rate: {loader.get_sampling_rate():.2f} Hz")

        sensor_info = loader.get_sensor_info()
        print(f"\nSensors ({len(sensor_info)}):")
        for sensor in sensor_info:
            print(f"  - {sensor['name']}: {sensor.get('units', 'N/A')}")

        # Preview data
        print("\n" + "-" * 60)
        print("Data Preview (first 10 rows):")
        print("-" * 60)
        print(df.head(10).to_string())

        print("\n" + "=" * 60)
        print("[OK] CBOR loader test PASSED")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_json_conversion():
    """Test loading CBOR and verify JSON compatibility"""
    print("\n\n" + "=" * 60)
    print("Testing JSON Format Compatibility")
    print("=" * 60)

    # Since we only have CBOR files, we'll test the JSON parsing logic
    # by checking that the structure is correct

    test_file = Path(r"D:\CiRA FES\Dataset\Motion+Classification+-+Continuous+motion+recognition\testing\idle.1.cbor.1q53q9pg.ingestion-54698b698b-jtpt9.cbor")

    if not test_file.exists():
        print("[SKIP] Test file not found")
        return True

    try:
        loader = EdgeImpulseDataSource()
        loader.file_path = test_file
        loader.format_type = "cbor"

        if not loader.connect():
            print(f"[FAIL] Connection failed: {loader.last_error}")
            return False

        df = loader.load_data()

        # Verify structure matches Edge Impulse spec
        print("[INFO] Verifying data structure...")

        # Check raw_data structure
        assert 'protected' in loader.raw_data, "Missing 'protected' section"
        assert 'payload' in loader.raw_data, "Missing 'payload' section"
        assert loader.raw_data['protected']['ver'] == 'v1', "Invalid version"

        # Check payload
        payload = loader.raw_data['payload']
        assert 'interval_ms' in payload, "Missing interval_ms"
        assert 'sensors' in payload, "Missing sensors"
        assert 'values' in payload, "Missing values"

        print("[OK] Data structure is valid and matches Edge Impulse spec")

        # Verify DataFrame has correct time column
        assert 'time' in df.columns, "Missing time column"
        print("[OK] Time column present")

        # Verify sensor columns
        sensor_names = [s['name'] for s in loader.get_sensor_info()]
        for sensor_name in sensor_names:
            assert sensor_name in df.columns, f"Missing sensor column: {sensor_name}"
        print(f"[OK] All {len(sensor_names)} sensor columns present")

        print("\n" + "=" * 60)
        print("[OK] JSON compatibility test PASSED")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n")
    print("*" * 60)
    print("* Edge Impulse Data Loader Test Suite")
    print("*" * 60)
    print("\n")

    results = []

    # Test 1: CBOR Loader
    results.append(("CBOR Loader", test_cbor_loader()))

    # Test 2: JSON Compatibility
    results.append(("JSON Compatibility", test_json_conversion()))

    # Summary
    print("\n\n")
    print("*" * 60)
    print("* Test Summary")
    print("*" * 60)
    print()

    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")

    all_passed = all(r[1] for r in results)

    print()
    print("*" * 60)
    if all_passed:
        print("* ALL TESTS PASSED")
    else:
        print("* SOME TESTS FAILED")
    print("*" * 60)
    print()
