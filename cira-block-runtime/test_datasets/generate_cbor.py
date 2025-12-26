#!/usr/bin/env python3
"""
Generate CBOR version of accelerometer dataset
"""

import json
import cbor2

# Load JSON dataset
with open('accelerometer_dataset.json', 'r') as f:
    data = json.load(f)

# Write CBOR version
with open('accelerometer_dataset.cbor', 'wb') as f:
    cbor2.dump(data, f)

print("Generated accelerometer_dataset.cbor")
