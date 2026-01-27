# CiRA FutureEdge Studio - User Guide

Comprehensive documentation for CiRA FES v1.0

## Table of Contents

1. [Overview](#overview)
2. [Pipeline Builder](#pipeline-builder)
3. [CiRA Studio](#cira-studio)
4. [Dataset Recording](#dataset-recording)
5. [Model Training](#model-training)
6. [Deployment](#deployment)
7. [Advanced Topics](#advanced-topics)

---

## Overview

CiRA FutureEdge Studio (FES) is a complete platform for building, training, and deploying edge AI applications on NVIDIA Jetson devices.

### Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Pipeline Builder│ --> │   CiRA Studio    │ --> │ Jetson Deployment│
│  (Design Flow)  │     │ (Train Models)   │     │ (Real-time Exec) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

**Pipeline Builder**: Visual editor for creating data processing pipelines
**CiRA Studio**: Data management, feature engineering, and model training
**Jetson Runtime**: High-performance C++ execution engine (100-1000+ Hz)

### Workflow

1. **Design** pipeline in Pipeline Builder (drag-and-drop blocks)
2. **Record** datasets using Data Recorder block
3. **Train** models in CiRA Studio (ML/DL/AutoML)
4. **Deploy** to Jetson via SSH (one-click deployment)
5. **Monitor** real-time execution via Web Dashboard

---

## Pipeline Builder

### Interface

**Block Library** (left): Available blocks organized by category
- Input Nodes: Analog Input, GPIO Input, Synthetic Signal Generator
- Processing Nodes: Channel Merge, Low Pass Filter, Sliding Window, TimesNet Model
- Output Nodes: OLED Display, GPIO Output, PWM Output, Web LED

**Pipeline Editor** (center): Visual canvas for building pipelines
- Drag blocks from library to canvas
- Connect blocks by dragging from output pins to input pins
- Right-click blocks for options (configure, delete, etc.)

**Properties Panel** (right): Configure selected block parameters
- Each block has specific parameters (see Block Reference below)
- Changes apply immediately (click **Save Changes**)

### Creating a Pipeline

1. **Add blocks**: Drag from Block Library to canvas
2. **Connect blocks**: Drag from output pin (right side) to input pin (left side)
3. **Configure blocks**: Select block, edit parameters in Properties panel
4. **Save pipeline**: File → Save Pipeline (saves as JSON)

### Block Reference

#### Synthetic Signal Generator
Generates test signals for development and testing.

**Parameters**:
- `frequency`: Signal frequency in Hz (default: 1.0)
- `amplitude`: Signal amplitude (default: 1.0)
- `offset`: DC offset (default: 0.0)
- `signal_type`: sine/square/sawtooth/triangular

**Outputs**:
- `channel_0`, `channel_1`, `channel_2`: 3 channels of generated data
- `class_name`: Current signal type (string)
- `class_id`: Numeric class ID (int)

**Interactive Controls**:
- `play`: Start signal generation
- `reset`: Reset to initial state
- `next_class`: Cycle through signal types

#### Channel Merge
Combines multiple input channels into a single multi-channel output.

**Parameters**:
- `num_channels`: Number of channels to merge (2-8)

**Inputs**:
- `channel_0` ... `channel_N`: Individual channels

**Outputs**:
- `merged_out`: Array of merged channels

#### Sliding Window
Creates fixed-size windows from streaming data for ML inference.

**Parameters**:
- `window_size`: Number of samples per window (e.g., 300)
- `step_size`: Samples between windows (e.g., 150 for 50% overlap)

**Inputs**:
- `input`: Multi-channel data array

**Outputs**:
- `window_out`: Windowed data (window_size × num_channels)
- `ready`: True when new window is available

#### TimesNet Model
Deep learning time-series classification using TimesNet architecture.

**Parameters**:
- `model_path`: Path to ONNX model file
- `seq_len`: Sequence length (must match training, e.g., 300)
- `input_channels`: Number of input channels (e.g., 3)
- `num_classes`: Number of output classes (e.g., 4)
- `class_names`: Comma-separated class names (e.g., "sawtooth,sine,square,triangular")
- `sensor_columns`: Comma-separated column names (e.g., "accX,accY,accZ")
- `confidence_threshold`: Minimum confidence for predictions (0.0-1.0)

**Inputs**:
- `features_in`: Windowed data from Sliding Window block

**Outputs**:
- `prediction_out`: Predicted class ID (int)
- `class_name`: Predicted class name (string)
- `confidence_out`: Prediction confidence (float 0-1)

#### Data Recorder
Records streaming data to CBOR format for dataset creation.

**Parameters**:
- `output_directory`: Where to save CBOR files (default: `Dataset/`)
- `window_size`: Samples per window (must match Sliding Window)
- `num_channels`: Number of channels to record
- `max_windows`: Windows to record per file (default: 100)
- `train_test_split`: Ratio for train/test split (default: 0.8 = 80% train)

**Inputs**:
- `window_in`: Windowed data from Sliding Window
- `class_name`: Label for current data (string)
- `class_id`: Numeric class ID (int)

**Interactive Controls**:
- `start`: Begin recording
- `stop`: Stop recording and save file

#### Web LED
Simple visual output for monitoring state (boolean on/off).

**Inputs**:
- `state`: Boolean value to display

**Outputs**: None (displays in Web Dashboard)

---

## CiRA Studio

### Data Sources Tab

Import and manage datasets for training.

#### Supported Formats

**CiRA CBOR** (native format):
```
{
    "samples": [
        {
            "values": [900 samples],  // window_size × channels
            "class_name": "sine",
            "class_id": 1
        },
        ...
    ]
}
```

**Edge Impulse CBOR** (signed format):
```
{
    "protected": {...},
    "signature": "...",
    "payload": {
        "device_name": "...",
        "sensors": [...],
        "values": [...]
    }
}
```

**CSV** (time-series):
- First column: timestamp
- Subsequent columns: sensor values
- Optional: label column

#### Adding Data Source

1. Click **Add Data Source**
2. Select format (CiRA CBOR / Edge Impulse CBOR / CSV)
3. Choose folder containing data files
4. CiRA Studio automatically:
   - Validates file format
   - Detects train/test split (if subdirectories exist)
   - Extracts class labels
   - Shows preview

### Machine Learning Tab

Classical ML algorithms for time-series classification.

**Supported Algorithms**:
- Random Forest
- XGBoost
- SVM (Support Vector Machine)
- KNN (K-Nearest Neighbors)

**Feature Engineering**:
- TSFresh automated feature extraction
- Time-domain features (mean, std, min, max, etc.)
- Frequency-domain features (FFT, spectral energy, etc.)
- Statistical features (skewness, kurtosis, etc.)

**Workflow**:
1. Select algorithm
2. Configure hyperparameters
3. Click **Train Model**
4. View metrics (accuracy, F1-score, confusion matrix)
5. Export model (pickle format)

### Deep Learning Tab

**TimesNet Model** (time-series classification):

#### Configuration

**Model Architecture**:
- `seq_len`: Input sequence length (e.g., 300 samples)
- `input_channels`: Number of input channels (e.g., 3 for X/Y/Z)
- `num_classes`: Number of output classes
- `d_model`: Model dimension (default: 64, range: 32-128)
- `num_layers`: Number of layers (default: 2, range: 1-4)

**Training Parameters**:
- `batch_size`: Samples per training batch (default: 32)
- `epochs`: Training iterations (default: 50)
- `learning_rate`: Optimizer learning rate (default: 0.001)
- `train_test_split`: Validation split ratio (default: 0.2)

**Advanced**:
- `use_tensorrt`: Enable TensorRT optimization for Jetson (recommended)
- `early_stopping`: Stop if no improvement for N epochs
- `class_weights`: Balance imbalanced datasets

#### Training Process

1. Click **Start Training**
2. Monitor progress:
   - Epoch progress bar
   - Training/validation loss curves
   - Accuracy metrics updated per epoch
3. Training completes when:
   - Max epochs reached
   - Early stopping triggered
   - Manual stop
4. Review results:
   - Final accuracy/F1-score
   - Confusion matrix
   - Per-class precision/recall

#### Model Export

1. Click **Export Model**
2. Choose format:
   - **ONNX** (recommended for Jetson deployment)
   - **PyTorch** (.pt for further training)
   - **TensorRT** (optimized engine for specific Jetson)
3. Model saved to `models/` directory

---

## Dataset Recording

### Setup

1. **Create pipeline** in Pipeline Builder:
   - Input block (e.g., Synthetic Signal Generator or Analog Input)
   - Channel Merge block
   - Sliding Window block (e.g., window_size=300, step_size=150)
   - Data Recorder block

2. **Configure Data Recorder**:
   - `output_directory`: `Dataset/MyDataset`
   - `window_size`: 300 (match Sliding Window)
   - `num_channels`: 3
   - `max_windows`: 100 (per file)

3. **Deploy to Jetson**:
   - Setup Device → Deploy

### Recording Workflow

1. **Prepare for recording**:
   - Ensure signal/sensor is stable
   - Set correct class label (via `class_name` input)

2. **Start recording**:
   - Click `start` button on Data Recorder block
   - Web Dashboard shows recording progress
   - Execution rate may drop (normal - data is being saved)

3. **Monitor progress**:
   - Check runtime logs for "Recorded window X/100"
   - Wait for "Recording complete, saved to..." message

4. **Stop recording**:
   - Automatic after `max_windows` reached
   - Or click `stop` button manually

5. **Repeat for each class**:
   - Change class label
   - Record another batch
   - Recommended: 100+ windows per class

### Performance Tips

- **Execution rate during recording**: ~30-50 Hz (normal, due to disk I/O)
- **Execution rate when NOT recording**: 100+ Hz
- **Dataset organization**:
  ```
  Dataset/MyDataset/
  ├── train/
  │   ├── class0_001.cbor
  │   ├── class1_001.cbor
  │   └── ...
  └── test/
      ├── class0_test.cbor
      └── ...
  ```
- **Manual train/test split**: Move 20% of files to `test/` subdirectory

---

## Model Training

### TimesNet Training (Recommended for Time-Series)

**When to use**: Multi-channel sensor data, continuous motion/activity recognition, signal classification

**Advantages**:
- Excellent for time-series patterns
- Handles multi-channel data natively
- Fast inference on Jetson (5-10ms per window)
- ONNX export for deployment

**Training Time**:
- Small dataset (<1000 windows): 5-10 minutes
- Medium dataset (1000-5000 windows): 15-30 minutes
- Large dataset (>5000 windows): 30-60 minutes

**Hardware**: CPU or GPU (auto-detected, GPU is 5-10× faster)

### Classical ML (Alternative)

**When to use**: Simple patterns, fewer features, resource-constrained scenarios

**Advantages**:
- Faster training (seconds to minutes)
- Smaller model size
- Interpretable (feature importance)

**Disadvantages**:
- Requires manual feature engineering
- May not capture complex patterns

---

## Deployment

### Setup Device (First Time Only)

1. **Configure Jetson connection**:
   - Deploy → Setup Device
   - Enter IP, username, password
   - Project name (e.g., `my_pipeline`)
   - Execution rate (default: 100 Hz)

2. **Run Setup Device**:
   - Installs dependencies (curl, cmake, build tools)
   - Creates project directory: `/home/<user>/cira_projects/<project>/`
   - Compiles or downloads precompiled runtime
   - **Takes 2-3 minutes first time**

### Deploy Pipeline

1. **Save pipeline** (File → Save)
2. **Deploy to Device**:
   - Deploy → Deploy to Device
   - Pipeline JSON uploaded
   - Runtime restarted automatically
   - **Takes ~30 seconds**

### Execution Rate Configuration

**Execution rate** controls how fast the pipeline runs (Hz = iterations per second).

**Common values**:
- `10 Hz`: Low-speed applications, low power consumption
- `100 Hz`: Standard rate for most applications (recommended)
- `1000 Hz`: High-speed sampling, may require performance mode

**How to set**:
- Deploy → Setup Device → Execution Rate (Hz)
- Applied on next deployment

**Jetson Performance Mode** (for high rates):
```bash
# Check current mode
sudo nvpmodel -q

# Set maximum performance (mode 0)
sudo nvpmodel -m 0

# Set CPU/GPU max frequency
sudo jetson_clocks
```

### Monitoring

**Web Dashboard**:
- Deploy → Monitor Dashboard
- Opens browser to `http://<jetson-ip>:8080`
- Shows:
  - Live data visualization
  - Block outputs (predictions, confidence, etc.)
  - Execution rate (actual Hz)
  - Runtime status

**Runtime Logs**:
```bash
ssh user@<jetson-ip>
cd ~/cira_projects/<project>/bin
tail -f runtime.log
```

---

## Advanced Topics

### Broadcast Throttling

To reduce network traffic and improve performance, numeric outputs are throttled by default.

**Throttle Rates**:
- **Normal mode**: 1× (no throttling, every value broadcast)
- **Recording mode**: 100× (every 100th value broadcast to UI, all values saved to file)

**String values** (e.g., class_name): Only broadcast when value changes (no throttling)

**Interactive controls** (e.g., buttons): Always broadcast immediately

### Custom Blocks

You can create custom blocks in C++ and add them to Pipeline Builder.

**See**: `cira-block-runtime/src/blocks/custom/` for examples

### TensorRT Optimization

For maximum Jetson inference performance, enable TensorRT:

1. In CiRA Studio, enable `use_tensorrt` during training
2. Export model with TensorRT optimization
3. Converts ONNX → TensorRT engine optimized for your specific Jetson

**Performance**:
- ONNX: 5-10ms per inference
- TensorRT: 1-3ms per inference (3-5× faster)

### Multi-Pipeline Deployment

You can run multiple pipelines simultaneously on one Jetson:

1. Create separate projects (different project names)
2. Deploy each pipeline to its project
3. Run runtimes on different ports

**Example**:
```bash
# Pipeline 1 (port 8080)
./cira-block-runtime --config pipeline1.json --port 8080

# Pipeline 2 (port 8081)
./cira-block-runtime --config pipeline2.json --port 8081
```

---

## Performance Benchmarks

**Jetson Nano** (4GB):
- Execution rate: 100-500 Hz (depending on pipeline complexity)
- TimesNet inference: ~10ms per window
- Recording: ~30 Hz (limited by SD card I/O)

**Jetson Xavier NX**:
- Execution rate: 500-1000+ Hz
- TimesNet inference: ~3-5ms per window
- Recording: ~50 Hz

**Optimization Tips**:
1. Use TensorRT for ML inference
2. Enable performance mode: `sudo nvpmodel -m 0`
3. Reduce broadcast rate for non-critical outputs
4. Use appropriate execution rate (don't over-sample)

---

## License Management

**FREE Tier** (default):
- 100 Deep Learning trainings
- 100 LLM analysis operations
- All core features included
- No time restrictions

**Usage Tracking**:
- View in CiRA Studio: Settings → License Info
- Shows remaining count (e.g., "DL Training: 45/100")

**Upgrade to PRO**:
- Unlimited trainings and LLM usage
- Priority support
- Advanced features (coming soon)
- Contact: support@cira-fes.com

---

## Next Steps

- **Try examples**: `examples/StandardWave/` and `examples/MotionClassification/`
- **Join community**: [GitHub discussions / Discord server]
- **Read API docs**: For programmatic access to CiRA features
- **Build custom blocks**: Extend functionality with C++

For troubleshooting, see [Troubleshooting.md](Troubleshooting.md)
