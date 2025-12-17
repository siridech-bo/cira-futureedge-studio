# C++ Pipeline Builder - Complete I/O Integration
## Phased Implementation with Full Sensor & Output Support

**Date:** 2025-12-15
**Goal:** Build complete pipeline builder with comprehensive I/O support
**Platforms:** Jetson Nano (DL) + Arduino Uno (ML)
**Total Timeline:** 5-6 weeks

---

## Overview: Enhanced Architecture

```
Pipeline Builder (C++ + imgui-node-editor)
══════════════════════════════════════════

Input Nodes:                Processing Nodes:           Output Nodes:
┌─────────────┐            ┌─────────────┐            ┌─────────────┐
│ MPU6050     │            │ Normalize   │            │ GPIO        │
│ ADXL345     │            │ Window      │            │ PWM/Servo   │
│ BME280      │  ────────► │ Filter      │  ────────► │ OLED        │
│ Analog ADC  │            │ FFT         │            │ MQTT        │
│ Camera*     │            │ TimesNet    │            │ HTTP API    │
│ GPIO In     │            │ Decision    │            │ WebSocket   │
└─────────────┘            │   Tree      │            │ AWS IoT     │
                           └─────────────┘            │ Azure IoT   │
                                                      └─────────────┘

* Camera only for Jetson Nano
```

---

## Phase 1: Foundation + Basic I/O (Week 1)

**Goal:** Get editor working with 3 input nodes + 2 output nodes

### **Deliverables:**

✅ Basic application window with imgui-node-editor
✅ **Input Nodes:** MPU6050, ADXL345, AnalogInput
✅ **Output Nodes:** GPIO, Serial
✅ Can connect nodes and see properties

### **New Files (Phase 1):**

#### **src/core/node_types.hpp**

```cpp
#pragma once
#include <string>
#include <vector>
#include <map>

enum class NodeCategory {
    Input,
    Processing,
    Output
};

enum class InterfaceType {
    I2C,
    SPI,
    Analog,
    GPIO,
    Network,
    Cloud,
    None
};

struct PinConfig {
    std::string name;
    std::string type;  // "vector3", "float", "int", "bool"
    bool is_input;
};

struct NodeTypeDefinition {
    std::string type_id;
    std::string display_name;
    std::string description;
    NodeCategory category;
    InterfaceType interface;
    std::vector<PinConfig> pins;
    std::map<std::string, std::string> default_config;
    std::string icon;  // Emoji or icon identifier
};

// Node type registry
class NodeTypeRegistry {
public:
    static NodeTypeRegistry& Instance();

    void RegisterNodeType(const NodeTypeDefinition& def);
    const NodeTypeDefinition* GetNodeType(const std::string& type_id) const;
    std::vector<NodeTypeDefinition> GetNodesByCategory(NodeCategory category) const;

private:
    NodeTypeRegistry();
    std::map<std::string, NodeTypeDefinition> node_types_;
};
```

#### **src/core/node_registry.cpp**

```cpp
#include "node_types.hpp"

NodeTypeRegistry& NodeTypeRegistry::Instance() {
    static NodeTypeRegistry instance;
    return instance;
}

NodeTypeRegistry::NodeTypeRegistry() {
    // ════════════════════════════════════════════════════════════
    // INPUT NODES
    // ════════════════════════════════════════════════════════════

    // MPU6050 - 6-axis IMU
    RegisterNodeType({
        .type_id = "MPU6050",
        .display_name = "MPU6050 IMU",
        .description = "6-axis accelerometer + gyroscope sensor",
        .category = NodeCategory::Input,
        .interface = InterfaceType::I2C,
        .pins = {
            {"accel_out", "vector3", false},
            {"gyro_out", "vector3", false}
        },
        .default_config = {
            {"i2c_bus", "1"},
            {"i2c_addr", "0x68"},
            {"sample_rate", "100"},
            {"accel_range", "±4g"},
            {"gyro_range", "±500°/s"},
            {"sda_pin", "3"},
            {"scl_pin", "5"}
        },
        .icon = "📡"
    });

    // ADXL345 - 3-axis Accelerometer
    RegisterNodeType({
        .type_id = "ADXL345",
        .display_name = "ADXL345 Accel",
        .description = "3-axis digital accelerometer",
        .category = NodeCategory::Input,
        .interface = InterfaceType::I2C,
        .pins = {
            {"accel_out", "vector3", false}
        },
        .default_config = {
            {"i2c_bus", "1"},
            {"i2c_addr", "0x53"},
            {"sample_rate", "100"},
            {"range", "±4g"},
            {"sda_pin", "3"},
            {"scl_pin", "5"}
        },
        .icon = "📡"
    });

    // BME280 - Environmental Sensor
    RegisterNodeType({
        .type_id = "BME280",
        .display_name = "BME280 Env",
        .description = "Temperature, humidity, pressure sensor",
        .category = NodeCategory::Input,
        .interface = InterfaceType::I2C,
        .pins = {
            {"temp_out", "float", false},
            {"humidity_out", "float", false},
            {"pressure_out", "float", false}
        },
        .default_config = {
            {"i2c_bus", "1"},
            {"i2c_addr", "0x76"},
            {"sample_rate", "1"},
            {"sda_pin", "3"},
            {"scl_pin", "5"}
        },
        .icon = "🌡️"
    });

    // Analog Input
    RegisterNodeType({
        .type_id = "AnalogInput",
        .display_name = "Analog ADC",
        .description = "Generic analog input (voltage, light, etc.)",
        .category = NodeCategory::Input,
        .interface = InterfaceType::Analog,
        .pins = {
            {"value_out", "float", false}
        },
        .default_config = {
            {"pin", "A0"},
            {"sample_rate", "10"},
            {"voltage_range", "0-3.3"},
            {"averaging", "10"}
        },
        .icon = "📊"
    });

    // GPIO Input (for buttons, switches)
    RegisterNodeType({
        .type_id = "GPIOInput",
        .display_name = "GPIO Input",
        .description = "Digital input (button, switch, sensor)",
        .category = NodeCategory::Input,
        .interface = InterfaceType::GPIO,
        .pins = {
            {"state_out", "bool", false}
        },
        .default_config = {
            {"pin", "7"},
            {"pull_mode", "PULL_UP"},
            {"debounce_ms", "50"}
        },
        .icon = "🔘"
    });

    // ════════════════════════════════════════════════════════════
    // PROCESSING NODES
    // ════════════════════════════════════════════════════════════

    // Normalize
    RegisterNodeType({
        .type_id = "Normalize",
        .display_name = "Normalize",
        .description = "Z-score or Min-Max normalization",
        .category = NodeCategory::Processing,
        .interface = InterfaceType::None,
        .pins = {
            {"data_in", "any", true},
            {"data_out", "same", false}
        },
        .default_config = {
            {"method", "z-score"},
            {"mean", "0.0,0.0,9.81"},
            {"std", "2.5,2.5,2.5"}
        },
        .icon = "📏"
    });

    // Sliding Window
    RegisterNodeType({
        .type_id = "SlidingWindow",
        .display_name = "Sliding Window",
        .description = "Create sliding windows from stream",
        .category = NodeCategory::Processing,
        .interface = InterfaceType::None,
        .pins = {
            {"stream_in", "any", true},
            {"window_out", "window", false}
        },
        .default_config = {
            {"window_size", "100"},
            {"stride", "20"}
        },
        .icon = "🪟"
    });

    // Low-Pass Filter
    RegisterNodeType({
        .type_id = "LowPassFilter",
        .display_name = "Low-Pass Filter",
        .description = "Remove high-frequency noise",
        .category = NodeCategory::Processing,
        .interface = InterfaceType::None,
        .pins = {
            {"signal_in", "any", true},
            {"filtered_out", "same", false}
        },
        .default_config = {
            {"cutoff_freq", "10"},
            {"order", "2"}
        },
        .icon = "🎛️"
    });

    // TimesNet Model
    RegisterNodeType({
        .type_id = "TimesNet",
        .display_name = "TimesNet Model",
        .description = "Deep learning time-series classifier",
        .category = NodeCategory::Processing,
        .interface = InterfaceType::None,
        .pins = {
            {"data_in", "window", true},
            {"prediction_out", "int", false},
            {"confidence_out", "float", false}
        },
        .default_config = {
            {"model_file", "model.onnx"},
            {"input_shape", "100,3"},
            {"num_classes", "2"},
            {"backend", "tensorrt"}  // or "onnx"
        },
        .icon = "🧠"
    });

    // Decision Tree
    RegisterNodeType({
        .type_id = "DecisionTree",
        .display_name = "Decision Tree",
        .description = "Classical ML classifier",
        .category = NodeCategory::Processing,
        .interface = InterfaceType::None,
        .pins = {
            {"features_in", "vector", true},
            {"prediction_out", "int", false}
        },
        .default_config = {
            {"model_file", "tree.json"},
            {"num_classes", "2"}
        },
        .icon = "🌳"
    });

    // ════════════════════════════════════════════════════════════
    // OUTPUT NODES - LOCAL
    // ════════════════════════════════════════════════════════════

    // GPIO Output (LED, Relay, etc.)
    RegisterNodeType({
        .type_id = "GPIOOutput",
        .display_name = "GPIO Output",
        .description = "Digital output (LED, relay, solenoid)",
        .category = NodeCategory::Output,
        .interface = InterfaceType::GPIO,
        .pins = {
            {"trigger_in", "int", true}
        },
        .default_config = {
            {"pin", "7"},
            {"active_high", "true"},
            {"trigger_value", "1"},
            {"duration_ms", "5000"},
            {"pulse_mode", "false"}
        },
        .icon = "💡"
    });

    // PWM Output (Servo, Motor, Dimmer)
    RegisterNodeType({
        .type_id = "PWMOutput",
        .display_name = "PWM Output",
        .description = "Servo motor or PWM control",
        .category = NodeCategory::Output,
        .interface = InterfaceType::GPIO,
        .pins = {
            {"value_in", "float", true}
        },
        .default_config = {
            {"pin", "9"},
            {"frequency", "50"},
            {"min_duty", "5"},
            {"max_duty", "10"},
            {"servo_mode", "true"}
        },
        .icon = "🔧"
    });

    // OLED Display
    RegisterNodeType({
        .type_id = "OLEDDisplay",
        .display_name = "OLED Display",
        .description = "128x64 I2C OLED screen",
        .category = NodeCategory::Output,
        .interface = InterfaceType::I2C,
        .pins = {
            {"text_in", "string", true},
            {"value_in", "int", true}
        },
        .default_config = {
            {"i2c_bus", "1"},
            {"i2c_addr", "0x3C"},
            {"width", "128"},
            {"height", "64"},
            {"sda_pin", "3"},
            {"scl_pin", "5"}
        },
        .icon = "🖥️"
    });

    // Serial Output
    RegisterNodeType({
        .type_id = "SerialOutput",
        .display_name = "Serial Output",
        .description = "Output to serial console",
        .category = NodeCategory::Output,
        .interface = InterfaceType::GPIO,
        .pins = {
            {"data_in", "any", true}
        },
        .default_config = {
            {"baud_rate", "115200"},
            {"format", "Prediction: {value}"},
            {"newline", "true"}
        },
        .icon = "📟"
    });

    // ════════════════════════════════════════════════════════════
    // OUTPUT NODES - NETWORK
    // ════════════════════════════════════════════════════════════

    // MQTT Publisher
    RegisterNodeType({
        .type_id = "MQTTPublisher",
        .display_name = "MQTT Publisher",
        .description = "Publish to MQTT broker",
        .category = NodeCategory::Output,
        .interface = InterfaceType::Network,
        .pins = {
            {"data_in", "any", true}
        },
        .default_config = {
            {"broker", "broker.hivemq.com"},
            {"port", "1883"},
            {"topic", "cira/predictions"},
            {"qos", "1"},
            {"retain", "false"},
            {"client_id", "cira_device"},
            {"username", ""},
            {"password", ""},
            {"payload_template", R"({"device":"{{device}}","prediction":{{value}},"timestamp":{{timestamp}}})"}
        },
        .icon = "📡"
    });

    // HTTP POST
    RegisterNodeType({
        .type_id = "HTTPPost",
        .display_name = "HTTP POST",
        .description = "Send HTTP POST request",
        .category = NodeCategory::Output,
        .interface = InterfaceType::Network,
        .pins = {
            {"data_in", "any", true}
        },
        .default_config = {
            {"url", "https://your-api.com/predictions"},
            {"method", "POST"},
            {"content_type", "application/json"},
            {"headers", "Authorization: Bearer TOKEN"},
            {"body_template", R"({"prediction":{{value}},"timestamp":{{timestamp}}})"},
            {"timeout_ms", "5000"}
        },
        .icon = "🌐"
    });

    // WebSocket
    RegisterNodeType({
        .type_id = "WebSocket",
        .display_name = "WebSocket",
        .description = "Real-time WebSocket connection",
        .category = NodeCategory::Output,
        .interface = InterfaceType::Network,
        .pins = {
            {"data_in", "any", true}
        },
        .default_config = {
            {"url", "ws://your-server.com/live"},
            {"protocol", ""},
            {"reconnect", "true"},
            {"message_template", R"({"type":"prediction","value":{{value}}})"}
        },
        .icon = "🔌"
    });

    // ════════════════════════════════════════════════════════════
    // OUTPUT NODES - CLOUD
    // ════════════════════════════════════════════════════════════

    // AWS IoT Core
    RegisterNodeType({
        .type_id = "AWSIoT",
        .display_name = "AWS IoT Core",
        .description = "Publish to AWS IoT Core",
        .category = NodeCategory::Output,
        .interface = InterfaceType::Cloud,
        .pins = {
            {"telemetry_in", "any", true}
        },
        .default_config = {
            {"endpoint", "xxxxx.iot.us-east-1.amazonaws.com"},
            {"port", "8883"},
            {"thing_name", "my_device"},
            {"topic", "devices/my_device/telemetry"},
            {"root_ca", "root-CA.crt"},
            {"certificate", "certificate.pem"},
            {"private_key", "private.key"}
        },
        .icon = "☁️"
    });

    // Azure IoT Hub
    RegisterNodeType({
        .type_id = "AzureIoT",
        .display_name = "Azure IoT Hub",
        .description = "Send messages to Azure IoT Hub",
        .category = NodeCategory::Output,
        .interface = InterfaceType::Cloud,
        .pins = {
            {"message_in", "any", true}
        },
        .default_config = {
            {"connection_string", "HostName=xxx.azure-devices.net;DeviceId=xxx;SharedAccessKey=xxx"},
            {"device_id", "my_device"},
            {"message_template", R"({"prediction":{{value}}})"}
        },
        .icon = "☁️"
    });

    // Google Cloud IoT
    RegisterNodeType({
        .type_id = "GoogleCloudIoT",
        .display_name = "Google Cloud IoT",
        .description = "Publish to Google Cloud IoT Core",
        .category = NodeCategory::Output,
        .interface = InterfaceType::Cloud,
        .pins = {
            {"data_in", "any", true}
        },
        .default_config = {
            {"project_id", "my-project"},
            {"region", "us-central1"},
            {"registry_id", "my-registry"},
            {"device_id", "my-device"},
            {"private_key", "rsa_private.pem"},
            {"algorithm", "RS256"}
        },
        .icon = "☁️"
    });
}

void NodeTypeRegistry::RegisterNodeType(const NodeTypeDefinition& def) {
    node_types_[def.type_id] = def;
}

const NodeTypeDefinition* NodeTypeRegistry::GetNodeType(const std::string& type_id) const {
    auto it = node_types_.find(type_id);
    return (it != node_types_.end()) ? &it->second : nullptr;
}

std::vector<NodeTypeDefinition> NodeTypeRegistry::GetNodesByCategory(NodeCategory category) const {
    std::vector<NodeTypeDefinition> result;
    for (const auto& [id, def] : node_types_) {
        if (def.category == category) {
            result.push_back(def);
        }
    }
    return result;
}
```

#### **src/ui/block_library_panel.cpp** (Enhanced)

```cpp
#include "block_library_panel.hpp"
#include "../core/node_registry.hpp"
#include <imgui.h>

void BlockLibraryPanel::Render(PipelineEditor* editor) {
    ImGui::BeginChild("BlockLibrary", ImVec2(0, 0), true);

    ImGui::Text("Block Library");
    ImGui::Separator();

    auto& registry = NodeTypeRegistry::Instance();

    // ═══════════════════════════════════════════════════════
    // INPUT NODES
    // ═══════════════════════════════════════════════════════
    if (ImGui::CollapsingHeader("📡 Input Sensors", ImGuiTreeNodeFlags_DefaultOpen)) {
        auto input_nodes = registry.GetNodesByCategory(NodeCategory::Input);

        for (const auto& node_def : input_nodes) {
            std::string button_label = node_def.icon + " " + node_def.display_name;

            if (ImGui::Button(button_label.c_str(), ImVec2(-1, 0))) {
                editor->AddNode(node_def.type_id);
            }

            // Tooltip
            if (ImGui::IsItemHovered()) {
                ImGui::BeginTooltip();
                ImGui::Text("%s", node_def.description.c_str());
                ImGui::Separator();
                ImGui::TextColored(ImVec4(0.6f, 0.8f, 1.0f, 1.0f),
                    "Interface: %s", GetInterfaceName(node_def.interface));
                ImGui::EndTooltip();
            }
        }
    }

    // ═══════════════════════════════════════════════════════
    // PROCESSING NODES
    // ═══════════════════════════════════════════════════════
    if (ImGui::CollapsingHeader("🔄 Processing", ImGuiTreeNodeFlags_DefaultOpen)) {
        auto processing_nodes = registry.GetNodesByCategory(NodeCategory::Processing);

        for (const auto& node_def : processing_nodes) {
            std::string button_label = node_def.icon + " " + node_def.display_name;

            if (ImGui::Button(button_label.c_str(), ImVec2(-1, 0))) {
                editor->AddNode(node_def.type_id);
            }

            if (ImGui::IsItemHovered()) {
                ImGui::BeginTooltip();
                ImGui::Text("%s", node_def.description.c_str());
                ImGui::EndTooltip();
            }
        }
    }

    // ═══════════════════════════════════════════════════════
    // OUTPUT NODES
    // ═══════════════════════════════════════════════════════
    if (ImGui::CollapsingHeader("📤 Outputs", ImGuiTreeNodeFlags_DefaultOpen)) {
        auto output_nodes = registry.GetNodesByCategory(NodeCategory::Output);

        // Group by interface type
        std::map<InterfaceType, std::vector<NodeTypeDefinition>> grouped;
        for (const auto& node : output_nodes) {
            grouped[node.interface].push_back(node);
        }

        // Local outputs
        if (!grouped[InterfaceType::GPIO].empty()) {
            ImGui::Text("  Local Outputs:");
            for (const auto& node_def : grouped[InterfaceType::GPIO]) {
                std::string button_label = "  " + node_def.icon + " " + node_def.display_name;
                if (ImGui::Button(button_label.c_str(), ImVec2(-1, 0))) {
                    editor->AddNode(node_def.type_id);
                }
            }
        }

        // Network outputs
        if (!grouped[InterfaceType::Network].empty()) {
            ImGui::Spacing();
            ImGui::Text("  Network Outputs:");
            for (const auto& node_def : grouped[InterfaceType::Network]) {
                std::string button_label = "  " + node_def.icon + " " + node_def.display_name;
                if (ImGui::Button(button_label.c_str(), ImVec2(-1, 0))) {
                    editor->AddNode(node_def.type_id);
                }
            }
        }

        // Cloud outputs
        if (!grouped[InterfaceType::Cloud].empty()) {
            ImGui::Spacing();
            ImGui::Text("  Cloud Services:");
            for (const auto& node_def : grouped[InterfaceType::Cloud]) {
                std::string button_label = "  " + node_def.icon + " " + node_def.display_name;
                if (ImGui::Button(button_label.c_str(), ImVec2(-1, 0))) {
                    editor->AddNode(node_def.type_id);
                }
            }
        }
    }

    ImGui::EndChild();
}

const char* BlockLibraryPanel::GetInterfaceName(InterfaceType type) {
    switch (type) {
        case InterfaceType::I2C: return "I2C";
        case InterfaceType::SPI: return "SPI";
        case InterfaceType::Analog: return "Analog";
        case InterfaceType::GPIO: return "GPIO";
        case InterfaceType::Network: return "Network";
        case InterfaceType::Cloud: return "Cloud";
        default: return "None";
    }
}
```

---

## Phase 2: Complete Node Properties (Week 2)

**Goal:** All nodes have full property editors with validation

### **Deliverables:**

✅ Dynamic property forms for all 20+ node types
✅ Pin configuration (for Jetson/Arduino)
✅ Input validation
✅ Save/Load pipeline to JSON

### **Enhanced Property Panel:**

```cpp
// src/ui/properties_panel.cpp
void PropertiesPanel::RenderNodeProperties(Node* node) {
    if (!node) return;

    auto node_def = NodeTypeRegistry::Instance().GetNodeType(node->GetType());
    if (!node_def) return;

    ImGui::Text("%s %s", node_def->icon.c_str(), node_def->display_name.c_str());
    ImGui::TextColored(ImVec4(0.6f, 0.6f, 0.6f, 1.0f), "%s", node_def->description.c_str());
    ImGui::Separator();

    // Render properties based on node type
    if (node_def->type_id == "MPU6050") {
        RenderMPU6050Properties(node);
    } else if (node_def->type_id == "MQTTPublisher") {
        RenderMQTTProperties(node);
    } else if (node_def->type_id == "HTTPPost") {
        RenderHTTPProperties(node);
    }
    // ... etc for all node types
}

void PropertiesPanel::RenderMQTTProperties(Node* node) {
    ImGui::Text("MQTT Configuration");
    ImGui::Separator();

    // Broker
    static char broker[256];
    strncpy(broker, node->GetConfig("broker").c_str(), 255);
    if (ImGui::InputText("Broker", broker, 256)) {
        node->SetConfig("broker", broker);
    }
    ImGui::TextColored(ImVec4(0.5f, 0.5f, 0.5f, 1.0f), "Example: broker.hivemq.com");

    // Port
    int port = std::stoi(node->GetConfig("port", "1883"));
    if (ImGui::InputInt("Port", &port)) {
        node->SetConfig("port", std::to_string(port));
    }

    // Topic
    static char topic[256];
    strncpy(topic, node->GetConfig("topic").c_str(), 255);
    if (ImGui::InputText("Topic", topic, 256)) {
        node->SetConfig("topic", topic);
    }
    ImGui::TextColored(ImVec4(0.5f, 0.5f, 0.5f, 1.0f), "Example: cira/device01/predictions");

    // QoS
    const char* qos_items[] = {"0 - At most once", "1 - At least once", "2 - Exactly once"};
    int qos = std::stoi(node->GetConfig("qos", "1"));
    if (ImGui::Combo("QoS", &qos, qos_items, 3)) {
        node->SetConfig("qos", std::to_string(qos));
    }

    // Payload template
    ImGui::Spacing();
    ImGui::Text("Payload Template:");
    static char payload[512];
    strncpy(payload, node->GetConfig("payload_template").c_str(), 511);
    if (ImGui::InputTextMultiline("##payload", payload, 512, ImVec2(-1, 100))) {
        node->SetConfig("payload_template", payload);
    }
    ImGui::TextColored(ImVec4(0.5f, 0.5f, 0.5f, 1.0f),
        "Variables: {{device}}, {{value}}, {{timestamp}}, {{confidence}}");

    // Authentication (collapsible)
    if (ImGui::CollapsingHeader("Authentication (Optional)")) {
        static char username[128];
        strncpy(username, node->GetConfig("username", "").c_str(), 127);
        if (ImGui::InputText("Username", username, 128)) {
            node->SetConfig("username", username);
        }

        static char password[128];
        strncpy(password, node->GetConfig("password", "").c_str(), 127);
        if (ImGui::InputText("Password", password, 128, ImGuiInputTextFlags_Password)) {
            node->SetConfig("password", password);
        }
    }

    // Test connection button
    ImGui::Spacing();
    if (ImGui::Button("Test Connection", ImVec2(-1, 0))) {
        TestMQTTConnection(node->GetConfig("broker"), std::stoi(node->GetConfig("port")));
    }
}

void PropertiesPanel::RenderHTTPProperties(Node* node) {
    ImGui::Text("HTTP Configuration");
    ImGui::Separator();

    // URL
    static char url[512];
    strncpy(url, node->GetConfig("url").c_str(), 511);
    if (ImGui::InputText("URL", url, 512)) {
        node->SetConfig("url", url);
    }

    // Method
    const char* methods[] = {"GET", "POST", "PUT", "DELETE"};
    int method_idx = 1;  // Default POST
    std::string current_method = node->GetConfig("method", "POST");
    for (int i = 0; i < 4; i++) {
        if (current_method == methods[i]) method_idx = i;
    }
    if (ImGui::Combo("Method", &method_idx, methods, 4)) {
        node->SetConfig("method", methods[method_idx]);
    }

    // Content-Type
    const char* content_types[] = {"application/json", "application/x-www-form-urlencoded", "text/plain"};
    int content_type_idx = 0;
    if (ImGui::Combo("Content-Type", &content_type_idx, content_types, 3)) {
        node->SetConfig("content_type", content_types[content_type_idx]);
    }

    // Headers
    ImGui::Spacing();
    ImGui::Text("Headers:");
    static char headers[512];
    strncpy(headers, node->GetConfig("headers", "").c_str(), 511);
    if (ImGui::InputTextMultiline("##headers", headers, 512, ImVec2(-1, 60))) {
        node->SetConfig("headers", headers);
    }
    ImGui::TextColored(ImVec4(0.5f, 0.5f, 0.5f, 1.0f), "One per line: Header-Name: Value");

    // Body template
    ImGui::Spacing();
    ImGui::Text("Request Body:");
    static char body[512];
    strncpy(body, node->GetConfig("body_template").c_str(), 511);
    if (ImGui::InputTextMultiline("##body", body, 512, ImVec2(-1, 100))) {
        node->SetConfig("body_template", body);
    }

    // Timeout
    int timeout = std::stoi(node->GetConfig("timeout_ms", "5000"));
    if (ImGui::InputInt("Timeout (ms)", &timeout)) {
        node->SetConfig("timeout_ms", std::to_string(timeout));
    }

    // Test button
    ImGui::Spacing();
    if (ImGui::Button("Test Request", ImVec2(-1, 0))) {
        TestHTTPRequest(url, node->GetConfig("method"));
    }
}
```

---

## Phase 3: Code Generation Engine (Week 3)

**Goal:** Generate complete deployment packages with all I/O support

### **Template System:**

#### **templates/jetson/main.py.jinja2** (with I/O)

```python
#!/usr/bin/env python3
"""
Auto-generated by CiRA FutureEdge Studio
Pipeline: {{ pipeline_name }}
Platform: NVIDIA Jetson Nano
Generated: {{ timestamp }}
"""

import time
import json
import numpy as np
{% if has_gpio %}
import Jetson.GPIO as GPIO
{% endif %}
{% if has_mqtt %}
import paho.mqtt.client as mqtt
{% endif %}
{% if has_http %}
import requests
{% endif %}
{% if has_websocket %}
import websocket
{% endif %}

# ════════════════════════════════════════════════════════════
# SENSOR IMPORTS
# ════════════════════════════════════════════════════════════
{% for node in input_nodes %}
{% if node.type == "MPU6050" %}
from sensor_mpu6050 import MPU6050
{% elif node.type == "ADXL345" %}
from sensor_adxl345 import ADXL345
{% elif node.type == "BME280" %}
from sensor_bme280 import BME280
{% endif %}
{% endfor %}

# ════════════════════════════════════════════════════════════
# MODEL IMPORTS
# ════════════════════════════════════════════════════════════
{% for node in processing_nodes %}
{% if node.type == "TimesNet" %}
from model_timesnet import TimesNetInference
{% elif node.type == "DecisionTree" %}
from model_decision_tree import DecisionTreeClassifier
{% endif %}
{% endfor %}

# ════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════
{% for node in input_nodes %}
{% if node.type == "MPU6050" %}
MPU6050_I2C_BUS = {{ node.config.i2c_bus }}
MPU6050_ADDR = {{ node.config.i2c_addr }}
MPU6050_SAMPLE_RATE = {{ node.config.sample_rate }}
{% endif %}
{% endfor %}

{% for node in output_nodes %}
{% if node.type == "GPIOOutput" %}
GPIO_PIN_{{ loop.index }} = {{ node.config.pin }}
GPIO_DURATION_{{ loop.index }} = {{ node.config.duration_ms }}
{% elif node.type == "MQTTPublisher" %}
MQTT_BROKER = "{{ node.config.broker }}"
MQTT_PORT = {{ node.config.port }}
MQTT_TOPIC = "{{ node.config.topic }}"
MQTT_QOS = {{ node.config.qos }}
{% elif node.type == "HTTPPost" %}
HTTP_URL = "{{ node.config.url }}"
HTTP_METHOD = "{{ node.config.method }}"
HTTP_TIMEOUT = {{ node.config.timeout_ms }} / 1000.0
{% endif %}
{% endfor %}

# ════════════════════════════════════════════════════════════
# SETUP
# ════════════════════════════════════════════════════════════
{% if has_gpio %}
GPIO.setmode(GPIO.BOARD)
{% for node in output_nodes %}
{% if node.type == "GPIOOutput" %}
GPIO.setup(GPIO_PIN_{{ loop.index }}, GPIO.OUT)
{% endif %}
{% endfor %}
{% endif %}

{% if has_mqtt %}
mqtt_client = mqtt.Client()
{% for node in output_nodes %}
{% if node.type == "MQTTPublisher" %}
{% if node.config.username %}
mqtt_client.username_pw_set("{{ node.config.username }}", "{{ node.config.password }}")
{% endif %}
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()
{% endif %}
{% endfor %}
{% endif %}

# Initialize sensors
{% for node in input_nodes %}
{% if node.type == "MPU6050" %}
sensor_{{ node.id }} = MPU6050(bus=MPU6050_I2C_BUS, address=MPU6050_ADDR)
sensor_{{ node.id }}.set_sample_rate(MPU6050_SAMPLE_RATE)
{% elif node.type == "ADXL345" %}
sensor_{{ node.id }} = ADXL345(bus={{ node.config.i2c_bus }}, address={{ node.config.i2c_addr }})
{% endif %}
{% endfor %}

# Initialize models
{% for node in processing_nodes %}
{% if node.type == "TimesNet" %}
model_{{ node.id }} = TimesNetInference("{{ node.config.model_file }}")
{% elif node.type == "DecisionTree" %}
model_{{ node.id }} = DecisionTreeClassifier("{{ node.config.model_file }}")
{% endif %}
{% endfor %}

# ════════════════════════════════════════════════════════════
# MAIN LOOP
# ════════════════════════════════════════════════════════════
print("{{ pipeline_name }} started...")

buffer = []
WINDOW_SIZE = {{ window_size }}

try:
    while True:
        # ──────────────────────────────────────────────
        # READ SENSORS
        # ──────────────────────────────────────────────
        {% for node in input_nodes %}
        {% if node.type == "MPU6050" %}
        accel_{{ node.id }} = sensor_{{ node.id }}.read_accel()
        {% endif %}
        {% endfor %}

        # ──────────────────────────────────────────────
        # PROCESS DATA
        # ──────────────────────────────────────────────
        {% for node in processing_nodes %}
        {% if node.type == "Normalize" %}
        # Normalization
        data_normalized = (accel - np.array([{{ node.config.mean }}])) / np.array([{{ node.config.std }}])
        {% elif node.type == "SlidingWindow" %}
        # Windowing
        buffer.append(data_normalized)
        if len(buffer) >= WINDOW_SIZE:
            window = np.array(buffer[-WINDOW_SIZE:])
        {% elif node.type == "TimesNet" %}
            # Model inference
            prediction = model_{{ node.id }}.infer(window)
        {% endif %}
        {% endfor %}

        # ──────────────────────────────────────────────
        # OUTPUT ACTIONS
        # ──────────────────────────────────────────────
        {% for node in output_nodes %}
        {% if node.type == "GPIOOutput" %}
        if prediction == {{ node.config.trigger_value }}:
            GPIO.output(GPIO_PIN_{{ loop.index }}, GPIO.HIGH)
            time.sleep(GPIO_DURATION_{{ loop.index }} / 1000.0)
            GPIO.output(GPIO_PIN_{{ loop.index }}, GPIO.LOW)
        {% elif node.type == "MQTTPublisher" %}
        payload = {{ node.config.payload_template | replace("{{device}}", device_id) | replace("{{value}}", "prediction") | replace("{{timestamp}}", "time.time()") }}
        mqtt_client.publish(MQTT_TOPIC, json.dumps(payload), qos=MQTT_QOS)
        {% elif node.type == "HTTPPost" %}
        body = {{ node.config.body_template }}
        requests.post(HTTP_URL, json=body, timeout=HTTP_TIMEOUT)
        {% elif node.type == "SerialOutput" %}
        print("{{ node.config.format }}".format(value=prediction))
        {% endif %}
        {% endfor %}

        time.sleep(1.0 / {{ sample_rate }})

except KeyboardInterrupt:
    print("Shutting down...")
    {% if has_gpio %}
    GPIO.cleanup()
    {% endif %}
    {% if has_mqtt %}
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    {% endif %}
```

---

## Phase 4: Firmware Packaging (Week 4)

**Goal:** Generate complete, ready-to-deploy packages

### **Generated Package Structure:**

```
jetson_fall_detection/
├── deploy.sh                       # Auto-deploy script
├── requirements.txt                # Python dependencies
├── systemd/
│   └── fall_detection.service      # Auto-start service
├── config/
│   ├── device.yaml                 # Device configuration
│   ├── mqtt_broker.yaml            # MQTT settings
│   └── credentials/                # Certificates (if needed)
│       ├── aws-root-ca.pem
│       └── device-cert.pem
├── src/
│   ├── main.py                     # Generated main script
│   ├── sensors/
│   │   ├── sensor_mpu6050.py
│   │   └── sensor_adxl345.py
│   ├── models/
│   │   ├── model_timesnet.py
│   │   └── model.onnx
│   └── outputs/
│       ├── mqtt_client.py
│       └── http_client.py
├── docs/
│   ├── README.md                   # Setup guide
│   ├── HARDWARE_SETUP.md           # Wiring diagrams
│   └── TROUBLESHOOTING.md
└── tests/
    ├── test_sensors.py             # Sensor test script
    └── test_mqtt.py                # MQTT test script
```

---

## Phase 5: Testing & Documentation (Week 5)

**Goal:** Full end-to-end testing with real hardware

### **Testing Matrix:**

| Component | Jetson Test | Arduino Test | Status |
|-----------|-------------|--------------|--------|
| **Sensors** |
| MPU6050 | I2C read test | I2C read test | ☐ |
| ADXL345 | I2C read test | I2C read test | ☐ |
| Analog Input | ADC read test | ADC read test | ☐ |
| **Local Outputs** |
| GPIO | LED blink | LED blink | ☐ |
| PWM | Servo control | Servo control | ☐ |
| Serial | Console output | Console output | ☐ |
| **Network Outputs** |
| MQTT | Publish test | Publish test (WiFi) | ☐ |
| HTTP POST | API call test | API call test (WiFi) | ☐ |
| **Cloud Outputs** |
| AWS IoT | Telemetry test | N/A | ☐ |
| Azure IoT | Message test | N/A | ☐ |
| **Models** |
| TimesNet | Inference test | N/A | ☐ |
| Decision Tree | N/A | Inference test | ☐ |

---

## Build Instructions

### **Phase 1 Build:**

```bash
# Install dependencies
sudo apt install cmake libglfw3-dev libgl1-mesa-dev

# Clone third-party libraries
git submodule update --init --recursive

# Build
mkdir build && cd build
cmake ..
make -j4

# Run
./bin/pipeline_builder
```

### **Phase 5 Build (Full Release):**

```bash
# Build with all features
cmake .. -DCMAKE_BUILD_TYPE=Release \
         -DENABLE_ALL_NODES=ON \
         -DENABLE_CLOUD_NODES=ON

make -j4

# Package
cpack -G ZIP

# Output: pipeline_builder_v1.0.0_linux_x64.zip
```

---

## Summary

**Total Implementation:**
- **Week 1:** Foundation + Basic I/O (5 input, 2 output nodes)
- **Week 2:** All 25+ nodes with properties
- **Week 3:** Code generation with I/O templates
- **Week 4:** Complete firmware packaging
- **Week 5:** Testing + documentation

**Final Product:**
✅ Visual pipeline builder with 25+ nodes
✅ Complete I/O coverage (sensors, GPIO, network, cloud)
✅ Generates ready-to-deploy packages
✅ Supports Jetson Nano + Arduino Uno
✅ Production-ready code quality

**Ready to start Phase 1?** 🚀
