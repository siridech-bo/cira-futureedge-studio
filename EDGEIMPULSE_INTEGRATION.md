# Edge Impulse Data Format Integration

## Overview

CiRA FutureEdge Studio now supports loading data in Edge Impulse JSON and CBOR formats, enabling seamless integration with Edge Impulse-exported datasets.

## Supported Formats

### 1. Edge Impulse JSON
- Standard JSON format following Edge Impulse data acquisition specification
- Human-readable format suitable for small to medium datasets
- File extension: `.json`

### 2. Edge Impulse CBOR
- Compact Binary Object Representation (CBOR) format
- Efficient binary format for large datasets
- File extension: `.cbor`
- Requires `cbor2` library (automatically installed with dependencies)

## Data Format Specification

Edge Impulse data files follow this structure:

```json
{
    "protected": {
        "ver": "v1",
        "alg": "HS256" or "none",
        "iat": timestamp (optional)
    },
    "signature": "cryptographic_signature",
    "payload": {
        "device_type": "Device model/type",
        "device_name": "Device identifier (optional)",
        "interval_ms": sampling_interval_in_milliseconds,
        "sensors": [
            {"name": "sensor_name", "units": "unit_string"}
        ],
        "values": [
            [val1, val2, val3, ...],
            ...
        ]
    }
}
```

### Key Fields

- **protected.ver**: Always "v1" for current specification
- **protected.alg**: Signature algorithm (HS256 or none)
- **payload.interval_ms**: Sampling interval in milliseconds (determines sampling rate)
- **payload.sensors**: Array of sensor definitions with names and units
- **payload.values**: 2D array where each row is a sample, columns match sensors array

## Implementation

### Files Modified/Created

1. **data_sources/edgeimpulse_loader.py** (NEW)
   - `EdgeImpulseDataSource` class implementing the DataSource interface
   - Automatic format detection (JSON vs CBOR)
   - Metadata extraction (device info, sensors, sampling rate)
   - Conversion to pandas DataFrame with time column

2. **ui/data_panel.py** (UPDATED)
   - Added "Edge Impulse JSON" and "Edge Impulse CBOR" options to data source selector
   - New UI frame for Edge Impulse file selection
   - Device information display (device type, name, sampling rate, sensors)
   - Automatic format handling in data loading

3. **requirements.txt** (UPDATED)
   - Added `cbor2==5.7.1` for CBOR parsing support

### Key Features

#### Auto-detection
- Automatically detects format based on file extension
- Falls back to content inspection if extension is ambiguous
- Supports both `.json` and `.cbor` files

#### Metadata Preservation
- Device type and name
- Sampling rate calculation from interval_ms
- Sensor information (names and units)
- Signature verification support (future enhancement)

#### Time Column Generation
- Automatically creates `time` column in seconds
- Time = sample_index × (interval_ms / 1000)
- Ensures compatibility with windowing and feature extraction

#### Validation
- Validates Edge Impulse data structure
- Checks required fields (protected, payload, sensors, values)
- Verifies data consistency (sensor count matches value columns)

## Usage

### In the UI

1. Launch CiRA FutureEdge Studio
2. Navigate to "Data Sources" panel
3. Select data source type:
   - "Edge Impulse JSON" for JSON files
   - "Edge Impulse CBOR" for CBOR files
4. Click "Browse..." to select file
5. Click "Load Data"
6. Device info appears below file selector
7. Data preview available in "Preview" tab

### Programmatic Usage

```python
from pathlib import Path
from data_sources.edgeimpulse_loader import EdgeImpulseDataSource

# Create loader
loader = EdgeImpulseDataSource()
loader.file_path = Path("path/to/data.cbor")
loader.format_type = "cbor"  # or "json" or "auto"

# Connect and load
if loader.connect():
    df = loader.load_data()

    # Access metadata
    device_info = loader.get_device_info()
    sensors = loader.get_sensor_info()
    sampling_rate = loader.get_sampling_rate()

    print(f"Device: {device_info['type']}")
    print(f"Sampling Rate: {sampling_rate} Hz")
    print(f"Sensors: {[s['name'] for s in sensors]}")
    print(f"Data shape: {df.shape}")
```

## Example Dataset

The implementation was tested with datasets from Edge Impulse:

**Location**: `D:\CiRA FES\Dataset\Motion+Classification+-+Continuous+motion+recognition\`

**Sample file**: `testing/idle.1.cbor.1q53q9pg.ingestion-54698b698b-jtpt9.cbor`

**Contents**:
- Device: Edge Impulse dataset
- Sensors: accX, accY, accZ (all in m/s²)
- Sampling Rate: 62.50 Hz (16ms interval)
- 622 samples (≈10 seconds of data)

## Test Results

All tests passed successfully:

```
[PASS] CBOR Loader
  - Loaded 622 samples
  - 4 columns (time, accX, accY, accZ)
  - Correct sampling rate (62.50 Hz)
  - Valid metadata extraction

[PASS] JSON Compatibility
  - Valid Edge Impulse structure
  - Time column generated correctly
  - All sensor columns present
```

## Integration with Existing Pipeline

The Edge Impulse loader integrates seamlessly with existing features:

1. **Windowing**: Loaded data works with the windowing engine
   - Automatic time column detection
   - Sensor column auto-detection
   - Sampling rate inference

2. **Feature Extraction** (Phase 3): Will support tsfresh on Edge Impulse data

3. **Project Management**: Edge Impulse data sources saved in `.ciraproject` files

4. **Data Preview**: Full preview available in tabbed interface

## Future Enhancements

- [ ] Signature verification using `protected.alg` and `signature` fields
- [ ] Support for binary attachments (images, audio)
- [ ] Batch loading of multiple Edge Impulse files
- [ ] Direct integration with Edge Impulse API
- [ ] Export to Edge Impulse format after processing

## References

- Edge Impulse Data Acquisition Spec: https://docs.edgeimpulse.com/tools/specifications/data-acquisition/json-cbor
- CBOR Specification: https://cbor.io/
- JSON Web Signature (JWS): https://tools.ietf.org/html/rfc7515

## Dependencies

- `cbor2>=5.7.1`: CBOR encoding/decoding
- `pandas>=2.1.4`: DataFrame operations
- `numpy>=1.24.4`: Numerical operations

## License

Edge Impulse format support follows the same license as CiRA FutureEdge Studio.
Edge Impulse SDK is Apache 2.0 licensed.
