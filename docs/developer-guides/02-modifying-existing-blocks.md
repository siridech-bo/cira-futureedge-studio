# Modifying Existing Blocks

This guide explains how to modify existing blocks, specifically focusing on **adding new output pins** (like the `class_name` pin we added to TimesNet).

## Overview

When modifying an existing block, you need to update **THREE locations**:
1. **Block Runtime** - The actual C++ implementation
2. **Pipeline Builder Node Definition** - The GUI representation
3. **Pipeline Builder Legacy Registry** (if used) - Old-style registry

---

## Example: Adding `class_name` Output to TimesNet

This real example shows how we added a string output pin to the TimesNet block.

---

## Step 1: Update Block Runtime (Jetson)

### 1.1 Update Block Header

**File**: `cira-block-runtime/blocks/ai/timesnet_onnx/timesnet_onnx_block.hpp`

```cpp
class TimesNetOnnxBlock : public IBlock {
private:
    // Configuration
    std::string model_path_;
    int num_classes_;
    int seq_len_;
    int num_channels_;
    std::vector<std::string> class_names_;  // ← ADD THIS

    // Input/Output
    std::vector<float> features_in_;
    int prediction_out_;
    float confidence_out_;
    // string class_name_out_;  ← Not needed, we compute on-the-fly
```

**Key Points:**
- Add storage for configuration data (`class_names_` vector)
- No need to store the output value if computed from `prediction_out_`

---

### 1.2 Update GetOutputPins()

**File**: `cira-block-runtime/blocks/ai/timesnet_onnx/timesnet_onnx_block.cpp`

```cpp
std::vector<Pin> TimesNetOnnxBlock::GetOutputPins() const {
    return {
        Pin("prediction_out", "int", false),
        Pin("class_name", "string", false),      // ← ADD THIS LINE
        Pin("confidence_out", "float", false),
        Pin("ready", "bool", false),
        Pin("running", "bool", false)
    };
}
```

**Key Points:**
- Add new pin with correct type: `"string"`, `"float"`, `"int"`, `"bool"`, `"array"`
- Order doesn't matter functionally, but keep it logical

---

### 1.3 Parse Configuration in Initialize()

**File**: `cira-block-runtime/blocks/ai/timesnet_onnx/timesnet_onnx_block.cpp`

Add **#include <sstream>** at the top if not already present:

```cpp
#include "timesnet_onnx_block.hpp"
#include <iostream>
#include <sstream>      // ← ADD THIS
#include <algorithm>
#include <numeric>
#include <cmath>
```

Then in `Initialize()`:

```cpp
bool TimesNetOnnxBlock::Initialize(const BlockConfig& config) {
    // ... existing config parsing ...

    // NEW: Parse class names
    if (config.find("class_names") != config.end()) {
        std::string class_names_str = config.at("class_names");

        // Parse comma-separated class names
        std::stringstream ss(class_names_str);
        std::string class_name;
        while (std::getline(ss, class_name, ',')) {
            // Trim whitespace
            class_name.erase(0, class_name.find_first_not_of(" \t"));
            class_name.erase(class_name.find_last_not_of(" \t") + 1);
            class_names_.push_back(class_name);
        }
    }

    std::cout << "  Class Names: " << class_names_.size() << " loaded" << std::endl;

    // ... rest of initialization ...
}
```

**Key Points:**
- Parse comma-separated values: `"idle,shake,snake,updown"`
- Trim whitespace from each value
- Store in member variable for later use

---

### 1.4 Implement GetOutput()

**File**: `cira-block-runtime/blocks/ai/timesnet_onnx/timesnet_onnx_block.cpp`

```cpp
BlockValue TimesNetOnnxBlock::GetOutput(const std::string& pin_name) const {
    if (pin_name == "prediction_out") {
        return prediction_out_;
    }
    else if (pin_name == "class_name") {
        // NEW: Return class name based on prediction_out index
        if (prediction_out_ >= 0 && prediction_out_ < static_cast<int>(class_names_.size())) {
            return class_names_[prediction_out_];
        }
        return std::string("");  // Return empty string if invalid
    }
    else if (pin_name == "confidence_out") {
        return confidence_out_;
    }
    // ... other pins ...

    return 0.0f;
}
```

**Key Points:**
- Check array bounds before accessing `class_names_[index]`
- Return appropriate default value for the type (empty string for string type)
- Use `std::string("")` to return BlockValue as string type

---

### 1.5 Build Runtime

```bash
cd cira-block-runtime/build
cmake --build . --config Release

# Verify compilation
ls -lh blocks/ai/timesnet_onnx/timesnet-v1.2.0.so
```

---

## Step 2: Update Pipeline Builder Node Definition

### 2.1 Update ExecutableNode Class

**File**: `pipeline_builder/include/nodes/timesnet_model_node.hpp`

```cpp
class TimesNetModelNode : public ExecutableNode {
public:
    TimesNetModelNode()
        : ExecutableNode(
            "processing.model.timesnet",
            "TimesNet Model",
            "AI model for time-series classification and prediction",
            NodeCategory::Processing,
            InterfaceType::None,
            PlatformType::JetsonNano,
            "🧠"
        )
    {
        // Define pins (MUST MATCH RUNTIME!)
        AddPin(PinConfig("features_in", "array", true));
        AddPin(PinConfig("prediction_out", "int", false));
        AddPin(PinConfig("class_name", "string", false));      // ← ADD THIS
        AddPin(PinConfig("confidence_out", "float", false));
        AddPin(PinConfig("ready", "bool", false));
        AddPin(PinConfig("running", "bool", false));

        // Default configuration
        SetDefaultConfig("model_path", "model.onnx");
        SetDefaultConfig("num_classes", "5");                   // ← ADD THIS
        SetDefaultConfig("seq_len", "100");                     // ← ADD THIS
        SetDefaultConfig("input_channels", "3");                // ← ADD THIS
        SetDefaultConfig("class_names", "idle,shake,snake,updown,circle");  // ← ADD THIS
        SetDefaultConfig("batch_size", "1");
        SetDefaultConfig("use_tensorrt", "false");

        // Block system metadata
        SetBlockInfo(
            "timesnet",
            "1.2.0",
            "onnx-runtime",
            false
        );
    }

    // ... rest of class ...
};
```

**Key Points:**
- Pin definitions MUST match runtime exactly
- Add default config values for new parameters
- Keep pin order logical but consistent

---

### 2.2 Update Legacy Node Registry (If Used)

**File**: `pipeline_builder/src/core/node_registry.cpp`

```cpp
void NodeRegistry::InitializeDefaultNodes() {
    // ... other nodes ...

    // TimesNet Model
    RegisterNodeType({
        "TimesNet",
        "TimesNet Model",
        "Deep learning classifier (ONNX/TensorRT)",
        NodeCategory::Processing,
        InterfaceType::None,
        PlatformType::JetsonNano,
        {
            PinConfig("features_in", "array", true),
            PinConfig("prediction_out", "int", false),
            PinConfig("class_name", "string", false),           // ← ADD THIS
            PinConfig("confidence_out", "float", false),
            PinConfig("ready", "bool", false),
            PinConfig("running", "bool", false)
        },
        {
            {"model_path", "model.onnx"},
            {"num_classes", "5"},                               // ← ADD THIS
            {"seq_len", "100"},                                 // ← ADD THIS
            {"input_channels", "3"},                            // ← ADD THIS
            {"class_names", "idle,shake,snake,updown,circle"},  // ← ADD THIS
            {"use_tensorrt", "false"},
            {"batch_size", "1"}
        },
        "🧠"
    });
}
```

---

### 2.3 Rebuild Pipeline Builder

```bash
cd pipeline_builder/build
cmake --build . --config Release
```

---

## Step 3: Deploy and Test

### 3.1 Deploy Runtime to Jetson

Option A: Use "Setup Device" (full recompile)
Option B: Use "Update Runtime" (incremental)

```
Pipeline Builder → Deploy → Setup Device
OR
Pipeline Builder → Deploy → Update Runtime
```

### 3.2 Update Pipeline

**IMPORTANT**: Existing nodes in saved pipelines have OLD pin definitions cached!

**Solution**: Delete and re-add the node
1. Open your pipeline
2. Select the TimesNet node
3. Delete it (Del key)
4. Drag a fresh TimesNet from block library
5. Reconnect wires
6. **The new node will have the `class_name` pin!**

### 3.3 Wire the New Pin

1. Connect `class_name` output to a Text Display widget
2. Or connect to HTTP POST / MQTT Publisher for monitoring
3. Save and Deploy

### 3.4 Verify on Jetson

```bash
# Check runtime logs
ssh user@jetson_ip
tail -f /home/user/cira_projects/cira-runtime/runtime.log

# Look for initialization output:
# [TimesNet ONNX] Initializing...
#   Model Path: model.onnx
#   Classes: 5
#   Seq Len: 100
#   Channels: 3
#   Class Names: 5 loaded      ← Should see this
```

---

## Common Modifications

### Adding an Input Pin

```cpp
// Runtime: GetInputPins()
std::vector<Pin> GetInputPins() const {
    return {
        Pin("existing_input", "float", true),
        Pin("new_input", "bool", true)      // ← Add this
    };
}

// Runtime: SetInput()
void SetInput(const std::string& pin_name, const BlockValue& value) {
    if (pin_name == "existing_input") {
        existing_value_ = std::get<float>(value);
    }
    else if (pin_name == "new_input") {
        new_input_value_ = std::get<bool>(value);  // ← Add this
    }
}

// Pipeline Builder: Node constructor
AddPin(PinConfig("new_input", "bool", true));
```

### Adding a Configuration Parameter

```cpp
// Runtime: Initialize()
if (config.find("new_param") != config.end()) {
    new_param_ = std::stoi(config.at("new_param"));
}

// Pipeline Builder: Node constructor
SetDefaultConfig("new_param", "42");
```

### Changing Pin Type

**WARNING**: This is a breaking change!

1. Update runtime pin type: `Pin("my_pin", "NEW_TYPE", false)`
2. Update Pipeline Builder: `AddPin(PinConfig("my_pin", "NEW_TYPE", false))`
3. Update any existing pipelines (delete old nodes, add new ones)
4. Increment block version: `1.0.0` → `1.1.0`

---

## Checklist for Modifying Blocks

- [ ] Update block header (.hpp) with new member variables
- [ ] Update `GetOutputPins()` or `GetInputPins()`
- [ ] Implement `GetOutput()` or update `SetInput()`
- [ ] Parse new config parameters in `Initialize()`
- [ ] Add required #includes (e.g., `<sstream>` for string parsing)
- [ ] Rebuild runtime on Jetson
- [ ] Update ExecutableNode in Pipeline Builder
- [ ] Update Legacy NodeRegistry (if used)
- [ ] Rebuild Pipeline Builder
- [ ] **Delete and re-add nodes** in existing pipelines
- [ ] Test on Jetson
- [ ] Update block version if breaking changes

---

## Troubleshooting

### Problem: New pin doesn't appear in Pipeline Builder

**Solution:**
1. Check if pin is added in **both** node definitions:
   - `timesnet_model_node.hpp` (ExecutableNode)
   - `node_registry.cpp` (NodeRegistry) if used
2. Rebuild Pipeline Builder
3. Restart application
4. **Delete old node and add fresh one**

### Problem: Runtime crashes with "bad_variant_access"

**Cause**: Type mismatch between pin declaration and GetOutput/SetInput

**Solution:**
```cpp
// If pin type is "string", return string:
return std::string("value");

// If pin type is "float":
return 0.0f;

// If pin type is "int":
return 0;

// If pin type is "array":
return std::vector<float>{};
```

### Problem: Config parameter not loaded

**Solution:** Check config parsing in `Initialize()`:
```cpp
if (config.find("param_name") != config.end()) {
    param_ = config.at("param_name");  // For string
    // OR
    param_ = std::stoi(config.at("param_name"));  // For int
    // OR
    param_ = std::stof(config.at("param_name"));  // For float
}
```

---

## Version Management

When to increment version:

- **Patch (1.0.0 → 1.0.1)**: Bug fixes, no API changes
- **Minor (1.0.0 → 1.1.0)**: New pins/features, backward compatible
- **Major (1.0.0 → 2.0.0)**: Breaking changes (removed pins, changed types)

Update version in:
1. Block: `GetBlockVersion()`
2. Pipeline Builder: `SetBlockInfo("block-id", "NEW_VERSION", ...)`
3. CMakeLists.txt: `set(BLOCK_VERSION "NEW_VERSION")`
