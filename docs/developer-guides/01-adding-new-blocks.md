# Adding New Blocks to CiRA Pipeline Builder

This guide explains how to add a completely new block type to the CiRA system.

## Overview

Adding a new block requires changes in **two places**:
1. **Block Runtime** (cira-block-runtime/) - The actual C++ implementation that runs on Jetson
2. **Pipeline Builder** (pipeline_builder/) - The GUI representation in the visual editor

---

## Part 1: Block Runtime Implementation (Jetson)

### 1.1 Create Block Directory

```bash
cd cira-block-runtime/blocks/
# Choose the appropriate category:
# - sensors/ (input blocks)
# - processing/ (processing blocks)
# - outputs/ (output blocks)

# Example: Creating a new sensor block
mkdir -p sensors/my_sensor
cd sensors/my_sensor
```

### 1.2 Create Block Header File

**File**: `my_sensor_block.hpp`

```cpp
#pragma once

#include "block_interface.hpp"
#include <string>
#include <vector>

namespace CiraBlockRuntime {

class MySensorBlock : public IBlock {
public:
    MySensorBlock();
    ~MySensorBlock() override;

    // Required interface methods
    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    // Block metadata
    std::string GetBlockId() const override { return "my-sensor"; }
    std::string GetBlockVersion() const override { return "1.0.0"; }
    std::string GetBlockType() const override { return "sensor"; }

    // Pin definitions
    std::vector<Pin> GetInputPins() const override;
    std::vector<Pin> GetOutputPins() const override;

    // Data flow
    void SetInput(const std::string& pin_name, const BlockValue& value) override;
    BlockValue GetOutput(const std::string& pin_name) const override;

private:
    // Configuration parameters
    int sample_rate_;

    // Output values
    float sensor_value_;
    bool is_initialized_;
};

// Block factory functions (required for dynamic loading)
extern "C" {
    IBlock* CreateBlock();
    void DestroyBlock(IBlock* block);
}

} // namespace CiraBlockRuntime
```

### 1.3 Create Block Implementation File

**File**: `my_sensor_block.cpp`

```cpp
#include "my_sensor_block.hpp"
#include <iostream>

using namespace CiraBlockRuntime;

MySensorBlock::MySensorBlock()
    : sample_rate_(100)
    , sensor_value_(0.0f)
    , is_initialized_(false) {
}

MySensorBlock::~MySensorBlock() {
    Shutdown();
}

bool MySensorBlock::Initialize(const BlockConfig& config) {
    std::cout << "[MySensor] Initializing..." << std::endl;

    // Load configuration parameters
    if (config.find("sample_rate") != config.end()) {
        sample_rate_ = std::stoi(config.at("sample_rate"));
    }

    std::cout << "  Sample rate: " << sample_rate_ << " Hz" << std::endl;

    // Initialize hardware/resources here
    // ...

    is_initialized_ = true;
    std::cout << "[MySensor] Initialization complete" << std::endl;
    return true;
}

bool MySensorBlock::Execute() {
    if (!is_initialized_) {
        return false;
    }

    // Read sensor data
    sensor_value_ = ReadSensorHardware(); // Implement this

    return true;
}

void MySensorBlock::Shutdown() {
    if (is_initialized_) {
        // Clean up resources
        is_initialized_ = false;
        std::cout << "[MySensor] Shutdown complete" << std::endl;
    }
}

std::vector<Pin> MySensorBlock::GetInputPins() const {
    return {}; // No inputs for a sensor
}

std::vector<Pin> MySensorBlock::GetOutputPins() const {
    return {
        Pin("value_out", "float", false),
        Pin("ready", "bool", false)
    };
}

void MySensorBlock::SetInput(const std::string& pin_name, const BlockValue& value) {
    // No inputs
}

BlockValue MySensorBlock::GetOutput(const std::string& pin_name) const {
    if (pin_name == "value_out") {
        return sensor_value_;
    } else if (pin_name == "ready") {
        return is_initialized_;
    }
    return 0.0f;
}

// Block factory implementation
extern "C" {
    IBlock* CreateBlock() {
        return new MySensorBlock();
    }

    void DestroyBlock(IBlock* block) {
        delete block;
    }
}
```

### 1.4 Create CMakeLists.txt

**File**: `CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.10)

# Block metadata
set(BLOCK_ID "my-sensor")
set(BLOCK_VERSION "1.0.0")
set(BLOCK_LIBRARY "${BLOCK_ID}-v${BLOCK_VERSION}")

# Source files
add_library(${BLOCK_LIBRARY} SHARED
    my_sensor_block.cpp
)

# Include directories
target_include_directories(${BLOCK_LIBRARY} PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

# Set output name and properties
set_target_properties(${BLOCK_LIBRARY} PROPERTIES
    OUTPUT_NAME "${BLOCK_LIBRARY}"
    PREFIX ""
    SUFFIX ".so"
)

# Install to blocks directory
install(TARGETS ${BLOCK_LIBRARY}
    LIBRARY DESTINATION blocks
)
```

### 1.5 Register in Parent CMakeLists.txt

Edit `cira-block-runtime/blocks/sensors/CMakeLists.txt`:

```cmake
add_subdirectory(my_sensor)
```

### 1.6 Build and Test

```bash
cd cira-block-runtime/build
cmake ..
make -j4
# The .so file will be in build/blocks/sensors/my_sensor/
```

---

## Part 2: Pipeline Builder Integration

### 2.1 Create Node Definition File

**File**: `pipeline_builder/include/nodes/my_sensor_node.hpp`

```cpp
#pragma once

#include "core/executable_node.hpp"
#include <sstream>

namespace PipelineBuilder {

class MySensorNode : public ExecutableNode {
public:
    MySensorNode()
        : ExecutableNode(
            "input.sensor.my_sensor",  // Type ID (must match block registry)
            "My Sensor",                // Display name
            "Custom sensor description",
            NodeCategory::Input,
            InterfaceType::I2C,         // or GPIO, SPI, None
            PlatformType::JetsonNano,   // or Both, Arduino
            "📡"                        // Icon emoji
        )
    {
        // Define pins (must match block implementation)
        AddPin(PinConfig("value_out", "float", false));
        AddPin(PinConfig("ready", "bool", false));

        // Default configuration
        SetDefaultConfig("sample_rate", "100");
        SetDefaultConfig("i2c_addr", "0x48");

        // Block system metadata
        SetBlockInfo(
            "my-sensor",     // block_id (must match GetBlockId())
            "1.0.0",         // version
            "sensor",        // type
            false            // requires_compilation
        );
    }

    // Code generation methods (optional - for standalone deployment)
    std::string GenerateJetsonIncludes() const override {
        return "#include <i2c_device.h>\n";
    }

    std::string GenerateJetsonInit(int node_id, const std::map<std::string, std::string>& config) const override {
        std::ostringstream code;
        code << "    // Initialize My Sensor Node " << node_id << "\n";
        code << "    InitializeMySensor(" << config.at("i2c_addr") << ");\n";
        return code.str();
    }
};

} // namespace PipelineBuilder
```

### 2.2 Register Node in Pipeline Builder

Edit `pipeline_builder/src/core/initialize_executable_nodes.cpp`:

```cpp
#include "nodes/my_sensor_node.hpp"

void InitializeExecutableNodes() {
    auto& registry = ExecutableNodeRegistry::Instance();

    // ... existing nodes ...

    // Add your new node
    registry.RegisterNode(std::make_unique<MySensorNode>());
}
```

### 2.3 Add to Legacy Node Registry (Optional)

If you need the node in the old registry system, edit `pipeline_builder/src/core/node_registry.cpp`:

```cpp
void NodeRegistry::InitializeDefaultNodes() {
    // ... existing nodes ...

    // My Sensor
    RegisterNodeType({
        "MySensor",
        "My Sensor",
        "Custom sensor description",
        NodeCategory::Input,
        InterfaceType::I2C,
        PlatformType::JetsonNano,
        {
            PinConfig("value_out", "float", false),
            PinConfig("ready", "bool", false)
        },
        {
            {"sample_rate", "100"},
            {"i2c_addr", "0x48"}
        },
        "📡"
    });
}
```

### 2.4 Rebuild Pipeline Builder

```bash
cd pipeline_builder/build
cmake --build . --config Release
```

---

## Testing the New Block

### On Jetson:

1. Deploy your pipeline using Pipeline Builder
2. Check runtime logs: `tail -f /home/user/cira_projects/cira-runtime/runtime.log`
3. Verify block loads: `ls -la /home/user/cira_projects/cira-runtime/blocks/my-sensor-v1.0.0.so`

### In Pipeline Builder:

1. Restart Pipeline Builder
2. The new block should appear in the block library under the appropriate category
3. Drag it onto the canvas
4. Configure properties
5. Connect wires
6. Deploy and test

---

## Block Types Reference

### Pin Types
- `float` - Single floating point value
- `int` - Integer value
- `bool` - Boolean value
- `string` - Text string
- `array` - Array of floats (std::vector<float>)
- `vector3` - 3D vector (x, y, z)

### Platform Types
- `PlatformType::JetsonNano` - Jetson only
- `PlatformType::Arduino` - Arduino only
- `PlatformType::Both` - Cross-platform

### Interface Types
- `InterfaceType::None` - Software only
- `InterfaceType::I2C` - I2C hardware
- `InterfaceType::GPIO` - GPIO pins
- `InterfaceType::SPI` - SPI bus
- `InterfaceType::PWM` - PWM output

---

## Common Issues

1. **Block not appearing in Pipeline Builder**
   - Check if node is registered in `initialize_executable_nodes.cpp`
   - Rebuild Pipeline Builder
   - Restart the application

2. **Block fails to load on Jetson**
   - Check .so file exists: `ls blocks/`
   - Check for compilation errors in runtime output
   - Verify block_id matches between runtime and manifest

3. **Pins don't match**
   - Pin definitions must be identical in both:
     - Block runtime: `GetInputPins()` / `GetOutputPins()`
     - Pipeline Builder: `AddPin()` calls in node constructor
