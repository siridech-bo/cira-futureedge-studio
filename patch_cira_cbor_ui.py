#!/usr/bin/env python3
"""Add CiRA CBOR to UI dropdown and mappings"""

# Read the file
with open('ui/data_panel.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line 171: Add to dropdown values
for i, line in enumerate(lines):
    if i == 170 and 'values=["CSV File"' in line:
        lines[i] = line.replace(
            '["CSV File", "Edge Impulse JSON", "Edge Impulse CBOR", "Database"',
            '["CSV File", "Edge Impulse JSON", "Edge Impulse CBOR", "CiRA CBOR", "Database"'
        )
        print(f"[OK] Line {i+1}: Added CiRA CBOR to dropdown")

    # Line 981: Add to conditional check
    elif i == 980 and 'elif choice in ["Edge Impulse JSON", "Edge Impulse CBOR"]:' in line:
        lines[i] = line.replace(
            '["Edge Impulse JSON", "Edge Impulse CBOR"]',
            '["Edge Impulse JSON", "Edge Impulse CBOR", "CiRA CBOR"]'
        )
        print(f"[OK] Line {i+1}: Added CiRA CBOR to choice check")

    # Line 1208: Add to source_type check
    elif i == 1207 and 'elif source_type in ["Edge Impulse JSON", "Edge Impulse CBOR"]:' in line:
        lines[i] = line.replace(
            '["Edge Impulse JSON", "Edge Impulse CBOR"]',
            '["Edge Impulse JSON", "Edge Impulse CBOR", "CiRA CBOR"]'
        )
        print(f"[OK] Line {i+1}: Added CiRA CBOR to source_type check")

    # Line 1429: Add to format mapping
    elif i == 1428 and '"Edge Impulse CBOR": "cbor"' in line:
        lines[i] = line.replace(
            '"Edge Impulse CBOR": "cbor"',
            '"Edge Impulse CBOR": "cbor",\n                "CiRA CBOR": "cbor"'
        )
        print(f"[OK] Line {i+1}: Added CiRA CBOR to format mapping")

# Write back
with open('ui/data_panel.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("[OK] Patched ui/data_panel.py with CiRA CBOR UI support")
