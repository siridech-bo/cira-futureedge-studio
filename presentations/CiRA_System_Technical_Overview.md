---
marp: true
theme: default
paginate: true
backgroundColor: #ffffff
style: |
  section {
    font-size: 24px;
  }
  h1 {
    color: #1e3a8a;
    border-bottom: 3px solid #3b82f6;
  }
  h2 {
    color: #1e40af;
  }
  code {
    background-color: #f1f5f9;
  }
  .columns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }
---

# CiRA FES: Complete System Architecture
## Time Series ML Development Platform

**Professional Training Guide**

CiRA FutureEdge Studio - From Dataset to Edge Deployment

---

# Table of Contents

1. **System Overview**
2. **CiRA Studio** - Dataset Recording & Model Training
3. **Pipeline Builder** - Visual Programming Interface
4. **CiRA Dashboard** - Jetson Deployment & Inference
5. **End-to-End Workflow**
6. **Technical Deep Dive**
7. **Libraries & Dependencies**

---

# System Overview

## Three-Component Architecture

---

# System Overview: Component 1

## CiRA FutureEdge Studio

```
┌─────────────────────────────────────────────────────────────┐
│                    CiRA FutureEdge Studio                   │
│                  (Windows Desktop Application)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. Data Collection & Recording                      │   │
│  │  2. Feature Engineering                              │   │
│  │  3. Model Training (TimesNet + Classical ML)         │   │
│  │  4. ONNX Export                                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Purpose:** Desktop ML development environment for dataset creation and model training

---

# System Overview: Component 2

## Pipeline Builder

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Builder                         │
│                  (C++ Visual Editor - Windows)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. Drag-and-drop pipeline design                    │   │
│  │  2. Node configuration (sensors, AI, outputs)        │   │
│  │  3. Code generation for Jetson                       │   │
│  │  4. Remote deployment via SSH                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Purpose:** Visual programming interface for edge pipeline design

---

# System Overview: Component 3

## CiRA Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│                    CiRA Dashboard                           │
│                  (Jetson Nano/Orin - Linux ARM64)            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. Real-time sensor data acquisition                │   │
│  │  2. ONNX model inference (TensorRT)                  │   │
│  │  3. Web-based visualization dashboard                │   │
│  │  4. GPIO/Network outputs                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Purpose:** Edge inference runtime with web-based monitoring

---

# Component 1: CiRA Studio

## Purpose
Desktop application for **dataset creation** and **deep learning model training**

## Key Features
- Multi-source data loading (CSV, CBOR, Database, REST API)
- Time-series windowing with label preservation
- TSFresh feature extraction (40+ temporal features)
- LLM-powered feature selection (Llama 3.2)
- TimesNet deep learning model training
- Classical ML algorithms (Random Forest, SVM, etc.)
- ONNX model export for deployment

---

# CiRA Studio: Architecture (UI Layer)

```
┌─────────────────────────────────────────────────────────────┐
│                        UI Layer                              │
│              (CustomTkinter - Modern GUI)                    │
├─────────────────────────────────────────────────────────────┤
│  Data Panel  │  Features  │  Model Panel  │  Build Panel   │
│              │   Panel    │               │                 │
└─────────────────────────────────────────────────────────────┘
```

**Modern GUI Interface:**
- **Data Panel** - Load and preview datasets
- **Features Panel** - Extract and select features
- **Model Panel** - Configure and train models
- **Build Panel** - Export and deploy models

---

# CiRA Studio: Architecture (Core Layer)

```
┌─────────────────────────────────────────────────────────────┐
│                      Core Layer                              │
├──────────────────┬──────────────────┬──────────────────────┤
│  Data Loaders    │  Feature Engine  │  Deep Models         │
│  - CSV           │  - TSFresh       │  - TimesNet          │
│  - CBOR          │  - DSP           │  - Layers            │
│  - EdgeImpulse   │  - LLM Select    │  - Training          │
│  - Database      │  - Windowing     │  - ONNX Export       │
│  - REST API      │                  │                      │
└──────────────────┴──────────────────┴──────────────────────┘
```

**Core Processing Components:**
- Data loading from multiple sources
- Time series feature extraction
- Deep learning model training

---

# CiRA Studio: Architecture (ML Layer)

```
┌─────────────────────────────────────────────────────────────┐
│                     ML Algorithms                            │
├─────────────────────────────────────────────────────────────┤
│  Anomaly Detection:                                          │
│    - IForest, LOF, OCSVM, HBOS, KNN (PyOD)                  │
│                                                              │
│  Classification:                                             │
│    - Random Forest, GBoost, SVM, MLP, KNN (Scikit-learn)    │
└─────────────────────────────────────────────────────────────┘
```

**Machine Learning Capabilities:**
- Anomaly detection algorithms for fault detection
- Classical ML algorithms for classification
- Integration with PyOD and Scikit-learn libraries

---

# CiRA Studio: Data Recording System

## Dataset Recorder Architecture

```
Sensor Input → Channel Merge → Data Recorder → CBOR Files
(3 channels)     (vector3)      (windowing)     (.cbor)
```

**Recording Pipeline:**
- Sensors generate 3 channels of data
- Channel Merge combines into vector3 format
- Data Recorder applies windowing and saves to CBOR

---

# CiRA Studio: Window Accumulation

```
Window Accumulation Process:
┌─────────────────────────────────────────────────────────┐
│  Sample Buffer: [s₀, s₁, s₂, ... s₂₉₉]                 │
│                                                         │
│  When len(buffer) == window_size (300):                │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Flatten to channel-by-channel format:            │ │
│  │  [ch₀₀, ch₀₁, ... ch₀₂₉₉,                        │ │
│  │   ch₁₀, ch₁₁, ... ch₁₂₉₉,                        │ │
│  │   ch₂₀, ch₂₁, ... ch₂₂₉₉]                        │ │
│  │                                                    │ │
│  │  Total: 900 values per window                     │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

# CiRA Studio: CBOR Metadata

**Saved with each window:**
```
CBOR File Metadata:
  - timestamp (ISO 8601 format)
  - class_name (e.g., "sine")
  - class_id (e.g., 1)
  - data (900 float values)
```

**File naming:** `class_name.index.cbor` (e.g., `sine.0.cbor`)

---

# CiRA Studio: TimesNet Model

## Architecture Overview

**TimesNet** transforms 1D time series into 2D tensors using FFT-based period detection

---

# CiRA Studio: TimesNet - Period Detection

**Step 1: Period Detection via FFT**
```
X_freq = FFT(X_input)
A(f) = |X_freq(f)|  // Amplitude spectrum
periods = TopK({1/f₁, 1/f₂, ..., 1/fₖ})  // K dominant periods
```

Identifies dominant periodic components in time series

---

# CiRA Studio: TimesNet - 2D Transformation

**Step 2: 2D Transformation**
```
For each period p:
  Reshape: X₁D(seq_len) → X₂D(p, seq_len/p)
  Apply 2D Inception convolution
  Reshape back: X₂D → X₁D
```

Converts 1D sequences to 2D for spatial convolution

---

# CiRA Studio: TimesNet Layers (Part 1)

```
Input: (batch, seq_len=300, channels=3)
  ↓
DataEmbedding (channels=3 → d_model=32)
  ↓
TimesBlock 1 (e_layers=2)
  ↓
TimesBlock 2 (same structure)
  ↓
LayerNorm
  ↓
Flatten & Linear Projection
  ↓
Output: Class logits
```

**Overall Architecture:** 2 TimesBlocks with data embedding and classification head

---

# CiRA Studio: TimesNet Layers (Part 2)

## TimesBlock Internal Structure

```
┌─────────────────────────────────────────┐
│         TimesBlock Processing           │
│  ┌───────────────────────────────────┐  │
│  │  FFT → Period Detection (top_k=3) │  │
│  │  ↓                                 │  │
│  │  Reshape to 2D for each period    │  │
│  │  ↓                                 │  │
│  │  Inception Block (num_kernels=4)  │  │
│  │  - Conv 1×1                        │  │
│  │  - Conv 3×3                        │  │
│  │  - Conv 5×5                        │  │
│  │  - Conv 7×7                        │  │
│  │  ↓                                 │  │
│  │  Concatenate → Reshape back to 1D │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

# CiRA Studio: Key Equations (Part 1)

## Embedding Layer

**Data Embedding:**
```
X_emb = Linear(X_in) + PositionalEncoding(t)
```

Transforms raw input to model dimension with positional information

---

# CiRA Studio: Key Equations (Part 2)

## Inception Block Processing

**Multi-scale Convolutions:**
```
H₁ = Conv2D(X_2D, kernel=1×1)
H₃ = Conv2D(X_2D, kernel=3×3)
H₅ = Conv2D(X_2D, kernel=5×5)
H₇ = Conv2D(X_2D, kernel=7×7)

H_concat = Concat([H₁, H₃, H₅, H₇], dim=channel)
H_out = Conv2D(H_concat, kernel=1×1)  // Channel reduction
```

---

# CiRA Studio: Key Equations (Part 3)

## Residual Connection

**Layer Normalization with Skip Connection:**
```
X_out = LayerNorm(X_in + H_out)
```

Enables stable gradient flow during training

---

# CiRA Studio: Feature Engineering (Part 1)

## TSFresh Feature Extraction

**Temporal Features (40+ per channel):**
- **Statistical:** mean, std, variance, skewness, kurtosis
- **Distribution:** percentiles, quantiles, median absolute deviation
- **Frequency:** FFT coefficients, spectral centroid, spectral entropy

---

# CiRA Studio: Feature Engineering (Part 2)

## Additional Feature Types

**More Temporal Features:**
- **Autocorrelation:** lag features, autocorrelation coefficients
- **Peak detection:** number of peaks, peak locations, peak heights
- **Change points:** linear trend, variance change, CWT coefficients

**Multi-channel Features:**
```
Total features = (40+ features) × (3 channels) = 120+ features
```

---

# CiRA Studio: Feature Engineering (Part 3)

## LLM-Based Feature Selection

**Intelligent Feature Selection with Llama 3.2:**
- Analyzes feature importance automatically
- Ranks features by relevance to classification task
- Recommends optimal subset (typically 10-30 features)
- Reduces dimensionality while maintaining accuracy

---

# CiRA Studio: Training Workflow (Step 1-2)

## Data Loading and Validation

**1. Data Loading**
```python
# Load CBOR dataset
data = load_cbor_files(directory)
# Expected format: (num_windows, 900) with class labels
```

**2. Validation**
```python
# Verify data shape
assert data.shape[1] == window_size * num_channels  # 900
# Verify class distribution
verify_class_balance(labels)
```

---

# CiRA Studio: Training Workflow (Step 3)

## Model Configuration

```python
config = TimesNetConfig(
    seq_len=300,        # Window size (samples)
    c_in=3,             # Number of channels
    num_classes=4,      # Classification classes
    d_model=32,         # Model dimension
    e_layers=2,         # Number of TimesNet blocks
    top_k=3             # Top-K periods
)
```

---

# CiRA Studio: Training Workflow (Step 4)

## Training Loop

**4. Training**
```python
# Create model
model = TimesNet(config)

# Training loop
optimizer = AdamW(model.parameters(), lr=1e-3)
criterion = CrossEntropyLoss()

for epoch in range(num_epochs):
    for batch in dataloader:
        X, y = batch
        # X: (batch, 300, 3) - windowed data
        # y: (batch,) - class labels

        logits = model(X)  # (batch, num_classes)
        loss = criterion(logits, y)

        loss.backward()
        optimizer.step()
```

---

# CiRA Studio: Training Workflow (Step 5)

## ONNX Export

**5. ONNX Export**
```python
# Export to ONNX for TensorRT deployment
torch.onnx.export(
    model, dummy_input,
    "model.onnx",
    input_names=['input'],
    output_names=['output']
)
```

Export trained model for edge deployment

---

# Component 2: Pipeline Builder

## Purpose
Visual programming interface for designing **edge inference pipelines**

## Key Features
- ImGui-based node editor with drag-and-drop
- 25+ pre-built nodes (sensors, processing, AI, outputs)
- Visual connection validation
- Property configuration panel
- Code generation for Jetson platform
- Remote deployment via SSH
- Block manifest generation (JSON)

---

# Pipeline Builder: Architecture (UI Layer)

```
┌─────────────────────────────────────────────────────────────┐
│                    UI Layer (ImGui)                          │
├──────────────────┬──────────────────┬──────────────────────┤
│  Block Library   │  Node Editor     │  Properties Panel    │
│  - Sensors       │  - Canvas        │  - Node config       │
│  - Processing    │  - Connections   │  - Pin validation    │
│  - AI Models     │  - Drag & Drop   │  - Type checking     │
│  - Outputs       │                  │                      │
└──────────────────┴──────────────────┴──────────────────────┘
```

**User Interface Components:**
- Block Library for browsing available nodes
- Canvas-based Node Editor with drag-and-drop
- Properties Panel for configuration

---

# Pipeline Builder: Architecture (Core Layer)

```
┌─────────────────────────────────────────────────────────────┐
│                     Core Layer                               │
├──────────────────┬──────────────────┬──────────────────────┤
│  Node Registry   │  Pipeline        │  Code Generator      │
│  - Node types    │  - Graph         │  - Jinja2 templates  │
│  - Pin configs   │  - Validation    │  - C++ generation    │
│  - Constraints   │  - Serialization │  - CMake generation  │
└──────────────────┴──────────────────┴──────────────────────┘
```

**Core Processing:**
- Node Registry manages available blocks
- Pipeline handles graph operations and validation
- Code Generator creates deployable artifacts

---

# Pipeline Builder: Architecture (Libraries)

```
┌─────────────────────────────────────────────────────────────┐
│                  Third-Party Libraries                       │
├─────────────────────────────────────────────────────────────┤
│  GLFW (windowing) | ImGui (UI) | imgui-node-editor         │
└─────────────────────────────────────────────────────────────┘
```

**Technology Stack:**
- **GLFW:** Cross-platform windowing and OpenGL context
- **Dear ImGui:** Immediate mode GUI framework
- **imgui-node-editor:** Blueprint-style node editor widget

---

# Pipeline Builder: Node Library (Part 1)

## Input Nodes - Sensors

- **Synthetic Signal Generator** - Test signals (sine, square, sawtooth, triangle)
- **ADXL345** - 3-axis accelerometer (I2C)
- **MPU6050** - 6-axis IMU (I2C)
- **BME280** - Temperature/humidity/pressure (I2C)
- **Analog Input** - ADC voltage reader
- **GPIO Input** - Digital input

---

# Pipeline Builder: Node Library (Part 2)

## Processing Nodes

- **Channel Merge** - Combine multiple channels → vector
- **Sliding Window** - Buffer accumulation
- **Low Pass Filter** - Butterworth filtering
- **Normalize** - Data normalization

---

# Pipeline Builder: Node Library (Part 3)

## AI Model Nodes

- **TimesNet (ONNX)** - Deep learning classification (Jetson only)
- **Decision Tree** - Classical ML (Arduino only)

---

# Pipeline Builder: Node Library (Part 4)

## Output Nodes

- **Data Recorder** - CBOR dataset recording
- **WebSocket** - Real-time data streaming
- **GPIO Output** - LED/relay control
- **PWM Output** - Servo/motor control
- **MQTT Publisher** - IoT messaging
- **HTTP Post** - REST API calls
- **Web LED** - Dashboard indicator
- **Web Button** - Dashboard control

---

# Pipeline Builder: Example Pipeline

```
┌─────────────────┐     ┌─────────────┐     ┌───────────────┐
│ Synthetic       │────▶│  Channel    │────▶│ Data Recorder │
│ Signal Gen      │     │  Merge      │     │               │
│                 │     │             │     │ - CBOR output │
│ - 3 channels    │     │ - vector3   │     │ - Windowing   │
│ - sine wave     │     │             │     │ - Class label │
│ - 100 Hz        │     │             │     │               │
└─────────────────┘     └─────────────┘     └───────────────┘
        │
        ├──────────────▶ class_id ──────────────┘
```

**Pin Connections:**
- `channel_0` (float) → `ch0` (float)
- `channel_1` (float) → `ch1` (float)
- `channel_2` (float) → `ch2` (float)
- `class_id` (int) → `class_id` (int)
- `merged_out` (array) → `signal_data` (array)

---

# Pipeline Builder: Deployment Pipeline (Part 1)

## Input and Processing

```
┌─────────────────┐     ┌─────────────┐     ┌────────────────┐
│  ADXL345        │────▶│  Sliding    │────▶│ TimesNet ONNX  │
│  Sensor         │     │  Window     │     │                │
│                 │     │             │     │ - TensorRT     │
│ - I2C addr 0x53 │     │ - size: 300 │     │ - 4 classes    │
│ - 100 Hz        │     │ - stride: 1 │     │                │
└─────────────────┘     └─────────────┘     └────────────────┘
```

**Data flow:** Sensor → Windowing → AI Inference

---

# Pipeline Builder: Deployment Pipeline (Part 2)

## Output Nodes

```
┌────────────────┐
│ TimesNet ONNX  │
│                │
└────────┬───────┘
         │
         ▼
┌──────────────────────────────────────┐
│         Output Nodes                 │
├─────────────┬────────────────────────┤
│  WebSocket  │  GPIO Output (LED)     │
│  - port 8765│  - pin: 12             │
│             │  - on: class == "fault"│
└─────────────┴────────────────────────┘
```

**Outputs:** Dashboard streaming and physical LED control

---

# Pipeline Builder: Code Generation (Part 1)

## Manifest Structure

```json
{
  "format_version": "1.0",
  "pipeline_name": "gesture_classifier",
  "target_platform": "jetson_nano",
  "blocks": [...]
}
```

Pipeline metadata and configuration

---

# Pipeline Builder: Code Generation (Part 2)

## Block Definitions

```json
"blocks": [
  {
    "id": "adxl345-sensor",
    "version": "1.0.0",
    "type": "i2c-device",
    "config": {
      "i2c_address": "0x53",
      "sample_rate": 100
    }
  },
  {
    "id": "timesnet-onnx",
    "version": "1.2.0",
    "type": "onnx-runtime",
    "config": {
      "model_path": "/home/user/models/gesture.onnx",
      "num_classes": 4
    }
  }
]
```

---

# Pipeline Builder: Deployment Process (Step 1-3)

## Design and Validation

**1. Design Pipeline** (drag-and-drop nodes)

**2. Configure Nodes** (properties panel)

**3. Validate Pipeline**
```
Menu → Edit → Validate Pipeline
- Check for disconnected pins
- Verify type compatibility
- Detect cycles in graph
```

---

# Pipeline Builder: Deployment Process (Step 4)

## Code Generation

**4. Generate Code**
```
Menu → Generate → Generate Code
- Creates block_manifest.json
- Generates CMakeLists.txt
- Creates deployment scripts
```

Generates all deployment artifacts

---

# Pipeline Builder: Deployment Process (Step 5)

## Deploy to Jetson

**5. Deploy to Jetson**
```
Menu → Deploy → Deploy to Device
- SSH to Jetson (user@jetson.local)
- Transfer manifest and models
- Install dependencies
- Compile and launch runtime
```

Automated remote deployment via SSH

---

# Component 3: CiRA Block Runtime

## Purpose
Dynamic pipeline execution engine for **Jetson devices**

## Key Features
- Block-based architecture (shared libraries)
- Manifest-driven configuration
- No recompilation needed for pipeline changes
- Configurable execution rate (Hz)
- Real-time statistics tracking
- Web dashboard (optional)
- Graceful shutdown handling

---

# CiRA Block Runtime: Architecture (Part 1)

```
┌─────────────────────────────────────────────────────────────┐
│                   cira-block-runtime                         │
│                    (C++ Executable)                          │
├─────────────────────────────────────────────────────────────┤
│                   Manifest Parser                            │
│              (JSON → BlockManifest)                          │
├─────────────────────────────────────────────────────────────┤
│                    Block Loader                              │
│              (dlopen .so libraries)                          │
└─────────────────────────────────────────────────────────────┘
```

**Top-level Components:**
- Main executable processes manifest configuration
- Manifest Parser converts JSON to internal structures
- Block Loader dynamically loads shared libraries

---

# CiRA Block Runtime: Architecture (Part 2)

```
┌─────────────────────────────────────────────────────────────┐
│                   Block Instances                            │
├──────────────────┬──────────────────┬──────────────────────┤
│  Block Instance  │  Block Instance  │  Block Instance      │
│  adxl345.so      │  sliding_window  │  timesnet_onnx.so    │
│  - Initialize()  │  .so             │  - Initialize()      │
│  - Execute()     │  - Initialize()  │  - Execute()         │
│  - GetOutput()   │  - Execute()     │  - GetOutput()       │
└──────────────────┴──────────────────┴──────────────────────┘
```

**Dynamic Block System:**
- Each block loaded as shared library (.so)
- Common interface: Initialize(), Execute(), GetOutput()
- Blocks can be added without recompiling runtime

---

# CiRA Block Runtime: Architecture (Part 3)

```
┌─────────────────────────────────────────────────────────────┐
│                   Block Executor                             │
│         (Topological sort + execution loop)                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  while (running):                                      │ │
│  │    for block in sorted_blocks:                        │ │
│  │      block.Execute()                                  │ │
│  │    sleep(1/rate_hz)                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Execution Engine:**
- Topological sort ensures correct execution order
- Configurable execution rate (Hz)
- Real-time processing loop

---

# CiRA Block Runtime: Architecture (Part 4)

```
┌─────────────────────────────────────────────────────────────┐
│            Web Server (optional - WITH_WEB_SERVER)           │
├─────────────────────────────────────────────────────────────┤
│  - Dashboard on port 8080                                   │
│  - Metrics API (/api/metrics)                               │
│  - Authentication (username/password)                       │
└─────────────────────────────────────────────────────────────┘
```

**Optional Web Interface:**
- HTTP server for dashboard access
- RESTful API for metrics
- Basic authentication support

---

# CiRA Block Runtime: Block Interface (Part 1)

## Lifecycle Methods

```cpp
class IBlock {
public:
    // Lifecycle
    virtual bool Initialize(const BlockConfig& config) = 0;
    virtual bool Execute() = 0;
    virtual void Shutdown() = 0;

    // Metadata
    virtual std::string GetBlockId() const = 0;
    virtual std::string GetBlockVersion() const = 0;
    virtual std::string GetBlockType() const = 0;
```

---

# CiRA Block Runtime: Block Interface (Part 2)

## I/O and Statistics

```cpp
    // I/O
    virtual std::vector<PinInfo> GetInputPins() const = 0;
    virtual std::vector<PinInfo> GetOutputPins() const = 0;

    virtual bool SetInput(const std::string& pin, const Any& value) = 0;
    virtual Any GetOutput(const std::string& pin) const = 0;

    // Statistics
    virtual BlockStats GetStats() const = 0;
};
```

All blocks implement this common interface

---

# CiRA Block Runtime: Example Block (Part 1)

## TimesNet ONNX - Initialization

```cpp
class TimesNetONNXBlock : public IBlock {
private:
    Ort::Env env_;
    Ort::Session session_;
    std::vector<float> input_buffer_;
    std::vector<float> output_buffer_;
    int predicted_class_;

public:
    bool Initialize(const BlockConfig& config) override {
        // Load ONNX model
        std::string model_path = config.at("model_path");
        session_ = Ort::Session(env_, model_path.c_str(),
                                Ort::SessionOptions{});

        // Allocate buffers
        input_buffer_.resize(300 * 3);  // seq_len × channels
        output_buffer_.resize(4);       // num_classes
        return true;
    }
```

---

# CiRA Block Runtime: Example Block (Part 2)

## TimesNet ONNX - Execution

```cpp
    bool Execute() override {
        // Run inference
        auto memory_info = Ort::MemoryInfo::CreateCpu(...);
        Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
            memory_info, input_buffer_.data(),
            input_buffer_.size(), ...);

        auto outputs = session_.Run(..., &input_tensor, 1, ...);

        // Get prediction
        float* out_data = outputs[0].GetTensorMutableData<float>();
        predicted_class_ = std::distance(out_data,
            std::max_element(out_data, out_data + 4));

        return true;
    }
};
```

---

# CiRA Block Runtime: Execution Flow (Part 1)

## Initialization

```
main()
  ↓
Parse command line args
  --rate 100           (100 Hz execution)
  --iterations 1000    (run 1000 times then exit)
  ↓
Load block_manifest.json
  ↓
For each block in manifest:
  ┌──────────────────────────────────┐
  │  dlopen("/usr/local/lib/cira/    │
  │         blocks/block-v1.0.0.so") │
  │         ↓                         │
  │  CreateBlock() → IBlock*         │
  │         ↓                         │
  │  block->Initialize(config)       │
  └──────────────────────────────────┘
```

---

# CiRA Block Runtime: Execution Flow (Part 2)

## Main Loop

```
Build execution graph (topological sort)
  ↓
┌──────────────────────────────────────┐
│  Execution Loop:                     │
│  while (running && iter < max_iter): │
│    for block in sorted_order:        │
│      block->Execute()                │
│    sleep(1/rate_hz)                  │
│    iter++                            │
└──────────────────────────────────────┘
  ↓
Shutdown all blocks
  ↓
Exit
```

---

# Component 4: CiRA Dashboard (Jetson)

## Purpose
Web-based **real-time monitoring and control** for deployed pipelines

## Key Features
- WebSocket-based live data streaming
- Interactive charts (Chart.js / Plotly)
- Control buttons for pipeline interaction
- LED status indicators
- Prediction visualization
- Metrics display (throughput, latency)

---

# CiRA Dashboard: Architecture (Part 1)

## Jetson Runtime

```
┌─────────────────────────────────────────────────────────────┐
│                  Jetson Nano/Orin (Linux)                    │
├─────────────────────────────────────────────────────────────┤
│                  cira-block-runtime                          │
│                    (running pipeline)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Sensor → Processing → AI Model → Outputs             │ │
│  │                           │                            │ │
│  │                           ├──▶ WebSocket Block         │ │
│  │                           │    - port: 8765            │ │
│  │                           │    - broadcast predictions │ │
│  │                           │                            │ │
│  │                           └──▶ Web LED Block           │ │
│  │                                - status: "running"     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Pipeline Execution on Jetson**

---

# CiRA Dashboard: Architecture (Part 2)

## Web Server

```
┌─────────────────────────────────────────────────────────────┐
│                   Web Server (optional)                      │
├─────────────────────────────────────────────────────────────┤
│  - HTTP on port 8080                                        │
│  - Serves dashboard HTML/CSS/JS                             │
│  - WebSocket connection on port 8765                        │
└─────────────────────────────────────────────────────────────┘
```

**Optional built-in web server for dashboard hosting**

---

# CiRA Dashboard: Architecture (Part 3)

## Browser Interface

```
┌─────────────────────────────────────────┐
│    Browser (any device on network)      │
│  http://jetson.local:8080               │
│  ┌─────────────────────────────────┐    │
│  │  CiRA Dashboard                 │    │
│  │  - Live waveform chart          │    │
│  │  - Prediction bar chart         │    │
│  │  - Control buttons              │    │
│  │  - LED indicators               │    │
│  │  - Metrics (FPS, latency)       │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Web-based monitoring accessible from any device**

---

# CiRA Dashboard: Web Interface (Part 1)

## Real-time Waveform Chart

```javascript
// Chart.js line chart
const ctx = document.getElementById('waveformChart');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        datasets: [
            { label: 'Channel 0', data: [] },
            { label: 'Channel 1', data: [] },
            { label: 'Channel 2', data: [] }
        ]
    },
    options: {
        animation: false,  // For real-time performance
        scales: { x: { type: 'realtime' } }
    }
});
```

---

# CiRA Dashboard: Web Interface (Part 2)

## WebSocket Data Reception

```javascript
// WebSocket listener for live data
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    chart.data.datasets[0].data.push({x: Date.now(), y: data.ch0});
    chart.data.datasets[1].data.push({x: Date.now(), y: data.ch1});
    chart.data.datasets[2].data.push({x: Date.now(), y: data.ch2});
    chart.update();
};
```

Updates chart in real-time as data arrives from Jetson

---

# CiRA Dashboard: Web Interface (Part 3)

## Prediction Visualization

```javascript
// Bar chart for class probabilities
const predChart = new Chart(predCtx, {
    type: 'bar',
    data: {
        labels: ['Normal', 'Fault A', 'Fault B', 'Fault C'],
        datasets: [{
            label: 'Probability',
            data: [0.1, 0.05, 0.8, 0.05],
            backgroundColor: ['#10b981', '#ef4444', '#f59e0b', '#8b5cf6']
        }]
    }
});

ws.onmessage = (event) => {
    const prediction = JSON.parse(event.data);
    predChart.data.datasets[0].data = prediction.probabilities;
    predChart.update();
};
```

---

# CiRA Dashboard: Web Interface (Part 4)

## Control Buttons

```javascript
// Web Button → Pipeline interaction
document.getElementById('recordBtn').onclick = () => {
    ws.send(JSON.stringify({
        type: 'button_press',
        button_id: 'record_trigger'
    }));
};
```

Enables interactive control of the pipeline from browser

---

# End-to-End Workflow (Step 1)

## Data Collection

```
Step 1: Data Collection (CiRA Studio)
  ┌──────────────────────────────────────────┐
  │ 1. Launch Pipeline Builder              │
  │ 2. Create recording pipeline:           │
  │    - Synthetic Signal Gen (or sensor)   │
  │    - Channel Merge                      │
  │    - Data Recorder                      │
  │ 3. Deploy to Jetson                     │
  │ 4. Record dataset (4 classes × 100 win) │
  │ 5. Download CBOR files to PC            │
  └──────────────────────────────────────────┘
```

---

# End-to-End Workflow (Step 2)

## Model Training

```
Step 2: Model Training (CiRA Studio)
  ┌──────────────────────────────────────────┐
  │ 1. Load CBOR dataset                    │
  │ 2. Verify format (900 values/window)    │
  │ 3. Configure TimesNet model             │
  │ 4. Train for 50-100 epochs              │
  │ 5. Evaluate (accuracy, F1 score)        │
  │ 6. Export to ONNX format                │
  └──────────────────────────────────────────┘
```

---

# End-to-End Workflow (Step 3)

## Pipeline Design

```
Step 3: Pipeline Design (Pipeline Builder)
  ┌──────────────────────────────────────────┐
  │ 1. Create inference pipeline:           │
  │    - ADXL345 Sensor → Sliding Window    │
  │    - Sliding Window → TimesNet ONNX     │
  │    - TimesNet → WebSocket (dashboard)   │
  │    - TimesNet → GPIO Output (LED)       │
  │ 2. Configure nodes                      │
  │ 3. Validate pipeline                    │
  │ 4. Generate code                        │
  └──────────────────────────────────────────┘
```

---

# End-to-End Workflow (Step 4)

## Deployment

```
Step 4: Deployment (Pipeline Builder)
  ┌──────────────────────────────────────────┐
  │ 1. SSH to Jetson                        │
  │ 2. Transfer:                            │
  │    - block_manifest.json                │
  │    - model.onnx                         │
  │ 3. Install blocks (if not present)      │
  │ 4. Launch: cira-block-runtime \         │
  │            manifest.json --rate 100     │
  └──────────────────────────────────────────┘
```

---

# End-to-End Workflow (Step 5)

## Monitoring

```
Step 5: Monitoring (Browser)
  ┌──────────────────────────────────────────┐
  │ 1. Open http://jetson.local:8080        │
  │ 2. View real-time dashboard:            │
  │    - Live sensor waveforms              │
  │    - Prediction probabilities           │
  │    - System metrics                     │
  │ 3. Interact with controls:              │
  │    - Start/stop recording               │
  │    - Adjust parameters                  │
  └──────────────────────────────────────────┘
```

---

# End-to-End Workflow (Step 6)

## Production Deployment

```
Step 6: Production Deployment
  ┌──────────────────────────────────────────┐
  │ 1. Create systemd service:              │
  │    [Unit]                               │
  │    Description=CiRA Pipeline            │
  │    [Service]                            │
  │    ExecStart=cira-block-runtime \       │
  │              /etc/cira/manifest.json    │
  │    Restart=always                       │
  │ 2. Enable on boot:                      │
  │    sudo systemctl enable cira-pipeline  │
  └──────────────────────────────────────────┘
```

---

# Technical Deep Dive: Libraries (Part 1)

## CiRA Studio - UI & Data

### UI Framework
- **CustomTkinter 5.2.2** - Modern Tkinter wrapper
- **Pillow 10.2.0** - Image processing
- **darkdetect 0.8.0** - System theme detection

### Data Processing
- **Pandas 2.1.4** - DataFrame operations
- **NumPy 1.24.4** - Numerical computing
- **SciPy 1.11.4** - Scientific computing

---

# Technical Deep Dive: Libraries (Part 2)

## CiRA Studio - Machine Learning

### Machine Learning
- **Scikit-learn 1.3.2** - Classical ML algorithms
- **PyOD 1.1.2** - Anomaly detection library
- **imbalanced-learn 0.11.0** - Class balancing

### Deep Learning
- **PyTorch 2.0+** - Neural network training
- **einops 0.7.0** - Tensor operations for TimesNet
- **ONNX 1.14.0** - Model serialization/export

---

# Technical Deep Dive: Libraries (Part 3)

## CiRA Studio - Feature Engineering

### Feature Engineering
- **TSFresh 0.20.2** - Time series feature extraction
- **PyWavelets 1.5.0** - Wavelet transforms
- **librosa 0.10.1** - Audio/signal features (optional)

### LLM Integration
- **llama-cpp-python 0.2.56** - Local LLM inference
- **huggingface-hub 0.20.3** - Model downloading

---

# Technical Deep Dive: Libraries (Part 4)

## CiRA Studio - Visualization & Files

### Visualization
- **Matplotlib 3.8.2** - Static plots
- **Seaborn 0.13.1** - Statistical visualization
- **Plotly 5.18.0** - Interactive charts

### File Formats
- **cbor2 5.7.1** - CBOR serialization
- **h5py 3.10.0** - HDF5 files
- **pyarrow 14.0.2** - Parquet format

---

# Technical Deep Dive: Libraries (Part 5)

## CiRA Studio - Code Generation & Build

### Code Generation
- **Jinja2 3.1.3** - Template engine
- **black 24.1.1** - Python formatter

### Build Tools
- **CMake 3.28.1** - C++ build system
- **ninja 1.11.1** - Fast build tool

---

# Technical Deep Dive: Pipeline Builder (C++)

## Core Libraries

### UI & Windowing
- **GLFW** - Cross-platform window management
  - OpenGL context creation
  - Input handling (mouse, keyboard)
  - Multi-monitor support

- **Dear ImGui** - Immediate mode GUI library
  - Lightweight, bloat-free UI
  - No dependencies on STL or exceptions
  - Dark theme customization

- **imgui-node-editor** - Node graph editor
  - Blueprint-style visual editor
  - Bezier curve connections
  - Pan/zoom canvas navigation

---

# Technical Deep Dive: Block Runtime (C++)

## Core Libraries

### Standard Libraries
- **C++17 STL** - Standard containers, algorithms
- **POSIX threads** - Multi-threading
- **dlopen/dlsym** - Dynamic library loading

### Optional Dependencies
- **ONNX Runtime** - For AI model blocks
  - CPU inference (default)
  - TensorRT acceleration (Jetson)
  - CUDA support

- **WebSocket++** - WebSocket server (if WITH_WEB_SERVER)
- **nlohmann/json** - JSON parsing
- **spdlog** - Logging library

---

# Technical Deep Dive: Signal Processing (Part 1)

## Windowing - Class Definition

```cpp
class SlidingWindowBlock : public IBlock {
    std::deque<float> buffer_;
    int window_size_;
    int stride_;

    bool Execute() override {
        float new_sample = GetInput<float>("input");
        buffer_.push_back(new_sample);
```

---

# Technical Deep Dive: Signal Processing (Part 2)

## Windowing - Buffer Management

```cpp
        if (buffer_.size() >= window_size_) {
            // Output window
            std::vector<float> window(
                buffer_.begin(),
                buffer_.begin() + window_size_
            );
            SetOutput("output", window);

            // Slide by stride
            for (int i = 0; i < stride_; i++) {
                buffer_.pop_front();
            }
        }
        return true;
    }
};
```

---

# Technical Deep Dive: Low Pass Filter (Part 1)

## Butterworth Filter Theory

**Transfer Function (2nd order):**
```
H(z) = (b₀ + b₁z⁻¹ + b₂z⁻²) / (1 + a₁z⁻¹ + a₂z⁻²)
```

**Difference Equation:**
```
y[n] = b₀x[n] + b₁x[n-1] + b₂x[n-2] - a₁y[n-1] - a₂y[n-2]
```

**Frequency Response:**
```
|H(f)| = 1 / √(1 + (f/fc)^(2n))
```
where n = filter order, fc = cutoff frequency

---

# Technical Deep Dive: Low Pass Filter (Part 2)

## Coefficient Calculation

```cpp
class LowPassFilterBlock : public IBlock {
    float b0_, b1_, b2_;  // Numerator coefficients
    float a1_, a2_;       // Denominator coefficients
    float x1_, x2_;       // Input history
    float y1_, y2_;       // Output history

    void CalculateCoefficients(float fc, float fs) {
        // fc: cutoff frequency, fs: sample rate
        float omega = 2.0f * M_PI * fc / fs;
        float alpha = sin(omega) / (2.0f * 0.707f);  // Q = 0.707

        b0_ = (1 - cos(omega)) / 2;
        b1_ = 1 - cos(omega);
        b2_ = (1 - cos(omega)) / 2;

        float a0 = 1 + alpha;
        a1_ = -2 * cos(omega) / a0;
        a2_ = (1 - alpha) / a0;
    }
```

---

# Technical Deep Dive: Low Pass Filter (Part 3)

## Filter Execution

```cpp
    bool Execute() override {
        float x = GetInput<float>("input");

        // Apply filter
        float y = b0_*x + b1_*x1_ + b2_*x2_
                       - a1_*y1_ - a2_*y2_;

        // Update history
        x2_ = x1_; x1_ = x;
        y2_ = y1_; y1_ = y;

        SetOutput("output", y);
        return true;
    }
};
```

Applies second-order IIR filter with history state management

---

# Technical Deep Dive: Data Format (Part 1)

## CBOR File Structure

**Structure:**
```
File: sine.0.cbor
{
  "timestamp": "2026-01-25T10:30:45.123Z",
  "class_name": "sine",
  "class_id": 1,
  "data": [...]
}
Total: 900 float values per window
```

---

# Technical Deep Dive: Data Format (Part 2)

## Channel Layout

**Data Array Organization:**
```
Channel 0 (samples 0-299):
  0.234, 0.456, 0.678, ..., (300 values)

Channel 1 (samples 0-299):
  0.123, 0.345, 0.567, ..., (300 values)

Channel 2 (samples 0-299):
  0.111, 0.333, 0.555, ..., (300 values)
```

**Index Mapping:**
```
Index    0-299:   Channel 0 (all samples)
Index  300-599:   Channel 1 (all samples)
Index  600-899:   Channel 2 (all samples)
```

---

# Technical Deep Dive: Multi-Channel Signals

## Phase Offset for Channel Diversity

**Mathematical Formula:**
```
For channel i:
  phase_i = phase_base + (2π × i / num_channels)

Signal generation:
  y_i(t) = A × sin(2πft + phase_i) + offset
```

**Example (3 channels, sine wave):**
```
Channel 0: y₀(t) = A × sin(2πft + 0°)
Channel 1: y₁(t) = A × sin(2πft + 120°)
Channel 2: y₂(t) = A × sin(2πft + 240°)
```

**Result:** 3 distinct waveforms with 120° phase separation

---

# Technical Deep Dive: Period Detection (Part 1)

## FFT Algorithm

```python
def detect_periods(x, top_k):
    # 1. Compute FFT
    X_freq = fft(x)  # Complex spectrum

    # 2. Compute amplitude spectrum
    A = np.abs(X_freq)  # |X(f)|

    # 3. Find top-k frequency components
    freq_indices = np.argsort(A)[-top_k:]  # Top-k peaks
```

---

# Technical Deep Dive: Period Detection (Part 2)

## Period Conversion

```python
    # 4. Convert to periods
    periods = []
    for idx in freq_indices:
        if idx > 0:  # Skip DC component
            period = len(x) / idx
            periods.append(int(period))

    return periods

# Example: seq_len=300, top_k=3
# Output: [100, 75, 60] (dominant periods)
```

---

# Technical Deep Dive: 2D Transformation (Part 1)

## 1D to 2D Reshape

**Transformation:**
```
Input: X₁D = [x₀, x₁, x₂, ..., x₂₉₉]  (seq_len=300)
Period: p = 100

Reshape:
X₂D = [
  [x₀,   x₁,   x₂,   ..., x₉₉  ],  // Row 0 (period 0)
  [x₁₀₀, x₁₀₁, x₁₀₂, ..., x₁₉₉],  // Row 1 (period 1)
  [x₂₀₀, x₂₀₁, x₂₀₂, ..., x₂₉₉]   // Row 2 (period 2)
]
Shape: (3, 100) = (seq_len/p, p)
```

---

# Technical Deep Dive: 2D Transformation (Part 2)

## Inception Processing

**Inception Convolution:**
```
Apply 2D convolutions with kernels: 1×1, 3×3, 5×5, 7×7
Concatenate results
Apply 1×1 conv for channel reduction
```

**2D → 1D Back:**
```
Flatten: X₂D(3, 100) → X₁D(300)
```

Multi-scale temporal pattern extraction

---

# Deployment Considerations (Part 1)

## Windows Development Platform

**Requirements:**
- **OS:** Windows 10/11 x64
- **Python:** 3.8-3.11
- **RAM:** 8 GB minimum, 16 GB recommended
- **GPU:** Optional (CUDA for faster training)
- **Visual Studio:** 2019/2022 with C++ Desktop Development

---

# Deployment Considerations (Part 2)

## Jetson Nano Deployment

**Requirements:**
- **OS:** Ubuntu 20.04 ARM64 (JetPack 4.6+)
- **RAM:** 4 GB
- **Storage:** 32 GB+ SD card (Class 10)
- **Dependencies:**
  - ONNX Runtime 1.16+ (with TensorRT EP)
  - CMake 3.10+, GCC 7+
  - I2C tools (for sensor communication)

---

# Deployment Considerations (Part 3)

## Jetson Orin High Performance

**Specifications:**
- **OS:** Ubuntu 20.04 ARM64 (JetPack 5.1+)
- **RAM:** 8-32 GB (depending on module)
- **GPU:** Ampere architecture (2048 CUDA cores)

**Performance:**
- 100+ FPS inference (TimesNet)
- TensorRT FP16/INT8 quantization support
- Multi-stream inference

---

# Performance Benchmarks

## CiRA Studio (Windows PC)

**Dataset Loading:**
- CSV (10K rows): < 1 second
- CBOR (1K windows): < 500 ms

**Feature Extraction (TSFresh):**
- 300-sample window × 3 channels
- 120 features
- Time: ~5-10 seconds per window

**TimesNet Training:**
- GPU (RTX 3060): 50 epochs ~ 2-3 minutes
- CPU (i7-10700): 50 epochs ~ 15-20 minutes

**ONNX Export:**
- < 1 second

---

# Performance Benchmarks (Part 2)

## Pipeline Builder

**UI Performance:**
- 60 FPS at 1920×1080
- 100+ nodes without lag
- Instantaneous connection validation

**Code Generation:**
- < 500 ms for typical pipeline

---

# Performance Benchmarks (Part 3)

## CiRA Block Runtime (Jetson Nano)

**Inference Performance:**
- TimesNet (ONNX + TensorRT): 50-100 FPS
- Latency: 10-20 ms per window
- Memory: ~200 MB

**Sensor Sampling:**
- ADXL345 @ 100 Hz: < 1% CPU
- I2C communication: ~1 ms per read

---

# Common Issues & Solutions

## Issue 1: Dataset Format Mismatch

**Symptom:** Training error "index 2 is out of bounds for axis 0 with size 2"

**Cause:** Dataset has wrong shape (sample-by-sample instead of windowed)

**Solution:**
1. Verify data shape: `data.shape[1] == 900`
2. Check channel layout: `[ch0_all, ch1_all, ch2_all]`
3. Re-record with correct Data Recorder configuration:
   - `window_size=300`
   - `num_channels=3`

---

# Common Issues & Solutions (Part 2)

## Issue 2: Poor Model Performance

**Symptom:** Accuracy < 60%

**Possible Causes:**
1. **Insufficient data** - Record 100+ windows per class
2. **Class imbalance** - Equal windows per class
3. **No channel diversity** - Verify phase offsets
4. **Model underfitting** - Increase `d_model` or epochs

---

# Common Issues & Solutions (Part 3)

## Issue 3: Deployment Failure

**Symptom:** "Block not found" error on Jetson

**Solution:**
1. Check block installation:
   ```bash
   ls /usr/local/lib/cira/blocks/
   ```

2. Install missing blocks:
   ```bash
   cd cira-block-runtime
   mkdir build && cd build
   cmake .. -DBUILD_BLOCKS=ON
   sudo make install
   ```

---

# Common Issues & Solutions (Part 4)

## Issue 4: WebSocket Connection Failed

**Symptom:** Dashboard not receiving data

**Solution:**
1. Check firewall: `sudo ufw allow 8765/tcp`
2. Verify WebSocket block in pipeline
3. Check browser console for errors
4. Ensure correct URL: `ws://jetson.local:8765`

---

# Best Practices (Part 1)

## Dataset Recording
1. ✅ **Equal windows per class** (100+ recommended)
2. ✅ **Verify format** before training (900 values)
3. ✅ **Use distinct signals** (phase offsets for multi-channel)
4. ✅ **Label consistently** (class_id mapping)
5. ✅ **Record test set** separately (30% of total)

---

# Best Practices (Part 2)

## Model Training
1. ✅ **Start small** (10 windows for format verification)
2. ✅ **Monitor metrics** (accuracy, F1 score, loss)
3. ✅ **Early stopping** (patience=10 epochs)
4. ✅ **Validate ONNX** before deployment
5. ✅ **Test on CPU first** (ensure compatibility)

---

# Best Practices (Part 3)

## Pipeline Design
1. ✅ **Validate connections** before deployment
2. ✅ **Use appropriate sample rates** (sensor → model compatibility)
3. ✅ **Buffer management** (sliding window stride)
4. ✅ **Error handling** (sensor disconnection)
5. ✅ **Modular design** (reusable sub-pipelines)

---

# Best Practices (Part 4)

## Deployment
1. ✅ **Test locally** (Pipeline Builder preview)
2. ✅ **Incremental deployment** (sensor → processing → AI)
3. ✅ **Monitor logs** (`journalctl -u cira-pipeline -f`)
4. ✅ **Systemd service** for production
5. ✅ **Version control** (manifest + models in git)

---

# Advanced Topics (Part 1)

## TensorRT Optimization (Jetson)

**Convert ONNX → TensorRT Engine:**
```bash
/usr/src/tensorrt/bin/trtexec \
  --onnx=model.onnx \
  --saveEngine=model.trt \
  --fp16 \
  --workspace=4096
```

**Benefits:**
- 2-5× faster inference
- FP16 precision (negligible accuracy loss)
- Optimized for Jetson GPU

---

# Advanced Topics (Part 2)

## Multi-Model Ensemble

**Pipeline Design:**
```
Sensor → Sliding Window
           ↓
   ┌───────┴────────┐
   ↓                ↓
Model A         Model B
(TimesNet)      (Random Forest)
   ↓                ↓
   └───────┬────────┘
           ↓
     Voting Block
   (majority vote)
           ↓
        Output
```

---

# Advanced Topics (Part 3)

## Custom Block Development - Header

**1. Create Block Header** (`my_block.hpp`)
```cpp
#include <cira-block-runtime/block_interface.hpp>

class MyCustomBlock : public CiraBlockRuntime::IBlock {
public:
    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    std::string GetBlockId() const override {
        return "my-custom-block";
    }
    std::string GetBlockVersion() const override {
        return "1.0.0";
    }
};
```

---

# Advanced Topics (Part 4)

## Custom Block Development - Implementation

**2. Implement Block** (`my_block.cpp`)
```cpp
#include "my_block.hpp"

bool MyCustomBlock::Initialize(const BlockConfig& config) {
    param_ = std::stoi(config.at("my_param"));
    return true;
}

bool MyCustomBlock::Execute() {
    float input = GetInput<float>("input");
    float output = custom_transform(input);
    SetOutput("output", output);
    return true;
}

extern "C" {
    IBlock* CreateBlock() { return new MyCustomBlock(); }
    void DestroyBlock(IBlock* block) { delete block; }
}
```

---

# Advanced Topics (Part 5)

## Custom Block Development - Build

**3. Build as Shared Library** (`CMakeLists.txt`)
```cmake
cmake_minimum_required(VERSION 3.10)
project(my-custom-block)

add_library(my-custom-block-v1.0.0 SHARED my_block.cpp)

target_include_directories(my-custom-block-v1.0.0 PRIVATE
    /usr/local/include/cira-block-runtime
)

install(TARGETS my-custom-block-v1.0.0
    LIBRARY DESTINATION /usr/local/lib/cira/blocks/
)
```

---

# Advanced Topics (Part 6)

## Custom Block Development - Installation

**4. Install on Jetson**
```bash
mkdir build && cd build
cmake ..
make
sudo make install
```

Block is now available for use in pipelines

---

# Resources & Support (Part 1)

## Documentation
- **CiRA Studio README:** `/README.md`
- **Pipeline Builder README:** `/pipeline_builder/README.md`
- **Block Runtime README:** `/cira-block-runtime/README.md`
- **Dataset Recording Protocol:** `/Dataset_Recording_Protocol.md`

---

# Resources & Support (Part 2)

## Example Pipelines
- **Recording Pipeline:** Synthetic Signal → Data Recorder
- **Inference Pipeline:** ADXL345 → TimesNet → WebSocket
- **Multi-Sensor Pipeline:** 3× Sensors → Merge → AI

## Source Code
- **GitHub Repository:** [Internal repository]
- **Issue Tracker:** For bug reports and feature requests

---

# Summary (Part 1)

## What You've Learned

1. ✅ **CiRA Studio** - Professional ML development environment
   - Dataset recording with CBOR format
   - TimesNet deep learning model training
   - ONNX export for deployment

2. ✅ **Pipeline Builder** - Visual pipeline design
   - Drag-and-drop interface
   - 25+ pre-built blocks
   - Code generation and deployment

---

# Summary (Part 2)

## System Components

3. ✅ **CiRA Block Runtime** - Edge execution engine
   - Dynamic block loading
   - Manifest-driven configuration
   - Real-time performance

4. ✅ **CiRA Dashboard** - Web-based monitoring
   - Real-time visualization
   - Control interface
   - Production deployment

---

# Summary (Part 3)

## Complete Workflow

5. ✅ **End-to-End Workflow**
   - From raw data to deployed AI
   - Professional best practices
   - Performance optimization

Complete ML development to edge deployment platform

---

# Next Steps (Part 1)

## Hands-On Training - Day 1

**Day 1: CiRA Studio**
- Setup and installation
- Record synthetic dataset (4 classes × 100 windows)
- Train TimesNet model
- Validate and export ONNX

---

# Next Steps (Part 2)

## Hands-On Training - Day 2-3

**Day 2: Pipeline Builder**
- Design recording pipeline
- Design inference pipeline
- Deploy to Jetson

**Day 3: Integration**
- Real sensor integration (ADXL345)
- Dashboard customization
- Production deployment with systemd

---

# Thank You!

## Questions?

**Contact Information:**
- Technical Support: [support email]
- Documentation: [docs link]
- Training Materials: [training portal]

---

# System Specifications

**Version Information:**
- **CiRA Studio:** v1.0 (Python 3.8+)
- **Pipeline Builder:** v1.0 (C++17)
- **Block Runtime:** v1.0 (Linux ARM64)
- **Supported Platforms:** Jetson Nano, Jetson Orin

---

# Appendix A: Quick Reference (Part 1)

## CiRA Studio Commands

**Launch Application:**
```bash
python main.py
```

**Dataset Verification:**
```python
import cbor2
with open('dataset.cbor', 'rb') as f:
    data = cbor2.load(f)
print(f"Shape: {len(data['data'])}")  # Should be 900
print(f"Class: {data['class_name']}")
```

---

# Appendix A: Quick Reference (Part 2)

## ONNX Export

**ONNX Export:**
```python
torch.onnx.export(
    model, dummy_input, "model.onnx",
    input_names=['input'], output_names=['output'],
    dynamic_axes={'input': {0: 'batch_size'}}
)
```

---

# Appendix B: Quick Reference (Part 1)

## Pipeline Builder Commands

**Build Application:**
```bash
mkdir build && cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
```

**Launch:**
```bash
.\bin\Release\pipeline_builder.exe
```

---

# Appendix B: Quick Reference (Part 2)

## Block Runtime Commands

**Run Pipeline:**
```bash
cira-block-runtime manifest.json --rate 100
```

**With Web Dashboard:**
```bash
cira-block-runtime manifest.json \
  --rate 100 \
  --web-port 8080 \
  --web-user admin \
  --web-pass password
```

---

# Appendix C: Configuration Files (Part 1)

## Data Recorder Config (Pipeline Builder)

```json
{
  "max_samples": 100,
  "output_format": "cbor",
  "output_dir": "/home/user/cira_datasets",
  "window_size": 300,
  "num_channels": 3
}
```

---

# Appendix C: Configuration Files (Part 2)

## TimesNet ONNX Config

```json
{
  "model_path": "/home/user/models/gesture.onnx",
  "num_classes": 4,
  "use_tensorrt": true,
  "fp16_mode": true
}
```

---

# Appendix D: Troubleshooting Checklist (Part 1)

## Before Deployment
- [ ] Dataset format verified (900 values)
- [ ] Model trained with >80% accuracy
- [ ] ONNX exported and validated
- [ ] Pipeline validated in Pipeline Builder
- [ ] All blocks available on Jetson

---

# Appendix D: Troubleshooting Checklist (Part 2)

## During Deployment
- [ ] SSH connection successful
- [ ] Manifest transferred
- [ ] Model file transferred
- [ ] Block runtime starts without errors
- [ ] Web dashboard accessible

---

# Appendix D: Troubleshooting Checklist (Part 3)

## After Deployment
- [ ] Real-time data streaming working
- [ ] Predictions appear reasonable
- [ ] Latency within acceptable range (<50ms)
- [ ] System logs show no errors
