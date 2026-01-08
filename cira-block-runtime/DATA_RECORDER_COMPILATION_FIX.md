# Data Recorder Block - Compilation Fix Required

## Problem
The data_recorder_block.cpp was written using wrong API types. The block interface uses:
- `Pin` (not `PinDefinition`)
- `SetInput()` + `Execute()` + `GetOutput()` pattern (not `Process(InputValues, OutputValues)`)

## Solution
Replace the entire `blocks/outputs/data_recorder/data_recorder_block.cpp` with the corrected version.

The fixed version is available in this repository at:
`/tmp/dataset_handlers.cpp` (if accessible) OR manually copy from below.

## Key Changes Needed:

1. **GetInputPins() / GetOutputPins()** - Return `std::vector<Pin>` not `std::vector<PinDefinition>`
2. **Process() method** - Remove this, replace with:
   - `void SetInput(const std::string& pin_name, const BlockValue& value)`
   - `bool Execute()`
   - `BlockValue GetOutput(const std::string& pin_name) const`

3. **Store input values as member variables** instead of using InputValues map

## Corrected API Pattern:

```cpp
class DataRecorderBlock : public IBlock {
    // Member variables to store inputs
    bool record_trigger_;
    float data_stream_1_;
    std::vector<float> data_stream_2_;
    int label_;

    std::vector<Pin> GetInputPins() const override {
        return {
            Pin("record_trigger", "bool", true),
            Pin("data_stream_1", "float", true),
            Pin("data_stream_2", "array", true),
            Pin("label", "int", true)
        };
    }

    void SetInput(const std::string& pin_name, const BlockValue& value) override {
        if (pin_name == "record_trigger") {
            if (std::holds_alternative<bool>(value)) {
                record_trigger_ = std::get<bool>(value);
            }
        }
        // ... handle other inputs
    }

    bool Execute() override {
        // Check trigger and start/stop recording
        if (record_trigger_ && !is_recording_) {
            StartRecording();
        }

        // If recording, save current sample
        if (is_recording_) {
            RecordSample();
        }

        return true;
    }

    BlockValue GetOutput(const std::string& pin_name) const override {
        if (pin_name == "recording_status") {
            return is_recording_;
        }
        return false;
    }
};
```

## After Fixing:
1. Rebuild: `cd build && cmake .. && make`
2. Test the data recorder

## Current Status:
- ❌ data_recorder_block.cpp uses WRONG API
- ✅ All other files (web_server.cpp, widgets, CSS) are CORRECT
- ✅ WebSocket commands added
- ✅ API routes added
- ✅ Handler methods added

**Only the data recorder block.cpp needs to be rewritten to match the actual block_interface.hpp API.**
