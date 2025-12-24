# GitHub Setup Guide for CiRA Projects

## Overview

We'll push two repositories:
1. **pipeline_builder** - Visual pipeline editor with deployment
2. **cira-block-runtime** - Block-based execution runtime

---

## Step 1: Create GitHub Repositories

Go to https://github.com/new and create two repositories:

### Repository 1: pipeline_builder
- **Name**: `cira-pipeline-builder`
- **Description**: Visual pipeline builder for AI/IoT workflows with block-based deployment
- **Visibility**: Public (or Private if you prefer)
- **Initialize**: ❌ Do NOT initialize with README (we have existing code)

### Repository 2: cira-block-runtime
- **Name**: `cira-block-runtime`
- **Description**: Dynamic block-based runtime for embedded AI pipelines (Jetson Nano, Arduino UNO Q)
- **Visibility**: Public (or Private if you prefer)
- **Initialize**: ❌ Do NOT initialize with README

---

## Step 2: Prepare .gitignore Files

Before pushing, we need to exclude build artifacts and temporary files.

### For pipeline_builder:

Create `D:\CiRA FES\pipeline_builder\.gitignore`:
```
# Build directories
build/
bin/
lib/
Debug/
Release/

# IDE files
.vs/
.vscode/
*.user
*.suo
*.sln.docstates

# Compiled files
*.exe
*.dll
*.so
*.a
*.lib
*.obj
*.o

# CMake
CMakeCache.txt
CMakeFiles/
cmake_install.cmake
install_manifest.txt

# Output directories (generated firmware)
output/*/

# Keep output folder structure but ignore generated content
!output/.gitkeep

# Temporary files
*.log
*.tmp
*~
.DS_Store

# Third-party (if large)
# third_party/
```

### For cira-block-runtime:

Create `D:\CiRA FES\cira-block-runtime\.gitignore`:
```
# Build directories
build/
Debug/
Release/

# Compiled files
*.exe
*.dll
*.so
*.a
*.lib
*.obj
*.o

# CMake
CMakeCache.txt
CMakeFiles/
cmake_install.cmake
install_manifest.txt

# IDE files
.vs/
.vscode/
*.user

# Test outputs
*.log
*~
```

---

## Step 3: Initialize Git and Push

### For pipeline_builder:

```bash
cd "D:\CiRA FES\pipeline_builder"

# Initialize git (if not already)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: CiRA Pipeline Builder

- Visual node-based pipeline editor
- Block metadata system with version tracking
- Deployment mode selector (Compiled Binary vs Block Runtime)
- Block manifest generator (JSON)
- SSH deployment to Jetson Nano
- Platform selection (Jetson Nano / Arduino UNO Q)
- 17 built-in nodes (sensors, processing, models, outputs)
- Pin color coding by data type
- Code generation for C++ and Arduino
- Integrated deployment wizard

Implements Phase 1-3 of Block System architecture."

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/cira-pipeline-builder.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### For cira-block-runtime:

```bash
cd "D:\CiRA FES\cira-block-runtime"

# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: CiRA Block Runtime

- Dynamic block loading system (.so/.dll)
- Manifest parser (JSON-based pipeline configuration)
- Block executor with topological sorting
- Example blocks:
  - ADXL345 accelerometer sensor
  - Sliding Window processor
  - Channel Merge processor
  - GPIO output controller
- Cross-platform support (Linux/Windows)
- Simulation mode for development
- Signal handling (graceful shutdown)
- Performance statistics tracking

Phase 4.1-4.2 complete: Core runtime + example blocks tested."

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/cira-block-runtime.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 4: Add README Files

### For pipeline_builder:

Create `D:\CiRA FES\pipeline_builder\README.md`:
```markdown
# CiRA Pipeline Builder

Visual pipeline builder for AI/IoT workflows with block-based deployment.

![Pipeline Builder](docs/screenshot.png)

## Features

- 🎨 **Visual Node Editor** - Blueprint-style visual programming
- 🔌 **17+ Built-in Blocks** - Sensors, processing, AI models, outputs
- 🚀 **Dual Deployment Modes**:
  - Compiled Binary (production)
  - Block Runtime (rapid iteration)
- 📦 **Block Manifest Generation** - JSON-based pipeline configuration
- 🎯 **Multi-Platform Support** - Jetson Nano, Arduino UNO Q
- 🔄 **SSH Deployment** - One-click deploy to devices
- 🎨 **Pin Color Coding** - Visual type checking

## Quick Start

### Build

\`\`\`bash
mkdir build && cd build
cmake ..
make -j$(nproc)
./pipeline_builder
\`\`\`

### Usage

1. Drag blocks from library to canvas
2. Connect nodes (color-coded by type)
3. Configure node properties
4. Generate → Deploy to Device
5. Select deployment mode:
   - **Compiled Binary**: Fast, production-ready
   - **Block Runtime**: Rapid prototyping, hot-reload

## Architecture

\`\`\`
Pipeline Builder → Block Manifest → Target Device
                       (JSON)         ├─ Jetson Nano
                                     └─ Arduino UNO Q
\`\`\`

## Documentation

- [Block System Implementation Plan](BLOCK_SYSTEM_IMPLEMENTATION_PLAN.md)
- [Pin Color Coding Guide](PIN_COLOR_CODING_GUIDE.md)
- [Arduino Code Generation TODO](ARDUINO_CODE_GENERATION_TODO.md)

## Requirements

- C++17 compiler
- CMake 3.10+
- ImGui + imgui-node-editor
- nlohmann/json

## License

Copyright (c) 2025 CiRA Project

## Related Projects

- [cira-block-runtime](https://github.com/YOUR_USERNAME/cira-block-runtime) - Execution runtime for deployed pipelines
```

### For cira-block-runtime:

Create `D:\CiRA FES\cira-block-runtime\README.md` (already exists, but verify it's up to date)

---

## Step 5: Add Documentation Files to Git

Make sure these important docs are committed:

### pipeline_builder:
```bash
cd "D:\CiRA FES\pipeline_builder"
git add BLOCK_SYSTEM_IMPLEMENTATION_PLAN.md
git add PIN_COLOR_CODING_GUIDE.md
git add ARDUINO_CODE_GENERATION_TODO.md
git commit -m "docs: Add architecture and planning documentation"
git push
```

### cira-block-runtime:
```bash
cd "D:\CiRA FES\cira-block-runtime"
git add BUILD_AND_TEST.md
git add PHASE_4_BLOCK_RUNTIME_IMPLEMENTATION_PLAN.md
git add PHASE_4_2_COMPLETE.md
git commit -m "docs: Add build guide and phase completion reports"
git push
```

---

## Step 6: Add Topics/Tags on GitHub

After pushing, go to each repository on GitHub and add topics:

### pipeline_builder topics:
- `pipeline-builder`
- `visual-programming`
- `iot`
- `embedded`
- `ai`
- `jetson-nano`
- `arduino`
- `imgui`
- `node-editor`

### cira-block-runtime topics:
- `runtime`
- `embedded-systems`
- `dynamic-loading`
- `iot`
- `jetson-nano`
- `arduino-uno-q`
- `block-system`
- `edge-ai`

---

## Step 7: Create GitHub Releases (Optional)

Tag the current state as v1.0.0:

### pipeline_builder:
```bash
cd "D:\CiRA FES\pipeline_builder"
git tag -a v1.0.0 -m "Release v1.0.0: Block System Phase 1-3 Complete"
git push origin v1.0.0
```

### cira-block-runtime:
```bash
cd "D:\CiRA FES\cira-block-runtime"
git tag -a v1.0.0 -m "Release v1.0.0: Core Runtime + Example Blocks"
git push origin v1.0.0
```

---

## Step 8: Link Repositories

Add cross-references in README files:

**In pipeline_builder/README.md**, add:
```markdown
## Related Projects

- [cira-block-runtime](https://github.com/YOUR_USERNAME/cira-block-runtime) - Execution runtime
```

**In cira-block-runtime/README.md**, add:
```markdown
## Related Projects

- [cira-pipeline-builder](https://github.com/YOUR_USERNAME/cira-pipeline-builder) - Visual editor
```

---

## Summary Checklist

### Pre-Push:
- [ ] Create both GitHub repositories
- [ ] Add .gitignore files
- [ ] Verify README.md files exist
- [ ] Review files to commit (exclude output/, build/)

### Push:
- [ ] Initialize git repos
- [ ] Add all files
- [ ] Create initial commits
- [ ] Add remote origins
- [ ] Push to GitHub

### Post-Push:
- [ ] Add repository topics/tags
- [ ] Create v1.0.0 releases
- [ ] Link repositories in READMEs
- [ ] Verify everything looks good on GitHub

---

## Commands Summary

Replace `YOUR_USERNAME` with your actual GitHub username.

### Pipeline Builder:
\`\`\`bash
cd "D:\CiRA FES\pipeline_builder"
git init
git add .
git commit -m "Initial commit: CiRA Pipeline Builder"
git remote add origin https://github.com/YOUR_USERNAME/cira-pipeline-builder.git
git branch -M main
git push -u origin main
\`\`\`

### Block Runtime:
\`\`\`bash
cd "D:\CiRA FES\cira-block-runtime"
git init
git add .
git commit -m "Initial commit: CiRA Block Runtime"
git remote add origin https://github.com/YOUR_USERNAME/cira-block-runtime.git
git branch -M main
git push -u origin main
\`\`\`

---

**Ready to push!** Let me know if you need help with any step. 🚀
