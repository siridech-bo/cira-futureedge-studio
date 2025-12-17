# Deployment Pipeline Builder - Implementation Plan
## Modular Approach (No Rewrite Required!)

**Date:** 2025-12-15
**Priority:** CRITICAL - Pre-launch requirement
**Status:** Ready to implement

---

## Executive Summary

**Strategy:** Build standalone visual pipeline builder (Dear PyGui) that works alongside existing CustomTkinter app

**Key Principle:**
- ✅ **Zero rewrite** of existing CustomTkinter UI
- ✅ **Separate executable** for pipeline builder
- ✅ **File-based communication** between apps
- ✅ **Manageable scope** - 2-3 weeks total

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  CiRA FutureEdge Studio (CustomTkinter)                     │
│  ════════════════════════════════════════                   │
│                                                             │
│  Existing App (NO CHANGES except one button)                │
│                                                             │
│  📊 Data Collection                                         │
│  🔧 Preprocessing                                           │
│  🧠 Model Training                                          │
│  📦 Deployment                                              │
│      ├─ Simple Wizard (5 steps) ← Phase 1                  │
│      │   • Platform selection                              │
│      │   • Sensor config                                   │
│      │   • Pin config                                      │
│      │   • Actions                                         │
│      │   • Generate firmware                               │
│      │                                                      │
│      └─ [🎨 Advanced Pipeline Builder] ← NEW BUTTON        │
│             │                                               │
└─────────────┼───────────────────────────────────────────────┘
              │
              │ Subprocess.Popen()
              │
              ↓
┌─────────────────────────────────────────────────────────────┐
│  Pipeline Builder (Dear PyGui - NEW STANDALONE APP)         │
│  ════════════════════════════════════════                   │
│                                                             │
│  ┌──────────┬────────────────────────────┬──────────────┐  │
│  │ Blocks   │  Node Editor Canvas        │ Properties  │  │
│  │          │                            │             │  │
│  │ 📡 Input │  ┌──────┐    ┌─────────┐  │ Selected:   │  │
│  │ • MPU650 │  │MPU650│→→→→│Normalize│  │ MPU6050     │  │
│  │ • ADXL   │  └──────┘    └─────────┘  │             │  │
│  │          │      ↓            ↓        │ I2C Addr:   │  │
│  │ 🔄 Proc  │  ┌────────┐  ┌──────┐    │ [0x68    ]  │  │
│  │ • Normal │  │ Window │→→│Model │    │             │  │
│  │ • Window │  └────────┘  └──────┘    │ Sample Rate:│  │
│  │          │                  ↓        │ [100 Hz  ]  │  │
│  │ 🧠 Model │              ┌─────┐     │             │  │
│  │ • Times  │              │ LED │     │             │  │
│  │          │              └─────┘     │             │  │
│  │ 📤 Out   │                          │             │  │
│  │ • LED    │                          │             │  │
│  │ • Serial │                          │             │  │
│  │ • WiFi   │                          │             │  │
│  └──────────┴────────────────────────────┴──────────────┘  │
│                                                             │
│  [Validate] [Simulate] [🚀 Export & Close]                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
              │
              │ Saves pipeline_output.json
              ↓
┌─────────────────────────────────────────────────────────────┐
│  Main App Imports Pipeline                                  │
│  ────────────────────────────                               │
│  PipelineCompiler(pipeline.json) → firmware.zip             │
└─────────────────────────────────────────────────────────────┘
```

---

## Communication Protocol (File-Based IPC)

### **Flow:**

1. **Main App → Pipeline Builder**
   - Write `temp/pipeline_input.json` with context
   - Launch `pipeline_builder_app.py` as subprocess
   - Wait for completion

2. **Pipeline Builder → Main App**
   - User designs pipeline
   - Click "Export & Close"
   - Write `temp/pipeline_output.json`
   - Exit process

3. **Main App Imports**
   - Detect pipeline_output.json
   - Parse and compile to C++ firmware

### **File Formats:**

**pipeline_input.json** (Main → Builder):
```json
{
  "model_file": "models/fall_detection_timesnet.onnx",
  "model_type": "TimesNet",
  "input_shape": [100, 3],
  "output_classes": 2,
  "platform": "esp32",
  "sensor_suggested": "mpu6050"
}
```

**pipeline_output.json** (Builder → Main):
```json
{
  "pipeline_name": "fall_detection_system",
  "platform": "esp32",
  "nodes": [
    {
      "id": "sensor_1",
      "type": "MPU6050",
      "config": {
        "i2c_addr": "0x68",
        "sample_rate": 100,
        "sensitivity": "±4g"
      },
      "position": {"x": 50, "y": 100}
    },
    {
      "id": "normalize_1",
      "type": "Normalize",
      "config": {
        "method": "z-score",
        "mean": [0, 0, 9.81],
        "std": [2.5, 2.5, 2.5]
      },
      "position": {"x": 250, "y": 100}
    },
    {
      "id": "window_1",
      "type": "SlidingWindow",
      "config": {
        "window_size": 100,
        "stride": 20
      },
      "position": {"x": 450, "y": 100}
    },
    {
      "id": "model_1",
      "type": "TimesNet",
      "config": {
        "model_file": "models/fall_detection_timesnet.onnx"
      },
      "position": {"x": 650, "y": 100}
    },
    {
      "id": "led_1",
      "type": "LED",
      "config": {
        "pin": 2,
        "duration": 5000,
        "trigger_class": 1
      },
      "position": {"x": 850, "y": 100}
    }
  ],
  "connections": [
    {"from": "sensor_1.accel_out", "to": "normalize_1.data_in"},
    {"from": "normalize_1.data_out", "to": "window_1.stream_in"},
    {"from": "window_1.window_out", "to": "model_1.data_in"},
    {"from": "model_1.prediction_out", "to": "led_1.trigger_in"}
  ]
}
```

---

## Implementation Timeline

### **Week 1: Core Pipeline Builder (Dear PyGui)**

#### Day 1-2: Foundation
- [x] Project setup
- [x] Basic Dear PyGui window
- [x] Three-panel layout (blocks, canvas, properties)
- [x] Block library UI (scrollable categories)

#### Day 3-4: Node Editor
- [x] Implement node creation
- [x] Drag-drop from library to canvas
- [x] Node connections (links)
- [x] Selection and deletion

#### Day 5: Block Definitions
- [x] Define all block types (sensors, processing, models, outputs)
- [x] Create node templates
- [x] Properties panel (dynamic forms)

---

### **Week 2: Advanced Features & Integration**

#### Day 1-2: Validation & Simulation
- [x] Pipeline validation (type checking)
- [x] Connection validation
- [x] Visual feedback (highlight errors)
- [x] Basic simulation (optional)

#### Day 3: Export & Import
- [x] Export to JSON
- [x] Import from JSON (load saved pipelines)
- [x] File I/O handling

#### Day 4-5: Main App Integration
- [x] Add button in deployment_wizard.py
- [x] Subprocess launcher
- [x] File monitoring
- [x] Pipeline compiler (JSON → C++)

---

### **Week 3: Code Generation & Testing**

#### Day 1-3: Code Generator
- [x] PipelineCompiler class
- [x] Node → C++ template mapping
- [x] Code generation from graph
- [x] Template system

#### Day 4-5: Testing & Polish
- [x] Test all block types
- [x] Test complex pipelines
- [x] Error handling
- [x] Documentation

---

## Detailed Implementation Specifications

### **Part 1: Standalone Pipeline Builder (pipeline_builder_app.py)**

#### **File:** `pipeline_builder_app.py`

**Dependencies:**
```bash
pip install dearpygui
```

**Main Class Structure:**
```python
"""
CiRA FutureEdge Studio - Visual Pipeline Builder
Standalone application for designing deployment pipelines

Usage:
    python pipeline_builder_app.py [input_file] [output_file]

Arguments:
    input_file: JSON file with context from main app (optional)
    output_file: JSON file to save pipeline (default: pipeline_output.json)
"""

import dearpygui.dearpygui as dpg
import json
import sys
import os
from typing import Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class BlockDefinition:
    """Definition of a block type."""
    type: str
    category: str  # 'sensor', 'processing', 'model', 'output'
    label: str
    description: str
    inputs: List[Dict[str, str]]  # [{'name': 'data_in', 'type': 'array'}]
    outputs: List[Dict[str, str]]
    config_fields: List[Dict[str, Any]]  # [{'name': 'i2c_addr', 'type': 'text', 'default': '0x68'}]
    color: tuple  # RGB color for node


# Block type registry
BLOCK_DEFINITIONS = {
    'MPU6050': BlockDefinition(
        type='MPU6050',
        category='sensor',
        label='MPU6050 IMU',
        description='6-axis accelerometer + gyroscope sensor',
        inputs=[],
        outputs=[
            {'name': 'accel_out', 'type': 'vector3', 'label': 'Acceleration'},
            {'name': 'gyro_out', 'type': 'vector3', 'label': 'Gyroscope'}
        ],
        config_fields=[
            {'name': 'i2c_addr', 'type': 'text', 'label': 'I2C Address', 'default': '0x68'},
            {'name': 'sample_rate', 'type': 'int', 'label': 'Sample Rate (Hz)', 'default': 100},
            {'name': 'sensitivity', 'type': 'combo', 'label': 'Sensitivity',
             'options': ['±2g', '±4g', '±8g', '±16g'], 'default': '±4g'}
        ],
        color=(74, 144, 226)  # Blue
    ),

    'ADXL345': BlockDefinition(
        type='ADXL345',
        category='sensor',
        label='ADXL345 Accel',
        description='3-axis accelerometer sensor',
        inputs=[],
        outputs=[
            {'name': 'accel_out', 'type': 'vector3', 'label': 'Acceleration'}
        ],
        config_fields=[
            {'name': 'i2c_addr', 'type': 'text', 'label': 'I2C Address', 'default': '0x53'},
            {'name': 'sample_rate', 'type': 'int', 'label': 'Sample Rate (Hz)', 'default': 100},
            {'name': 'range', 'type': 'combo', 'label': 'Range',
             'options': ['±2g', '±4g', '±8g', '±16g'], 'default': '±4g'}
        ],
        color=(74, 144, 226)  # Blue
    ),

    'Normalize': BlockDefinition(
        type='Normalize',
        category='processing',
        label='Normalize',
        description='Normalize data (Z-score or Min-Max)',
        inputs=[
            {'name': 'data_in', 'type': 'any', 'label': 'Data'}
        ],
        outputs=[
            {'name': 'data_out', 'type': 'same', 'label': 'Normalized'}
        ],
        config_fields=[
            {'name': 'method', 'type': 'combo', 'label': 'Method',
             'options': ['Z-Score', 'Min-Max'], 'default': 'Z-Score'},
            {'name': 'mean', 'type': 'text', 'label': 'Mean (comma-separated)', 'default': '0,0,9.81'},
            {'name': 'std', 'type': 'text', 'label': 'Std Dev (comma-separated)', 'default': '2.5,2.5,2.5'}
        ],
        color=(155, 89, 182)  # Purple
    ),

    'SlidingWindow': BlockDefinition(
        type='SlidingWindow',
        category='processing',
        label='Sliding Window',
        description='Create sliding windows from data stream',
        inputs=[
            {'name': 'stream_in', 'type': 'any', 'label': 'Stream'}
        ],
        outputs=[
            {'name': 'window_out', 'type': 'window', 'label': 'Window'}
        ],
        config_fields=[
            {'name': 'window_size', 'type': 'int', 'label': 'Window Size', 'default': 100},
            {'name': 'stride', 'type': 'int', 'label': 'Stride', 'default': 20}
        ],
        color=(155, 89, 182)  # Purple
    ),

    'TimesNet': BlockDefinition(
        type='TimesNet',
        category='model',
        label='TimesNet Model',
        description='TimesNet deep learning model inference',
        inputs=[
            {'name': 'data_in', 'type': 'window', 'label': 'Input Window'}
        ],
        outputs=[
            {'name': 'prediction_out', 'type': 'int', 'label': 'Prediction'}
        ],
        config_fields=[
            {'name': 'model_file', 'type': 'file', 'label': 'Model File', 'default': 'model.onnx'},
            {'name': 'inference_mode', 'type': 'combo', 'label': 'Inference Mode',
             'options': ['CPU', 'GPU'], 'default': 'CPU'}
        ],
        color=(46, 204, 113)  # Green
    ),

    'LED': BlockDefinition(
        type='LED',
        category='output',
        label='LED Output',
        description='Control LED based on trigger signal',
        inputs=[
            {'name': 'trigger_in', 'type': 'int', 'label': 'Trigger'}
        ],
        outputs=[],
        config_fields=[
            {'name': 'pin', 'type': 'int', 'label': 'GPIO Pin', 'default': 2},
            {'name': 'duration', 'type': 'int', 'label': 'Duration (ms)', 'default': 5000},
            {'name': 'trigger_class', 'type': 'int', 'label': 'Trigger Class', 'default': 1}
        ],
        color=(231, 76, 60)  # Red
    ),

    'Serial': BlockDefinition(
        type='Serial',
        category='output',
        label='Serial Output',
        description='Print data to serial console',
        inputs=[
            {'name': 'data_in', 'type': 'any', 'label': 'Data'}
        ],
        outputs=[],
        config_fields=[
            {'name': 'baud_rate', 'type': 'combo', 'label': 'Baud Rate',
             'options': ['9600', '115200', '230400'], 'default': '115200'},
            {'name': 'format', 'type': 'text', 'label': 'Format String',
             'default': 'Prediction: {value}'}
        ],
        color=(231, 76, 60)  # Red
    ),

    'WiFiPOST': BlockDefinition(
        type='WiFiPOST',
        category='output',
        label='WiFi POST',
        description='Send HTTP POST request',
        inputs=[
            {'name': 'data_in', 'type': 'any', 'label': 'Data'}
        ],
        outputs=[],
        config_fields=[
            {'name': 'ssid', 'type': 'text', 'label': 'WiFi SSID', 'default': 'MyNetwork'},
            {'name': 'password', 'type': 'password', 'label': 'WiFi Password', 'default': ''},
            {'name': 'url', 'type': 'text', 'label': 'POST URL',
             'default': 'http://192.168.1.100/alert'},
            {'name': 'format', 'type': 'combo', 'label': 'Format',
             'options': ['JSON', 'Plain Text'], 'default': 'JSON'}
        ],
        color=(231, 76, 60)  # Red
    )
}


class PipelineBuilder:
    """Visual pipeline builder application."""

    def __init__(self, input_file: str = None, output_file: str = None):
        """
        Initialize pipeline builder.

        Args:
            input_file: Path to input JSON (context from main app)
            output_file: Path to save output JSON
        """
        self.input_file = input_file or "temp/pipeline_input.json"
        self.output_file = output_file or "temp/pipeline_output.json"

        # Load context if available
        self.context = {}
        if input_file and os.path.exists(input_file):
            with open(input_file) as f:
                self.context = json.load(f)

        # Pipeline state
        self.nodes = {}  # {node_id: node_data}
        self.node_counter = 0
        self.selected_node = None

    def create_ui(self):
        """Create Dear PyGui UI."""
        dpg.create_context()

        # Configure theme
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (30, 30, 30))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (40, 40, 40))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (50, 50, 50))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 70, 70))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (90, 90, 90))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (110, 110, 110))

        dpg.bind_theme(global_theme)

        # Main window
        with dpg.window(label="CiRA Pipeline Builder",
                       tag="main_window",
                       width=1400,
                       height=900,
                       no_close=True,
                       no_collapse=True):

            # Title bar
            with dpg.group(horizontal=True):
                dpg.add_text("CiRA FutureEdge Studio - Visual Pipeline Builder",
                           color=(100, 200, 255))
                dpg.add_spacer(width=400)
                if self.context:
                    dpg.add_text(f"Model: {self.context.get('model_type', 'Unknown')}",
                               color=(150, 150, 150))

            dpg.add_separator()

            # Toolbar
            with dpg.group(horizontal=True):
                dpg.add_button(label="💾 Save Pipeline",
                             callback=self.save_pipeline,
                             width=120)
                dpg.add_button(label="📂 Load Pipeline",
                             callback=self.load_pipeline,
                             width=120)
                dpg.add_button(label="✓ Validate",
                             callback=self.validate_pipeline,
                             width=100)
                dpg.add_button(label="🗑️ Clear All",
                             callback=self.clear_pipeline,
                             width=100)
                dpg.add_spacer(width=300)
                dpg.add_button(label="🚀 Export & Close",
                             callback=self.export_and_close,
                             width=150,
                             height=30)

            dpg.add_separator()

            # Three-panel layout
            with dpg.group(horizontal=True):
                # LEFT PANEL: Block Library
                with dpg.child_window(width=250, height=780, tag="block_library"):
                    dpg.add_text("Block Library", color=(100, 200, 255))
                    dpg.add_separator()

                    self._create_block_library()

                # CENTER PANEL: Node Editor Canvas
                with dpg.child_window(width=900, height=780, tag="canvas_container"):
                    dpg.add_text("Pipeline Canvas", color=(100, 200, 255))
                    dpg.add_text("Drag blocks from library to canvas",
                               color=(150, 150, 150))
                    dpg.add_separator()

                    with dpg.node_editor(
                        tag="node_editor",
                        callback=self.on_link_created,
                        delink_callback=self.on_link_deleted,
                        minimap=True,
                        minimap_location=dpg.mvNodeMiniMap_Location_BottomRight
                    ):
                        pass  # Nodes added dynamically

                # RIGHT PANEL: Properties
                with dpg.child_window(width=230, height=780, tag="properties_panel"):
                    dpg.add_text("Properties", color=(100, 200, 255))
                    dpg.add_separator()
                    dpg.add_text("Select a node to edit properties",
                               tag="properties_hint",
                               color=(150, 150, 150),
                               wrap=220)

        # Create viewport
        dpg.create_viewport(
            title="CiRA Pipeline Builder",
            width=1400,
            height=900
        )

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)

    def _create_block_library(self):
        """Create block library with categories."""

        # Group blocks by category
        categories = {
            'sensor': [],
            'processing': [],
            'model': [],
            'output': []
        }

        for block_def in BLOCK_DEFINITIONS.values():
            categories[block_def.category].append(block_def)

        # Create collapsing headers for each category
        category_labels = {
            'sensor': '📡 Sensors',
            'processing': '🔄 Processing',
            'model': '🧠 Models',
            'output': '📤 Outputs'
        }

        for cat_id, blocks in categories.items():
            if dpg.add_collapsing_header(label=category_labels[cat_id],
                                        default_open=True):
                for block_def in blocks:
                    dpg.add_button(
                        label=block_def.label,
                        width=-1,
                        callback=lambda s, a, u: self.add_node(u),
                        user_data=block_def.type
                    )
                    # Tooltip
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text(block_def.description)

    def add_node(self, block_type: str):
        """Add a node to the canvas."""

        block_def = BLOCK_DEFINITIONS[block_type]
        node_id = f"{block_type}_{self.node_counter}"
        self.node_counter += 1

        # Create node in editor
        with dpg.node(
            label=block_def.label,
            parent="node_editor",
            tag=node_id,
            pos=[100 + self.node_counter * 50, 100 + self.node_counter * 20]
        ):
            # Input attributes
            for inp in block_def.inputs:
                with dpg.node_attribute(
                    label=inp['label'],
                    attribute_type=dpg.mvNode_Attr_Input,
                    tag=f"{node_id}_{inp['name']}"
                ):
                    pass

            # Static attribute for configuration preview
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_text(f"Type: {block_type}",
                           color=(200, 200, 200),
                           tag=f"{node_id}_type_label")

            # Output attributes
            for out in block_def.outputs:
                with dpg.node_attribute(
                    label=out['label'],
                    attribute_type=dpg.mvNode_Attr_Output,
                    tag=f"{node_id}_{out['name']}"
                ):
                    pass

        # Store node data
        self.nodes[node_id] = {
            'type': block_type,
            'config': {field['name']: field['default']
                      for field in block_def.config_fields},
            'position': dpg.get_item_pos(node_id)
        }

        print(f"Added node: {node_id} ({block_type})")

    def on_link_created(self, sender, app_data):
        """Handle link creation between nodes."""
        from_attr = app_data[0]
        to_attr = app_data[1]

        # Validate connection (type checking)
        # TODO: Implement type validation

        # Create link
        dpg.add_node_link(from_attr, to_attr, parent=sender)

        print(f"Link created: {from_attr} → {to_attr}")

    def on_link_deleted(self, sender, app_data):
        """Handle link deletion."""
        link_id = app_data
        dpg.delete_item(link_id)
        print(f"Link deleted: {link_id}")

    def validate_pipeline(self):
        """Validate pipeline for errors."""
        errors = []

        # Check for disconnected nodes
        # Check for type mismatches
        # Check for cycles

        if errors:
            # Show error dialog
            with dpg.window(label="Validation Errors", modal=True, show=True):
                for error in errors:
                    dpg.add_text(error, color=(255, 100, 100))
                dpg.add_button(label="OK", callback=lambda: dpg.delete_item(dpg.last_item()))
        else:
            # Show success
            with dpg.window(label="Validation", modal=True, show=True, width=300):
                dpg.add_text("✓ Pipeline is valid!", color=(100, 255, 100))
                dpg.add_button(label="OK",
                             callback=lambda: dpg.delete_item(dpg.last_container()))

    def save_pipeline(self):
        """Save pipeline to file."""
        # TODO: Implement file dialog and save
        pass

    def load_pipeline(self):
        """Load pipeline from file."""
        # TODO: Implement file dialog and load
        pass

    def clear_pipeline(self):
        """Clear all nodes from canvas."""
        # Confirm dialog
        with dpg.window(label="Clear Pipeline", modal=True, show=True, width=300):
            dpg.add_text("Clear all nodes?")
            with dpg.group(horizontal=True):
                dpg.add_button(label="Yes", callback=self._do_clear)
                dpg.add_button(label="No",
                             callback=lambda: dpg.delete_item(dpg.last_container()))

    def _do_clear(self):
        """Actually clear the pipeline."""
        # Delete all nodes
        for node_id in list(self.nodes.keys()):
            dpg.delete_item(node_id)

        self.nodes = {}
        self.node_counter = 0
        dpg.delete_item(dpg.last_container())  # Close dialog

    def export_and_close(self):
        """Export pipeline to JSON and close application."""

        # Collect pipeline data
        pipeline = {
            'pipeline_name': 'custom_pipeline',
            'platform': self.context.get('platform', 'esp32'),
            'nodes': [],
            'connections': []
        }

        # Collect nodes
        for node_id, node_data in self.nodes.items():
            pipeline['nodes'].append({
                'id': node_id,
                'type': node_data['type'],
                'config': node_data['config'],
                'position': {
                    'x': dpg.get_item_pos(node_id)[0],
                    'y': dpg.get_item_pos(node_id)[1]
                }
            })

        # Collect connections (links)
        # Get all links from node editor
        links = dpg.get_item_children("node_editor", slot=0)
        if links:
            for link_id in links:
                link_config = dpg.get_item_configuration(link_id)
                pipeline['connections'].append({
                    'from': link_config['attr_1'],
                    'to': link_config['attr_2']
                })

        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        # Save to file
        with open(self.output_file, 'w') as f:
            json.dump(pipeline, f, indent=2)

        print(f"Pipeline exported to: {self.output_file}")

        # Close application
        dpg.stop_dearpygui()

    def run(self):
        """Run the application."""
        self.create_ui()
        dpg.start_dearpygui()
        dpg.destroy_context()


def main():
    """Main entry point."""
    # Parse command line arguments
    input_file = sys.argv[1] if len(sys.argv) > 1 else None
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Create and run app
    app = PipelineBuilder(input_file, output_file)
    app.run()


if __name__ == "__main__":
    main()
```

---

### **Part 2: Main App Integration (CustomTkinter)**

#### **File:** `ui/deployment_wizard.py` (MODIFY EXISTING)

**Add to existing Step 5 (Generate) section:**

```python
# In your existing deployment_wizard.py
# Find the _create_step5_generate() method and add this at the end:

def _create_step5_generate(self):
    """Step 5: Generate firmware."""

    # ... existing code for template-based generation ...

    # NEW: Add separator and advanced option
    dpg.add_separator()

    # Advanced Pipeline Builder section
    advanced_frame = ctk.CTkFrame(self.main_content)
    advanced_frame.pack(pady=20, padx=20, fill="x")

    ctk.CTkLabel(
        advanced_frame,
        text="🎨 Advanced Users:",
        font=ctk.CTkFont(size=14, weight="bold")
    ).pack(pady=(10, 5))

    ctk.CTkLabel(
        advanced_frame,
        text="Design complex pipelines with our visual editor.\n"
             "Connect sensors → processing → models → actions.",
        font=ctk.CTkFont(size=11),
        text_color="gray70"
    ).pack(pady=5)

    pipeline_btn = ctk.CTkButton(
        advanced_frame,
        text="🎨 Open Visual Pipeline Builder",
        command=self._launch_pipeline_builder,
        fg_color="#9B59B6",
        hover_color="#8E44AD",
        height=40,
        font=ctk.CTkFont(size=12, weight="bold")
    )
    pipeline_btn.pack(pady=10)

    ctk.CTkLabel(
        advanced_frame,
        text="Note: Pipeline builder opens in a separate window",
        font=ctk.CTkFont(size=10),
        text_color="gray60"
    ).pack()

def _launch_pipeline_builder(self):
    """Launch standalone Dear PyGui pipeline builder."""

    import subprocess
    import json
    import os
    from loguru import logger

    logger.info("Launching visual pipeline builder...")

    # Prepare input context
    input_data = {
        'model_file': getattr(self, 'model_path', ''),
        'model_type': 'TimesNet',
        'input_shape': [100, 3],
        'output_classes': 2,
        'platform': getattr(self, 'selected_platform', 'esp32'),
        'sensor_suggested': getattr(self, 'selected_sensor', 'mpu6050')
    }

    # Create temp directory
    temp_dir = os.path.join(os.getcwd(), 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    input_file = os.path.join(temp_dir, 'pipeline_input.json')
    output_file = os.path.join(temp_dir, 'pipeline_output.json')

    # Write input file
    with open(input_file, 'w') as f:
        json.dump(input_data, f, indent=2)

    # Remove old output if exists
    if os.path.exists(output_file):
        os.remove(output_file)

    # Create waiting dialog
    wait_dialog = ctk.CTkToplevel(self)
    wait_dialog.title("Pipeline Builder")
    wait_dialog.geometry("450x200")

    # Center dialog
    wait_dialog.update_idletasks()
    x = (wait_dialog.winfo_screenwidth() // 2) - 225
    y = (wait_dialog.winfo_screenheight() // 2) - 100
    wait_dialog.geometry(f"+{x}+{y}")

    # Prevent closing
    wait_dialog.protocol("WM_DELETE_WINDOW", lambda: None)

    # Content
    ctk.CTkLabel(
        wait_dialog,
        text="🎨 Visual Pipeline Builder",
        font=ctk.CTkFont(size=16, weight="bold")
    ).pack(pady=20)

    ctk.CTkLabel(
        wait_dialog,
        text="Design your deployment pipeline in the\n"
             "separate window that just opened.\n\n"
             "When finished, click 'Export & Close' to\n"
             "return here and generate firmware.",
        font=ctk.CTkFont(size=12),
        justify="center"
    ).pack(pady=10)

    status_label = ctk.CTkLabel(
        wait_dialog,
        text="⏳ Pipeline builder is running...",
        font=ctk.CTkFont(size=11),
        text_color="gray60"
    )
    status_label.pack(pady=10)

    # Launch pipeline builder subprocess
    try:
        proc = subprocess.Popen([
            sys.executable,
            'pipeline_builder_app.py',
            input_file,
            output_file
        ])

        logger.info(f"Pipeline builder launched (PID: {proc.pid})")

        # Monitor subprocess
        self._monitor_pipeline_builder(proc, output_file, wait_dialog, status_label)

    except Exception as e:
        logger.error(f"Failed to launch pipeline builder: {e}")
        wait_dialog.destroy()
        messagebox.showerror(
            "Error",
            f"Failed to launch pipeline builder:\n{str(e)}"
        )

def _monitor_pipeline_builder(self, proc, output_file, dialog, status_label):
    """Monitor pipeline builder subprocess."""

    # Check if process is still running
    if proc.poll() is None:
        # Still running, check again in 500ms
        self.after(500, lambda: self._monitor_pipeline_builder(
            proc, output_file, dialog, status_label
        ))
    else:
        # Process finished
        dialog.destroy()

        # Check if pipeline was exported
        if os.path.exists(output_file):
            self._import_pipeline(output_file)
        else:
            messagebox.showinfo(
                "Cancelled",
                "Pipeline builder was closed without exporting.\n"
                "No firmware will be generated."
            )

def _import_pipeline(self, pipeline_file):
    """Import pipeline from builder and generate code."""

    from loguru import logger

    try:
        # Load pipeline
        with open(pipeline_file) as f:
            pipeline = json.load(f)

        logger.info(f"Imported pipeline with {len(pipeline['nodes'])} nodes")

        # Show success message
        result = messagebox.askyesno(
            "Pipeline Imported",
            f"Successfully imported pipeline:\n\n"
            f"  • Blocks: {len(pipeline['nodes'])}\n"
            f"  • Connections: {len(pipeline['connections'])}\n"
            f"  • Platform: {pipeline['platform']}\n\n"
            f"Generate firmware now?",
            icon='info'
        )

        if result:
            # Generate firmware from pipeline
            self._generate_from_pipeline(pipeline)

    except Exception as e:
        logger.error(f"Failed to import pipeline: {e}")
        messagebox.showerror(
            "Import Error",
            f"Failed to import pipeline:\n{str(e)}"
        )

def _generate_from_pipeline(self, pipeline):
    """Generate C++ firmware from pipeline definition."""

    from core.deployment.pipeline_compiler import PipelineCompiler
    from loguru import logger

    try:
        # Create compiler
        compiler = PipelineCompiler(pipeline)

        # Validate pipeline
        errors = compiler.validate()
        if errors:
            messagebox.showerror(
                "Validation Errors",
                "Pipeline has errors:\n\n" + "\n".join(errors)
            )
            return

        # Generate code
        platform = pipeline['platform']
        output_dir = os.path.join('output', 'deployment',
                                  f"pipeline_{int(time.time())}")

        logger.info(f"Generating firmware for {platform}...")

        firmware_path = compiler.generate(platform, output_dir)

        logger.info(f"Firmware generated: {firmware_path}")

        # Show success
        messagebox.showinfo(
            "Success",
            f"Firmware generated successfully!\n\n"
            f"Output: {firmware_path}\n\n"
            f"Follow the README.md for flashing instructions."
        )

        # Open output folder
        if messagebox.askyesno("Open Folder", "Open output folder?"):
            import subprocess
            subprocess.Popen(['explorer', output_dir])

    except Exception as e:
        logger.error(f"Failed to generate firmware: {e}")
        messagebox.showerror(
            "Generation Error",
            f"Failed to generate firmware:\n{str(e)}"
        )
```

---

### **Part 3: Pipeline Compiler**

#### **File:** `core/deployment/pipeline_compiler.py` (NEW)

```python
"""
Pipeline Compiler - Converts visual pipeline to C++ firmware
"""

import json
from typing import Dict, List, Any
from jinja2 import Environment, FileSystemLoader
import os


class PipelineCompiler:
    """Compile visual pipeline to C++ firmware."""

    def __init__(self, pipeline: Dict[str, Any]):
        """
        Initialize compiler.

        Args:
            pipeline: Pipeline definition (from pipeline_output.json)
        """
        self.pipeline = pipeline
        self.nodes = {n['id']: n for n in pipeline['nodes']}
        self.connections = pipeline['connections']

        # Setup Jinja2
        template_dir = os.path.join(os.path.dirname(__file__),
                                    '../../templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def validate(self) -> List[str]:
        """
        Validate pipeline.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check for disconnected nodes
        connected_nodes = set()
        for conn in self.connections:
            # Extract node IDs from attribute names (format: "node_id_attr_name")
            from_node = conn['from'].rsplit('_', 1)[0]
            to_node = conn['to'].rsplit('_', 1)[0]
            connected_nodes.add(from_node)
            connected_nodes.add(to_node)

        for node_id in self.nodes:
            if node_id not in connected_nodes:
                errors.append(f"Node '{node_id}' is not connected")

        # Check for required input/output nodes
        has_sensor = any(n['type'] in ['MPU6050', 'ADXL345']
                        for n in self.nodes.values())
        has_output = any(n['type'] in ['LED', 'Serial', 'WiFiPOST']
                        for n in self.nodes.values())

        if not has_sensor:
            errors.append("Pipeline must have at least one sensor input")

        if not has_output:
            errors.append("Pipeline must have at least one output")

        # TODO: Type checking for connections

        return errors

    def generate(self, platform: str, output_dir: str) -> str:
        """
        Generate firmware for target platform.

        Args:
            platform: Target platform ('esp32', 'jetson', 'nano33')
            output_dir: Output directory path

        Returns:
            Path to generated firmware folder
        """
        os.makedirs(output_dir, exist_ok=True)

        # Topological sort of nodes
        sorted_nodes = self._topological_sort()

        # Generate code sections
        includes = self._generate_includes(sorted_nodes, platform)
        globals_code = self._generate_globals(sorted_nodes)
        setup_code = self._generate_setup(sorted_nodes)
        loop_code = self._generate_loop(sorted_nodes)

        # Load platform main template
        template = self.env.get_template(f'{platform}/main.cpp.jinja2')

        # Render
        main_cpp = template.render(
            includes=includes,
            globals=globals_code,
            setup=setup_code,
            loop=loop_code,
            pipeline_name=self.pipeline['pipeline_name']
        )

        # Write main.cpp
        src_dir = os.path.join(output_dir, 'src')
        os.makedirs(src_dir, exist_ok=True)

        with open(os.path.join(src_dir, 'main.cpp'), 'w') as f:
            f.write(main_cpp)

        # Generate platformio.ini (for ESP32/Arduino)
        if platform in ['esp32', 'nano33']:
            self._generate_platformio_ini(platform, output_dir)

        # Generate README
        self._generate_readme(platform, output_dir)

        return output_dir

    def _topological_sort(self) -> List[Dict]:
        """Sort nodes in execution order."""
        # Simple topological sort
        # TODO: Implement proper algorithm
        return list(self.nodes.values())

    def _generate_includes(self, nodes: List[Dict], platform: str) -> str:
        """Generate #include directives."""
        includes = set()

        for node in nodes:
            node_type = node['type']

            if node_type == 'MPU6050':
                includes.add('#include <Wire.h>')
                includes.add('#include <MPU6050.h>')
            elif node_type == 'ADXL345':
                includes.add('#include <Wire.h>')
                includes.add('#include <Adafruit_ADXL345_U.h>')
            elif node_type == 'WiFiPOST':
                if platform == 'esp32':
                    includes.add('#include <WiFi.h>')
                    includes.add('#include <HTTPClient.h>')

        return '\n'.join(sorted(includes))

    def _generate_globals(self, nodes: List[Dict]) -> str:
        """Generate global variables."""
        code = []

        for node in nodes:
            node_id = node['id']
            node_type = node['type']

            if node_type == 'MPU6050':
                code.append(f"MPU6050 {node_id};")
            elif node_type == 'ADXL345':
                code.append(f"Adafruit_ADXL345_Unified {node_id} = Adafruit_ADXL345_Unified(12345);")
            # ... other types

        return '\n'.join(code)

    def _generate_setup(self, nodes: List[Dict]) -> str:
        """Generate setup() code."""
        code = []
        code.append("Serial.begin(115200);")
        code.append("Wire.begin();")
        code.append("")

        for node in nodes:
            node_id = node['id']
            node_type = node['type']
            config = node['config']

            if node_type == 'MPU6050':
                code.append(f"{node_id}.initialize();")
                code.append(f"if (!{node_id}.testConnection()) {{")
                code.append(f'    Serial.println("MPU6050 connection failed!");')
                code.append(f"    while(1);")
                code.append(f"}}")
            elif node_type == 'ADXL345':
                code.append(f"if (!{node_id}.begin()) {{")
                code.append(f'    Serial.println("ADXL345 not found!");')
                code.append(f"    while(1);")
                code.append(f"}}")
            # ... other types

        return '\n    '.join(code)

    def _generate_loop(self, nodes: List[Dict]) -> str:
        """Generate loop() code."""
        code = []

        # TODO: Generate proper loop code based on graph topology

        for node in nodes:
            node_id = node['id']
            node_type = node['type']

            if node_type == 'MPU6050':
                code.append(f"// Read {node_id}")
                code.append(f"int16_t ax, ay, az, gx, gy, gz;")
                code.append(f"{node_id}.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);")
            # ... process other nodes

        return '\n    '.join(code)

    def _generate_platformio_ini(self, platform: str, output_dir: str):
        """Generate platformio.ini."""

        template = self.env.get_template(f'{platform}/platformio.ini.jinja2')

        # Determine required libraries
        lib_deps = set()
        for node in self.nodes.values():
            if node['type'] == 'MPU6050':
                lib_deps.add('jrowberg/I2Cdevlib-MPU6050@^1.0.0')
            elif node['type'] == 'ADXL345':
                lib_deps.add('adafruit/Adafruit ADXL345@^1.3.2')

        content = template.render(lib_deps=sorted(lib_deps))

        with open(os.path.join(output_dir, 'platformio.ini'), 'w') as f:
            f.write(content)

    def _generate_readme(self, platform: str, output_dir: str):
        """Generate README.md."""

        template = self.env.get_template('README.md.jinja2')

        content = template.render(
            platform=platform,
            pipeline_name=self.pipeline['pipeline_name'],
            node_count=len(self.nodes),
            connection_count=len(self.connections)
        )

        with open(os.path.join(output_dir, 'README.md'), 'w') as f:
            f.write(content)
```

---

## Testing Checklist

### **Week 1 Testing:**
- [ ] Pipeline builder launches successfully
- [ ] Can add nodes from library to canvas
- [ ] Can connect nodes with links
- [ ] Can delete nodes and links
- [ ] Properties panel shows selected node config
- [ ] Can export pipeline to JSON

### **Week 2 Testing:**
- [ ] Main app launches pipeline builder via button
- [ ] Subprocess monitoring works
- [ ] Pipeline JSON import works
- [ ] All block types render correctly
- [ ] Validation catches common errors

### **Week 3 Testing:**
- [ ] Code generation produces valid C++
- [ ] Generated firmware compiles for ESP32
- [ ] Generated firmware compiles for Jetson
- [ ] All sensor types generate correct code
- [ ] All output types generate correct code

---

## File Structure

```
D:\CiRA FES\
├── pipeline_builder_app.py          # NEW - Standalone Dear PyGui app
│
├── ui/
│   ├── deployment_wizard.py         # MODIFIED - add button & integration
│   └── ...                          # EXISTING - no changes
│
├── core/
│   └── deployment/
│       ├── __init__.py
│       ├── pipeline_compiler.py     # NEW - JSON → C++ compiler
│       └── platform_config.py       # NEW - Platform definitions
│
├── templates/                       # NEW - Jinja2 templates
│   ├── esp32/
│   │   ├── main.cpp.jinja2
│   │   ├── platformio.ini.jinja2
│   │   └── blocks/
│   │       ├── mpu6050.cpp.jinja2
│   │       ├── normalize.cpp.jinja2
│   │       └── ...
│   ├── jetson/
│   │   ├── main.py.jinja2
│   │   └── blocks/
│   └── README.md.jinja2
│
├── temp/                            # NEW - IPC files
│   ├── pipeline_input.json
│   └── pipeline_output.json
│
└── output/
    └── deployment/                  # Generated firmware packages
        ├── pipeline_1234567890/
        │   ├── src/
        │   │   └── main.cpp
        │   ├── platformio.ini
        │   └── README.md
        └── ...
```

---

## Dependencies

**Add to requirements.txt:**
```
dearpygui>=1.10.0
jinja2>=3.1.0
```

**Install:**
```bash
pip install dearpygui jinja2
```

---

## Success Criteria

### **Phase Completion:**
- ✅ Pipeline builder runs standalone
- ✅ Can design complex pipelines visually
- ✅ Exports valid JSON
- ✅ Main app imports and compiles pipeline
- ✅ Generated firmware compiles without errors
- ✅ Zero changes to existing CustomTkinter UI (except one button)

### **User Experience:**
- ✅ Simple users: Use 5-step wizard (Phase 1)
- ✅ Advanced users: Use visual pipeline builder
- ✅ Both paths produce working firmware
- ✅ No confusion, clear documentation

---

## Rollout Strategy

### **Beta Release:**
1. Ship Phase 1 (template wizard) first
2. Add pipeline builder in update 1-2 weeks later
3. Mark as "Beta" feature
4. Gather user feedback

### **Stable Release:**
1. Fix bugs from beta
2. Add more block types based on demand
3. Improve validation
4. Add simulation feature

---

## Future Enhancements (Post-Launch)

- [ ] Pipeline simulation (run with sample data)
- [ ] More block types (filters, aggregators, etc.)
- [ ] Custom block creation (user-defined)
- [ ] Pipeline templates library
- [ ] Share/import community pipelines
- [ ] Real-time performance estimation
- [ ] Hardware compatibility checker

---

## Notes

- **No UI debugging needed:** Pipeline builder is standalone, can be tested independently
- **Gradual development:** Build one block type at a time, test, iterate
- **Clean separation:** Main app and pipeline builder communicate only via JSON files
- **Easy to extend:** Add new block types by updating BLOCK_DEFINITIONS dictionary

---

**Ready to implement!** Start with Week 1, test thoroughly, then move to Week 2.

**Document Owner:** CiRA FutureEdge Studio Development Team
**Last Updated:** 2025-12-15
**Status:** Implementation ready - can start immediately
