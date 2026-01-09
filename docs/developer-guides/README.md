# CiRA Pipeline Builder - Developer Guides

Welcome to the CiRA Pipeline Builder developer documentation! This directory contains comprehensive guides for extending and customizing the CiRA system.

## 📚 Available Guides

### 1. [Adding New Blocks](01-adding-new-blocks.md)
Learn how to create completely new block types from scratch.

**Topics covered:**
- Block runtime implementation (C++ on Jetson)
- Pipeline Builder GUI integration
- Pin definitions and data flow
- CMake configuration
- Testing and deployment

**When to use:** Creating a new sensor, processor, or output block type.

---

### 2. [Modifying Existing Blocks](02-modifying-existing-blocks.md)
Learn how to add new features to existing blocks (pins, parameters, etc.).

**Topics covered:**
- Adding new output pins (real example: TimesNet `class_name`)
- Adding new input pins
- Parsing configuration parameters
- String parsing (comma-separated values)
- Version management
- Handling breaking changes

**When to use:** Adding features like:
- New output values (e.g., class names, additional metrics)
- New configuration parameters
- Enhanced functionality to existing blocks

**Real-world example:** We added a `class_name` string output pin to TimesNet block to display human-readable class names instead of just numeric IDs.

---

### 3. [Properties Panel Customization](03-properties-panel-customization.md)
Learn how to add custom UI controls to the Properties Panel.

**Topics covered:**
- Adding dropdown menus for predefined choices
- Adding sliders for numeric ranges
- Specialized inputs (hex, pin numbers, colors)
- Conditional controls
- Multi-value editors

**When to use:** Making configuration more user-friendly:
- Dropdown instead of typing: `output_format: csv|json|cbor`
- Sliders for ranges: `sample_rate: 1-1000 Hz`
- Color pickers for visual properties
- File browsers for paths

**Real-world example:** We added a dropdown for `output_format` in Data Recorder to easily choose between CSV, JSON, and CBOR formats.

---
### I want to...

#### Create a brand new sensor/actuator block
→ **Read:** [01-adding-new-blocks.md](01-adding-new-blocks.md)

#### Add a new output value to an existing block
→ **Read:** [02-modifying-existing-blocks.md](02-modifying-existing-blocks.md) - Section "Adding an Output Pin"

#### Add a dropdown menu to a block property
→ **Read:** [03-properties-panel-customization.md](03-properties-panel-customization.md) - Section "Adding a Dropdown"

#### Add configuration parameters (sample_rate, threshold, etc.)
→ **Read:** [02-modifying-existing-blocks.md](02-modifying-existing-blocks.md) - Section "Adding a Configuration Parameter"

#### Parse comma-separated values (class names, etc.)
→ **Read:** [02-modifying-existing-blocks.md](02-modifying-existing-blocks.md) - Section 1.3 "Parse Configuration in Initialize()"

#### Make a slider for numeric input
→ **Read:** [03-properties-panel-customization.md](03-properties-panel-customization.md) - Section "Adding a Slider"

---

## 🏗️ Architecture Overview

```
CiRA System
├── Block Runtime (Jetson Nano - ARM Linux)
│   ├── C++ blocks (.so dynamic libraries)
│   ├── Block executor (loads and runs blocks)
│   └── Web server (dashboard, WebSocket API)
│
└── Pipeline Builder (Windows - x64)
    ├── Visual node editor (ImGui)
    ├── Block library definitions
    ├── Properties panel (configuration UI)
    └── Deployment system (SSH/SFTP to Jetson)
```

**Key Insight:** When you modify a block, you need to update **BOTH** sides:
1. **Runtime** - The actual implementation that runs on Jetson
2. **Pipeline Builder** - The visual representation and configuration UI

---

## 🔄 Development Workflow

### Typical workflow when modifying blocks:

```
1. Edit block runtime code (cira-block-runtime/)
   ↓
2. Build runtime locally (Windows - for syntax checking)
   ↓
3. Edit Pipeline Builder node definition
   ↓
4. Build Pipeline Builder
   ↓
5. Open Pipeline Builder → Deploy → Setup Device
   (This compiles runtime on Jetson and installs blocks)
   ↓
6. In Pipeline Builder: Delete old node, add fresh node
   (This ensures new pin definitions are loaded)
   ↓
7. Save pipeline → Deploy → Test
```

### Quick updates (incremental):

```
1. Edit block code
   ↓
2. Build locally
   ↓
3. Pipeline Builder → Deploy → Update Runtime
   (Only recompiles changed blocks - faster!)
   ↓
4. Deploy → Refresh browser (Ctrl+F5)
```

---

## 📋 Common Operations Cheat Sheet

### Adding a new output pin:

**Runtime:**
```cpp
// In GetOutputPins()
return {
    Pin("existing_pin", "float", false),
    Pin("new_pin", "string", false)  // ← Add this
};

// In GetOutput()
if (pin_name == "new_pin") {
    return new_value_;
}
```

**Pipeline Builder:**
```cpp
// In node constructor
AddPin(PinConfig("new_pin", "string", false));
```

### Adding a dropdown:

**Pipeline Builder:** (properties_panel.cpp)
```cpp
else if (key == "my_param") {
    const char* options[] = {"opt1", "opt2", "opt3"};
    int current_item = 0;
    for (int i = 0; i < 3; i++) {
        if (value == options[i]) { current_item = i; break; }
    }
    if (edit_mode_) {
        if (ImGui::Combo("##value", &current_item, options, 3)) {
            value = options[current_item];
        }
    }
}
```

### Parsing comma-separated config:

**Runtime:**
```cpp
// In Initialize()
if (config.find("items") != config.end()) {
    std::string items_str = config.at("items");
    std::stringstream ss(items_str);
    std::string item;
    while (std::getline(ss, item, ',')) {
        item.erase(0, item.find_first_not_of(" \t"));  // Trim
        item.erase(item.find_last_not_of(" \t") + 1);
        items_.push_back(item);
    }
}
```

---

## 🐛 Troubleshooting Guide

### Problem: New pin doesn't appear in Pipeline Builder

**Cause:** Old node definition cached in pipeline file

**Solution:**
1. Delete the node from your pipeline
2. Drag a fresh node from the block library
3. The new instance will have updated pins

---

### Problem: Runtime crashes with "bad_variant_access"

**Cause:** Type mismatch between pin declaration and GetOutput/SetInput

**Solution:** Match types exactly:
```cpp
// If pin is "string":
Pin("my_pin", "string", false)
→ return std::string("value");

// If pin is "float":
Pin("my_pin", "float", false)
→ return 0.0f;

// If pin is "array":
Pin("my_pin", "array", false)
→ return std::vector<float>{};
```

---

### Problem: Configuration parameter not loaded

**Solution:** Check spelling and parsing:
```cpp
// Block defines: SetDefaultConfig("sample_rate", "100")
// Runtime must read: config.at("sample_rate")
//                    NOT config.at("sampleRate") ❌
```

---

### Problem: Block compiles but doesn't load on Jetson

**Check list:**
- [ ] .so file exists: `ls /home/user/cira_projects/cira-runtime/blocks/`
- [ ] Permissions correct: `-rwxrwxr-x`
- [ ] No missing dependencies: `ldd block-name.so`
- [ ] Runtime logs: `tail -f runtime.log`
- [ ] Block ID matches manifest

---

## 📖 Additional Resources

### File Locations Quick Reference

```
cira-block-runtime/
├── blocks/
│   ├── sensors/          # Input blocks
│   ├── processing/       # Processing blocks
│   └── outputs/          # Output blocks
├── include/
│   └── block_interface.hpp  # Block interface definition
└── src/
    └── block_executor.cpp   # Block loading and execution

pipeline_builder/
├── include/
│   └── nodes/            # Node definitions (ExecutableNode classes)
├── src/
│   ├── core/
│   │   ├── node_registry.cpp              # Legacy node registry
│   │   └── initialize_executable_nodes.cpp # Node registration
│   └── ui/
│       └── properties_panel.cpp            # Properties UI customization
```

### Important Interfaces

**Block Runtime:**
- `IBlock` - Base interface for all blocks
- `Pin` - Input/output pin definition
- `BlockValue` - Variant type for pin values (float, int, bool, string, array)
- `BlockConfig` - Configuration map (string → string)

**Pipeline Builder:**
- `ExecutableNode` - Base class for node definitions
- `PinConfig` - Pin definition for GUI
- `NodeCategory` - Input / Processing / Output
- `PlatformType` - JetsonNano / Arduino / Both

---

## 📝 Contribution Guidelines

When documenting your changes:

1. **Update block version** if you make breaking changes
2. **Add comments** explaining why, not just what
3. **Test on actual hardware** before committing
4. **Update this guide** if you discover new patterns

---

## 🎓 Learning Path

**Beginner:**
1. Read "Adding New Blocks" - understand the full stack
2. Try adding a simple sensor block (e.g., temperature sensor)
3. Test deployment to Jetson

**Intermediate:**
1. Read "Modifying Existing Blocks"
2. Add a new output pin to an existing block
3. Parse a comma-separated configuration parameter

**Advanced:**
1. Read "Properties Panel Customization"
2. Add a custom dropdown or slider
3. Create a block with conditional UI (show/hide fields)

---

## 🆘 Getting Help

If you're stuck:

1. **Check the troubleshooting sections** in each guide
2. **Look at similar blocks** in the codebase for examples
3. **Search for error messages** in the guides
4. **Check compilation output** for specific errors

Common error patterns are documented in each guide's troubleshooting section.

---

## 📊 Real-World Examples

All guides include **real-world examples** from actual development:

- **TimesNet `class_name` addition** - Shows complete pin addition workflow
- **Data Recorder CBOR format** - Shows format options and configuration
- **Properties dropdown** - Shows UI customization for better UX

These are not theoretical examples - they're actual features we implemented!

---

**Last Updated:** 2026-01-09

**Version:** 1.0

**Maintained by:** CiRA Development Team

### 4. [Web Dashboard Widgets](04-web-dashboard-widgets.md)
Learn how to create custom widgets for the web-based runtime dashboard.

**Topics covered:**
- Widget base class and lifecycle
- WebSocket subscriptions for real-time data
- Interactive widgets (buttons, controls)
- Sending commands to blocks
- Chart integration (Chart.js)
- Dashboard persistence

**When to use:**
- Creating custom data visualizations
- Building control panels for your pipeline
- Real-time monitoring displays
- Interactive device controls

**Real-world example:** Dataset Recorder widget with file management, download, and delete functionality.

---

### 5. [Deployment System](05-deployment-system.md)
Comprehensive guide to the Pipeline Builder deployment system.

**Topics covered:**
- All deployment buttons explained (Setup Device, Update Runtime, Deploy, etc.)
- Deployment modes (Compiled Binary vs Block Runtime)
- SSH/SFTP file transfer
- Remote compilation process
- Precompiled binary caching
- Customizing deployment workflow

**When to use:**
- Understanding deployment process
- Troubleshooting deployment issues
- Optimizing deployment speed
- Adding custom deployment steps
- Managing multiple devices

**Real-world example:** Using "Update Runtime" for quick iterative development, then "Install from Precompiled" for production deployment to multiple devices.


#### Create a custom widget for the web dashboard
→ **Read:** [04-web-dashboard-widgets.md](04-web-dashboard-widgets.md)

#### Understand the deployment system buttons
→ **Read:** [05-deployment-system.md](05-deployment-system.md) - Section "Deployment Buttons Explained"

#### Speed up deployment with precompiled binaries
→ **Read:** [05-deployment-system.md](05-deployment-system.md) - Section "Install from Precompiled"

#### Add custom deployment steps
→ **Read:** [05-deployment-system.md](05-deployment-system.md) - Section "Customizing Deployment"

