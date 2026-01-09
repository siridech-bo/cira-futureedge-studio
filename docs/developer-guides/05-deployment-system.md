# Deployment System Guide

This guide explains the Pipeline Builder deployment system, including all deployment modes, buttons, and how to customize the deployment functionality.

## Overview

The deployment system transfers your pipeline from Pipeline Builder (Windows) to the target device (Jetson Nano) via SSH/SFTP, compiles the runtime and blocks, and starts execution.

**Architecture:**
```
Pipeline Builder (Windows)
    ↓ SSH/SFTP (libssh)
Jetson Nano (ARM Linux)
    ↓ Compile & Install
Block Runtime + Blocks
    ↓ Execute
Running Pipeline
```

---

## Deployment Dialog Overview

When you click **Deploy → Deploy to Device**, you see the deployment dialog with these sections:

### 1. Deployment Mode

**Two modes available:**

#### Compiled Binary (Production)
- Uses pre-compiled binaries from cache
- **Fast deployment** (seconds)
- No compilation on device
- Requires cache from "Install from Precompiled"

#### Block Runtime (Development) ✅ (Default)
- Compiles source code on device
- **Slower** (minutes) but always up-to-date
- Used for development and testing
- Creates cache after successful compilation

---

### 2. Web Dashboard Settings

```
☑ Enable Web Dashboard
Port: 8083
Username: admin
Password: *******
Dashboard will be accessible at: http://device-ip:8083
```

**Purpose:** Enable/disable the web-based monitoring dashboard

**Customization:** See section "Modifying Web Dashboard Settings"

---

### 3. Deployment Target

```
Deployment Target: [Jetson Nano ▼] [Connected] [Add Target] [Edit] [Remove] [Test Connection]
Platform: jetson_nano
Host: user@192.168.1.200:22
Workspace: /home/user/cira_projects
Project: ts3_new
Path: C:/Users/bmwsb/AppData/Local/CiRA/output/ts3_new_manifest
```

**Components:**
- **Target Dropdown**: Select from saved device profiles
- **Connected**: Shows connection status (green = connected)
- **Add Target**: Add new device profile
- **Edit**: Modify existing device profile
- **Remove**: Delete device profile
- **Test Connection**: Verify SSH connectivity

---

### 4. Deployment Buttons

```
[Validate] [Check Device Space] [Setup Device] [Update Runtime] [Install from Precompiled] [Deploy] [Test Inference] [Copy Log] [Clear Log]
```

---

## Deployment Buttons Explained

### Button 1: Validate

**Function:** Validates the pipeline before deployment

**What it checks:**
- All nodes have required connections
- No missing block implementations
- Configuration parameters are valid
- No circular dependencies

**Code Location:** `pipeline_builder/src/deployment/pipeline_validator.cpp`

**When to use:** Before deploying to catch errors early

**Output:**
```
✓ Pipeline validation successful
- 7 nodes
- 12 connections
- All blocks available
```

---


### Button 2: Check Device Status

**Function:** Comprehensive device status check - verifies device state and block library

**What it checks (6 steps):**

1. **Device Connection**
   - SSH connectivity
   - Network reachability
   - Authentication

2. **Runtime Installation**
   - Check if runtime binary exists
   - Verify executable permissions
   - Check version

3. **Block Library Status**
   - Count installed blocks on device
   - Compare with precompiled cache
   - Check block versions

4. **Disk Space**
   - Available space in workspace
   - Check if sufficient for deployment

5. **Build Tools**
   - Verify CMake, g++, make are installed
   - Check versions

6. **Recommendations**
   - Suggest actions based on device state
   - "Setup Device" if no blocks installed
   - "Install from Precompiled" if cache mismatch
   - "Up-to-date" if everything matches

**Code Location:** \`pipeline_builder/src/deployment/precompiled_cache.cpp:CheckDeviceStatus()\`

**When to use:**
- Before first deployment
- After device reboot
- Troubleshooting deployment issues
- Verifying device state

**Output:**
\`\`\`
===== DEVICE STATUS CHECK =====
[1/6] Checking device connection...
  ✓ Connected to 192.168.1.200:22

[2/6] Checking runtime installation...
  ✓ Runtime binary found: /home/user/cira_projects/cira-runtime/bin/cira-block-runtime

[3/6] Checking block library...
  ✓ 21 blocks installed on device
  ✓ 21 blocks in precompiled cache
  ✓ Block library is synchronized

[4/6] Checking disk space...
  ✓ Available: 12.4 GB in /home/user/cira_projects

[5/6] Checking build tools...
  ✓ CMake 3.10.2
  ✓ g++ 7.5.0
  ✓ make 4.1

[6/6] Status summary:
  Device Status: Ready ✓
  Recommendation: ✓ Device library is up-to-date (21 blocks installed). No action needed.
\`\`\`

---

---

### Button 3: Setup Device

**Function:** Full device setup - compiles everything from scratch

**What it does (7 steps):**

1. **Transfer Source Code**
   - Upload cira-block-runtime/ directory
   - Upload all block source code
   - Upload CMake configuration
   - Upload web assets

2. **Install Dependencies**
   - Check for CMake, g++, make
   - Install missing packages via apt (if needed)

3. **Create Build Directory**
   - `/home/user/cira_projects/cira-runtime/build`

4. **Run CMake**
   - Configure build system
   - Detect dependencies (ONNX Runtime, etc.)
   - Generate Makefiles

5. **Compile Runtime**
   - `make -j1 cira-block-runtime`
   - Compile main runtime binary

6. **Compile All Blocks**
   - `make -j1` (all targets)
   - Compile each block .so file
   - Install to blocks/ directory

7. **Create Precompiled Cache**
   - Download compiled binaries to Windows
   - Store in `./compiled_cache/jetson_nano/`
   - Enable "Install from Precompiled" for other devices

**Duration:** 5-10 minutes (first time)

**Code Location:** `pipeline_builder/src/deployment/block_runtime_deployer.cpp:SetupDevice()`

**When to use:**
- First time deploying to a device
- After major code changes
- After adding new dependencies
- To rebuild the precompiled cache

**Output:**
```
===== DEVICE SETUP =====
[1/3] Setting up device...
[2/3] Compiling and installing block library...
  Compiling runtime (this may take 2-5 minutes)...
  Compiling blocks (this may take 2-5 minutes)...
  ✓ 21 block(s) installed
[3/3] Device setup complete!

Downloading compiled binaries to cache...
✓ Downloaded 21 block libraries
✓ Precompiled cache saved successfully!
```

---

### Button 4: Update Runtime

**Function:** Quick incremental update - only recompiles changed files

**What it does (5 steps):**

1. **Upload Source Files**
   - Only upload changed source files
   - Upload changed headers
   - Upload changed block implementations

2. **Incremental Compilation**
   - `make -j1` (only rebuilds changed files)
   - Much faster than full rebuild

3. **Copy Block Libraries**
   - Copy updated .so files to blocks/ directory
   - Only copies changed blocks

4. **Validate Installation**
   - Check file timestamps
   - Verify all required files exist
   - Display validation summary

5. **Stop Running Runtime**
   - Kill existing runtime process
   - Ready for new deployment

**Duration:** 1-2 minutes (only changed files)

**Code Location:** `pipeline_builder/src/deployment/block_runtime_deployer.cpp:DeployRuntimeOnly()`

**When to use:**
- During iterative development
- After modifying block code
- After adding new pins/parameters
- Quick testing cycles

**Output:**
```
===== RUNTIME UPDATE =====
[1/5] Updating runtime on device...
  Uploading runtime source files...
  Uploading block source files...
  Building runtime binary (CMake reconfigure + compile)...
  Runtime binary copied successfully
  Copying updated block libraries...
  Block libraries copied successfully
  Validating updated files...
  Updated files: 21 files at 15:08
  Runtime update complete!
```

---

### Button 5: Install from Precompiled

**Function:** Deploy pre-compiled binaries without compilation

**What it does (3 steps):**

1. **Load Precompiled Cache**
   - Read from `./compiled_cache/jetson_nano/`
   - Verify cache is valid and up-to-date

2. **Upload Binaries**
   - Upload runtime binary
   - Upload all .so block libraries

3. **Set Permissions**
   - `chmod +x cira-block-runtime`
   - `chmod +x *.so`

**Duration:** 10-30 seconds (no compilation!)

**Code Location:** `pipeline_builder/src/deployment/block_runtime_deployer.cpp:InstallPrecompiled()`

**Requirements:**
- Must have run "Setup Device" first (to create cache)
- Cache must be for same platform architecture
- Code must not have changed since cache was created

**When to use:**
- Deploying to multiple identical devices
- Production deployments
- When code hasn't changed
- Quick device setup

**Output:**
```
===== INSTALL FROM PRECOMPILED =====
Loading precompiled cache...
✓ Cache found: 21 blocks
Uploading runtime binary...
Uploading block libraries...
✓ Installation complete!
```

---

### Button 6: Deploy

**Function:** Deploy the current pipeline and start execution

**What it does (4 steps):**

1. **Generate Block Manifest**
   - Create JSON manifest with pipeline configuration
   - Include all node configs, connections, pins

2. **Upload Manifest**
   - Upload to `/home/user/cira_projects/cira-runtime/manifests/`

3. **Upload Model Files**
   - Copy ONNX models, datasets, config files
   - Upload to `/home/user/cira_projects/cira-runtime/models/`

4. **Start Runtime**
   - Kill existing process
   - Start new runtime: `./cira-block-runtime manifest.json --web-port 8083`

**Duration:** 5-10 seconds

**Code Location:** `pipeline_builder/src/deployment/block_runtime_deployer.cpp:Deploy()`

**When to use:**
- After "Setup Device" or "Update Runtime"
- Every time you change pipeline configuration
- Every time you connect/disconnect wires
- Every time you modify node properties

**Output:**
```
Starting Block Runtime deployment...
Generating block manifest...
Block manifest saved to: block_manifest.json
Required blocks:
  - channel-merge v1.0.0
  - data-recorder v1.0.0
  - sliding-window v1.0.0
  - synthetic-signal-generator v1.0.0
  - timesnet v1.2.0
  - web-button v1.0.0
  - web-led v1.0.0
Transferring manifest...
Starting runtime on device...
✓ Deployment successful!
Runtime is now running at http://192.168.1.200:8083
```

---

### Button 7: Test Inference

**Function:** Run a quick inference test with sample data

**Code Location:** `pipeline_builder/src/deployment/block_runtime_deployer.cpp:TestInference()`

**What it does:**
- Send test data via WebSocket
- Capture inference results
- Display latency and accuracy

**When to use:** After deploying ML models

---

### Button 8: Copy Log

**Function:** Copy deployment log to clipboard

**When to use:** Sharing error messages, debugging

---

### Button 9: Clear Log

**Function:** Clear the deployment log window

---

## Deployment Workflow

### Typical Development Workflow

```
1. Create/modify pipeline in Pipeline Builder
   ↓
2. First time: [Setup Device] (5-10 min)
   ↓
3. [Validate] - Check pipeline is valid
   ↓
4. [Deploy] - Upload and start runtime
   ↓
5. Test in web dashboard (http://device-ip:8083)
   ↓
6. Modify blocks/pipeline
   ↓
7. [Update Runtime] (1-2 min) - Only if code changed
   ↓
8. [Deploy] - Upload new config
   ↓
9. Repeat steps 5-8 until satisfied
```

### Production Deployment Workflow

```
1. Development complete and tested
   ↓
2. [Setup Device] on main device (creates cache)
   ↓
3. For each additional device:
   [Add Target] → [Install from Precompiled] → [Deploy]
   ↓
4. Done! (30 seconds per device)
```

---

## File Locations

### Source Code

```
pipeline_builder/src/deployment/
├── block_runtime_deployer.h        # Main deployer interface
├── block_runtime_deployer.cpp      # Deployment implementation
├── block_library_locator.h         # Block discovery
├── block_library_locator.cpp       # Find blocks in project
├── deployment_dialog.h             # UI dialog
└── deployment_dialog.cpp           # UI implementation
```

### Key Methods

**block_runtime_deployer.cpp:**
```cpp
bool SetupDevice()           // Setup Device button
bool DeployRuntimeOnly()     // Update Runtime button
bool InstallPrecompiled()    // Install from Precompiled button
bool Deploy()                // Deploy button
bool TestInference()         // Test Inference button
bool CheckDeviceSpace()      // Check Device Space button
bool Validate()              // Validate button
```

---

## Customizing Deployment

### Modify Compilation Flags

**File:** `pipeline_builder/src/deployment/block_runtime_deployer.cpp`

```cpp
bool BlockRuntimeDeployer::SetupDevice() {
    // ... existing code ...

    // Change compilation command
    std::string compile_cmd =
        "cd " + build_dir + " && "
        "make -j1 "              // ← Change parallelism
        "CMAKE_BUILD_TYPE=Release "  // ← Add build flags
        "ENABLE_TENSORRT=ON "    // ← Add custom flags
        "2>&1";

    // Execute compilation
    std::string compile_output = ExecuteSSHCommand(compile_cmd);
}
```

### Add Custom Deployment Step

```cpp
bool BlockRuntimeDeployer::Deploy() {
    // ... existing deployment steps ...

    // Add custom step: Copy configuration files
    ReportProgress("Copying custom configs...", 80);
    std::string remote_config_dir = remote_workspace_ + "/configs";
    if (!TransferDirectory("D:/MyProject/configs", remote_config_dir)) {
        ReportError("Failed to copy configs");
        return false;
    }

    // Add custom step: Set environment variables
    std::string env_cmd = "echo 'export MY_VAR=value' >> ~/.bashrc";
    ExecuteSSHCommand(env_cmd);

    // ... continue with deployment ...
}
```

### Modify Web Dashboard Port

**File:** `pipeline_builder/src/deployment/deployment_dialog.cpp`

```cpp
void DeploymentDialog::RenderWebDashboardSettings() {
    ImGui::Checkbox("Enable Web Dashboard", &enable_web_dashboard_);

    if (enable_web_dashboard_) {
        // Change default port
        ImGui::InputInt("Port", &web_port_);  // Default: 8083

        // Add SSL option
        ImGui::Checkbox("Enable HTTPS", &enable_https_);

        // ... rest of settings ...
    }
}
```

### Change SSH Connection Timeout

**File:** `pipeline_builder/src/deployment/block_runtime_deployer.cpp`

```cpp
bool BlockRuntimeDeployer::ConnectSSH() {
    // ... existing connection code ...

    // Set custom timeout (default: 10 seconds)
    ssh_options_set(ssh_session_, SSH_OPTIONS_TIMEOUT, 30);  // 30 seconds

    // Set custom connection attempts
    int attempts = 3;
    while (attempts-- > 0) {
        rc = ssh_connect(ssh_session_);
        if (rc == SSH_OK) break;

        std::this_thread::sleep_for(std::chrono::seconds(2));
    }
}
```

---

## Adding New Deployment Modes

### Example: Adding "Quick Deploy" Mode

**1. Add to deployment_dialog.h:**

```cpp
class DeploymentDialog {
public:
    enum DeploymentMode {
        MODE_COMPILED_BINARY,
        MODE_BLOCK_RUNTIME,
        MODE_QUICK_DEPLOY       // ← Add this
    };

private:
    DeploymentMode deployment_mode_;
};
```

**2. Add UI option in deployment_dialog.cpp:**

```cpp
void DeploymentDialog::RenderDeploymentMode() {
    ImGui::Text("Deployment Mode:");

    if (ImGui::RadioButton("Compiled Binary (Production)", deployment_mode_ == MODE_COMPILED_BINARY)) {
        deployment_mode_ = MODE_COMPILED_BINARY;
    }
    if (ImGui::RadioButton("Block Runtime (Development)", deployment_mode_ == MODE_BLOCK_RUNTIME)) {
        deployment_mode_ = MODE_BLOCK_RUNTIME;
    }
    if (ImGui::RadioButton("Quick Deploy (No Compilation)", deployment_mode_ == MODE_QUICK_DEPLOY)) {
        deployment_mode_ = MODE_QUICK_DEPLOY;
    }
}
```

**3. Implement in block_runtime_deployer.cpp:**

```cpp
bool BlockRuntimeDeployer::QuickDeploy() {
    ReportProgress("Quick Deploy - Manifest only...", 0);

    // 1. Generate manifest
    if (!GenerateManifest()) {
        return false;
    }

    // 2. Upload manifest
    ReportProgress("Uploading manifest...", 50);
    if (!TransferFile(manifest_path_, remote_manifest_path_)) {
        return false;
    }

    // 3. Restart runtime (use existing binaries)
    ReportProgress("Restarting runtime...", 90);
    std::string restart_cmd = "pkill -9 cira-block-runtime && "
                              "cd " + remote_workspace_ + " && "
                              "./cira-block-runtime " + remote_manifest_path_ + " &";
    ExecuteSSHCommand(restart_cmd);

    ReportProgress("Quick Deploy complete!", 100);
    return true;
}
```

---

## Adding Deployment Hooks

### Pre-Deployment Hook

**File:** `pipeline_builder/src/deployment/block_runtime_deployer.cpp`

```cpp
bool BlockRuntimeDeployer::Deploy() {
    // Call pre-deployment hook
    if (!PreDeploymentHook()) {
        ReportError("Pre-deployment hook failed");
        return false;
    }

    // ... existing deployment code ...

    // Call post-deployment hook
    if (!PostDeploymentHook()) {
        ReportWarning("Post-deployment hook failed (non-critical)");
    }

    return true;
}

bool BlockRuntimeDeployer::PreDeploymentHook() {
    // Example: Validate disk space
    ReportProgress("Running pre-deployment checks...", 0);

    std::string space_cmd = "df -h " + remote_workspace_ + " | tail -1 | awk '{print $4}'";
    std::string available = ExecuteSSHCommand(space_cmd);

    // Parse available space
    // ... (implementation)

    if (available_mb < 100) {
        ReportError("Insufficient disk space: " + available);
        return false;
    }

    return true;
}

bool BlockRuntimeDeployer::PostDeploymentHook() {
    // Example: Send notification
    ReportProgress("Sending deployment notification...", 0);

    std::string notify_cmd = "curl -X POST http://notification-server/deploy "
                             "-d 'status=success&device=" + target_host_ + "'";
    ExecuteSSHCommand(notify_cmd);

    return true;
}
```

---

## Troubleshooting

### Problem: "Failed to connect to device"

**Causes:**
- SSH credentials incorrect
- Device not on network
- Firewall blocking SSH (port 22)

**Solution:**
1. Click "Test Connection"
2. Check SSH credentials in "Edit" target
3. Ping device: `ping device-ip`
4. Try manual SSH: `ssh user@device-ip`

---

### Problem: "Compilation failed" or OOM error

**Causes:**
- Insufficient memory on Jetson (4GB RAM)
- Too many parallel jobs

**Solution:**
- Use `-j1` flag (compile one file at a time)
- Close other applications on Jetson
- Add swap space

**Code fix:**
```cpp
// In SetupDevice() or DeployRuntimeOnly()
std::string make_cmd = "cd " + build_dir + " && make -j1 2>&1";
//                                                    ^^^ Force single thread
```

---

### Problem: "Block not found" error at runtime

**Causes:**
- Block .so not installed
- Block version mismatch
- Missing dependencies

**Solution:**
1. Check `ls /home/user/cira_projects/cira-runtime/blocks/`
2. Verify block version matches manifest
3. Check runtime logs: `tail -f runtime.log`
4. Run "Setup Device" to rebuild all blocks

---

### Problem: Pipeline deploys but doesn't run

**Causes:**
- Runtime crash on startup
- Missing model files
- Port already in use

**Solution:**
1. Check deployment log for errors
2. SSH to device: `ssh user@device-ip`
3. Check runtime status: `ps aux | grep cira-block-runtime`
4. View runtime output: `tail -f /home/user/cira_projects/cira-runtime/runtime.log`
5. Try manual start: `./cira-block-runtime manifest.json --web-port 8083`

---

## Performance Optimization

### Speed Up Compilation

**Use ccache:**
```cpp
std::string cmake_cmd = "cd " + build_dir + " && "
                        "CMAKE_CXX_COMPILER_LAUNCHER=ccache "
                        "cmake .. 2>&1";
```

**Install on Jetson:**
```bash
sudo apt install ccache
```

### Speed Up File Transfer

**Use compression:**
```cpp
bool TransferDirectory(const std::string& local_path, const std::string& remote_path) {
    // Create compressed archive
    std::string tar_cmd = "tar czf temp.tar.gz " + local_path;
    system(tar_cmd.c_str());

    // Transfer compressed file
    TransferFile("temp.tar.gz", remote_path + "/temp.tar.gz");

    // Extract on remote
    std::string extract_cmd = "cd " + remote_path + " && tar xzf temp.tar.gz";
    ExecuteSSHCommand(extract_cmd);
}
```

---

## Checklist for Custom Deployment

- [ ] Understand current deployment flow
- [ ] Identify customization point
- [ ] Modify appropriate method in block_runtime_deployer.cpp
- [ ] Test with "Update Runtime"
- [ ] Test with "Setup Device"
- [ ] Handle errors gracefully
- [ ] Add progress reporting
- [ ] Update documentation

---

## Reference: Command Examples

### SSH Commands

```bash
# Check disk space
df -h /home/user/cira_projects

# List processes
ps aux | grep cira-block-runtime

# Kill runtime
pkill -9 cira-block-runtime

# Check file permissions
ls -la /home/user/cira_projects/cira-runtime/blocks/

# View logs
tail -f /home/user/cira_projects/cira-runtime/runtime.log

# Test compilation
cd /home/user/cira_projects/cira-runtime/build && make -j1
```

### SFTP Commands (Programmatic)

```cpp
// Upload file
sftp_write_file(sftp, local_path, remote_path);

// Download file
sftp_read_file(sftp, remote_path, local_path);

// Create directory
sftp_mkdir(sftp, remote_dir, 0755);

// List directory
sftp_dir_handle = sftp_opendir(sftp, remote_path);
```

---

**See also:**
- [Block Development Guide](01-adding-new-blocks.md)
- [Block Modification Guide](02-modifying-existing-blocks.md)
- [Web Dashboard Widgets](04-web-dashboard-widgets.md)
