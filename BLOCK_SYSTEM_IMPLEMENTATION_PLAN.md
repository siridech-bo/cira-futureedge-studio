# CiRA Block System Implementation Plan
**Integrating Dynamic Block Runtime with Pipeline Builder**

**Date:** 2024-12-24
**Status:** Planning Phase
**Terminology:** "Block" (aligned with Arduino App Bricks architecture)

---

## Executive Summary

Transform the CiRA Pipeline Builder from a **compiled-binary-only** deployment tool into a **dual-mode platform** that supports:
1. **Option 1 (Current):** Compiled binaries for production
2. **Option 2 (New):** Dynamic block runtime for rapid development

This enables a **block marketplace ecosystem** with recurring revenue while maintaining backward compatibility.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  Pipeline Builder (C++ Application)                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                     │
│  User composes pipeline visually                   │
│  ├─ Block Library Panel                            │
│  ├─ Node Editor Panel                              │
│  ├─ Properties Panel                               │
│  └─ Deployment Dialog ← ADD MODE SELECTOR          │
│                                                     │
└─────────────────────────────────────────────────────┘
                       │
                       │ Generates
                       ↓
         ┌─────────────────────────────┐
         │  Deployment Configuration   │
         │  ┌───────────┬───────────┐  │
         │  │ Option 1  │ Option 2  │  │
         │  └───────────┴───────────┘  │
         └─────────────────────────────┘
          │                         │
          │                         │
          ↓ Option 1                ↓ Option 2
┌──────────────────────┐  ┌──────────────────────────┐
│ Compiled Binary      │  │ Block Runtime Config     │
│ (EXISTING)           │  │ (NEW)                    │
│                      │  │                          │
│ C++ Code Generator   │  │ Block Manifest:          │
│      ↓               │  │ {                        │
│ Cross-compile        │  │   "blocks": [            │
│      ↓               │  │     {                    │
│ Flash to HW          │  │       "id": "timesnet",  │
│                      │  │       "version": "1.2.0" │
│ ✅ Works NOW         │  │     },                   │
│ ✅ Production ready  │  │     {                    │
│ ✅ Optimized         │  │       "id": "http-srv",  │
│                      │  │       "version": "2.0.0" │
│                      │  │     }                    │
│                      │  │   ],                     │
│                      │  │   "pipeline": {...}      │
│                      │  │ }                        │
└──────────────────────┘  └──────────────────────────┘
          │                         │
          ↓                         ↓
┌──────────────────────┐  ┌──────────────────────────┐
│ Arduino UNO Q        │  │ Arduino UNO Q            │
│ ─────────────        │  │ ─────────────            │
│ [Compiled binary]    │  │ CiRA Block Runtime       │
│  Runs standalone     │  │   ↓                      │
│                      │  │ Block Manager            │
│                      │  │   ↓                      │
│                      │  │ Loads blocks:            │
│                      │  │ ├─ timesnet.so           │
│                      │  │ ├─ http_server.so        │
│                      │  │ └─ mqtt_client.so        │
│                      │  │   ↓                      │
│                      │  │ Pipeline Executor        │
│                      │  │ Executes flow            │
└──────────────────────┘  └──────────────────────────┘
```

---

## Block Terminology

### What is a "Block"?

A **Block** is a pre-packaged, reusable software component that provides specific functionality in a CiRA pipeline:

- **AI Blocks:** TimesNet, Decision Tree, YOLO, custom ONNX models
- **Network Blocks:** HTTP Server, MQTT Publisher, WebSocket, REST API
- **Sensor Blocks:** I2C sensors, SPI devices, GPIO interfaces
- **Processing Blocks:** Filters, normalizers, feature extractors

### Block vs. Node

| Term | Definition | Usage |
|------|------------|-------|
| **Node** | Visual element in Pipeline Builder UI | User drags nodes onto canvas |
| **Block** | Runtime implementation of node functionality | Hardware loads blocks at runtime |
| **Executable Node** | Code term for nodes that map to blocks | `initialize_executable_nodes.cpp` |

**Relationship:** A **Node** in the Pipeline Builder UI represents a **Block** that will run on hardware.

---

## Implementation Phases

### Phase 0: Current State (✅ COMPLETE)

**What exists now:**
- ✅ Visual Pipeline Builder (imgui-node-editor based)
- ✅ Block Library UI with categorized nodes
- ✅ Node Editor with drag-drop connections
- ✅ Properties Panel for node configuration
- ✅ C++ Code Generator (`code_generator.cpp`)
- ✅ Firmware Generator (`firmware_generator.cpp`)
- ✅ SSH Deployment (`ssh_manager.cpp`)
- ✅ Project file format (`.ciraproject`)

**Deployment Flow:**
```
Pipeline → C++ Code → Cross-compile → SSH Deploy → Run Binary
```

**This remains untouched and production-ready.**

---

### Phase 1: Block Metadata Layer (Weeks 1-2)

**Goal:** Add block metadata to existing nodes without breaking current functionality.

#### 1.1 Extend Node Definition

**File:** `src/core/node_registry.hpp`

```cpp
// BEFORE (existing):
struct NodeDefinition {
    std::string type;
    std::string category;
    std::string label;
    std::vector<PinDefinition> inputs;
    std::vector<PinDefinition> outputs;
    nlohmann::json default_config;
};

// AFTER (add block metadata):
struct NodeDefinition {
    std::string type;
    std::string category;
    std::string label;
    std::vector<PinDefinition> inputs;
    std::vector<PinDefinition> outputs;
    nlohmann::json default_config;

    // NEW: Block system metadata
    struct BlockInfo {
        std::string block_id;           // "timesnet"
        std::string block_version;      // "1.2.0"
        std::string runtime_type;       // "onnx-runtime" | "native" | "python"
        std::vector<std::string> dependencies;  // ["onnx-runtime-1.16"]
        bool requires_compilation;      // true = Option 1 only, false = supports Option 2
    };
    std::optional<BlockInfo> block_info;  // Optional: null if not a block (legacy nodes)
};
```

#### 1.2 Update Node Registry

**File:** `src/core/node_registry.cpp` or `src/core/initialize_executable_nodes.cpp`

```cpp
void NodeRegistry::RegisterDefaultNodes() {
    // Example: TimesNet node with block metadata
    RegisterNode({
        .type = "TimesNet",
        .category = "Processing/AI",
        .label = "TimesNet Model",
        .inputs = {
            {"features_in", PinType::Array}
        },
        .outputs = {
            {"prediction_out", PinType::Int},
            {"confidence_out", PinType::Float}
        },
        .default_config = {
            {"model_path", "model.onnx"},
            {"num_classes", 5}
        },
        // NEW: Block metadata
        .block_info = {
            .block_id = "timesnet",
            .block_version = "1.2.0",
            .runtime_type = "onnx-runtime",
            .dependencies = {"onnx-runtime-1.16.0"},
            .requires_compilation = false  // Supports dynamic loading
        }
    });

    // Example: HTTP Server node
    RegisterNode({
        .type = "HTTPServer",
        .category = "Network",
        .label = "HTTP POST",
        .inputs = {
            {"data_in", PinType::Any}
        },
        .outputs = {},
        .default_config = {
            {"endpoint", "http://localhost:8080/data"},
            {"method", "POST"}
        },
        // NEW: Block metadata
        .block_info = {
            .block_id = "http-server",
            .block_version = "2.0.0",
            .runtime_type = "native",
            .dependencies = {"libcurl-8.4.0"},
            .requires_compilation = false
        }
    });
}
```

**Impact:** ✅ Zero breaking changes - existing code ignores `.block_info` if not used.

---

### Phase 2: Block Manifest Generator (Weeks 3-4)

**Goal:** Generate block deployment manifests from pipelines.

#### 2.1 Create Block Manifest Generator

**File:** `src/generation/block_manifest_generator.hpp`

```cpp
#pragma once
#include "core/pipeline.hpp"
#include <nlohmann/json.hpp>
#include <set>
#include <string>

namespace PipelineBuilder {

struct BlockReference {
    std::string id;
    std::string version;
    std::string type;
    std::vector<std::string> dependencies;
};

struct BlockManifest {
    std::string format_version = "1.0";
    std::string pipeline_name;
    std::string target_platform;
    std::vector<BlockReference> blocks;
    nlohmann::json pipeline_config;  // Node graph + connections

    nlohmann::json ToJson() const;
    static BlockManifest FromJson(const nlohmann::json& j);
};

class BlockManifestGenerator {
public:
    BlockManifestGenerator(const NodeRegistry& registry);

    // Generate manifest from pipeline
    BlockManifest Generate(const Pipeline& pipeline, const std::string& platform);

    // Check if pipeline is block-compatible
    bool IsBlockCompatible(const Pipeline& pipeline) const;

    // Get reasons why pipeline can't use block runtime
    std::vector<std::string> GetIncompatibilityReasons(const Pipeline& pipeline) const;

private:
    const NodeRegistry& node_registry_;

    std::set<BlockReference> ExtractRequiredBlocks(const Pipeline& pipeline);
    std::set<std::string> ResolveDependencies(const std::set<BlockReference>& blocks);
};

} // namespace PipelineBuilder
```

**File:** `src/generation/block_manifest_generator.cpp`

```cpp
#include "block_manifest_generator.hpp"
#include <algorithm>

namespace PipelineBuilder {

BlockManifest BlockManifestGenerator::Generate(
    const Pipeline& pipeline,
    const std::string& platform
) {
    BlockManifest manifest;
    manifest.pipeline_name = pipeline.GetName();
    manifest.target_platform = platform;

    // Extract blocks from pipeline nodes
    auto blocks = ExtractRequiredBlocks(pipeline);
    manifest.blocks.assign(blocks.begin(), blocks.end());

    // Serialize pipeline graph
    manifest.pipeline_config = pipeline.ToJson();

    return manifest;
}

bool BlockManifestGenerator::IsBlockCompatible(const Pipeline& pipeline) const {
    return GetIncompatibilityReasons(pipeline).empty();
}

std::vector<std::string> BlockManifestGenerator::GetIncompatibilityReasons(
    const Pipeline& pipeline
) const {
    std::vector<std::string> reasons;

    for (const auto& node : pipeline.GetNodes()) {
        auto node_def = node_registry_.GetNodeDefinition(node.type);

        // Check if node has block info
        if (!node_def.block_info.has_value()) {
            reasons.push_back(
                "Node '" + node.label + "' does not support block runtime (legacy node)"
            );
            continue;
        }

        // Check if block requires compilation
        if (node_def.block_info->requires_compilation) {
            reasons.push_back(
                "Node '" + node.label + "' requires compilation (not available as dynamic block)"
            );
        }
    }

    return reasons;
}

std::set<BlockReference> BlockManifestGenerator::ExtractRequiredBlocks(
    const Pipeline& pipeline
) {
    std::set<BlockReference> blocks;

    for (const auto& node : pipeline.GetNodes()) {
        auto node_def = node_registry_.GetNodeDefinition(node.type);

        if (node_def.block_info.has_value()) {
            blocks.insert({
                .id = node_def.block_info->block_id,
                .version = node_def.block_info->block_version,
                .type = node_def.block_info->runtime_type,
                .dependencies = node_def.block_info->dependencies
            });
        }
    }

    return blocks;
}

nlohmann::json BlockManifest::ToJson() const {
    nlohmann::json j;
    j["format_version"] = format_version;
    j["pipeline_name"] = pipeline_name;
    j["target_platform"] = target_platform;

    j["blocks"] = nlohmann::json::array();
    for (const auto& block : blocks) {
        j["blocks"].push_back({
            {"id", block.id},
            {"version", block.version},
            {"type", block.type},
            {"dependencies", block.dependencies}
        });
    }

    j["pipeline"] = pipeline_config;

    return j;
}

} // namespace PipelineBuilder
```

#### 2.2 Example Manifest Output

**File:** `output/ts6_jetson_nano/block_manifest.json`

```json
{
  "format_version": "1.0",
  "pipeline_name": "TimesNet Activity Recognition",
  "target_platform": "jetson_nano",
  "blocks": [
    {
      "id": "timesnet",
      "version": "1.2.0",
      "type": "onnx-runtime",
      "dependencies": [
        "onnx-runtime-1.16.0"
      ]
    },
    {
      "id": "sliding-window",
      "version": "1.0.0",
      "type": "native",
      "dependencies": []
    },
    {
      "id": "http-server",
      "version": "2.0.0",
      "type": "native",
      "dependencies": [
        "libcurl-8.4.0"
      ]
    },
    {
      "id": "oled-display",
      "version": "1.1.0",
      "type": "i2c-device",
      "dependencies": [
        "i2c-tools"
      ]
    }
  ],
  "pipeline": {
    "nodes": [
      {
        "id": "sliding_window_1",
        "type": "SlidingWindow",
        "config": {
          "window_size": 100,
          "stride": 20
        }
      },
      {
        "id": "timesnet_1",
        "type": "TimesNet",
        "config": {
          "model_path": "timesnet_model.onnx",
          "num_classes": 5,
          "seq_len": 100,
          "input_channels": 3
        }
      },
      {
        "id": "http_post_1",
        "type": "HTTPServer",
        "config": {
          "endpoint": "http://192.168.1.100:8080/predictions",
          "method": "POST"
        }
      }
    ],
    "connections": [
      {
        "from": "sliding_window_1.window_out",
        "to": "timesnet_1.features_in"
      },
      {
        "from": "timesnet_1.prediction_out",
        "to": "http_post_1.data_in"
      }
    ]
  }
}
```

---

### Phase 3: Deployment Mode Selector (Week 5)

**Goal:** Add UI option to choose between compiled binary and block runtime.

#### 3.1 Update Deployment Dialog

**File:** `src/ui/deployment_dialog.hpp`

```cpp
enum class DeploymentMode {
    COMPILED_BINARY,   // Option 1: Current approach
    BLOCK_RUNTIME      // Option 2: Dynamic blocks
};

class DeploymentDialog {
public:
    // ... existing methods ...

    DeploymentMode GetSelectedMode() const { return deployment_mode_; }

private:
    DeploymentMode deployment_mode_ = DeploymentMode::COMPILED_BINARY;

    void RenderModeSelector();
    void RenderCompatibilityWarnings();
};
```

**File:** `src/ui/deployment_dialog.cpp`

```cpp
void DeploymentDialog::Render() {
    ImGui::Begin("Deploy Pipeline", &show_);

    // NEW: Mode selector
    RenderModeSelector();

    ImGui::Separator();

    // Existing deployment options...
    RenderTargetSelector();
    RenderSSHSettings();

    if (ImGui::Button("Deploy")) {
        OnDeploy();
    }

    ImGui::End();
}

void DeploymentDialog::RenderModeSelector() {
    ImGui::Text("Deployment Mode:");

    if (ImGui::RadioButton("Compiled Binary (Production)",
                           deployment_mode_ == DeploymentMode::COMPILED_BINARY)) {
        deployment_mode_ = DeploymentMode::COMPILED_BINARY;
    }
    ImGui::SameLine();
    ImGui::TextDisabled("(?)");
    if (ImGui::IsItemHovered()) {
        ImGui::SetTooltip(
            "Generates optimized C++ code, cross-compiles, and deploys binary.\n"
            "Best for: Production deployments, maximum performance."
        );
    }

    if (ImGui::RadioButton("Block Runtime (Development)",
                           deployment_mode_ == DeploymentMode::BLOCK_RUNTIME)) {
        deployment_mode_ = DeploymentMode::BLOCK_RUNTIME;
    }
    ImGui::SameLine();
    ImGui::TextDisabled("(?)");
    if (ImGui::IsItemHovered()) {
        ImGui::SetTooltip(
            "Deploys pipeline configuration and dynamically loads blocks.\n"
            "Best for: Rapid prototyping, remote updates, A/B testing."
        );
    }

    // Show compatibility warnings
    if (deployment_mode_ == DeploymentMode::BLOCK_RUNTIME) {
        RenderCompatibilityWarnings();
    }
}

void DeploymentDialog::RenderCompatibilityWarnings() {
    BlockManifestGenerator generator(app_->GetNodeRegistry());
    auto reasons = generator.GetIncompatibilityReasons(app_->GetPipeline());

    if (!reasons.empty()) {
        ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(1.0f, 0.6f, 0.0f, 1.0f));
        ImGui::TextWrapped("⚠ Warning: This pipeline has compatibility issues:");
        ImGui::PopStyleColor();

        for (const auto& reason : reasons) {
            ImGui::BulletText("%s", reason.c_str());
        }

        ImGui::TextWrapped("Consider using Compiled Binary mode instead.");
    } else {
        ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.0f, 1.0f, 0.0f, 1.0f));
        ImGui::Text("✓ Pipeline is compatible with Block Runtime");
        ImGui::PopStyleColor();
    }
}
```

#### 3.2 Update Deployment Pipeline

**File:** `src/deployment/deployment_pipeline.hpp`

```cpp
class DeploymentPipeline {
public:
    void Deploy(const Pipeline& pipeline,
                DeploymentMode mode,
                const DeploymentConfig& config);

private:
    void DeployCompiledBinary(const Pipeline& pipeline, const DeploymentConfig& config);
    void DeployBlockRuntime(const Pipeline& pipeline, const DeploymentConfig& config);
};
```

**File:** `src/deployment/deployment_pipeline.cpp`

```cpp
void DeploymentPipeline::Deploy(
    const Pipeline& pipeline,
    DeploymentMode mode,
    const DeploymentConfig& config
) {
    switch (mode) {
        case DeploymentMode::COMPILED_BINARY:
            DeployCompiledBinary(pipeline, config);
            break;

        case DeploymentMode::BLOCK_RUNTIME:
            DeployBlockRuntime(pipeline, config);
            break;
    }
}

void DeploymentPipeline::DeployCompiledBinary(
    const Pipeline& pipeline,
    const DeploymentConfig& config
) {
    // EXISTING CODE - no changes
    CodeGenerator code_gen;
    FirmwareGenerator firmware_gen;
    SSHManager ssh;

    // Generate C++
    auto cpp_code = code_gen.Generate(pipeline, config.platform);

    // Cross-compile
    auto binary_path = firmware_gen.Compile(cpp_code, config);

    // Deploy via SSH
    ssh.Connect(config.ssh_host, config.ssh_user, config.ssh_password);
    ssh.UploadFile(binary_path, "/home/user/app");
    ssh.ExecuteCommand("chmod +x /home/user/app && /home/user/app");
}

void DeploymentPipeline::DeployBlockRuntime(
    const Pipeline& pipeline,
    const DeploymentConfig& config
) {
    // NEW CODE
    BlockManifestGenerator manifest_gen(node_registry_);
    BlockDeployer block_deployer;

    // Generate manifest
    auto manifest = manifest_gen.Generate(pipeline, config.platform);
    auto manifest_json = manifest.ToJson();

    // Save to temp file
    std::string manifest_path = "/tmp/block_manifest.json";
    std::ofstream f(manifest_path);
    f << manifest_json.dump(2);
    f.close();

    // Deploy to hardware
    SSHManager ssh;
    ssh.Connect(config.ssh_host, config.ssh_user, config.ssh_password);

    // Upload manifest
    ssh.UploadFile(manifest_path, "/opt/cira/manifests/pipeline.json");

    // Trigger block runtime reload
    ssh.ExecuteCommand("systemctl restart cira-block-runtime");

    std::cout << "✓ Block runtime deployment complete" << std::endl;
}
```

---

### Phase 4: Block Runtime on Hardware (Weeks 6-10)

**Goal:** Create the runtime system that runs on Arduino UNO Q / Jetson Nano.

**This is a SEPARATE repository:** `cira-block-runtime`

#### 4.1 Block Runtime Architecture

```
CiRA Block Runtime (C++ Daemon)
├─ Block Manager
│  ├─ Block Loader (dlopen for .so files)
│  ├─ Block Registry
│  └─ Dependency Resolver
│
├─ Pipeline Executor
│  ├─ Manifest Parser
│  ├─ Node Graph Builder
│  └─ Execution Engine
│
└─ Block API
   ├─ IBlock interface
   ├─ Data passing (shared memory / pipes)
   └─ Lifecycle hooks (init, execute, cleanup)
```

#### 4.2 Block Interface

**File:** `cira-block-runtime/include/cira/iblock.hpp`

```cpp
#pragma once
#include <string>
#include <vector>
#include <any>
#include <map>

namespace CiRA {

struct BlockMetadata {
    std::string id;
    std::string version;
    std::string author;
    std::vector<std::string> dependencies;
};

class IBlock {
public:
    virtual ~IBlock() = default;

    // Lifecycle
    virtual bool Initialize(const std::map<std::string, std::any>& config) = 0;
    virtual void Shutdown() = 0;

    // Execution
    virtual std::map<std::string, std::any> Execute(
        const std::map<std::string, std::any>& inputs
    ) = 0;

    // Metadata
    virtual BlockMetadata GetMetadata() const = 0;
};

// Block factory function signature
using BlockFactory = IBlock* (*)();

} // namespace CiRA

// Every block .so must export this
#define CIRA_EXPORT_BLOCK(BlockClass) \
    extern "C" { \
        CiRA::IBlock* CreateBlock() { \
            return new BlockClass(); \
        } \
    }
```

#### 4.3 Example Block Implementation

**File:** `blocks/timesnet/timesnet_block.cpp`

```cpp
#include <cira/iblock.hpp>
#include <onnxruntime/core/session/onnxruntime_cxx_api.h>

class TimesNetBlock : public CiRA::IBlock {
public:
    bool Initialize(const std::map<std::string, std::any>& config) override {
        model_path_ = std::any_cast<std::string>(config.at("model_path"));

        // Initialize ONNX Runtime
        Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "TimesNetBlock");
        Ort::SessionOptions session_options;
        session_ = std::make_unique<Ort::Session>(env, model_path_.c_str(), session_options);

        return true;
    }

    void Shutdown() override {
        session_.reset();
    }

    std::map<std::string, std::any> Execute(
        const std::map<std::string, std::any>& inputs
    ) override {
        // Get input tensor
        auto features = std::any_cast<std::vector<float>>(inputs.at("features_in"));

        // Run inference
        auto output = RunInference(features);

        // Return outputs
        return {
            {"prediction_out", output.class_id},
            {"confidence_out", output.confidence}
        };
    }

    BlockMetadata GetMetadata() const override {
        return {
            .id = "timesnet",
            .version = "1.2.0",
            .author = "CiRA Labs",
            .dependencies = {"onnx-runtime-1.16.0"}
        };
    }

private:
    std::string model_path_;
    std::unique_ptr<Ort::Session> session_;

    struct InferenceResult {
        int class_id;
        float confidence;
    };

    InferenceResult RunInference(const std::vector<float>& input) {
        // ONNX inference implementation...
        // (existing TimesNet inference code)
    }
};

CIRA_EXPORT_BLOCK(TimesNetBlock)
```

**Compile to shared library:**
```bash
g++ -shared -fPIC timesnet_block.cpp -o libtimesnet.so \
    -I/opt/cira/include \
    -lonnxruntime
```

#### 4.4 Block Runtime Main Application

**File:** `cira-block-runtime/src/main.cpp`

```cpp
#include "block_manager.hpp"
#include "pipeline_executor.hpp"
#include <iostream>
#include <filesystem>

int main(int argc, char** argv) {
    std::cout << "CiRA Block Runtime v1.0.0" << std::endl;

    // Load manifest
    std::string manifest_path = "/opt/cira/manifests/pipeline.json";
    if (argc > 1) {
        manifest_path = argv[1];
    }

    if (!std::filesystem::exists(manifest_path)) {
        std::cerr << "Manifest not found: " << manifest_path << std::endl;
        return 1;
    }

    // Initialize block manager
    CiRA::BlockManager block_mgr("/opt/cira/blocks");

    // Load manifest
    auto manifest = CiRA::BlockManifest::LoadFromFile(manifest_path);

    // Load required blocks
    for (const auto& block_ref : manifest.blocks) {
        std::cout << "Loading block: " << block_ref.id
                  << " v" << block_ref.version << std::endl;

        if (!block_mgr.LoadBlock(block_ref.id, block_ref.version)) {
            std::cerr << "Failed to load block: " << block_ref.id << std::endl;
            return 1;
        }
    }

    // Create pipeline executor
    CiRA::PipelineExecutor executor(block_mgr);

    // Build pipeline from manifest
    if (!executor.BuildFromManifest(manifest)) {
        std::cerr << "Failed to build pipeline" << std::endl;
        return 1;
    }

    // Run pipeline
    std::cout << "Starting pipeline execution..." << std::endl;
    executor.Run();

    return 0;
}
```

---

### Phase 5: Block Marketplace Infrastructure (Weeks 11-16)

**Goal:** Build the ecosystem for discovering, distributing, and licensing blocks.

#### 5.1 Block Registry Service

**Repository:** `cira-block-registry` (Backend service)

```
Block Registry API (REST)
├─ GET  /blocks              → List available blocks
├─ GET  /blocks/:id          → Get block details
├─ GET  /blocks/:id/download → Download block .so file
├─ POST /blocks              → Publish new block (authenticated)
└─ GET  /blocks/:id/license  → Check license status
```

#### 5.2 Block CLI Tool

**Tool:** `cira-cli` (Command-line tool for hardware)

```bash
# Install on Arduino UNO Q / Jetson
$ cira-cli block install timesnet@1.2.0
Downloading timesnet v1.2.0... ✓
Installing dependencies: onnx-runtime-1.16.0... ✓
Block installed to: /opt/cira/blocks/timesnet/1.2.0/

$ cira-cli block list
Installed blocks:
  - timesnet v1.2.0
  - http-server v2.0.0
  - sliding-window v1.0.0

$ cira-cli block update
Checking for updates...
  - timesnet: 1.2.0 → 1.3.0 available
Update? [y/N] y
```

#### 5.3 Block Manifest in Pipeline Builder

**Update deployment to auto-install missing blocks:**

```cpp
void DeploymentPipeline::DeployBlockRuntime(
    const Pipeline& pipeline,
    const DeploymentConfig& config
) {
    // Generate manifest
    auto manifest = manifest_gen.Generate(pipeline, config.platform);

    // SSH to hardware
    SSHManager ssh;
    ssh.Connect(config.ssh_host, config.ssh_user, config.ssh_password);

    // Check installed blocks
    auto installed = ssh.ExecuteCommand("cira-cli block list --json");
    auto installed_blocks = ParseInstalledBlocks(installed);

    // Install missing blocks
    for (const auto& block : manifest.blocks) {
        if (!IsBlockInstalled(installed_blocks, block)) {
            std::cout << "Installing block: " << block.id << std::endl;
            ssh.ExecuteCommand("cira-cli block install " + block.id + "@" + block.version);
        }
    }

    // Deploy manifest
    ssh.UploadFile(manifest_path, "/opt/cira/manifests/pipeline.json");
    ssh.ExecuteCommand("systemctl restart cira-block-runtime");
}
```

---

## Commercialization Strategy

### Licensing Models

#### Free Tier
- ✅ Pipeline Builder (community edition)
- ✅ Basic blocks (GPIO, I2C, simple filters, normalization)
- ✅ Up to 3 deployments
- ✅ Community support

#### Pro Tier ($49/month)
- ✅ Advanced AI blocks (TimesNet, YOLO, custom ONNX)
- ✅ Network blocks (HTTP, MQTT, WebSocket, cloud connectors)
- ✅ Unlimited deployments
- ✅ Email support
- ✅ Access to block marketplace

#### Enterprise Tier (Custom pricing)
- ✅ On-premise block registry
- ✅ Custom block development
- ✅ White-label options
- ✅ SLA guarantees
- ✅ Dedicated support

### Block Marketplace Revenue

**Platform fee:** 30% of block sales (like App Store model)

**Example block pricing:**
- Free blocks: Community-contributed, basic functionality
- Premium blocks: $5-50/month subscription
- Enterprise blocks: Custom pricing, licensed per deployment

---

## Migration Timeline

### Immediate (Now - Week 2)
- ✅ Use Option 1 (compiled binary) for current projects
- ✅ Continue shipping products with existing flow
- ✅ Add block metadata to node definitions (non-breaking)

### Short-term (Weeks 3-5)
- 🔨 Implement block manifest generator
- 🔨 Add deployment mode selector to UI
- 🔨 Test block manifest generation

### Medium-term (Weeks 6-10)
- 🔨 Develop block runtime (cira-block-runtime)
- 🔨 Create initial block library
  - TimesNet block
  - HTTP Server block
  - MQTT block
  - OLED Display block
- 🔨 Beta test with Arduino UNO Q

### Long-term (Weeks 11-16)
- 🔨 Build block registry service
- 🔨 Create cira-cli tool
- 🔨 Develop block marketplace UI
- 🔨 Launch beta program with early adopters

### Future (6+ months)
- 🚀 Public launch of block marketplace
- 🚀 Open block SDK to 3rd party developers
- 🚀 Community contributions
- 🚀 Revenue sharing with block creators

---

## Code Changes Summary

### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/core/node_registry.hpp` | ✏️ **Extend** | Add `BlockInfo` struct to `NodeDefinition` |
| `src/core/initialize_executable_nodes.cpp` | ✏️ **Extend** | Add block metadata when registering nodes |
| `src/ui/deployment_dialog.hpp` | ✏️ **Extend** | Add `DeploymentMode` enum and mode selector |
| `src/ui/deployment_dialog.cpp` | ✏️ **Extend** | Implement mode selector UI |
| `src/deployment/deployment_pipeline.hpp` | ✏️ **Extend** | Add block runtime deployment method |
| `src/deployment/deployment_pipeline.cpp` | ✏️ **Extend** | Implement block deployment flow |

### Files to Create

| File | Type | Description |
|------|------|-------------|
| `src/generation/block_manifest_generator.hpp` | ✨ **New** | Block manifest generator interface |
| `src/generation/block_manifest_generator.cpp` | ✨ **New** | Block manifest generation logic |
| `src/deployment/block_deployer.hpp` | ✨ **New** | Block deployment utilities |
| `src/deployment/block_deployer.cpp` | ✨ **New** | Block installation and sync |

### External Projects

| Repository | Type | Description |
|------------|------|-------------|
| `cira-block-runtime` | ✨ **New** | C++ runtime for executing block pipelines on hardware |
| `cira-block-registry` | ✨ **New** | Backend service for block marketplace |
| `cira-cli` | ✨ **New** | Command-line tool for block management |
| `blocks/` | ✨ **New** | Individual block implementations (timesnet, http, etc.) |

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Block runtime performance overhead | Medium | Benchmark early; keep Option 1 for production |
| Dynamic loading complexity on embedded | High | Start with Jetson Nano (powerful); Arduino later |
| Block versioning conflicts | Medium | Strict semantic versioning; dependency resolver |
| Breaking changes in block API | High | Version block API separately; maintain compatibility |

### Business Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low block marketplace adoption | High | Start with official blocks; incentivize developers |
| Piracy of premium blocks | Medium | License verification in block runtime |
| Competition from similar platforms | Medium | Unique integration with existing Pipeline Builder |

---

## Success Metrics

### Phase 1-2 (Block Metadata)
- ✅ All nodes have block metadata
- ✅ Manifest generator produces valid JSON
- ✅ Zero regressions in existing deployments

### Phase 3 (Deployment Mode)
- ✅ Users can toggle between modes
- ✅ Compatibility warnings work correctly
- ✅ Both deployment paths functional

### Phase 4 (Block Runtime)
- ✅ Runtime loads and executes at least 3 blocks
- ✅ Performance within 20% of compiled binary
- ✅ Successfully deploys to Arduino UNO Q

### Phase 5 (Marketplace)
- ✅ 10+ blocks available
- ✅ 100+ users registered
- ✅ 5+ community-contributed blocks
- ✅ Revenue from block subscriptions

---

## Next Steps

1. **Get approval on this plan** ✋ (You are here!)
2. **Phase 1:** Add block metadata (Week 1-2)
3. **Phase 2:** Build manifest generator (Week 3-4)
4. **Phase 3:** Implement deployment mode selector (Week 5)
5. **Phase 4:** Develop block runtime (Week 6-10)
6. **Phase 5:** Launch marketplace (Week 11-16)

---

## References

- **Arduino App Bricks:** Similar architecture for Arduino platform
- **Pipeline Builder:** Current C++ implementation (imgui-node-editor)
- **Node-based systems:** Unreal Blueprints, Blender nodes, Unity Visual Scripting
- **Plugin marketplaces:** Unity Asset Store, Unreal Marketplace, VSCode Extensions

---

**Document Version:** 1.0
**Last Updated:** 2024-12-24
**Status:** Ready for implementation
