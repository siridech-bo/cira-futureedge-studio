# Pipeline Builder - C++ Standalone Implementation Plan
## Complete End-to-End Deployment Tool

**Date:** 2025-12-15
**Priority:** CRITICAL - Pre-launch requirement
**Status:** Ready to implement
**Technology:** C++ with imgui-node-editor

---

## Vision: Standalone Deployment Tool

**One executable that does EVERYTHING:**
- ✅ Visual pipeline design (imgui-node-editor)
- ✅ Code generation (C++ → C++ firmware)
- ✅ Firmware packaging (ready-to-flash .zip)
- ✅ No dependency on Python app

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  CiRA FutureEdge Studio (Python)                            │
│  ══════════════════════════════════                         │
│                                                             │
│  [Train Model] → model.onnx ✅                              │
│                                                             │
│  [🎨 Deploy to Hardware]                                    │
│     │                                                        │
│     └─→ Launches: pipeline_builder.exe --model model.onnx  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Subprocess
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Pipeline Builder (C++ Standalone Executable)               │
│  ══════════════════════════════════════════════             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Stage 1: Visual Pipeline Design                    │   │
│  │  ────────────────────────────────                   │   │
│  │                                                     │   │
│  │  [Block Library] [Node Editor] [Properties]        │   │
│  │                                                     │   │
│  │  User drags: Sensor → Normalize → Model → LED      │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Stage 2: Platform Selection                        │   │
│  │  ─────────────────────────────                      │   │
│  │                                                     │   │
│  │  [ESP32] [Jetson Nano] [Arduino Nano 33]           │   │
│  │                                                     │   │
│  │  User clicks: ESP32                                 │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Stage 3: Code Generation (Built-in)                │   │
│  │  ──────────────────────────────────                 │   │
│  │                                                     │   │
│  │  ✓ Parse node graph                                │   │
│  │  ✓ Topological sort                                │   │
│  │  ✓ Generate main.cpp from templates               │   │
│  │  ✓ Generate sensor drivers                         │   │
│  │  ✓ Generate model runner                           │   │
│  │  ✓ Generate platformio.ini                         │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Stage 4: Firmware Packaging                        │   │
│  │  ───────────────────────────                        │   │
│  │                                                     │   │
│  │  📁 output/firmware_esp32_1234567890/              │   │
│  │     ├── src/                                       │   │
│  │     │   ├── main.cpp                               │   │
│  │     │   ├── model_runner.cpp                       │   │
│  │     │   ├── sensor_manager.cpp                     │   │
│  │     │   └── model_data.h (from ONNX)               │   │
│  │     ├── lib/                                       │   │
│  │     │   └── sensor_libs/                           │   │
│  │     ├── platformio.ini                             │   │
│  │     ├── README.md (flash instructions)             │   │
│  │     └── wiring_diagram.png                         │   │
│  │                                                     │   │
│  │  📦 firmware_esp32_1234567890.zip ✅                │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Stage 5: Success Dialog                            │   │
│  │  ─────────────────────────                          │   │
│  │                                                     │   │
│  │  🎉 Firmware Generated!                            │   │
│  │                                                     │   │
│  │  Output: output/firmware_esp32_1234567890.zip      │   │
│  │                                                     │   │
│  │  [Open Folder] [Flash Now] [Close]                 │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ↓
                    User flashes to ESP32 ✅
```

---

## Project Structure

```
pipeline_builder/                    # C++ project
├── CMakeLists.txt                   # Build configuration
├── src/
│   ├── main.cpp                     # Entry point
│   ├── ui/
│   │   ├── pipeline_editor.cpp      # Node editor UI
│   │   ├── platform_selector.cpp    # Platform selection dialog
│   │   ├── block_library.cpp        # Block library panel
│   │   └── properties_panel.cpp     # Properties panel
│   ├── core/
│   │   ├── node.hpp                 # Node data structures
│   │   ├── pipeline.hpp             # Pipeline graph
│   │   ├── code_generator.cpp       # Code generation engine
│   │   ├── template_engine.cpp      # Template rendering
│   │   └── firmware_packager.cpp    # Zip creation, file copying
│   └── templates/
│       ├── esp32/
│       │   ├── main.cpp.tmpl        # Main template
│       │   ├── sensor_manager.cpp.tmpl
│       │   └── platformio.ini.tmpl
│       ├── jetson/
│       │   └── main.py.tmpl
│       └── nano33/
│           └── main.cpp.tmpl
├── assets/
│   ├── fonts/
│   ├── icons/
│   └── wiring_diagrams/
│       ├── esp32_pinout.png
│       └── jetson_pinout.png
├── libs/                            # Sensor libraries (bundled)
│   ├── MPU6050/
│   ├── ADXL345/
│   └── ...
└── third_party/
    ├── imgui/
    ├── imgui-node-editor/
    ├── glfw/
    ├── inja/                        # Template engine
    └── miniz/                       # Zip compression
```

---

## Implementation Timeline

### **Week 1: Core Pipeline Editor**

#### **Day 1-2: Project Setup + Basic UI**

**CMakeLists.txt:**
```cmake
cmake_minimum_required(VERSION 3.15)
project(PipelineBuilder)

set(CMAKE_CXX_STANDARD 17)

# Dependencies
find_package(OpenGL REQUIRED)
find_package(glfw3 REQUIRED)

# imgui
add_subdirectory(third_party/imgui)

# imgui-node-editor
add_subdirectory(third_party/imgui-node-editor)

# inja (template engine)
add_subdirectory(third_party/inja)

# miniz (zip)
add_subdirectory(third_party/miniz)

# Main executable
add_executable(pipeline_builder
    src/main.cpp
    src/ui/pipeline_editor.cpp
    src/ui/block_library.cpp
    src/ui/properties_panel.cpp
    src/core/pipeline.cpp
    src/core/code_generator.cpp
    src/core/firmware_packager.cpp
)

target_link_libraries(pipeline_builder
    imgui
    imgui-node-editor
    glfw
    OpenGL::GL
    inja
    miniz
)

# Copy templates and assets
add_custom_command(TARGET pipeline_builder POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/src/templates
        $<TARGET_FILE_DIR:pipeline_builder>/templates
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/assets
        $<TARGET_FILE_DIR:pipeline_builder>/assets
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/libs
        $<TARGET_FILE_DIR:pipeline_builder>/libs
)
```

**main.cpp:**
```cpp
#include <imgui.h>
#include <imgui_impl_glfw.h>
#include <imgui_impl_opengl3.h>
#include <imgui-node-editor/imgui_node_editor.h>
#include <GLFW/glfw3.h>

#include "ui/pipeline_editor.hpp"
#include "core/pipeline.hpp"
#include "core/code_generator.hpp"

namespace ed = ax::NodeEditor;

int main(int argc, char** argv) {
    // Parse command line arguments
    std::string model_file;
    if (argc > 2 && std::string(argv[1]) == "--model") {
        model_file = argv[2];
    }

    // Initialize GLFW
    if (!glfwInit()) {
        return -1;
    }

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

    // Create window
    GLFWwindow* window = glfwCreateWindow(
        1400, 900,
        "CiRA Pipeline Builder",
        nullptr, nullptr
    );

    if (!window) {
        glfwTerminate();
        return -1;
    }

    glfwMakeContextCurrent(window);
    glfwSwapInterval(1); // VSync

    // Initialize ImGui
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();

    // Setup style (dark theme with blue accents)
    ImGui::StyleColorsDark();
    SetupCustomStyle();

    // Initialize ImGui backends
    ImGui_ImplGlfw_InitForOpenGL(window, true);
    ImGui_ImplOpenGL3_Init("#version 330");

    // Initialize node editor
    ed::Config config;
    config.SettingsFile = "pipeline_builder.ini";
    ed::EditorContext* editorContext = ed::CreateEditor(&config);

    // Create pipeline editor
    PipelineEditor editor(model_file);

    // Main loop
    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();

        // Start ImGui frame
        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();

        // Render pipeline editor
        editor.Render(editorContext);

        // Render ImGui
        ImGui::Render();
        int display_w, display_h;
        glfwGetFramebufferSize(window, &display_w, &display_h);
        glViewport(0, 0, display_w, display_h);
        glClearColor(0.15f, 0.15f, 0.15f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());

        glfwSwapBuffers(window);
    }

    // Cleanup
    ed::DestroyEditor(editorContext);
    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
    glfwDestroyWindow(window);
    glfwTerminate();

    return 0;
}

void SetupCustomStyle() {
    ImGuiStyle& style = ImGui::GetStyle();

    // Colors (dark theme with blue accents)
    ImVec4* colors = style.Colors;
    colors[ImGuiCol_WindowBg] = ImVec4(0.15f, 0.15f, 0.15f, 1.0f);
    colors[ImGuiCol_ChildBg] = ImVec4(0.18f, 0.18f, 0.18f, 1.0f);
    colors[ImGuiCol_FrameBg] = ImVec4(0.25f, 0.25f, 0.25f, 1.0f);
    colors[ImGuiCol_Header] = ImVec4(0.26f, 0.59f, 0.98f, 0.31f);
    colors[ImGuiCol_HeaderHovered] = ImVec4(0.26f, 0.59f, 0.98f, 0.80f);
    colors[ImGuiCol_HeaderActive] = ImVec4(0.26f, 0.59f, 0.98f, 1.00f);
    colors[ImGuiCol_Button] = ImVec4(0.26f, 0.59f, 0.98f, 0.40f);
    colors[ImGuiCol_ButtonHovered] = ImVec4(0.26f, 0.59f, 0.98f, 1.00f);
    colors[ImGuiCol_ButtonActive] = ImVec4(0.06f, 0.53f, 0.98f, 1.00f);

    // Rounding
    style.WindowRounding = 5.0f;
    style.FrameRounding = 3.0f;
    style.GrabRounding = 3.0f;
}
```

#### **Day 3-4: Node Editor Implementation**

**pipeline_editor.hpp:**
```cpp
#pragma once
#include <imgui-node-editor/imgui_node_editor.h>
#include <vector>
#include <memory>
#include "../core/pipeline.hpp"

namespace ed = ax::NodeEditor;

class PipelineEditor {
public:
    PipelineEditor(const std::string& model_file);
    ~PipelineEditor();

    void Render(ed::EditorContext* context);

private:
    void RenderToolbar();
    void RenderBlockLibrary();
    void RenderNodeEditor(ed::EditorContext* context);
    void RenderPropertiesPanel();

    void AddNode(NodeType type);
    void HandleLinks();
    void GenerateFirmware();

    Pipeline pipeline_;
    std::string model_file_;
    int selected_node_id_ = -1;
};
```

**pipeline_editor.cpp:**
```cpp
#include "pipeline_editor.hpp"
#include "../core/code_generator.hpp"
#include <imgui.h>

PipelineEditor::PipelineEditor(const std::string& model_file)
    : model_file_(model_file) {
}

void PipelineEditor::Render(ed::EditorContext* context) {
    // Full-screen window
    ImGui::SetNextWindowPos(ImVec2(0, 0));
    ImGui::SetNextWindowSize(ImGui::GetIO().DisplaySize);

    ImGui::Begin("CiRA Pipeline Builder", nullptr,
        ImGuiWindowFlags_NoResize |
        ImGuiWindowFlags_NoMove |
        ImGuiWindowFlags_NoCollapse |
        ImGuiWindowFlags_NoBringToFrontOnFocus);

    // Title
    ImGui::Text("CiRA FutureEdge Studio - Visual Pipeline Builder");
    if (!model_file_.empty()) {
        ImGui::SameLine(0, 400);
        ImGui::TextColored(ImVec4(0.6f, 0.6f, 0.6f, 1.0f),
                          "Model: %s", model_file_.c_str());
    }
    ImGui::Separator();

    // Toolbar
    RenderToolbar();
    ImGui::Separator();

    // Three-panel layout
    ImGui::Columns(3);
    ImGui::SetColumnWidth(0, 250);
    ImGui::SetColumnWidth(1, 900);
    ImGui::SetColumnWidth(2, 250);

    // Left: Block Library
    RenderBlockLibrary();
    ImGui::NextColumn();

    // Center: Node Editor
    RenderNodeEditor(context);
    ImGui::NextColumn();

    // Right: Properties
    RenderPropertiesPanel();

    ImGui::Columns(1);
    ImGui::End();
}

void PipelineEditor::RenderToolbar() {
    if (ImGui::Button("💾 Save")) {
        pipeline_.SaveToFile("pipeline.json");
    }
    ImGui::SameLine();
    if (ImGui::Button("📂 Load")) {
        pipeline_.LoadFromFile("pipeline.json");
    }
    ImGui::SameLine();
    if (ImGui::Button("✓ Validate")) {
        pipeline_.Validate();
    }
    ImGui::SameLine();
    if (ImGui::Button("🗑️ Clear")) {
        pipeline_.Clear();
    }

    ImGui::SameLine(0, 300);

    // Main action button
    if (ImGui::Button("🚀 Generate Firmware")) {
        GenerateFirmware();
    }
}

void PipelineEditor::RenderBlockLibrary() {
    ImGui::BeginChild("BlockLibrary", ImVec2(0, 0), true);

    ImGui::Text("Block Library");
    ImGui::Separator();

    // Sensors
    if (ImGui::CollapsingHeader("📡 Sensors", ImGuiTreeNodeFlags_DefaultOpen)) {
        if (ImGui::Button("MPU6050", ImVec2(-1, 0))) {
            AddNode(NodeType::MPU6050);
        }
        if (ImGui::Button("ADXL345", ImVec2(-1, 0))) {
            AddNode(NodeType::ADXL345);
        }
    }

    // Processing
    if (ImGui::CollapsingHeader("🔄 Processing", ImGuiTreeNodeFlags_DefaultOpen)) {
        if (ImGui::Button("Normalize", ImVec2(-1, 0))) {
            AddNode(NodeType::Normalize);
        }
        if (ImGui::Button("Sliding Window", ImVec2(-1, 0))) {
            AddNode(NodeType::SlidingWindow);
        }
    }

    // Models
    if (ImGui::CollapsingHeader("🧠 Models", ImGuiTreeNodeFlags_DefaultOpen)) {
        if (ImGui::Button("TimesNet", ImVec2(-1, 0))) {
            AddNode(NodeType::TimesNet);
        }
    }

    // Outputs
    if (ImGui::CollapsingHeader("📤 Outputs", ImGuiTreeNodeFlags_DefaultOpen)) {
        if (ImGui::Button("LED", ImVec2(-1, 0))) {
            AddNode(NodeType::LED);
        }
        if (ImGui::Button("Serial", ImVec2(-1, 0))) {
            AddNode(NodeType::Serial);
        }
        if (ImGui::Button("WiFi POST", ImVec2(-1, 0))) {
            AddNode(NodeType::WiFiPOST);
        }
    }

    ImGui::EndChild();
}

void PipelineEditor::RenderNodeEditor(ed::EditorContext* context) {
    ImGui::BeginChild("NodeEditor", ImVec2(0, 0), true);

    ed::SetCurrentEditor(context);
    ed::Begin("Pipeline");

    // Render all nodes
    for (auto& node : pipeline_.GetNodes()) {
        node->Render();
    }

    // Render all links
    for (auto& link : pipeline_.GetLinks()) {
        ed::Link(link.id, link.from_pin, link.to_pin);
    }

    // Handle new links
    HandleLinks();

    ed::End();
    ed::SetCurrentEditor(nullptr);

    ImGui::EndChild();
}

void PipelineEditor::RenderPropertiesPanel() {
    ImGui::BeginChild("Properties", ImVec2(0, 0), true);

    ImGui::Text("Properties");
    ImGui::Separator();

    if (selected_node_id_ >= 0) {
        auto node = pipeline_.GetNode(selected_node_id_);
        if (node) {
            node->RenderProperties();
        }
    } else {
        ImGui::TextWrapped("Select a node to edit properties");
    }

    ImGui::EndChild();
}

void PipelineEditor::AddNode(NodeType type) {
    pipeline_.AddNode(type);
}

void PipelineEditor::HandleLinks() {
    // Handle link creation
    if (ed::BeginCreate()) {
        ed::PinId from, to;
        if (ed::QueryNewLink(&from, &to)) {
            if (ed::AcceptNewItem()) {
                pipeline_.AddLink(from.Get(), to.Get());
            }
        }
    }
    ed::EndCreate();

    // Handle link deletion
    if (ed::BeginDelete()) {
        ed::LinkId linkId;
        while (ed::QueryDeletedLink(&linkId)) {
            if (ed::AcceptDeletedItem()) {
                pipeline_.RemoveLink(linkId.Get());
            }
        }
    }
    ed::EndDelete();

    // Handle node selection
    auto selected = ed::GetSelectedNodes();
    if (!selected.empty()) {
        selected_node_id_ = selected[0].Get();
    }
}

void PipelineEditor::GenerateFirmware() {
    // Step 1: Show platform selection dialog
    std::string platform = ShowPlatformSelectionDialog();
    if (platform.empty()) return;  // User cancelled

    // Step 2: Validate pipeline
    auto errors = pipeline_.Validate();
    if (!errors.empty()) {
        ShowErrorDialog(errors);
        return;
    }

    // Step 3: Generate code
    CodeGenerator generator(pipeline_, model_file_);
    std::string output_dir = generator.Generate(platform);

    // Step 4: Show success dialog
    ShowSuccessDialog(output_dir);
}
```

#### **Day 5: Code Generator**

**code_generator.hpp:**
```cpp
#pragma once
#include "pipeline.hpp"
#include <string>

class CodeGenerator {
public:
    CodeGenerator(const Pipeline& pipeline, const std::string& model_file);

    // Generate firmware and return output directory
    std::string Generate(const std::string& platform);

private:
    void GenerateMainCpp(const std::string& output_dir);
    void GenerateSensorManager(const std::string& output_dir);
    void GenerateModelRunner(const std::string& output_dir);
    void GeneratePlatformIO(const std::string& output_dir);
    void CopyLibraries(const std::string& output_dir);
    void GenerateREADME(const std::string& output_dir);
    std::string CreateZip(const std::string& output_dir);

    const Pipeline& pipeline_;
    std::string model_file_;
    std::string platform_;
};
```

**code_generator.cpp (using inja template engine):**
```cpp
#include "code_generator.hpp"
#include <inja/inja.hpp>
#include <filesystem>
#include <fstream>

namespace fs = std::filesystem;

std::string CodeGenerator::Generate(const std::string& platform) {
    platform_ = platform;

    // Create output directory
    auto timestamp = std::time(nullptr);
    std::string output_dir = "output/firmware_" + platform + "_" +
                            std::to_string(timestamp);
    fs::create_directories(output_dir);
    fs::create_directories(output_dir + "/src");
    fs::create_directories(output_dir + "/lib");

    // Generate all files
    GenerateMainCpp(output_dir);
    GenerateSensorManager(output_dir);
    GenerateModelRunner(output_dir);
    GeneratePlatformIO(output_dir);
    CopyLibraries(output_dir);
    GenerateREADME(output_dir);

    // Create zip
    std::string zip_file = CreateZip(output_dir);

    return output_dir;
}

void CodeGenerator::GenerateMainCpp(const std::string& output_dir) {
    // Load template
    inja::Environment env;
    env.set_template_directory("templates/" + platform_ + "/");

    // Prepare data
    nlohmann::json data;
    data["nodes"] = nlohmann::json::array();

    for (const auto& node : pipeline_.GetNodes()) {
        data["nodes"].push_back({
            {"type", node->GetTypeString()},
            {"id", node->GetId()},
            {"config", node->GetConfig()}
        });
    }

    data["links"] = nlohmann::json::array();
    for (const auto& link : pipeline_.GetLinks()) {
        data["links"].push_back({
            {"from", link.from_pin},
            {"to", link.to_pin}
        });
    }

    // Render template
    std::string code = env.render_file("main.cpp.tmpl", data);

    // Write file
    std::ofstream out(output_dir + "/src/main.cpp");
    out << code;
    out.close();
}

// Similar implementations for other methods...
```

---

### **Week 2: Platform Selection & Firmware Packaging**

**platform_selector.cpp:**
```cpp
std::string ShowPlatformSelectionDialog() {
    static std::string selected_platform;
    static bool show_dialog = true;

    if (show_dialog) {
        ImGui::OpenPopup("Select Platform");
    }

    ImVec2 center = ImGui::GetMainViewport()->GetCenter();
    ImGui::SetNextWindowPos(center, ImGuiCond_Appearing, ImVec2(0.5f, 0.5f));

    if (ImGui::BeginPopupModal("Select Platform", nullptr,
        ImGuiWindowFlags_AlwaysAutoResize)) {

        ImGui::Text("Choose target hardware platform:");
        ImGui::Separator();

        // ESP32
        if (ImGui::ImageButton(...)) {  // Platform icon
            selected_platform = "esp32";
            ImGui::CloseCurrentPopup();
            show_dialog = false;
        }
        ImGui::SameLine();
        ImGui::Text("ESP32 DevKit\n"
                   "⚡ 240MHz\n"
                   "📶 WiFi/BT\n"
                   "💰 $10");

        // Jetson Nano
        if (ImGui::ImageButton(...)) {
            selected_platform = "jetson";
            ImGui::CloseCurrentPopup();
            show_dialog = false;
        }
        ImGui::SameLine();
        ImGui::Text("Jetson Nano\n"
                   "🚀 GPU\n"
                   "💪 4GB RAM\n"
                   "💰 $99");

        // Arduino Nano 33
        if (ImGui::ImageButton(...)) {
            selected_platform = "nano33";
            ImGui::CloseCurrentPopup();
            show_dialog = false;
        }
        ImGui::SameLine();
        ImGui::Text("Arduino Nano 33\n"
                   "🔋 Ultra Low Power\n"
                   "📡 Built-in IMU\n"
                   "💰 $33");

        ImGui::EndPopup();
    }

    return selected_platform;
}
```

---

### **Week 3: Polish & Testing**

- Error handling
- Progress dialogs during generation
- File validation
- Cross-platform testing (Windows/Linux/Mac builds)

---

## Python Integration (Minimal!)

**ui/deployment_wizard.py:**
```python
# Just add ONE button:

def _create_deployment_section(self):
    """Add deployment button."""

    deploy_btn = ctk.CTkButton(
        self,
        text="🎨 Deploy to Hardware (Visual Pipeline)",
        command=self._launch_pipeline_builder,
        height=50,
        font=ctk.CTkFont(size=14, weight="bold")
    )
    deploy_btn.pack(pady=20)

def _launch_pipeline_builder(self):
    """Launch C++ pipeline builder."""
    import subprocess

    # Get trained model path
    model_path = getattr(self, 'model_path', '')

    # Launch C++ executable
    subprocess.Popen([
        'pipeline_builder.exe',
        '--model', model_path
    ])

    # That's it! C++ app does everything else.
    messagebox.showinfo(
        "Pipeline Builder Launched",
        "Visual pipeline builder is now open.\n\n"
        "Design your pipeline and click 'Generate Firmware'\n"
        "The C++ app will create ready-to-flash firmware."
    )
```

**That's the ENTIRE Python integration!** One function, ~15 lines.

---

## Build Instructions

**Windows:**
```bash
# Install dependencies
vcpkg install glfw3 opengl

# Build
mkdir build
cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake
cmake --build . --config Release

# Output: build/Release/pipeline_builder.exe
```

**Linux:**
```bash
# Install dependencies
sudo apt install libglfw3-dev libgl1-mesa-dev

# Build
mkdir build && cd build
cmake ..
make -j4

# Output: build/pipeline_builder
```

---

## Distribution

**Package structure:**
```
CiRA_FutureEdge_Studio/
├── CiRA_Studio.exe          # Python app (PyInstaller)
├── pipeline_builder.exe     # C++ standalone tool
├── templates/               # C++ code templates (bundled)
├── libs/                    # Sensor libraries (bundled)
└── README.md
```

**Users get:**
- Python GUI for training
- C++ tool for deployment
- Both work independently!

---

## Advantages Summary

| Aspect | Old Plan (Python bindings) | New Plan (C++ standalone) |
|--------|---------------------------|---------------------------|
| **Python bindings** | ❌ Required | ✅ Not needed |
| **Python integration** | Complex (subprocess + JSON) | ✅ Trivial (one button) |
| **C++ code** | None | ~2000 lines |
| **Performance** | Good | ⭐ Excellent |
| **Distribution** | 2 parts (Python + binding) | ✅ 2 independent exes |
| **Maintenance** | Python + C++ | C++ only |
| **Standalone use** | ❌ No | ✅ Yes! |
| **Commercial value** | Medium | ⭐ High (can sell separately) |

---

## Timeline

**Week 1:** Core pipeline editor (C++)
**Week 2:** Code generation + packaging (C++)
**Week 3:** Polish + Python integration (trivial)

**Total: 3 weeks**

---

## Future: Sell as Standalone Product! 💰

Since pipeline builder is **completely independent**:

```
CiRA Pipeline Builder Pro
─────────────────────────
Standalone deployment tool for embedded ML

✓ Visual pipeline design
✓ Multi-platform support (ESP32, Jetson, Arduino)
✓ Code generation
✓ Firmware packaging
✓ No Python dependency

Price: $99/license
```

Users can use it with ANY ML model, not just from your Python app!

---

**Ready to implement?** This is the BEST architecture - clean, performant, and commercially viable!
