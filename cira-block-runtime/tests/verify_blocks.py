#!/usr/bin/env python3
"""
Simple block verification - just checks if all expected blocks were built
"""

import os
import platform
from pathlib import Path

def main():
    print("=" * 70)
    print("CiRA Block Runtime - Block Verification")
    print("=" * 70)

    build_dir = Path(__file__).parent.parent / "build" / "blocks"
    ext = ".dll" if platform.system() == "Windows" else ".so"

    # Expected blocks
    expected_blocks = {
        "Sensors": [
            "adxl345-sensor-v1.0.0",
            "bme280-sensor-v1.0.0",
            "analog-input-v1.0.0",
            "gpio-input-v1.0.0"
        ],
        "Processing": [
            "low-pass-filter-v1.0.0",
            "sliding-window-v1.0.0",
            "normalize-v1.0.0",
            "channel-merge-v1.0.0"
        ],
        "AI/Models": [
            "timesnet-v1.2.0",
            "decision-tree-v1.0.0"
        ],
        "Outputs": [
            "oled-display-v1.1.0",
            "gpio-output-v1.0.0",
            "pwm-output-v1.0.0",
            "mqtt-publisher-v1.0.0",
            "http-post-v1.0.0",
            "websocket-v1.0.0"
        ]
    }

    # Find all blocks
    found_blocks = {}
    for root, dirs, files in os.walk(build_dir):
        for file in files:
            if file.endswith(ext):
                block_name = file.replace(ext, "")
                found_blocks[block_name] = os.path.join(root, file)

    # Check each category
    total_expected = 0
    total_found = 0

    for category, blocks in expected_blocks.items():
        print(f"\n{category}:")
        for block in blocks:
            total_expected += 1
            if block in found_blocks:
                size_kb = os.path.getsize(found_blocks[block]) / 1024
                print(f"  [OK] {block:40s} ({size_kb:6.1f} KB)")
                total_found += 1
            else:
                print(f"  [MISSING] {block}")

    # Summary
    print("\n" + "=" * 70)
    print(f"Summary: {total_found}/{total_expected} blocks found")
    print(f"Success Rate: {100.0 * total_found / total_expected:.1f}%")

    if total_found == total_expected:
        print("\n[SUCCESS] All blocks compiled successfully!")
        print("\nNext steps:")
        print("  1. Test on Jetson Nano: Deploy .so files to target hardware")
        print("  2. Create test manifest: manifests/test.json")
        print("  3. Run block runtime: ./cira_block_runtime --manifest test.json")
        return 0
    else:
        print(f"\n[FAIL] {total_expected - total_found} blocks missing")
        return 1

if __name__ == "__main__":
    exit(main())
