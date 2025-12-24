# Pin Color Coding Guide
**CiRA Pipeline Builder - Visual Connection Compatibility**

---

## Pin Color Scheme

Pins are color-coded by **data type** to make it easy to see which pins can connect together. Matching colors indicate compatible connections.

### Data Type Colors

| Data Type | Color | RGB Values | Use Case | Example |
|-----------|-------|------------|----------|---------|
| **float** | 🟢 Green | (0.3, 0.8, 0.3) | Floating-point numbers | Sensor readings, measurements |
| **int** | 🔵 Blue | (0.3, 0.5, 0.9) | Integer numbers | Counts, IDs, class predictions |
| **bool** | 🔴 Red | (0.9, 0.3, 0.3) | Boolean values | Digital signals, states, flags |
| **string** | 🟠 Orange | (0.9, 0.7, 0.3) | Text/String data | JSON, messages, labels |
| **vector3** | 🟣 Purple | (0.7, 0.3, 0.9) | 3D vectors | Accelerometer (X,Y,Z), RGB colors |
| **array** | 🔵 Cyan | (0.3, 0.9, 0.9) | Arrays/Tensors | Time series windows, feature vectors |
| **any** | ⚪ Gray | (0.7, 0.7, 0.7) | Wildcard type | Can connect to any type |

---

## Connection Rules

### ✅ Compatible Connections

Pins can connect when:
1. **Same type**: `float` → `float`, `int` → `int`, etc.
2. **Wildcard**: `any` can connect to any type
3. **Implicit casting**: `float` ↔ `int` (with automatic conversion)

### ❌ Incompatible Connections

- **Different types**: Cannot connect `bool` → `string`
- **Same direction**: Cannot connect `input` → `input` or `output` → `output`

---

## Visual Examples

### Example 1: Accelerometer to TimesNet
```
┌─────────────────┐           ┌──────────────────┐
│  ADXL345        │           │  Channel Merge   │
│  Accelerometer  │           │                  │
│                 │           │                  │
│  accel_x  🟢───────────────→🟢 channel_0      │
│  accel_y  🟢───────────────→🟢 channel_1      │
│  accel_z  🟢───────────────→🟢 channel_2      │
│                 │           │                  │
│                 │           │  merged_out 🟣───┐
└─────────────────┘           └──────────────────┘
                                                  │
                              ┌──────────────────┐│
                              │  Sliding Window  ││
                              │                  ││
                              │  input      🟣←──┘
                              │                  │
                              │  window_out 🔵───┐
                              └──────────────────┘│
                                                  │
                              ┌──────────────────┐│
                              │  TimesNet Model  ││
                              │                  ││
                              │  features_in🔵←──┘
                              │                  │
                              │  prediction 🔵───→
                              └──────────────────┘
```

### Example 2: GPIO Control
```
┌─────────────────┐           ┌──────────────────┐
│  Decision Tree  │           │  GPIO Output     │
│                 │           │                  │
│  prediction🔵──────────────→🔵 state (via cast)│
└─────────────────┘           └──────────────────┘
                              (int → bool cast)
```

---

## Implementation Details

### Pin Color Logic

**File:** `include/core/node_types.hpp`
```cpp
Color GetPinColor() const {
    if (type == "float")       return {0.3f, 0.8f, 0.3f, 1.0f};  // Green
    if (type == "int")         return {0.3f, 0.5f, 0.9f, 1.0f};  // Blue
    if (type == "bool")        return {0.9f, 0.3f, 0.3f, 1.0f};  // Red
    if (type == "string")      return {0.9f, 0.7f, 0.3f, 1.0f};  // Orange
    if (type == "vector3")     return {0.7f, 0.3f, 0.9f, 1.0f};  // Purple
    if (type == "array")       return {0.3f, 0.9f, 0.9f, 1.0f};  // Cyan
    if (type == "any")         return {0.7f, 0.7f, 0.7f, 1.0f};  // Gray
    return {0.5f, 0.5f, 0.5f, 1.0f};  // Default gray
}
```

### Connection Validation

**File:** `include/core/node_types.hpp`
```cpp
bool CanConnectTo(const PinConfig& other) const {
    // Can't connect input to input or output to output
    if (is_input == other.is_input) return false;

    // "any" type can connect to anything
    if (type == "any" || other.type == "any") return true;

    // Same types can connect
    if (type == other.type) return true;

    // float can connect to int (with implicit cast)
    if ((type == "float" && other.type == "int") ||
        (type == "int" && other.type == "float")) return true;

    return false;
}
```

### UI Rendering

**File:** `include/ui/blueprint_style.hpp`
```cpp
static ImVec4 GetPinTypeColor(const std::string& type) {
    // Data type based colors (matching PinConfig::GetPinColor)
    if (type == "float")   return ImVec4(0.3f, 0.8f, 0.3f, 1.0f);  // Green
    if (type == "int")     return ImVec4(0.3f, 0.5f, 0.9f, 1.0f);  // Blue
    if (type == "bool")    return ImVec4(0.9f, 0.3f, 0.3f, 1.0f);  // Red
    if (type == "string")  return ImVec4(0.9f, 0.7f, 0.3f, 1.0f);  // Orange
    if (type == "vector3") return ImVec4(0.7f, 0.3f, 0.9f, 1.0f);  // Purple
    if (type == "array")   return ImVec4(0.3f, 0.9f, 0.9f, 1.0f);  // Cyan
    if (type == "any")     return ImVec4(0.7f, 0.7f, 0.7f, 1.0f);  // Gray
    // ...
}
```

---

## Quick Reference

### Color Matching Cheat Sheet

When dragging a connection:
- **Same color** = ✅ Compatible
- **Green ↔ Blue** = ✅ Compatible (float ↔ int cast)
- **Gray** = ✅ Compatible with any color (wildcard)
- **Different colors** = ❌ Incompatible

### Node Output → Input Examples

| From (Output) | To (Input) | Compatible? | Notes |
|---------------|------------|-------------|-------|
| float 🟢 | float 🟢 | ✅ Yes | Same type |
| int 🔵 | int 🔵 | ✅ Yes | Same type |
| float 🟢 | int 🔵 | ✅ Yes | Implicit cast |
| int 🔵 | float 🟢 | ✅ Yes | Implicit cast |
| bool 🔴 | string 🟠 | ❌ No | Type mismatch |
| any ⚪ | float 🟢 | ✅ Yes | Wildcard |
| vector3 🟣 | array 🔵 | ❌ No | Different structures |

---

## Benefits

### For Users
1. **Visual clarity**: Instantly see compatible connections
2. **Error prevention**: Can't accidentally connect wrong types
3. **Learning aid**: Colors reinforce data type concepts
4. **Faster workflow**: Less trial and error

### For Debugging
1. **Type errors visible**: Red connections stand out
2. **Data flow tracking**: Follow color chains through pipeline
3. **Documentation**: Colors serve as visual type hints

---

## Inspired By

This color-coding system is inspired by:
- **Unreal Engine Blueprints**: Industry-standard visual scripting
- **Node-based compositing tools**: Blender, Nuke, TouchDesigner
- **Data flow programming**: Max/MSP, Pure Data

---

**Version:** 1.0
**Last Updated:** 2024-12-24
**Status:** Implemented in Phase 1
