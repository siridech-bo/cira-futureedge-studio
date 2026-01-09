# Properties Panel Customization

This guide explains how to add custom UI controls (dropdowns, sliders, etc.) to the Properties Panel in Pipeline Builder.

## Overview

The Properties Panel displays node configuration in the right sidebar. By default, all config parameters are shown as text input fields. You can customize specific parameters to use:

- **Dropdowns** - For predefined choices
- **Sliders** - For numeric ranges
- **Hex input** - For addresses
- **Color pickers** - For color values
- **File pickers** - For file paths

---

## File Location

**File**: `pipeline_builder/src/ui/properties_panel.cpp`

All customization happens in the `RenderProperties()` method around line 85-130.

---

## Adding a Dropdown

### Example: Adding `output_format` Dropdown

**Real example from Data Recorder block:**

```cpp
void PropertiesPanel::RenderProperties() {
    // ... existing code ...

    for (auto& [key, value] : node->config) {
        // ... buffer setup ...

        ImGui::Text("%s:", key.c_str());
        ImGui::SameLine(150);
        ImGui::SetNextItemWidth(-1);

        // Different input types based on key name
        if (key == "signal_type") {
            // Existing dropdown for signal type
            const char* signal_types[] = {"dataset", "sine", "square", "triangular", "sawtooth", "noise", "constant"};
            int current_item = 0;
            for (int i = 0; i < 7; i++) {
                if (value == signal_types[i]) {
                    current_item = i;
                    break;
                }
            }

            if (edit_mode_) {
                if (ImGui::Combo("##value", &current_item, signal_types, 7)) {
                    value = signal_types[current_item];
                }
            } else {
                int temp = current_item;
                ImGui::Combo("##value", &temp, signal_types, 7, ImGuiComboFlags_NoArrowButton);
            }
        }
        // ========== ADD NEW DROPDOWN HERE ==========
        else if (key == "output_format") {
            // Dropdown for output format selection
            const char* output_formats[] = {"csv", "json", "cbor"};
            int current_item = 0;

            // Find current selection
            for (int i = 0; i < 3; i++) {
                if (value == output_formats[i]) {
                    current_item = i;
                    break;
                }
            }

            // Render dropdown
            if (edit_mode_) {
                if (ImGui::Combo("##value", &current_item, output_formats, 3)) {
                    value = output_formats[current_item];
                }
            } else {
                int temp = current_item;
                ImGui::Combo("##value", &temp, output_formats, 3, ImGuiComboFlags_NoArrowButton);
            }
        }
        // ========== END NEW DROPDOWN ==========
        else if (key.find("addr") != std::string::npos) {
            // ... existing hex input ...
        }
        // ... rest of the conditions ...
    }
}
```

### Dropdown Template

```cpp
else if (key == "YOUR_PARAM_NAME") {
    // Define options
    const char* options[] = {"option1", "option2", "option3"};
    const int num_options = 3;
    int current_item = 0;

    // Find current selection
    for (int i = 0; i < num_options; i++) {
        if (value == options[i]) {
            current_item = i;
            break;
        }
    }

    // Render dropdown (editable in edit mode, read-only otherwise)
    if (edit_mode_) {
        if (ImGui::Combo("##value", &current_item, options, num_options)) {
            value = options[current_item];  // Update value when changed
        }
    } else {
        int temp = current_item;
        ImGui::Combo("##value", &temp, options, num_options, ImGuiComboFlags_NoArrowButton);
    }
}
```

---

## Adding a Slider

### Integer Slider

```cpp
else if (key == "sample_rate") {
    int int_value = std::stoi(value);
    int min_value = 1;
    int max_value = 1000;

    if (edit_mode_) {
        if (ImGui::SliderInt("##value", &int_value, min_value, max_value)) {
            value = std::to_string(int_value);
        }
    } else {
        ImGui::SliderInt("##value", &int_value, min_value, max_value, "%d", ImGuiSliderFlags_NoInput);
    }
}
```

### Float Slider

```cpp
else if (key == "gain") {
    float float_value = std::stof(value);
    float min_value = 0.0f;
    float max_value = 10.0f;

    if (edit_mode_) {
        if (ImGui::SliderFloat("##value", &float_value, min_value, max_value, "%.2f")) {
            value = std::to_string(float_value);
        }
    } else {
        ImGui::SliderFloat("##value", &float_value, min_value, max_value, "%.2f", ImGuiSliderFlags_NoInput);
    }
}
```

---

## Specialized Input Types

### Hex Address Input

**Already implemented** for keys containing "addr" or "0x":

```cpp
else if (key.find("addr") != std::string::npos || key.find("0x") != std::string::npos) {
    // Hex input
    if (edit_mode_) {
        if (ImGui::InputText("##value", buffer, sizeof(buffer))) {
            value = buffer;
        }
    } else {
        ImGui::InputText("##value", buffer, sizeof(buffer), ImGuiInputTextFlags_ReadOnly);
    }
}
```

### Pin Number Input

**Already implemented** for keys containing "pin":

```cpp
else if (key.find("pin") != std::string::npos) {
    // Pin selector
    if (edit_mode_) {
        if (ImGui::InputText("##value", buffer, sizeof(buffer))) {
            value = buffer;
        }
    } else {
        ImGui::InputText("##value", buffer, sizeof(buffer), ImGuiInputTextFlags_ReadOnly);
    }
}
```

### File Path Picker

```cpp
else if (key == "model_path" || key == "config_file") {
    if (edit_mode_) {
        ImGui::InputText("##value", buffer, sizeof(buffer));
        ImGui::SameLine();
        if (ImGui::Button("Browse...")) {
            // TODO: Add file dialog
            // value = ShowFileDialog();
        }
    } else {
        ImGui::InputText("##value", buffer, sizeof(buffer), ImGuiInputTextFlags_ReadOnly);
    }
}
```

### Color Picker

```cpp
else if (key == "color" || key.find("color") != std::string::npos) {
    // Parse hex color "#RRGGBB"
    float color[3] = {0.0f, 0.0f, 0.0f};
    if (value.length() == 7 && value[0] == '#') {
        int r, g, b;
        sscanf(value.c_str(), "#%02x%02x%02x", &r, &g, &b);
        color[0] = r / 255.0f;
        color[1] = g / 255.0f;
        color[2] = b / 255.0f;
    }

    if (edit_mode_) {
        if (ImGui::ColorEdit3("##value", color)) {
            char hex[8];
            sprintf(hex, "#%02x%02x%02x",
                (int)(color[0] * 255),
                (int)(color[1] * 255),
                (int)(color[2] * 255));
            value = hex;
        }
    } else {
        ImGui::ColorEdit3("##value", color, ImGuiColorEditFlags_NoInputs | ImGuiColorEditFlags_NoPicker);
    }
}
```

---

## Conditional Controls

### Show Control Based on Another Value

```cpp
// Example: Show "threshold" slider only when "mode" is "threshold"
if (key == "threshold") {
    // Check if mode is "threshold"
    auto mode_it = node->config.find("mode");
    if (mode_it != node->config.end() && mode_it->second == "threshold") {
        // Show threshold slider
        float threshold = std::stof(value);
        if (edit_mode_) {
            if (ImGui::SliderFloat("##value", &threshold, 0.0f, 1.0f)) {
                value = std::to_string(threshold);
            }
        }
    } else {
        // Hide or show disabled
        ImGui::TextDisabled("(Not applicable)");
    }
}
```

---

## Multi-Value Inputs

### Comma-Separated List Editor

```cpp
else if (key == "class_names") {
    // Show as multi-line text area
    char buffer[512];
    strncpy_s(buffer, sizeof(buffer), value.c_str(), _TRUNCATE);

    if (edit_mode_) {
        if (ImGui::InputTextMultiline("##value", buffer, sizeof(buffer), ImVec2(-1, 100))) {
            value = buffer;
        }
        ImGui::TextDisabled("Comma-separated: idle,shake,snake,updown");
    } else {
        ImGui::InputTextMultiline("##value", buffer, sizeof(buffer), ImVec2(-1, 100), ImGuiInputTextFlags_ReadOnly);
    }
}
```

---

## Complete Example: Adding Multiple Custom Controls

**File**: `pipeline_builder/src/ui/properties_panel.cpp`

```cpp
void PropertiesPanel::RenderProperties() {
    // ... existing code ...

    for (auto& [key, value] : node->config) {
        char buffer[256];
        strncpy_s(buffer, sizeof(buffer), value.c_str(), _TRUNCATE);

        ImGui::Text("%s:", key.c_str());
        ImGui::SameLine(150);
        ImGui::SetNextItemWidth(-1);

        // ========== CUSTOM CONTROLS ==========

        // Dropdown for signal type
        if (key == "signal_type") {
            const char* signal_types[] = {"dataset", "sine", "square", "triangular", "sawtooth", "noise", "constant"};
            int current_item = 0;
            for (int i = 0; i < 7; i++) {
                if (value == signal_types[i]) { current_item = i; break; }
            }
            if (edit_mode_) {
                if (ImGui::Combo("##value", &current_item, signal_types, 7)) {
                    value = signal_types[current_item];
                }
            } else {
                int temp = current_item;
                ImGui::Combo("##value", &temp, signal_types, 7, ImGuiComboFlags_NoArrowButton);
            }
        }

        // Dropdown for output format
        else if (key == "output_format") {
            const char* formats[] = {"csv", "json", "cbor"};
            int current_item = 0;
            for (int i = 0; i < 3; i++) {
                if (value == formats[i]) { current_item = i; break; }
            }
            if (edit_mode_) {
                if (ImGui::Combo("##value", &current_item, formats, 3)) {
                    value = formats[current_item];
                }
            } else {
                int temp = current_item;
                ImGui::Combo("##value", &temp, formats, 3, ImGuiComboFlags_NoArrowButton);
            }
        }

        // Slider for sample rate
        else if (key == "sample_rate") {
            int rate = std::stoi(value);
            if (edit_mode_) {
                if (ImGui::SliderInt("##value", &rate, 1, 1000)) {
                    value = std::to_string(rate);
                }
            } else {
                ImGui::SliderInt("##value", &rate, 1, 1000, "%d Hz", ImGuiSliderFlags_NoInput);
            }
        }

        // Hex input for addresses
        else if (key.find("addr") != std::string::npos) {
            if (edit_mode_) {
                if (ImGui::InputText("##value", buffer, sizeof(buffer))) {
                    value = buffer;
                }
            } else {
                ImGui::InputText("##value", buffer, sizeof(buffer), ImGuiInputTextFlags_ReadOnly);
            }
        }

        // Default: Regular text input
        else {
            if (edit_mode_) {
                if (ImGui::InputText("##value", buffer, sizeof(buffer))) {
                    value = buffer;
                }
            } else {
                ImGui::InputText("##value", buffer, sizeof(buffer), ImGuiInputTextFlags_ReadOnly);
            }
        }
    }

    // ... rest of the code ...
}
```

---

## Testing Custom Controls

1. **Rebuild Pipeline Builder**:
   ```bash
   cd pipeline_builder/build
   cmake --build . --config Release
   ```

2. **Test in Pipeline Builder**:
   - Open Pipeline Builder
   - Add a node with the custom property
   - Click on the node to open Properties Panel
   - Click "Edit Configuration"
   - Verify the custom control appears (dropdown, slider, etc.)
   - Change the value
   - Click "Apply"
   - Save and deploy

3. **Verify on Jetson**:
   ```bash
   # Check the deployed manifest contains the correct value
   ssh user@jetson_ip
   cat /home/user/cira_projects/cira-runtime/manifests/block_manifest.json | grep -A 5 "your_param"
   ```

---

## ImGui Control Reference

### Common Widgets

```cpp
// Text input
ImGui::InputText("##label", buffer, size);

// Multiline text
ImGui::InputTextMultiline("##label", buffer, size, ImVec2(width, height));

// Integer input
ImGui::InputInt("##label", &int_value);

// Float input
ImGui::InputFloat("##label", &float_value);

// Checkbox
ImGui::Checkbox("##label", &bool_value);

// Slider (int)
ImGui::SliderInt("##label", &int_value, min, max);

// Slider (float)
ImGui::SliderFloat("##label", &float_value, min, max, "%.2f");

// Dropdown/Combo box
ImGui::Combo("##label", &current_item, items_array, num_items);

// Color picker
ImGui::ColorEdit3("##label", color_float3);
ImGui::ColorEdit4("##label", color_float4);  // With alpha

// Button
if (ImGui::Button("Click Me")) {
    // Handle click
}
```

### Flags

```cpp
// Input flags
ImGuiInputTextFlags_ReadOnly
ImGuiInputTextFlags_Password
ImGuiInputTextFlags_CharsDecimal
ImGuiInputTextFlags_CharsHexadecimal

// Combo flags
ImGuiComboFlags_NoArrowButton    // Hide dropdown arrow
ImGuiComboFlags_PopupAlignLeft   // Left-align popup

// Slider flags
ImGuiSliderFlags_NoInput         // Hide text input
ImGuiSliderFlags_Logarithmic     // Logarithmic scale

// Color edit flags
ImGuiColorEditFlags_NoInputs     // Hide RGB inputs
ImGuiColorEditFlags_NoPicker     // Disable color picker popup
```

---

## Advanced: Dynamic Property Types

If you want to define property types in block metadata instead of hardcoding in properties_panel.cpp:

### In Block Definition

```cpp
// In timesnet_model_node.hpp
SetDefaultConfig("output_format", "csv");
SetConfigMetadata("output_format", "type", "dropdown");
SetConfigMetadata("output_format", "options", "csv,json,cbor");
```

### In Properties Panel

```cpp
// Check for metadata
auto type_it = node->config_metadata.find(key + "_type");
if (type_it != node->config_metadata.end() && type_it->second == "dropdown") {
    // Parse options
    auto options_it = node->config_metadata.find(key + "_options");
    if (options_it != node->config_metadata.end()) {
        // Split options and render dropdown
    }
}
```

**Note**: This requires extending the data structures in the Pipeline Builder. For simple cases, hardcoding in properties_panel.cpp is sufficient.

---

## Common Issues

### Problem: Dropdown doesn't show correct value

**Solution**: Check the loop that finds `current_item`:
```cpp
for (int i = 0; i < num_options; i++) {
    if (value == options[i]) {
        current_item = i;
        break;  // ← Make sure to break!
    }
}
```

### Problem: Value doesn't update when dropdown changes

**Solution**: Make sure to assign back to `value`:
```cpp
if (ImGui::Combo("##value", &current_item, options, num_options)) {
    value = options[current_item];  // ← This updates the config
}
```

### Problem: Control is disabled in edit mode

**Solution**: Check that it's inside the `if (edit_mode_)` block:
```cpp
if (edit_mode_) {
    // Editable controls here
} else {
    // Read-only display here
}
```

---

## Checklist for Adding Custom Controls

- [ ] Identify the config parameter key name
- [ ] Determine control type (dropdown, slider, etc.)
- [ ] Add `else if (key == "param_name")` condition in properties_panel.cpp
- [ ] Implement control for `edit_mode_ == true` (editable)
- [ ] Implement control for `edit_mode_ == false` (read-only display)
- [ ] Update `value` variable when control changes
- [ ] Rebuild Pipeline Builder
- [ ] Test in Pipeline Builder UI
- [ ] Verify value is saved in .ciraproject file
- [ ] Verify value is deployed to Jetson correctly
