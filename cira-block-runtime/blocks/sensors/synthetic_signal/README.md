# Synthetic Signal Generator Block

## Overview
The Synthetic Signal Generator block replays pre-recorded test datasets for pipeline testing and validation on embedded devices. It supports dynamic channel adaptation and class-based signal truncation.

## Features
- **Multiple Dataset Formats**: JSON, CBOR, CSV, NPY (planned), MAT (planned)
- **Dynamic Channel Adaptation**: Automatically adjusts output channels based on dataset structure
- **Class-Based Truncation**: Filter and replay specific activity classes
- **Playback Control**: Play/pause, reset, and class navigation
- **Loop Modes**: Sequential class playback or single-class looping

## Block Metadata
- **Block ID**: `synthetic-signal-generator`
- **Version**: 1.0.0
- **Type**: Sensor (Input)
- **Platform**: Jetson Nano

## Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_path` | string | *required* | Absolute path to dataset file |
| `sample_rate` | float | 100 | Sampling rate in Hz |
| `loop_mode` | bool | true | Enable continuous looping |
| `sequential_mode` | bool | true | Cycle through all classes |
| `selected_classes` | string | "" | Comma-separated class names (empty = all) |

## Input Pins

| Pin Name | Type | Description |
|----------|------|-------------|
| `play` | bool | Control playback (true = play, false = pause) |
| `reset` | bool | Reset playback to beginning |
| `next_class` | bool | Skip to next class |

## Output Pins

| Pin Name | Type | Description |
|----------|------|-------------|
| `channel_0` | float | First data channel (e.g., X-axis) |
| `channel_1` | float | Second data channel (e.g., Y-axis) |
| `channel_2` | float | Third data channel (e.g., Z-axis) |
| `...` | float | Additional channels (dynamic) |
| `class_name` | string | Current activity class name |

**Note**: Number of `channel_N` pins adapts to dataset dimensions.

## Dataset Format

### JSON Format
```json
{
  "sample_rate": 100,
  "channels": ["x", "y", "z"],
  "classes": {
    "walking": [
      [0.12, -0.05, 9.81],
      [0.15, -0.03, 9.79]
    ],
    "running": [
      [0.45, -0.32, 9.81],
      [0.62, -0.41, 9.68]
    ]
  }
}
```

### CSV Format
```csv
class,channel_0,channel_1,channel_2
walking,0.12,-0.05,9.81
walking,0.15,-0.03,9.79
running,0.45,-0.32,9.81
```

### CBOR Format
Binary encoding of JSON structure (use `cbor2` Python library to generate).

## Usage Examples

### Basic Test Pipeline
```json
{
  "blocks": [
    {
      "id": "synth_gen",
      "type": "synthetic-signal-generator",
      "version": "1.0.0",
      "config": {
        "dataset_path": "/home/jetson/test_data/accel.json",
        "sample_rate": "100"
      }
    }
  ]
}
```

### Full Activity Recognition Test
```json
{
  "blocks": [
    {
      "id": "synth_gen",
      "type": "synthetic-signal-generator",
      "config": {
        "dataset_path": "/home/jetson/datasets/har_test.json",
        "selected_classes": "walking,running,standing"
      }
    },
    {
      "id": "merge",
      "type": "channel-merge",
      "config": {"num_channels": "3"}
    },
    {
      "id": "window",
      "type": "sliding-window",
      "config": {"window_size": "100"}
    },
    {
      "id": "model",
      "type": "timesnet",
      "config": {
        "model_path": "/home/jetson/models/har.onnx",
        "num_classes": "3"
      }
    }
  ],
  "connections": [
    {"from_block": "synth_gen", "from_pin": "channel_0", "to_block": "merge", "to_pin": "input_0"},
    {"from_block": "synth_gen", "from_pin": "channel_1", "to_block": "merge", "to_pin": "input_1"},
    {"from_block": "synth_gen", "from_pin": "channel_2", "to_block": "merge", "to_pin": "input_2"},
    {"from_block": "merge", "from_pin": "output", "to_block": "window", "to_pin": "input"},
    {"from_block": "window", "from_pin": "output", "to_block": "model", "to_pin": "features_in"}
  ]
}
```

## Building

### Prerequisites
- nlohmann/json library (included in `third_party/`)

### Compile Block
```bash
cd cira-block-runtime/build
cmake ..
make synthetic-signal-generator-v1.0.0
sudo make install
```

### Installation Path
`/usr/local/lib/cira/blocks/synthetic-signal-generator-v1.0.0.so`

## Testing

### Create Test Dataset
```bash
cd cira-block-runtime/test_datasets
python3 generate_cbor.py
```

### Run Test Manifest
```bash
cira-block-runtime ../pipeline_builder/manifests/test_synthetic_signal.json
```

## Use Cases

1. **Pipeline Validation**: Test entire pipeline without hardware sensors
2. **Model Verification**: Validate ML model inference with known ground truth
3. **Performance Benchmarking**: Measure processing latency with controlled input
4. **Edge Case Testing**: Replay specific failure scenarios
5. **Continuous Integration**: Automated testing in deployment pipeline

## Dependencies
- C++17 compiler
- nlohmann/json (header-only)
- Standard C++ libraries

## Limitations
- Dataset must fit in RAM
- File I/O during initialization may cause delay
- NPY and MAT formats not yet implemented

## Future Enhancements
- [ ] NumPy (.npy) file support
- [ ] MATLAB (.mat) file support
- [ ] Streaming mode for large datasets
- [ ] Real-time timestamp simulation
- [ ] Random noise injection
- [ ] Signal interpolation/resampling

## License
Part of CiRA Block Runtime System
