# Phase 4: Block Runtime on Hardware - Implementation Plan

## Overview
Build the `cira-block-runtime` executable that runs on target devices (Jetson Nano, Arduino UNO Q) to dynamically load and execute blocks based on the manifest file.

## Goals
1. Create standalone runtime that can execute pipelines without recompilation
2. Support both Jetson Nano (ARM64 Linux) and Arduino UNO Q (Debian + Zephyr)
3. Enable remote updates via manifest deployment
4. Provide block marketplace foundation

## Architecture

### High-Level Design
```
┌─────────────────────────────────────────────────────┐
│  Pipeline Builder (Dev Machine)                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  Block Manifest Generator                     │  │
│  │  - Analyzes pipeline                          │  │
│  │  - Generates block_manifest.json              │  │
│  │  - Lists required blocks + dependencies       │  │
│  └───────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────┘
                   │ SSH Transfer
                   ▼
┌─────────────────────────────────────────────────────┐
│  Target Device (Jetson Nano / UNO Q)                │
│  ┌───────────────────────────────────────────────┐  │
│  │  cira-block-runtime                           │  │
│  │  1. Load block_manifest.json                  │  │
│  │  2. Verify required blocks exist              │  │
│  │  3. Load blocks (.so shared libraries)        │  │
│  │  4. Build execution graph                     │  │
│  │  5. Execute pipeline loop                     │  │
│  └───────────────────────────────────────────────┘  │
│                                                      │
│  ┌───────────────────────────────────────────────┐  │
│  │  Block Library (/usr/local/lib/cira/blocks/)  │  │
│  │  - timesnet-v1.2.0.so                         │  │
│  │  - adxl345-sensor-v1.0.0.so                   │  │
│  │  - sliding-window-v1.0.0.so                   │  │
│  │  - ...                                         │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Platform-Specific Considerations

### Jetson Nano (ARM64 Linux)
- **OS**: Ubuntu 20.04 ARM64
- **Runtime**: Single-process, all blocks in one address space
- **Block Format**: `.so` shared libraries
- **Dependencies**: ONNX Runtime, I2C tools, GPIO libraries

### Arduino UNO Q (Debian + Zephyr)
- **OS**: Debian Linux (Trixie/Bookworm) on MPU + Zephyr on MCU
- **Runtime Strategy**: Hybrid dual-core
  - **MPU (Debian)**: Runs `cira-block-runtime` for AI/network blocks
  - **MCU (Zephyr)**: Runs real-time sensor/GPIO blocks
  - **IPC**: Message passing between MPU and MCU
- **Block Format**:
  - MPU blocks: `.so` shared libraries (like Jetson)
  - MCU blocks: Zephyr modules (compile-time linked)

### UNO Q Dual-Core Architecture
```
┌─────────────────────────────────────────────────────┐
│  Arduino UNO Q                                      │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  Debian Linux (Qualcomm MPU)                   │ │
│  │                                                 │ │
│  │  cira-block-runtime (MPU)                      │ │
│  │  ├─ TimesNet Model Block (.so)                 │ │
│  │  ├─ HTTP POST Block (.so)                      │ │
│  │  ├─ MQTT Publisher Block (.so)                 │ │
│  │  └─ Sliding Window Block (.so)                 │ │
│  │                                                 │ │
│  │       ▲         │                               │ │
│  │       │         ▼                               │ │
│  │  ┌─────────────────────┐                       │ │
│  │  │   IPC Bridge        │                       │ │
│  │  │  (Shared Memory/    │                       │ │
│  │  │   Message Queue)    │                       │ │
│  │  └─────────────────────┘                       │ │
│  └────────────────────────────────────────────────┘ │
│               ▲         │                           │
│               │         ▼                           │
│  ┌────────────────────────────────────────────────┐ │
│  │  Zephyr OS (STM32U585 MCU)                     │ │
│  │                                                 │ │
│  │  cira-mcu-adapter                              │ │
│  │  ├─ ADXL345 Sensor Driver                      │ │
│  │  ├─ BME280 Sensor Driver                       │ │
│  │  ├─ GPIO Output Driver                         │ │
│  │  └─ PWM Output Driver                          │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## Repository Structure

### Create New Repository: `cira-block-runtime`
```
cira-block-runtime/
├── CMakeLists.txt
├── README.md
├── include/
│   ├── block_interface.hpp       # Block API definition
│   ├── block_loader.hpp          # Dynamic library loader
│   ├── block_executor.hpp        # Execution engine
│   ├── manifest_parser.hpp       # JSON manifest parser
│   └── data_types.hpp            # Common data structures
├── src/
│   ├── main.cpp                  # Entry point
│   ├── block_loader.cpp
│   ├── block_executor.cpp
│   ├── manifest_parser.cpp
│   └── runtime_context.cpp
├── blocks/                       # Example blocks implementation
│   ├── sensors/
│   │   ├── adxl345/
│   │   │   ├── adxl345_block.cpp
│   │   │   └── CMakeLists.txt
│   │   └── bme280/
│   ├── processing/
│   │   ├── sliding_window/
│   │   ├── low_pass_filter/
│   │   └── channel_merge/
│   ├── models/
│   │   └── timesnet/
│   │       ├── timesnet_block.cpp
│   │       └── CMakeLists.txt
│   └── outputs/
│       ├── gpio_output/
│       ├── oled_display/
│       └── mqtt_publisher/
├── platforms/
│   ├── jetson_nano/              # Platform-specific code
│   │   └── platform_init.cpp
│   └── uno_q/
│       ├── mpu/                  # Debian MPU runtime
│       │   ├── mpu_runtime.cpp
│       │   └── ipc_bridge.cpp
│       └── mcu/                  # Zephyr MCU adapter
│           ├── mcu_adapter.c
│           └── CMakeLists.txt
├── third_party/
│   └── json.hpp                  # nlohmann/json (same as pipeline_builder)
└── tests/
    ├── test_block_loader.cpp
    └── test_manifest_parser.cpp
```

## Block Interface Design

### Core Block API
```cpp
// include/block_interface.hpp
#pragma once
#include <string>
#include <vector>
#include <map>
#include <variant>

namespace CiraBlockRuntime {

// Data types that can be passed between blocks
using BlockValue = std::variant<
    float,
    int,
    bool,
    std::string,
    std::vector<float>  // For arrays/vectors
>;

// Pin connection
struct Pin {
    std::string name;
    std::string type;  // "float", "int", "bool", "string", "array"
    bool is_input;
    BlockValue value;
};

// Block configuration (from manifest)
using BlockConfig = std::map<std::string, std::string>;

// Abstract base class for all blocks
class IBlock {
public:
    virtual ~IBlock() = default;

    // Initialize block with configuration
    virtual bool Initialize(const BlockConfig& config) = 0;

    // Get block metadata
    virtual std::string GetBlockId() const = 0;
    virtual std::string GetBlockVersion() const = 0;

    // Get input/output pins
    virtual std::vector<Pin> GetInputPins() const = 0;
    virtual std::vector<Pin> GetOutputPins() const = 0;

    // Set input value
    virtual void SetInput(const std::string& pin_name, const BlockValue& value) = 0;

    // Execute block (process inputs -> outputs)
    virtual bool Execute() = 0;

    // Get output value
    virtual BlockValue GetOutput(const std::string& pin_name) const = 0;

    // Cleanup
    virtual void Shutdown() = 0;
};

// Factory function type (each block .so exports this)
using BlockCreateFunc = IBlock* (*)();
using BlockDestroyFunc = void (*)(IBlock*);

} // namespace CiraBlockRuntime
```

### Example Block Implementation
```cpp
// blocks/sensors/adxl345/adxl345_block.cpp
#include "block_interface.hpp"
#include <linux/i2c-dev.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>

namespace CiraBlockRuntime {

class ADXL345Block : public IBlock {
public:
    ADXL345Block() : i2c_fd_(-1), i2c_address_(0x53) {}

    bool Initialize(const BlockConfig& config) override {
        // Parse config
        if (config.count("i2c_address")) {
            i2c_address_ = std::stoi(config.at("i2c_address"), nullptr, 16);
        }

        // Open I2C device
        i2c_fd_ = open("/dev/i2c-1", O_RDWR);
        if (i2c_fd_ < 0) return false;

        if (ioctl(i2c_fd_, I2C_SLAVE, i2c_address_) < 0) {
            close(i2c_fd_);
            return false;
        }

        // Initialize ADXL345 (set range, etc.)
        // ... sensor initialization code ...

        return true;
    }

    std::string GetBlockId() const override { return "adxl345-sensor"; }
    std::string GetBlockVersion() const override { return "1.0.0"; }

    std::vector<Pin> GetInputPins() const override {
        return {}; // No inputs (sensor node)
    }

    std::vector<Pin> GetOutputPins() const override {
        return {
            {"accel_x", "float", false, 0.0f},
            {"accel_y", "float", false, 0.0f},
            {"accel_z", "float", false, 0.0f}
        };
    }

    void SetInput(const std::string& pin_name, const BlockValue& value) override {
        // No inputs
    }

    bool Execute() override {
        // Read acceleration data from sensor
        uint8_t buffer[6];
        if (read(i2c_fd_, buffer, 6) != 6) {
            return false;
        }

        // Convert raw data to g values
        int16_t x = (buffer[1] << 8) | buffer[0];
        int16_t y = (buffer[3] << 8) | buffer[2];
        int16_t z = (buffer[5] << 8) | buffer[4];

        // Scale based on range (±2g = 256 LSB/g)
        accel_x_ = x / 256.0f;
        accel_y_ = y / 256.0f;
        accel_z_ = z / 256.0f;

        return true;
    }

    BlockValue GetOutput(const std::string& pin_name) const override {
        if (pin_name == "accel_x") return accel_x_;
        if (pin_name == "accel_y") return accel_y_;
        if (pin_name == "accel_z") return accel_z_;
        return 0.0f;
    }

    void Shutdown() override {
        if (i2c_fd_ >= 0) {
            close(i2c_fd_);
            i2c_fd_ = -1;
        }
    }

private:
    int i2c_fd_;
    int i2c_address_;
    float accel_x_, accel_y_, accel_z_;
};

// Export factory functions (C linkage for dlopen)
extern "C" {
    IBlock* CreateBlock() {
        return new ADXL345Block();
    }

    void DestroyBlock(IBlock* block) {
        delete block;
    }
}

} // namespace CiraBlockRuntime
```

## Implementation Phases

### Phase 4.1: Core Runtime Infrastructure (Week 1)
**Goal**: Build basic runtime that can load and execute blocks

**Tasks**:
- [ ] Create `cira-block-runtime` repository
- [ ] Implement `ManifestParser` to read `block_manifest.json`
- [ ] Implement `BlockLoader` using `dlopen()`/`dlsym()`
- [ ] Implement `BlockExecutor` for execution graph
- [ ] Create `block_interface.hpp` API
- [ ] Build basic `main.cpp` that loads manifest and runs pipeline

**Deliverable**: Runtime that can load a simple manifest and execute 2-3 blocks

### Phase 4.2: Example Block Implementations (Week 2)
**Goal**: Create reference blocks to test runtime

**Priority Blocks** (for TimesNet pipeline):
1. **ADXL345 Sensor Block** - I2C accelerometer
2. **Sliding Window Block** - Data buffering
3. **TimesNet Model Block** - ONNX inference
4. **GPIO Output Block** - LED control
5. **OLED Display Block** - I2C display

**Tasks**:
- [ ] Implement each block following `IBlock` interface
- [ ] Create CMakeLists.txt to build each block as `.so`
- [ ] Test individual blocks in isolation
- [ ] Test blocks connected in runtime

**Deliverable**: 5 working blocks that can run TimesNet gesture recognition pipeline

### Phase 4.3: SSH File Transfer & Deployment (Week 2)
**Goal**: Complete the deployment flow from Pipeline Builder

**Tasks**:
- [ ] Add file transfer to `SSHManager` (SCP or SFTP)
- [ ] Implement `DeployBlockRuntimeThreadFunction()` fully:
  - Create remote workspace directory
  - Transfer `block_manifest.json`
  - Verify blocks exist on device
  - Start `cira-block-runtime` process
- [ ] Add runtime status monitoring
- [ ] Handle errors gracefully (missing blocks, etc.)

**Deliverable**: One-click deployment from Pipeline Builder to Jetson Nano

### Phase 4.4: Arduino UNO Q Dual-Core Support (Week 3-4)
**Goal**: Adapt runtime for UNO Q's MPU+MCU architecture

**MPU (Debian) Side**:
- [ ] Port `cira-block-runtime` to ARM64 Debian
- [ ] Build blocks as `.so` for UNO Q MPU
- [ ] Implement IPC bridge for MCU communication

**MCU (Zephyr) Side**:
- [ ] Create `cira-mcu-adapter` for Zephyr
- [ ] Implement sensor/GPIO blocks as Zephyr drivers
- [ ] Set up IPC receiver on MCU side

**IPC Design**:
```cpp
// IPC message format
struct IPCMessage {
    uint32_t msg_type;      // READ_SENSOR, WRITE_GPIO, etc.
    uint32_t node_id;       // Which block
    char pin_name[32];      // Which pin
    float value;            // Data payload
};

// MPU -> MCU: "Read ADXL345 sensor"
// MCU -> MPU: "ADXL345 data: x=0.5, y=0.2, z=9.8"
```

**Deliverable**: Pipeline running on UNO Q with blocks split between MPU and MCU

## Testing Strategy

### Unit Tests
- Block loader can open `.so` files
- Manifest parser handles valid/invalid JSON
- Block executor builds correct execution graph

### Integration Tests
- Full pipeline execution on Jetson Nano
- Deployment from Pipeline Builder works
- Runtime handles missing blocks gracefully

### Hardware Tests
- **Jetson Nano**: Complete TimesNet pipeline
- **Arduino UNO Q**: Dual-core split execution
- Performance benchmarking (latency, throughput)

## Deployment & Installation

### On Target Device (Jetson Nano / UNO Q)
```bash
# 1. Install runtime binary
sudo cp cira-block-runtime /usr/local/bin/
sudo chmod +x /usr/local/bin/cira-block-runtime

# 2. Create block library directory
sudo mkdir -p /usr/local/lib/cira/blocks/

# 3. Install blocks
sudo cp blocks/*.so /usr/local/lib/cira/blocks/

# 4. Run with manifest
cira-block-runtime /path/to/block_manifest.json
```

### From Pipeline Builder
```
Generate Menu -> Deploy to Device
  ├─ Select Mode: Block Runtime
  ├─ Generate block_manifest.json
  └─ Deploy via SSH:
      ├─ Transfer manifest
      ├─ Verify blocks exist
      └─ Start cira-block-runtime
```

## Success Criteria

**Phase 4 Complete When**:
- ✅ `cira-block-runtime` runs on Jetson Nano
- ✅ TimesNet gesture recognition pipeline works via blocks
- ✅ Deployment from Pipeline Builder succeeds
- ✅ Can update pipeline by changing manifest (no recompile)
- ✅ UNO Q dual-core architecture supported

## Next Steps After Phase 4

**Phase 5: Block Marketplace** (Future)
- Block versioning and dependency resolution
- Block signing and verification
- Marketplace web interface
- Licensing and monetization

**Phase 6: Remote Updates** (Future)
- Over-the-air manifest updates
- A/B testing support
- Rollback capability

## Open Questions

1. **IPC Mechanism for UNO Q**: Shared memory vs message queue vs custom protocol?
2. **Block Versioning**: How to handle multiple versions of same block?
3. **Performance**: Dynamic loading vs compiled - what's the overhead?
4. **Security**: Should blocks be sandboxed? Code signing?

## Resources Needed

- Jetson Nano with SSH access (already have)
- Arduino UNO Q hardware (for testing dual-core)
- ADXL345 + BME280 sensors (for testing sensor blocks)
- OLED display (for testing output blocks)

## Timeline

**Week 1**: Core runtime infrastructure (Phase 4.1)
**Week 2**: Example blocks + SSH deployment (Phase 4.2-4.3)
**Week 3-4**: Arduino UNO Q dual-core support (Phase 4.4)
**Week 5**: Testing, documentation, refinement

**Total Estimate**: 4-5 weeks for full Phase 4 completion
