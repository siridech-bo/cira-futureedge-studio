# C++ Pipeline Builder - Phased Implementation Plan
## Build the Standalone Tool Incrementally

**Date:** 2025-12-15
**Goal:** Implement C++ standalone pipeline builder in manageable phases
**Technology:** C++ with imgui-node-editor
**Total Timeline:** 4-5 weeks

---

## Overview: Building in Phases

Instead of building everything at once, we'll implement the C++ pipeline builder in **4 distinct phases**, each deliverable and testable independently.

```
Phase 1 (Week 1)     → Basic UI + Node Editor Working
Phase 2 (Week 2)     → All Block Types + Properties
Phase 3 (Week 3)     → Code Generation Engine
Phase 4 (Week 4)     → Firmware Packaging + Polish
Phase 5 (Week 5)     → Python Integration + Testing
```

---

## Phase 1: Foundation + Basic Node Editor

**Timeline:** Week 1 (5-7 days)
**Goal:** Get imgui-node-editor working with basic nodes

### **Deliverables:**

✅ **Day 1-2: Project Setup**
- CMake project structure
- Dependencies integrated (imgui, imgui-node-editor, glfw)
- Basic window renders
- Dark theme applied

✅ **Day 3-4: Node Editor Integration**
- imgui-node-editor context created
- Can create empty nodes
- Can connect nodes with links
- Can delete nodes and links

✅ **Day 5: Basic Block Library**
- Left sidebar with block categories
- Can add 2-3 basic nodes (MPU6050, LED)
- Nodes have inputs/outputs pins

### **File Structure (Phase 1):**

```
pipeline_builder/
├── CMakeLists.txt
├── src/
│   ├── main.cpp                    # Entry point + window
│   ├── ui/
│   │   ├── application.hpp         # Window/rendering wrapper
│   │   ├── application.cpp
│   │   ├── pipeline_editor.hpp     # Main editor UI
│   │   └── pipeline_editor.cpp
│   └── core/
│       ├── node.hpp                # Node data structure
│       ├── node.cpp
│       ├── pin.hpp                 # Pin data structure
│       └── link.hpp                # Link data structure
└── third_party/
    ├── imgui/
    ├── imgui-node-editor/
    └── glfw/
```

### **Code to Write (Phase 1):**

#### **CMakeLists.txt**

```cmake
cmake_minimum_required(VERSION 3.15)
project(PipelineBuilder VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find OpenGL
find_package(OpenGL REQUIRED)

# Add subdirectories for third-party libraries
add_subdirectory(third_party/glfw)
add_subdirectory(third_party/imgui)
add_subdirectory(third_party/imgui-node-editor)

# Source files
set(SOURCES
    src/main.cpp
    src/ui/application.cpp
    src/ui/pipeline_editor.cpp
    src/core/node.cpp
)

# Executable
add_executable(pipeline_builder ${SOURCES})

# Include directories
target_include_directories(pipeline_builder PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party
)

# Link libraries
target_link_libraries(pipeline_builder PRIVATE
    imgui
    imgui-node-editor
    glfw
    OpenGL::GL
)

# Set output directory
set_target_properties(pipeline_builder PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Platform-specific settings
if(WIN32)
    # Windows: Hide console window in Release mode
    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        set_target_properties(pipeline_builder PROPERTIES
            WIN32_EXECUTABLE TRUE
        )
    endif()
endif()
```

#### **src/main.cpp**

```cpp
#include "ui/application.hpp"
#include "ui/pipeline_editor.hpp"
#include <iostream>

int main(int argc, char** argv) {
    // Parse command line arguments
    std::string model_file;
    std::string output_file;

    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--model" && i + 1 < argc) {
            model_file = argv[++i];
        } else if (arg == "--output" && i + 1 < argc) {
            output_file = argv[++i];
        }
    }

    try {
        // Create application
        Application app("CiRA Pipeline Builder", 1400, 900);

        // Create pipeline editor
        PipelineEditor editor(model_file, output_file);

        // Main loop
        while (app.BeginFrame()) {
            editor.Render();
            app.EndFrame();
        }

        return 0;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}
```

#### **src/ui/application.hpp**

```cpp
#pragma once

#include <string>

struct GLFWwindow;

namespace ImGui { struct Context; }
namespace ax { namespace NodeEditor { struct EditorContext; } }

class Application {
public:
    Application(const std::string& title, int width, int height);
    ~Application();

    bool BeginFrame();
    void EndFrame();

    GLFWwindow* GetWindow() const { return window_; }

private:
    void SetupImGuiStyle();

    GLFWwindow* window_;
    ImGui::Context* imgui_context_;
    int width_;
    int height_;
};
```

#### **src/ui/application.cpp**

```cpp
#include "application.hpp"
#include <imgui.h>
#include <imgui_impl_glfw.h>
#include <imgui_impl_opengl3.h>
#include <GLFW/glfw3.h>
#include <stdexcept>

Application::Application(const std::string& title, int width, int height)
    : width_(width), height_(height) {

    // Initialize GLFW
    if (!glfwInit()) {
        throw std::runtime_error("Failed to initialize GLFW");
    }

    // OpenGL 3.3 Core
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

#ifdef __APPLE__
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
#endif

    // Create window
    window_ = glfwCreateWindow(width, height, title.c_str(), nullptr, nullptr);
    if (!window_) {
        glfwTerminate();
        throw std::runtime_error("Failed to create GLFW window");
    }

    glfwMakeContextCurrent(window_);
    glfwSwapInterval(1); // VSync

    // Initialize ImGui
    IMGUI_CHECKVERSION();
    imgui_context_ = ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;

    // Setup style
    SetupImGuiStyle();

    // Setup Platform/Renderer backends
    ImGui_ImplGlfw_InitForOpenGL(window_, true);
    ImGui_ImplOpenGL3_Init("#version 330");
}

Application::~Application() {
    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext(imgui_context_);

    glfwDestroyWindow(window_);
    glfwTerminate();
}

bool Application::BeginFrame() {
    if (glfwWindowShouldClose(window_)) {
        return false;
    }

    glfwPollEvents();

    // Start ImGui frame
    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();

    return true;
}

void Application::EndFrame() {
    // Render
    ImGui::Render();

    int display_w, display_h;
    glfwGetFramebufferSize(window_, &display_w, &display_h);
    glViewport(0, 0, display_w, display_h);
    glClearColor(0.15f, 0.15f, 0.15f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);

    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
    glfwSwapBuffers(window_);
}

void Application::SetupImGuiStyle() {
    ImGuiStyle& style = ImGui::GetStyle();

    // Dark theme
    ImGui::StyleColorsDark();

    // Custom colors (dark theme with blue accents)
    ImVec4* colors = style.Colors;
    colors[ImGuiCol_WindowBg] = ImVec4(0.15f, 0.15f, 0.15f, 1.0f);
    colors[ImGuiCol_ChildBg] = ImVec4(0.18f, 0.18f, 0.18f, 1.0f);
    colors[ImGuiCol_FrameBg] = ImVec4(0.25f, 0.25f, 0.25f, 1.0f);
    colors[ImGuiCol_FrameBgHovered] = ImVec4(0.30f, 0.30f, 0.30f, 1.0f);
    colors[ImGuiCol_FrameBgActive] = ImVec4(0.35f, 0.35f, 0.35f, 1.0f);

    // Blue accents
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
    style.ScrollbarRounding = 3.0f;

    // Borders
    style.WindowBorderSize = 1.0f;
    style.FrameBorderSize = 1.0f;
}
```

#### **src/ui/pipeline_editor.hpp**

```cpp
#pragma once

#include <string>
#include <vector>
#include <memory>
#include "../core/node.hpp"
#include "../core/link.hpp"

namespace ax { namespace NodeEditor { struct EditorContext; } }

class PipelineEditor {
public:
    PipelineEditor(const std::string& model_file, const std::string& output_file);
    ~PipelineEditor();

    void Render();

private:
    void RenderToolbar();
    void RenderBlockLibrary();
    void RenderNodeEditor();
    void RenderPropertiesPanel();

    void AddNode(const std::string& type);
    void HandleNodeEditorEvents();

    std::string model_file_;
    std::string output_file_;

    ax::NodeEditor::EditorContext* editor_context_;

    std::vector<std::shared_ptr<Node>> nodes_;
    std::vector<Link> links_;

    int next_node_id_;
    int next_pin_id_;
    int next_link_id_;

    int selected_node_id_;
};
```

#### **src/ui/pipeline_editor.cpp**

```cpp
#include "pipeline_editor.hpp"
#include <imgui.h>
#include <imgui-node-editor/imgui_node_editor.h>

namespace ed = ax::NodeEditor;

PipelineEditor::PipelineEditor(const std::string& model_file, const std::string& output_file)
    : model_file_(model_file)
    , output_file_(output_file)
    , next_node_id_(1)
    , next_pin_id_(1000)
    , next_link_id_(2000)
    , selected_node_id_(-1) {

    // Create node editor context
    ed::Config config;
    config.SettingsFile = "pipeline_builder.ini";
    editor_context_ = ed::CreateEditor(&config);

    // Setup node editor style (blue theme)
    ed::PushStyleColor(ed::StyleColor_NodeBg, ImVec4(0.16f, 0.16f, 0.16f, 1.0f));
    ed::PushStyleColor(ed::StyleColor_NodeBorder, ImVec4(0.4f, 0.4f, 0.4f, 1.0f));
    ed::PushStyleColor(ed::StyleColor_HovNodeBorder, ImVec4(0.6f, 0.6f, 0.6f, 1.0f));
    ed::PushStyleColor(ed::StyleColor_SelNodeBorder, ImVec4(0.26f, 0.59f, 0.98f, 1.0f));
    ed::PushStyleColor(ed::StyleColor_NodeSelRect, ImVec4(0.26f, 0.59f, 0.98f, 0.3f));
    ed::PushStyleColor(ed::StyleColor_LinkSelRect, ImVec4(0.26f, 0.59f, 0.98f, 0.3f));
    ed::PushStyleColor(ed::StyleColor_PinRect, ImVec4(0.26f, 0.59f, 0.98f, 0.6f));
    ed::PushStyleColor(ed::StyleColor_Flow, ImVec4(0.26f, 0.59f, 0.98f, 1.0f));
}

PipelineEditor::~PipelineEditor() {
    ed::DestroyEditor(editor_context_);
}

void PipelineEditor::Render() {
    // Full-screen window
    ImGui::SetNextWindowPos(ImVec2(0, 0));
    ImGui::SetNextWindowSize(ImGui::GetIO().DisplaySize);

    ImGui::Begin("CiRA Pipeline Builder", nullptr,
        ImGuiWindowFlags_NoResize |
        ImGuiWindowFlags_NoMove |
        ImGuiWindowFlags_NoCollapse |
        ImGuiWindowFlags_NoBringToFrontOnFocus |
        ImGuiWindowFlags_NoTitleBar);

    // Title
    ImGui::Text("CiRA FutureEdge Studio - Visual Pipeline Builder");
    if (!model_file_.empty()) {
        ImGui::SameLine(0, 400);
        ImGui::TextColored(ImVec4(0.6f, 0.6f, 0.6f, 1.0f), "Model: %s", model_file_.c_str());
    }
    ImGui::Separator();

    // Toolbar
    RenderToolbar();
    ImGui::Separator();

    // Three-column layout
    ImGui::Columns(3);
    ImGui::SetColumnWidth(0, 250);
    ImGui::SetColumnWidth(1, 900);
    ImGui::SetColumnWidth(2, 250);

    // Left: Block Library
    RenderBlockLibrary();
    ImGui::NextColumn();

    // Center: Node Editor
    RenderNodeEditor();
    ImGui::NextColumn();

    // Right: Properties
    RenderPropertiesPanel();

    ImGui::Columns(1);
    ImGui::End();
}

void PipelineEditor::RenderToolbar() {
    if (ImGui::Button("💾 Save")) {
        // TODO: Save pipeline
    }
    ImGui::SameLine();
    if (ImGui::Button("📂 Load")) {
        // TODO: Load pipeline
    }
    ImGui::SameLine();
    if (ImGui::Button("✓ Validate")) {
        // TODO: Validate pipeline
    }
    ImGui::SameLine();
    if (ImGui::Button("🗑️ Clear")) {
        nodes_.clear();
        links_.clear();
    }

    ImGui::SameLine(0, 300);

    if (ImGui::Button("🚀 Generate Firmware", ImVec2(150, 30))) {
        // TODO: Generate firmware
    }
}

void PipelineEditor::RenderBlockLibrary() {
    ImGui::BeginChild("BlockLibrary", ImVec2(0, 0), true);

    ImGui::Text("Block Library");
    ImGui::Separator();

    // Sensors
    if (ImGui::CollapsingHeader("📡 Sensors", ImGuiTreeNodeFlags_DefaultOpen)) {
        if (ImGui::Button("MPU6050", ImVec2(-1, 0))) {
            AddNode("MPU6050");
        }
        if (ImGui::Button("ADXL345", ImVec2(-1, 0))) {
            AddNode("ADXL345");
        }
    }

    // Outputs
    if (ImGui::CollapsingHeader("📤 Outputs", ImGuiTreeNodeFlags_DefaultOpen)) {
        if (ImGui::Button("LED", ImVec2(-1, 0))) {
            AddNode("LED");
        }
    }

    ImGui::EndChild();
}

void PipelineEditor::RenderNodeEditor() {
    ImGui::BeginChild("NodeEditor", ImVec2(0, 0), true);

    ed::SetCurrentEditor(editor_context_);
    ed::Begin("Pipeline Editor");

    // Render nodes
    for (const auto& node : nodes_) {
        node->Render();
    }

    // Render links
    for (const auto& link : links_) {
        ed::Link(link.id, link.start_pin_id, link.end_pin_id);
    }

    // Handle events
    HandleNodeEditorEvents();

    ed::End();
    ed::SetCurrentEditor(nullptr);

    ImGui::EndChild();
}

void PipelineEditor::RenderPropertiesPanel() {
    ImGui::BeginChild("Properties", ImVec2(0, 0), true);

    ImGui::Text("Properties");
    ImGui::Separator();

    if (selected_node_id_ >= 0) {
        // Find selected node
        for (const auto& node : nodes_) {
            if (node->GetId() == selected_node_id_) {
                node->RenderProperties();
                break;
            }
        }
    } else {
        ImGui::TextWrapped("Select a node to edit properties");
    }

    ImGui::EndChild();
}

void PipelineEditor::AddNode(const std::string& type) {
    auto node = std::make_shared<Node>(next_node_id_++, type);

    // Set initial position (staggered)
    float x = 100.0f + (nodes_.size() % 5) * 200.0f;
    float y = 100.0f + (nodes_.size() / 5) * 150.0f;
    node->SetPosition(x, y);

    // Add pins based on type
    if (type == "MPU6050") {
        node->AddOutputPin(next_pin_id_++, "Accel");
        node->AddOutputPin(next_pin_id_++, "Gyro");
    } else if (type == "LED") {
        node->AddInputPin(next_pin_id_++, "Trigger");
    }

    nodes_.push_back(node);
}

void PipelineEditor::HandleNodeEditorEvents() {
    // Handle link creation
    if (ed::BeginCreate()) {
        ed::PinId start_pin_id, end_pin_id;
        if (ed::QueryNewLink(&start_pin_id, &end_pin_id)) {
            if (ed::AcceptNewItem()) {
                links_.push_back({next_link_id_++, (int)start_pin_id.Get(), (int)end_pin_id.Get()});
            }
        }
    }
    ed::EndCreate();

    // Handle link deletion
    if (ed::BeginDelete()) {
        ed::LinkId link_id;
        while (ed::QueryDeletedLink(&link_id)) {
            if (ed::AcceptDeletedItem()) {
                links_.erase(
                    std::remove_if(links_.begin(), links_.end(),
                        [&](const Link& l) { return l.id == (int)link_id.Get(); }),
                    links_.end()
                );
            }
        }

        ed::NodeId node_id;
        while (ed::QueryDeletedNode(&node_id)) {
            if (ed::AcceptDeletedItem()) {
                nodes_.erase(
                    std::remove_if(nodes_.begin(), nodes_.end(),
                        [&](const std::shared_ptr<Node>& n) { return n->GetId() == (int)node_id.Get(); }),
                    nodes_.end()
                );
            }
        }
    }
    ed::EndDelete();

    // Handle node selection
    int selected_count = ed::GetSelectedObjectCount();
    if (selected_count > 0) {
        std::vector<ed::NodeId> selected_nodes;
        selected_nodes.resize(selected_count);
        ed::GetSelectedNodes(selected_nodes.data(), selected_count);
        if (!selected_nodes.empty()) {
            selected_node_id_ = (int)selected_nodes[0].Get();
        }
    }
}
```

#### **src/core/node.hpp**

```cpp
#pragma once

#include <string>
#include <vector>
#include <map>
#include "pin.hpp"

class Node {
public:
    Node(int id, const std::string& type);

    void Render();
    void RenderProperties();

    void AddInputPin(int id, const std::string& name);
    void AddOutputPin(int id, const std::string& name);

    void SetPosition(float x, float y);

    int GetId() const { return id_; }
    const std::string& GetType() const { return type_; }

private:
    int id_;
    std::string type_;
    std::string label_;

    std::vector<Pin> input_pins_;
    std::vector<Pin> output_pins_;

    std::map<std::string, std::string> config_;

    float pos_x_;
    float pos_y_;
};
```

#### **src/core/node.cpp**

```cpp
#include "node.hpp"
#include <imgui.h>
#include <imgui-node-editor/imgui_node_editor.h>

namespace ed = ax::NodeEditor;

Node::Node(int id, const std::string& type)
    : id_(id)
    , type_(type)
    , label_(type)
    , pos_x_(0)
    , pos_y_(0) {
}

void Node::Render() {
    ed::BeginNode(id_);

    // Title bar
    ImGui::Text("%s", label_.c_str());
    ImGui::Dummy(ImVec2(150, 0)); // Min width

    // Input pins
    for (const auto& pin : input_pins_) {
        ed::BeginPin(pin.id, ed::PinKind::Input);
        ImGui::Text("► %s", pin.name.c_str());
        ed::EndPin();
    }

    // Output pins
    for (const auto& pin : output_pins_) {
        ed::BeginPin(pin.id, ed::PinKind::Output);
        ImGui::Text("%s ►", pin.name.c_str());
        ed::EndPin();
    }

    ed::EndNode();

    // Set position if specified
    if (pos_x_ != 0 || pos_y_ != 0) {
        ed::SetNodePosition(id_, ImVec2(pos_x_, pos_y_));
    }
}

void Node::RenderProperties() {
    ImGui::Text("Node: %s", label_.c_str());
    ImGui::Separator();

    // Type-specific properties will be added in Phase 2
    ImGui::TextWrapped("Properties for %s node", type_.c_str());
}

void Node::AddInputPin(int id, const std::string& name) {
    input_pins_.push_back({id, name});
}

void Node::AddOutputPin(int id, const std::string& name) {
    output_pins_.push_back({id, name});
}

void Node::SetPosition(float x, float y) {
    pos_x_ = x;
    pos_y_ = y;
}
```

#### **src/core/pin.hpp**

```cpp
#pragma once

#include <string>

struct Pin {
    int id;
    std::string name;
};
```

#### **src/core/link.hpp**

```cpp
#pragma once

struct Link {
    int id;
    int start_pin_id;
    int end_pin_id;
};
```

### **Phase 1 Success Criteria:**

✅ Application window opens with dark theme
✅ Can add MPU6050 and LED nodes from library
✅ Nodes appear in editor canvas
✅ Can connect MPU6050 output to LED input
✅ Can delete nodes and links
✅ Selection works (click node shows in properties panel)

**Build command:**
```bash
mkdir build && cd build
cmake ..
cmake --build .
./bin/pipeline_builder
```

---

## Phase 2: Complete Block Types + Properties

**Timeline:** Week 2 (5-7 days)
**Goal:** Add all node types with full property editing

### **Deliverables:**

✅ **Day 1-2: Complete Node Types**
- MPU6050, ADXL345 (sensors)
- Normalize, SlidingWindow (processing)
- TimesNet (model)
- LED, Serial, WiFiPOST (outputs)

✅ **Day 3-4: Property Editors**
- Dynamic property forms per node type
- Input validation
- Default values

✅ **Day 5: Save/Load Pipeline**
- Save pipeline to JSON
- Load pipeline from JSON

### **Files to Add/Modify:**

```cpp
// src/core/node_factory.hpp
class NodeFactory {
public:
    static std::shared_ptr<Node> CreateNode(const std::string& type, int id);
};

// src/core/nodes/
mpu6050_node.hpp/cpp
adxl345_node.hpp/cpp
normalize_node.hpp/cpp
timesnet_node.hpp/cpp
led_node.hpp/cpp
// ... etc
```

---

## Phase 3: Code Generation Engine

**Timeline:** Week 3 (5-7 days)
**Goal:** Generate C++ firmware from pipeline graph

### **Deliverables:**

✅ **Day 1-2: Template System**
- Integrate inja template engine
- Create ESP32 templates (main.cpp, platformio.ini)

✅ **Day 3-4: Code Generator**
- Traverse pipeline graph
- Topological sort
- Generate code from templates

✅ **Day 5: Platform Selection**
- Dialog to choose ESP32/Jetson/Nano33
- Platform-specific code generation

### **Files to Add:**

```cpp
// src/core/code_generator.hpp
class CodeGenerator {
public:
    std::string Generate(const Pipeline& pipeline, const std::string& platform);
};

// templates/esp32/
main.cpp.jinja2
platformio.ini.jinja2
sensor_manager.cpp.jinja2
```

---

## Phase 4: Firmware Packaging + Polish

**Timeline:** Week 4 (5-7 days)
**Goal:** Complete firmware packaging and UI polish

### **Deliverables:**

✅ **Day 1-2: Firmware Packager**
- Copy sensor libraries
- Generate README
- Create .zip file

✅ **Day 3-4: UI Polish**
- Success dialogs
- Error handling
- Progress indicators

✅ **Day 5: Testing**
- Test generated firmware compiles
- Test on real hardware

---

## Phase 5: Python Integration + Release

**Timeline:** Week 5 (3-5 days)
**Goal:** Integrate with main Python app

### **Deliverables:**

✅ **Day 1: Python Integration**
- Add button in deployment_wizard.py
- Subprocess launcher

✅ **Day 2-3: End-to-End Testing**
- Test full workflow: Python → C++ → Firmware
- Bug fixes

✅ **Day 4-5: Documentation**
- User guide
- Developer documentation

---

## Build Script (build.sh)

```bash
#!/bin/bash

# Build script for pipeline_builder

set -e

echo "Building Pipeline Builder..."

# Create build directory
mkdir -p build
cd build

# Configure
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build . --config Release -j4

# Copy to output
mkdir -p ../bin
cp pipeline_builder ../bin/

echo "Build complete: ../bin/pipeline_builder"
```

---

## Testing Checklist (Per Phase)

### **Phase 1:**
- [ ] Application starts without errors
- [ ] Dark theme applied correctly
- [ ] Can add nodes from library
- [ ] Can create links between nodes
- [ ] Can delete nodes and links
- [ ] Properties panel shows selected node

### **Phase 2:**
- [ ] All 8 node types work
- [ ] Properties panel shows correct fields per type
- [ ] Can edit all properties
- [ ] Can save pipeline to JSON
- [ ] Can load pipeline from JSON

### **Phase 3:**
- [ ] Platform selection dialog works
- [ ] Code generation produces valid C++
- [ ] Generated code compiles without errors
- [ ] Templates render correctly

### **Phase 4:**
- [ ] Firmware package includes all files
- [ ] .zip file created successfully
- [ ] README generated with correct instructions
- [ ] Success dialog shows correct paths

### **Phase 5:**
- [ ] Python app launches C++ tool
- [ ] Model file passed correctly
- [ ] Generated firmware works on hardware
- [ ] Full workflow smooth and bug-free

---

## Risk Management

### **High Risk Items:**

1. **imgui-node-editor integration**
   - Mitigation: Complete in Phase 1, validate early
   - Fallback: Use simpler node rendering if needed

2. **Cross-platform builds**
   - Mitigation: Test on Windows/Linux from Phase 1
   - Fallback: Support Windows only initially

3. **Template complexity**
   - Mitigation: Start with simple ESP32 template
   - Fallback: Manual code generation if templates too complex

---

## Summary

**Total Timeline:** 4-5 weeks

| Phase | Week | Deliverable | Risk |
|-------|------|-------------|------|
| Phase 1 | Week 1 | Basic node editor working | Medium |
| Phase 2 | Week 2 | All blocks + properties | Low |
| Phase 3 | Week 3 | Code generation | Medium |
| Phase 4 | Week 4 | Firmware packaging | Low |
| Phase 5 | Week 5 | Python integration | Low |

**Can ship incrementally:**
- End of Phase 1: Demo node editor
- End of Phase 3: Can generate code (manual packaging)
- End of Phase 4: **Full product ready!**

---

**Ready to start Phase 1?** 🚀
