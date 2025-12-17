# Deployment Code Generation - Implementation Plan

**Date:** 2025-12-15
**Priority:** CRITICAL - Must complete before product launch
**Status:** Planning Phase

---

## Executive Summary

**Problem Statement:**
> "Users get 80% of value (trained model). Last 20% takes 80% of effort (integration hell). Most users give up here."

**Solution:**
Implement automated firmware generation that bridges the gap between trained models and running hardware, eliminating the "integration hell" that causes user abandonment.

**Scope:**
- ✅ **Phase 1:** Template-Based Code Generation (MVP)
- ⏸️ **Phase 2:** Additional Platforms/Sensors (Future, post-launch)
- ✅ **Phase 3:** Visual Pipeline Builder (Pre-launch requirement)

**Target Platforms (Phase 1):**
1. ESP32 (IoT, low-power embedded)
2. NVIDIA Jetson Nano (Edge AI with GPU)
3. Arduino Nano 33 BLE Sense (Tiny ML, built-in sensors)

---

## Phase 1: Template-Based Code Generation

**Timeline:** 3-4 weeks
**Deliverable:** Automated firmware generation for 3 platforms

### Architecture Overview

```
User Workflow:
┌─────────────────┐
│  Train Model    │ (Existing: model_panel.py)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Export Model   │ (Existing: ONNX/DSP export)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 🆕 Deployment   │ ← NEW SEPARATE UI PAGE
│    Wizard       │
└────────┬────────┘
         │
         ├─ Step 1: Select Platform (ESP32/Jetson/Nano33)
         ├─ Step 2: Configure Sensor (MPU6050, Built-in, etc.)
         ├─ Step 3: Pin Configuration (I2C, SPI, GPIO)
         ├─ Step 4: Actions (LED, Serial, WiFi, MQTT)
         └─ Step 5: Generate & Download
                    │
                    ▼
            ┌──────────────────┐
            │  firmware.zip    │
            │  - main.cpp      │
            │  - sensor driver │
            │  - model_data.h  │
            │  - platformio.ini│
            │  - README.md     │
            └──────────────────┘
```

### UI Structure - Separate Page Design

**Navigation Flow:**

```
Main Application
├── Data Collection Tab
├── Data Preprocessing Tab
├── Model Training Tab (DL/ML)
│   └── [After successful training/export]
│       └── Button: "📦 Deploy to Hardware" ──┐
│                                              │
│  ┌───────────────────────────────────────────┘
│  ▼
├── 🆕 DEPLOYMENT PAGE (New CustomTkinter Window)
│   │
│   ├── Header
│   │   ├── Title: "Hardware Deployment Wizard"
│   │   ├── Model Info: "Deploying: fall_detection_timesnet.onnx"
│   │   └── Back Button: "← Back to Training"
│   │
│   ├── Sidebar (Step Navigator)
│   │   ├── ✅ 1. Platform Selection
│   │   ├── ⚪ 2. Sensor Configuration
│   │   ├── ⚪ 3. Hardware Pins
│   │   ├── ⚪ 4. Output Actions
│   │   └── ⚪ 5. Generate Code
│   │
│   └── Main Content Area
│       └── (Changes based on current step)
│
└── Settings Tab
```

### Detailed UI Design - Step by Step

#### **Step 1: Platform Selection**

**Layout:**
```
┌────────────────────────────────────────────────────────────┐
│  Hardware Deployment Wizard                     [← Back]   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Step 1: Select Target Platform                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                            │
│  Choose the hardware platform for deployment:              │
│                                                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │  ESP32     │  │  Jetson    │  │ Arduino    │          │
│  │  DevKit    │  │  Nano      │  │ Nano 33    │          │
│  │            │  │            │  │ BLE Sense  │          │
│  │  [Image]   │  │  [Image]   │  │  [Image]   │          │
│  │            │  │            │  │            │          │
│  │ ⚡ 240MHz  │  │ 🚀 GPU     │  │ 🔋 Ultra   │          │
│  │ 📶 WiFi/BT │  │ 💪 4GB RAM │  │   Low Power│          │
│  │ 💰 $10     │  │ 💰 $99     │  │ 💰 $33     │          │
│  │            │  │            │  │            │          │
│  │ [SELECT]   │  │ [SELECT]   │  │ [SELECT]   │          │
│  └────────────┘  └────────────┘  └────────────┘          │
│                                                            │
│  ℹ️ Recommended: ESP32 for battery-powered IoT devices    │
│                                                            │
│                              [Next Step →]                 │
└────────────────────────────────────────────────────────────┘
```

**Implementation:**
- `ui/deployment_wizard.py` - New file
- Large clickable cards with platform icons
- Show specs, price, use cases
- Selected card highlights with accent color

---

#### **Step 2: Sensor Configuration**

**Layout:**
```
┌────────────────────────────────────────────────────────────┐
│  Step 2: Configure Sensors                      [← Back]   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                            │
│  Platform: ESP32 DevKit                    [Change]       │
│  Model Input: 3-axis accelerometer (100 samples/window)   │
│                                                            │
│  Select Sensor Type:                                       │
│  ┌────────────────────────────────────────────────────┐   │
│  │ ○ MPU6050 (I2C Accelerometer + Gyroscope)         │   │
│  │   📊 6-axis IMU, 16-bit ADC, ±2g to ±16g range    │   │
│  │   💰 ~$3, widely available                         │   │
│  │                                                    │   │
│  │ ● ADXL345 (I2C/SPI Accelerometer)                 │   │
│  │   📊 3-axis, 13-bit, ±2g to ±16g                  │   │
│  │   💰 ~$5, low power consumption                   │   │
│  │                                                    │   │
│  │ ○ Custom Analog Input                             │   │
│  │   ⚙️ Advanced: Map analog pins to model inputs    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  Sensor Configuration:                                     │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Sample Rate:  [100 Hz ▼]                          │   │
│  │ Sensitivity:  [±4g     ▼]                          │   │
│  │ Axis Mapping: X: Accel-X  Y: Accel-Y  Z: Accel-Z  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  [← Previous]                          [Next Step →]      │
└────────────────────────────────────────────────────────────┘
```

**Implementation:**
- Radio buttons for sensor selection
- Dynamic configuration based on sensor type
- Validation: Check sensor outputs match model inputs
- Show compatibility warnings if mismatch

---

#### **Step 3: Hardware Pins**

**Layout:**
```
┌────────────────────────────────────────────────────────────┐
│  Step 3: Pin Configuration                      [← Back]   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                            │
│  Platform: ESP32 DevKit                                    │
│  Sensor: ADXL345 (I2C Mode)                                │
│                                                            │
│  I2C Configuration:                                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │ SDA Pin:  [GPIO 21 ▼]  (Default: 21)              │   │
│  │ SCL Pin:  [GPIO 22 ▼]  (Default: 22)              │   │
│  │ I2C Addr: [0x53    ▼]  (ADXL345 default)          │   │
│  │ Speed:    [400kHz  ▼]  (Fast mode)                │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  Visual Pinout Reference:                                  │
│  ┌────────────────────────────────────────────────────┐   │
│  │         ESP32 DevKit Pinout                        │   │
│  │                                                    │   │
│  │    3V3 ●─────  ─────● GND                         │   │
│  │    EN  ●─────  ─────● GPIO 23                     │   │
│  │   VP   ●─────  ─────● GPIO 22 (SCL) ← Selected    │   │
│  │   VN   ●─────  ─────● GPIO 21 (SDA) ← Selected    │   │
│  │  [... full pinout diagram ...]                    │   │
│  │                                                    │   │
│  │  💡 Connect sensor VCC to 3V3, GND to GND         │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  [← Previous]                          [Next Step →]      │
└────────────────────────────────────────────────────────────┘
```

**Implementation:**
- Dropdown menus for GPIO selection
- Visual pinout diagram (embedded image or canvas drawing)
- Highlight selected pins on diagram
- Show wiring instructions

---

#### **Step 4: Output Actions**

**Layout:**
```
┌────────────────────────────────────────────────────────────┐
│  Step 4: Configure Output Actions               [← Back]   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                            │
│  Define what happens when model makes predictions:         │
│                                                            │
│  Prediction Classes:                                       │
│  • Class 0: Normal Activity                                │
│  • Class 1: Fall Detected                                  │
│                                                            │
│  ┌─ Actions ──────────────────────────────────────────┐   │
│  │                                                    │   │
│  │  [+ Add Action]                                    │   │
│  │                                                    │   │
│  │  ┌────────────────────────────────────────────┐   │   │
│  │  │ Action 1: LED Indicator               [×]  │   │   │
│  │  ├────────────────────────────────────────────┤   │   │
│  │  │ Type: [LED Control      ▼]             │   │   │
│  │  │ Trigger: [Class 1 (Fall) ▼]               │   │   │
│  │  │ Pin: [GPIO 2 ▼]                           │   │   │
│  │  │ Behavior: [Turn ON ▼]  Duration: [5000ms] │   │   │
│  │  └────────────────────────────────────────────┘   │   │
│  │                                                    │   │
│  │  ┌────────────────────────────────────────────┐   │   │
│  │  │ Action 2: Serial Debug            [×]  │   │   │
│  │  ├────────────────────────────────────────────┤   │   │
│  │  │ Type: [Serial Output    ▼]             │   │   │
│  │  │ Trigger: [All Classes   ▼]                │   │   │
│  │  │ Baud Rate: [115200 ▼]                     │   │   │
│  │  │ Format: [Prediction: {class} ({conf}%)▼]  │   │   │
│  │  └────────────────────────────────────────────┘   │   │
│  │                                                    │   │
│  │  ┌────────────────────────────────────────────┐   │   │
│  │  │ Action 3: WiFi Alert              [×]  │   │   │
│  │  ├────────────────────────────────────────────┤   │   │
│  │  │ Type: [HTTP POST        ▼]             │   │   │
│  │  │ Trigger: [Class 1 (Fall) ▼]               │   │   │
│  │  │ URL: [http://192.168.1.100/alert      ]   │   │   │
│  │  │ WiFi SSID: [MyNetwork]  Pass: [••••••]    │   │   │
│  │  └────────────────────────────────────────────┘   │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  Available Action Types:                                   │
│  • LED Control  • Serial Output  • HTTP/MQTT               │
│  • Buzzer Alert • SD Card Logging • BLE Notification       │
│                                                            │
│  [← Previous]                          [Next Step →]      │
└────────────────────────────────────────────────────────────┘
```

**Implementation:**
- Scrollable frame with action cards
- Add/remove actions dynamically
- Each action has type-specific configuration fields
- Validation: Check GPIO conflicts

---

#### **Step 5: Generate & Download**

**Layout:**
```
┌────────────────────────────────────────────────────────────┐
│  Step 5: Generate Firmware                      [← Back]   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                            │
│  Review Configuration:                                     │
│  ┌────────────────────────────────────────────────────┐   │
│  │ ✓ Platform:   ESP32 DevKit                        │   │
│  │ ✓ Sensor:     ADXL345 (I2C)                       │   │
│  │ ✓ I2C Pins:   SDA=21, SCL=22                      │   │
│  │ ✓ Actions:    3 configured (LED, Serial, WiFi)   │   │
│  │ ✓ Model:      fall_detection_timesnet.onnx       │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  Project Name:                                             │
│  [fall_detection_esp32          ]                          │
│                                                            │
│  Output Options:                                           │
│  ☑ Include README with flash instructions                 │
│  ☑ Include wiring diagram                                 │
│  ☑ Include test/debug sketches                            │
│  ☐ Generate Dockerfile for Jetson (if applicable)         │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │                                                    │   │
│  │           [🚀 Generate Firmware]                   │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ─────────────────── OR ────────────────────               │
│                                                            │
│  [💾 Save Configuration]  (for later use)                 │
│  [📂 Load Configuration]  (from file)                     │
│                                                            │
└────────────────────────────────────────────────────────────┘

After clicking "Generate Firmware":

┌────────────────────────────────────────────────────────────┐
│  🎉 Firmware Generated Successfully!                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                            │
│  Output: fall_detection_esp32.zip (2.3 MB)                 │
│                                                            │
│  Package Contents:                                         │
│  📁 fall_detection_esp32/                                  │
│     ├── platformio.ini                                     │
│     ├── src/                                               │
│     │   ├── main.cpp                   (Generated)         │
│     │   ├── model_runner.cpp           (Generated)         │
│     │   ├── model_runner.h                                 │
│     │   └── model_data.h               (Your model)        │
│     ├── lib/                                               │
│     │   ├── ADXL345/                   (Sensor driver)     │
│     │   └── WiFiManager/               (WiFi helper)       │
│     ├── docs/                                              │
│     │   ├── README.md                  (Flash guide)       │
│     │   ├── wiring_diagram.png                             │
│     │   └── troubleshooting.md                             │
│     └── test/                                              │
│         └── sensor_test.cpp            (Debug tool)        │
│                                                            │
│  Next Steps:                                               │
│  1. Extract the ZIP file                                   │
│  2. Install PlatformIO IDE                                 │
│  3. Open the project folder                                │
│  4. Connect your ESP32 via USB                             │
│  5. Click "Upload" in PlatformIO                           │
│                                                            │
│  [📥 Download ZIP]    [📋 View README]                     │
│                                                            │
│  [🔄 Generate Another]  [✓ Done - Back to Main]           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Implementation:**
- Summary review screen
- Progress spinner during generation
- Success screen with file details
- Direct download or open folder option
- One-click deployment guide

---

### File Structure Generated

**For ESP32 Example:**
```
fall_detection_esp32/
├── platformio.ini                 # Build configuration
│   [env:esp32dev]
│   platform = espressif32
│   board = esp32dev
│   framework = arduino
│   lib_deps =
│       adafruit/Adafruit ADXL345@^1.3.2
│       WiFi
│
├── src/
│   ├── main.cpp                   # GENERATED from template
│   │   // Auto-generated by CiRA FutureEdge Studio
│   │   // DO NOT EDIT - Regenerate from GUI if needed
│   │   #include "sensor_manager.h"
│   │   #include "model_runner.h"
│   │   // ... full implementation
│   │
│   ├── sensor_manager.cpp         # GENERATED - sensor abstraction
│   ├── sensor_manager.h
│   ├── model_runner.cpp           # GENERATED - inference wrapper
│   ├── model_runner.h
│   ├── config.h                   # GENERATED - user configuration
│   └── model_data.h               # EXPORTED - trained model
│
├── lib/
│   └── (PlatformIO auto-downloads dependencies)
│
├── docs/
│   ├── README.md                  # GENERATED - flash instructions
│   ├── wiring_diagram.png         # GENERATED - pin connections
│   └── troubleshooting.md         # TEMPLATE - common issues
│
├── test/
│   └── sensor_test.cpp            # TEMPLATE - sensor debug tool
│
└── deployment_config.json         # SAVED - for regeneration
    {
        "platform": "esp32",
        "sensor": "adxl345",
        "pins": {"sda": 21, "scl": 22},
        "actions": [...]
    }
```

---

## Phase 3: Visual Pipeline Builder

**Timeline:** 6-8 weeks (complex UI)
**Deliverable:** Drag-and-drop deployment pipeline editor

### Architecture Overview

```
Visual Pipeline Builder UI
┌──────────────────────────────────────────────────────────────┐
│  Deployment Pipeline: fall_detection_system      [← Back]    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Block Library          Pipeline Canvas                     │
│  ┌──────────────┐     ┌─────────────────────────────────┐  │
│  │ 📡 INPUTS    │     │                                 │  │
│  │  • MPU6050   │     │  [MPU6050] → [Normalize]       │  │
│  │  • ADXL345   │     │      ↓                          │  │
│  │  • Analog    │     │  [Window(100)] → [TimesNet]    │  │
│  │              │     │                     ↓            │  │
│  │ 🔄 PROCESS   │     │                  [Router]       │  │
│  │  • Normalize │     │                   ╱  ╲          │  │
│  │  • Window    │     │                  ↙    ↘         │  │
│  │  • FFT       │     │             [LED]    [WiFi]     │  │
│  │  • Filter    │     │                                 │  │
│  │              │     │  Click blocks to configure      │  │
│  │ 🧠 MODELS    │     │  Drag to connect                │  │
│  │  • TimesNet  │     │                                 │  │
│  │  • Trained   │     └─────────────────────────────────┘  │
│  │                                                          │
│  │ 📤 OUTPUTS   │     Block Properties                     │
│  │  • LED       │     ┌─────────────────────────────────┐  │
│  │  • Serial    │     │ Selected: TimesNet Model        │  │
│  │  • WiFi      │     │ ───────────────────────────────  │  │
│  │  • MQTT      │     │ Model File: fall_detect.onnx    │  │
│  │  • Buzzer    │     │ Input Shape: (100, 3)           │  │
│  │  • Display   │     │ Output Classes: 2               │  │
│  └──────────────┘     │ Inference Mode: [CPU ▼]         │  │
│                       │                                 │  │
│                       │ ☑ Enable debug logging          │  │
│                       │ Latency Budget: [50ms]          │  │
│                       └─────────────────────────────────┘  │
│                                                              │
│  [Validate Pipeline]  [Simulate]  [Generate Code]           │
└──────────────────────────────────────────────────────────────┘
```

### Key Features

#### 1. **Block-Based Programming**
- Drag blocks from library to canvas
- Connect blocks with arrows (data flow)
- Each block has configurable properties
- Type checking: 3-axis sensor → model expecting 3 channels

#### 2. **Visual Data Flow**
- See data shape at each stage
- Highlight incompatible connections in red
- Show processing latency estimates

#### 3. **Real-Time Validation**
- Check for disconnected blocks
- Verify model input/output compatibility
- Warn about resource constraints (RAM, CPU)

#### 4. **Pipeline Simulation**
- Upload sample CSV data
- "Play" pipeline to see data flow
- Visualize intermediate outputs
- Catch bugs before deployment

#### 5. **Code Generation from Graph**
- Traverse pipeline graph
- Generate optimized C++ code
- Each block has code template
- Smart optimizations (fuse operations)

### Block Types

#### **Input Blocks**
```python
blocks = {
    'MPU6050': {
        'outputs': {'accel': (3,), 'gyro': (3,)},
        'config': ['i2c_addr', 'sample_rate', 'sensitivity'],
        'code_template': 'templates/blocks/mpu6050.cpp.jinja2'
    },
    'ADXL345': {
        'outputs': {'accel': (3,)},
        'config': ['i2c_addr', 'sample_rate', 'range'],
        'code_template': 'templates/blocks/adxl345.cpp.jinja2'
    },
    'AnalogInput': {
        'outputs': {'value': (1,)},
        'config': ['pin', 'sample_rate', 'bit_resolution'],
        'code_template': 'templates/blocks/analog.cpp.jinja2'
    }
}
```

#### **Processing Blocks**
```python
processing_blocks = {
    'Normalize': {
        'inputs': {'data': ('any',)},
        'outputs': {'normalized': ('same',)},
        'config': ['method', 'mean', 'std'],
        'code_template': 'templates/blocks/normalize.cpp.jinja2'
    },
    'SlidingWindow': {
        'inputs': {'stream': ('any',)},
        'outputs': {'window': ('window_size', 'input_dim')},
        'config': ['window_size', 'stride'],
        'code_template': 'templates/blocks/window.cpp.jinja2'
    },
    'FFT': {
        'inputs': {'signal': ('n',)},
        'outputs': {'spectrum': ('n/2+1',)},
        'config': ['window_type'],
        'code_template': 'templates/blocks/fft.cpp.jinja2'
    }
}
```

#### **Model Blocks**
```python
model_blocks = {
    'TimesNet': {
        'inputs': {'data': ('seq_len', 'n_features')},
        'outputs': {'logits': ('n_classes',)},
        'config': ['model_file', 'inference_mode'],
        'code_template': 'templates/blocks/timesnet.cpp.jinja2'
    },
    'CustomModel': {
        'inputs': {'data': 'configurable'},
        'outputs': {'output': 'configurable'},
        'config': ['onnx_file', 'input_shape', 'output_shape'],
        'code_template': 'templates/blocks/onnx.cpp.jinja2'
    }
}
```

#### **Output Blocks**
```python
output_blocks = {
    'LED': {
        'inputs': {'trigger': ('1',)},
        'config': ['pin', 'duration', 'trigger_value'],
        'code_template': 'templates/blocks/led.cpp.jinja2'
    },
    'Serial': {
        'inputs': {'data': ('any',)},
        'config': ['baud_rate', 'format_string'],
        'code_template': 'templates/blocks/serial.cpp.jinja2'
    },
    'WiFiPOST': {
        'inputs': {'data': ('any',)},
        'config': ['ssid', 'password', 'url', 'format'],
        'code_template': 'templates/blocks/wifi_post.cpp.jinja2'
    },
    'Router': {
        'inputs': {'value': (1,)},
        'outputs': {'out1': (1,), 'out2': (1,), 'out3': (1,)},
        'config': ['conditions'],  # Route based on value
        'code_template': 'templates/blocks/router.cpp.jinja2'
    }
}
```

### UI Implementation

**File:** `ui/pipeline_builder.py`

**Key Components:**

1. **Canvas Widget**
   - CustomTkinter canvas or tkinter Canvas
   - Drag-drop functionality
   - Connection drawing (arrows)
   - Zoom/pan for large pipelines

2. **Block Library Panel**
   - Scrollable frame with block categories
   - Drag to instantiate on canvas
   - Search/filter blocks

3. **Properties Panel**
   - Shows selected block configuration
   - Dynamic form based on block type
   - Real-time validation

4. **Toolbar**
   - Validate, Simulate, Generate buttons
   - Save/Load pipeline files (.cira format)
   - Undo/Redo

### Code Generation Engine

**File:** `core/deployment/pipeline_compiler.py`

```python
class PipelineCompiler:
    def __init__(self, pipeline_graph):
        self.graph = pipeline_graph
        self.blocks = []

    def validate(self) -> List[str]:
        """Validate pipeline for errors."""
        errors = []

        # Check for disconnected blocks
        # Verify type compatibility
        # Check for cycles
        # Validate resource usage

        return errors

    def compile(self, platform: str) -> str:
        """Generate C++ code from pipeline graph."""

        # 1. Topological sort of blocks
        sorted_blocks = self._topological_sort()

        # 2. Generate includes
        includes = self._generate_includes(sorted_blocks)

        # 3. Generate global variables
        globals_code = self._generate_globals(sorted_blocks)

        # 4. Generate setup() function
        setup_code = self._generate_setup(sorted_blocks)

        # 5. Generate loop() function
        loop_code = self._generate_loop(sorted_blocks)

        # 6. Assemble final code
        template = self.env.get_template('main.cpp.jinja2')
        return template.render(
            includes=includes,
            globals=globals_code,
            setup=setup_code,
            loop=loop_code
        )

    def _generate_loop(self, blocks):
        """Generate main loop code by traversing graph."""
        code = []

        for block in blocks:
            # Load block template
            template = self.env.get_template(block.code_template)

            # Render with block configuration
            block_code = template.render(
                block_id=block.id,
                config=block.config,
                inputs=block.input_connections,
                outputs=block.output_connections
            )

            code.append(block_code)

        return '\n'.join(code)
```

### Pipeline Save Format

**File:** `deployment_pipelines/fall_detection.cira` (JSON)

```json
{
    "pipeline_name": "fall_detection_system",
    "platform": "esp32",
    "version": "1.0.0",
    "blocks": [
        {
            "id": "sensor_1",
            "type": "MPU6050",
            "position": {"x": 100, "y": 200},
            "config": {
                "i2c_addr": "0x68",
                "sample_rate": 100,
                "sensitivity": "±4g"
            },
            "outputs": ["accel", "gyro"]
        },
        {
            "id": "normalize_1",
            "type": "Normalize",
            "position": {"x": 300, "y": 200},
            "config": {
                "method": "z-score",
                "mean": [0.0, 0.0, 9.81],
                "std": [2.5, 2.5, 2.5]
            }
        },
        {
            "id": "window_1",
            "type": "SlidingWindow",
            "position": {"x": 500, "y": 200},
            "config": {
                "window_size": 100,
                "stride": 20
            }
        },
        {
            "id": "model_1",
            "type": "TimesNet",
            "position": {"x": 700, "y": 200},
            "config": {
                "model_file": "models/fall_detect.onnx",
                "inference_mode": "cpu"
            }
        },
        {
            "id": "router_1",
            "type": "Router",
            "position": {"x": 900, "y": 200},
            "config": {
                "conditions": [
                    {"output": "out1", "when": "value == 0"},
                    {"output": "out2", "when": "value == 1"}
                ]
            }
        },
        {
            "id": "led_1",
            "type": "LED",
            "position": {"x": 1100, "y": 150},
            "config": {
                "pin": 2,
                "duration": 5000,
                "trigger_value": 1
            }
        },
        {
            "id": "wifi_1",
            "type": "WiFiPOST",
            "position": {"x": 1100, "y": 250},
            "config": {
                "ssid": "MyNetwork",
                "password": "********",
                "url": "http://192.168.1.100/alert",
                "format": "json"
            }
        }
    ],
    "connections": [
        {
            "from": {"block": "sensor_1", "output": "accel"},
            "to": {"block": "normalize_1", "input": "data"}
        },
        {
            "from": {"block": "normalize_1", "output": "normalized"},
            "to": {"block": "window_1", "input": "stream"}
        },
        {
            "from": {"block": "window_1", "output": "window"},
            "to": {"block": "model_1", "input": "data"}
        },
        {
            "from": {"block": "model_1", "output": "logits"},
            "to": {"block": "router_1", "input": "value"}
        },
        {
            "from": {"block": "router_1", "output": "out2"},
            "to": {"block": "led_1", "input": "trigger"}
        },
        {
            "from": {"block": "router_1", "output": "out2"},
            "to": {"block": "wifi_1", "input": "data"}
        }
    ]
}
```

---

## Integration with Existing UI

### Navigation Flow

**Option A: Tab-Based**
```python
# In main_window.py
self.tabview = ctk.CTkTabview(self)
self.tabview.add("Data Collection")
self.tabview.add("Preprocessing")
self.tabview.add("Model Training")
self.tabview.add("🚀 Deployment")  # NEW TAB

# Load deployment page when tab selected
if self.tabview.get() == "🚀 Deployment":
    self._load_deployment_page()
```

**Option B: Separate Window (RECOMMENDED)**
```python
# In model_panel.py (DL tab)
def _create_export_section(self):
    # ... existing ONNX/DSP export buttons ...

    # NEW: Deploy button
    deploy_btn = ctk.CTkButton(
        export_frame,
        text="📦 Deploy to Hardware",
        command=self._open_deployment_wizard,
        fg_color="#FF6B35",  # Orange highlight
        height=40
    )
    deploy_btn.pack(pady=10)

def _open_deployment_wizard(self):
    """Open deployment wizard in new window."""
    from ui.deployment_wizard import DeploymentWizard

    # Get current trained model
    model_info = {
        'name': self.current_model_name,
        'path': self.model_path,
        'input_shape': (100, 3),
        'output_classes': 2
    }

    # Open wizard window
    wizard = DeploymentWizard(self, model_info)
    wizard.mainloop()
```

**Back Navigation:**
```python
# In deployment_wizard.py
def _create_header(self):
    header_frame = ctk.CTkFrame(self)

    # Back button
    back_btn = ctk.CTkButton(
        header_frame,
        text="← Back to Training",
        command=self._go_back
    )

def _go_back(self):
    """Return to main application."""
    self.destroy()  # Close wizard window
    # Main window still open in background
```

---

## Implementation Checklist

### Phase 1: Template-Based Generation

**Week 1: Foundation**
- [ ] Create `ui/deployment_wizard.py` (separate window)
- [ ] Create `core/deployment/code_generator.py`
- [ ] Create `core/deployment/platform_config.py` (platform specs)
- [ ] Create template directory structure: `templates/{esp32,jetson,nano33}/`

**Week 2: Platform Templates**
- [ ] ESP32 templates (main.cpp, sensor drivers, platformio.ini)
- [ ] Jetson Nano templates (Python/C++ with TensorRT)
- [ ] Arduino Nano 33 templates (TinyML, built-in sensors)

**Week 3: Sensor Library**
- [ ] MPU6050 driver template
- [ ] ADXL345 driver template
- [ ] Built-in sensor abstractions (Nano 33)
- [ ] Generic analog input template

**Week 4: UI & Integration**
- [ ] Step 1: Platform selection UI
- [ ] Step 2: Sensor configuration UI
- [ ] Step 3: Pin configuration UI (with pinout diagrams)
- [ ] Step 4: Actions configuration UI
- [ ] Step 5: Generation & download UI
- [ ] Add "Deploy to Hardware" button to model_panel.py
- [ ] Testing: Generate sample projects for all 3 platforms

### Phase 3: Visual Pipeline Builder

**Week 1-2: Canvas Infrastructure**
- [ ] Create `ui/pipeline_builder.py` (separate window)
- [ ] Implement drag-drop canvas (tkinter Canvas or custom)
- [ ] Block rendering (rectangles, icons, labels)
- [ ] Connection drawing (arrows between blocks)
- [ ] Zoom/pan controls

**Week 3-4: Block System**
- [ ] Define block type definitions (JSON/Python dataclasses)
- [ ] Block library panel UI
- [ ] Properties panel (dynamic forms)
- [ ] Block instantiation on canvas
- [ ] Connection validation (type checking)

**Week 5: Pipeline Logic**
- [ ] Graph data structure (nodes, edges)
- [ ] Topological sort (execution order)
- [ ] Validation engine (disconnected, cycles, types)
- [ ] Save/Load pipeline files (.cira JSON format)

**Week 6: Code Generation**
- [ ] Create `core/deployment/pipeline_compiler.py`
- [ ] Block code templates (Jinja2)
- [ ] Code generator (traverse graph, render templates)
- [ ] Optimization passes (fuse operations, reduce copies)

**Week 7: Simulation**
- [ ] Pipeline simulation engine
- [ ] CSV data upload for testing
- [ ] Step-through debugger
- [ ] Visualize intermediate outputs

**Week 8: Integration & Polish**
- [ ] Connect pipeline builder to deployment wizard
- [ ] Add "Advanced: Pipeline Builder" option in wizard
- [ ] Testing with complex pipelines
- [ ] Documentation and examples

---

## File Organization

```
D:\CiRA FES\
├── ui/
│   ├── deployment_wizard.py        # NEW - Phase 1 wizard (5 steps)
│   ├── pipeline_builder.py         # NEW - Phase 3 visual editor
│   └── model_panel.py              # MODIFIED - add deploy button
│
├── core/
│   └── deployment/
│       ├── __init__.py
│       ├── code_generator.py       # NEW - Template renderer
│       ├── pipeline_compiler.py    # NEW - Graph → Code compiler
│       ├── platform_config.py      # NEW - Platform specs
│       └── validators.py           # NEW - Pipeline validation
│
├── templates/                      # NEW - Code generation templates
│   ├── esp32/
│   │   ├── main.cpp.jinja2
│   │   ├── platformio.ini.jinja2
│   │   ├── README.md.jinja2
│   │   └── blocks/                 # Phase 3 block templates
│   │       ├── mpu6050.cpp.jinja2
│   │       ├── normalize.cpp.jinja2
│   │       └── ...
│   ├── jetson/
│   │   ├── main.py.jinja2
│   │   ├── Dockerfile.jinja2
│   │   └── blocks/
│   └── nano33/
│       ├── main.cpp.jinja2
│       └── blocks/
│
├── assets/                         # NEW - UI resources
│   ├── platform_icons/
│   │   ├── esp32.png
│   │   ├── jetson.png
│   │   └── nano33.png
│   └── pinout_diagrams/
│       ├── esp32_pinout.png
│       ├── jetson_nano_pinout.png
│       └── nano33_pinout.png
│
├── deployment_pipelines/           # NEW - Saved pipelines
│   ├── examples/
│   │   ├── fall_detection.cira
│   │   ├── gesture_recognition.cira
│   │   └── anomaly_detection.cira
│   └── user_pipelines/
│
└── docs/
    ├── DEPLOYMENT_WIZARD_GUIDE.md
    ├── PIPELINE_BUILDER_GUIDE.md
    └── SUPPORTED_PLATFORMS.md
```

---

## Success Metrics

### Phase 1 Success Criteria:
- ✅ User can go from trained model → flashable firmware in < 5 minutes
- ✅ Generated code compiles without errors on all 3 platforms
- ✅ At least 80% of users successfully deploy (telemetry)
- ✅ No C++ knowledge required for basic deployment

### Phase 3 Success Criteria:
- ✅ Users can create custom pipelines without writing code
- ✅ Pipeline validation catches 90%+ of errors before generation
- ✅ Advanced users adopt pipeline builder for complex workflows
- ✅ Community shares reusable pipeline templates

---

## Risk Mitigation

### Risk 1: Platform SDKs Change
**Mitigation:**
- Pin exact SDK versions in templates
- CI/CD pipeline tests templates weekly
- Maintain version matrix (template v1.0 → ESP-IDF v4.4)

### Risk 2: User Hardware Variations
**Mitigation:**
- Generate debug/test sketches with every deployment
- Include serial diagnostics in generated code
- FAQ: "My sensor doesn't work" troubleshooting

### Risk 3: Pipeline Builder Complexity
**Mitigation:**
- Ship Phase 1 first (proven value before complex feature)
- Provide example pipelines (copy-paste-modify workflow)
- Fallback: Users can still use Phase 1 wizard

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 1** | 3-4 weeks | Template-based firmware generation for ESP32, Jetson, Nano33 |
| **Phase 3** | 6-8 weeks | Visual pipeline builder with drag-drop, simulation, code generation |
| **Total** | **10-12 weeks** | Complete deployment solution ready for product launch |

**Critical Path:** Phase 1 must complete before Phase 3 begins (Phase 3 builds on Phase 1 templates).

---

## Next Steps

When ready to implement:

1. **Create detailed UI mockups** (Figma or hand-drawn sketches)
2. **Build Phase 1 Step 1** (Platform selection screen) as prototype
3. **Test template generation** with single platform (ESP32)
4. **Iterate based on user feedback**
5. **Complete Phase 1** before starting Phase 3

**Recommendation:** Start with **Phase 1 ESP32 only** as MVP (1-2 weeks), validate with users, then expand to Jetson/Nano33.

---

**Document Owner:** CiRA FutureEdge Studio Development Team
**Last Updated:** 2025-12-15
**Status:** Implementation plan ready - awaiting execution approval
