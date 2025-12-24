# Phase 4.3: SSH Deployment for Block Runtime

## Overview
Implement complete SSH deployment workflow for the block runtime system, enabling one-click deployment from the Pipeline Builder to target hardware (Jetson Nano, Arduino UNO Q).

## Current State
- ✅ Block runtime binary builds successfully
- ✅ Block libraries (.dll/.so) compile successfully
- ✅ Block manifest generator creates JSON manifests
- ✅ SSH deployment infrastructure exists for compiled binaries
- ⚠️ Block runtime deployment thread is skeleton only

## Architecture

### Deployment Flow
```
Pipeline Builder (Windows/Linux)
    ↓
[Generate Block Manifest] → block_manifest.json
    ↓
[Package Artifacts]
    - cira-block-runtime binary
    - Block libraries (*.so files)
    - block_manifest.json
    ↓
[SSH Transfer via libssh]
    ↓
Target Hardware (Jetson Nano / Arduino UNO Q)
    ↓
[Setup & Execute]
    - Create deployment directory
    - Set permissions (+x for binary)
    - Run runtime with manifest
```

### File Structure on Target
```
/home/username/cira-runtime/
├── bin/
│   └── cira-block-runtime          # Runtime binary
├── blocks/
│   ├── adxl345-v1.0.0.so          # Block libraries
│   ├── sliding_window-v1.0.0.so
│   ├── channel_merge-v1.0.0.so
│   └── gpio_output-v1.0.0.so
├── manifests/
│   └── pipeline_name.json          # Block manifest
└── logs/
    └── runtime.log                 # Execution logs
```

## Implementation Tasks

### 1. Update DeploymentDialog for Block Runtime Mode

**File**: `pipeline_builder/src/ui/deployment_dialog.cpp`

**Changes**:
- Complete `DeployBlockRuntimeThreadFunction()`
- Add progress messages for block runtime deployment:
  - "Generating block manifest..."
  - "Packaging runtime binary..."
  - "Transferring block libraries..."
  - "Setting up remote environment..."
  - "Starting block runtime..."

**UI Updates**:
- Show different progress messages based on deployment mode
- Display list of blocks being deployed
- Show transfer progress for each block library

### 2. Create BlockRuntimeDeployer Class

**New File**: `pipeline_builder/include/deployment/block_runtime_deployer.hpp`

```cpp
class BlockRuntimeDeployer {
public:
    struct DeploymentConfig {
        std::string host;
        int port;
        std::string username;
        std::string password;
        std::string remote_base_path;  // e.g., /home/user/cira-runtime
        std::string manifest_path;     // Local manifest file
        std::string runtime_binary_path;
        std::vector<std::string> block_library_paths;
    };

    struct DeploymentProgress {
        std::string current_step;
        int total_steps;
        int current_step_num;
        int bytes_transferred;
        int total_bytes;
    };

    using ProgressCallback = std::function<void(const DeploymentProgress&)>;

    bool Deploy(const DeploymentConfig& config, ProgressCallback callback);
    bool Start(const std::string& manifest_name);
    bool Stop();
    std::string GetRemoteLog();

private:
    bool SetupRemoteDirectories();
    bool TransferRuntimeBinary();
    bool TransferBlockLibraries();
    bool TransferManifest();
    bool StartRemoteRuntime(const std::string& manifest_name);

    ssh_session session_;
    DeploymentConfig config_;
    ProgressCallback progress_callback_;
};
```

### 3. Implement Block Library Discovery

**New File**: `pipeline_builder/include/deployment/block_library_locator.hpp`

```cpp
class BlockLibraryLocator {
public:
    struct BlockLibrary {
        std::string block_id;
        std::string version;
        std::string local_path;
        std::string filename;  // e.g., adxl345-v1.0.0.so
    };

    // Find all block libraries needed by manifest
    std::vector<BlockLibrary> LocateLibraries(
        const BlockManifest& manifest,
        const std::string& library_search_path
    );

    // Find specific block library
    std::optional<BlockLibrary> FindLibrary(
        const std::string& block_id,
        const std::string& version,
        const std::string& search_path
    );

private:
    std::string GetLibraryExtension() const;  // .so for Linux, .dll for Windows
};
```

### 4. Extend SSH Utilities

**File**: `pipeline_builder/src/deployment/ssh_utils.cpp`

**New Functions**:
```cpp
// Transfer entire directory recursively
bool SSHTransferDirectory(
    ssh_session session,
    const std::string& local_dir,
    const std::string& remote_dir,
    std::function<void(const std::string&, int, int)> progress_callback
);

// Execute command and stream output
bool SSHExecuteWithOutput(
    ssh_session session,
    const std::string& command,
    std::function<void(const std::string&)> output_callback
);

// Check if remote file exists
bool SSHFileExists(
    ssh_session session,
    const std::string& remote_path
);

// Get file size
int64_t SSHGetFileSize(
    ssh_session session,
    const std::string& remote_path
);
```

### 5. Update Manifest Generator

**File**: `pipeline_builder/src/generation/block_manifest_generator.cpp`

**Additions**:
- Add `runtime_config` section to manifest:
```json
{
  "runtime_config": {
    "block_library_path": "./blocks",
    "log_level": "info",
    "enable_stats": true,
    "execution_mode": "continuous"
  }
}
```

### 6. Create Deployment Package Builder

**New File**: `pipeline_builder/include/deployment/deployment_package.hpp`

```cpp
class DeploymentPackage {
public:
    struct PackageInfo {
        std::string manifest_path;
        std::string runtime_binary_path;
        std::vector<std::string> block_libraries;
        std::vector<std::string> dependencies;  // e.g., onnxruntime.so
        int64_t total_size_bytes;
    };

    // Create deployment package from manifest
    static PackageInfo CreateFromManifest(
        const BlockManifest& manifest,
        const std::string& runtime_binary_path,
        const std::string& block_search_path
    );

    // Validate package (all files exist, compatible architectures)
    static bool Validate(const PackageInfo& package, std::vector<std::string>& errors);
};
```

## Platform-Specific Considerations

### Jetson Nano (ARM64 Linux)
- Target architecture: aarch64
- Runtime binary must be cross-compiled or built on ARM64
- Block libraries must be ARM64 .so files
- Remote path: `/home/jetson/cira-runtime/`
- Requires: ONNX Runtime ARM64 libraries

### Arduino UNO Q (Debian Linux MPU)
- Target architecture: ARM (specific to Qualcomm MPU)
- Only MPU-compatible blocks deployed
- MCU blocks handled separately (future Phase 4.4)
- Remote path: `/home/debian/cira-runtime/`
- IPC setup for MPU-MCU communication

## Testing Strategy

### Test 1: Local Deployment (Loopback)
```bash
# Deploy to localhost for testing
ssh user@localhost "mkdir -p ~/cira-runtime-test"
# Verify all files transferred correctly
# Run runtime and check output
```

### Test 2: Jetson Nano Deployment
```bash
# Deploy full ADXL345 pipeline
# Expected files:
# - cira-block-runtime (ARM64)
# - adxl345-v1.0.0.so
# - sliding_window-v1.0.0.so
# - channel_merge-v1.0.0.so
# - gpio_output-v1.0.0.so
# - test_manifest.json
```

### Test 3: Missing Block Handling
```bash
# Deploy manifest referencing non-existent block
# Expected: Deployment fails with clear error message
# "Block 'foo-v1.0.0' not found in library search path"
```

### Test 4: Version Compatibility
```bash
# Deploy manifest requiring v2.0.0 when only v1.0.0 available
# Expected: Warning or error about version mismatch
```

## Progress Messages

User will see these in deployment dialog:

```
[Block Runtime Deployment]

[1/7] Generating block manifest...
      ✓ Found 4 blocks in pipeline
      ✓ Manifest saved: output/ts6_jetson_nano/block_manifest.json

[2/7] Locating block libraries...
      ✓ adxl345-v1.0.0.so (245 KB)
      ✓ sliding_window-v1.0.0.so (128 KB)
      ✓ channel_merge-v1.0.0.so (98 KB)
      ✓ gpio_output-v1.0.0.so (112 KB)

[3/7] Connecting to jetson-nano (192.168.1.100:22)...
      ✓ Connected

[4/7] Setting up remote environment...
      ✓ Created /home/jetson/cira-runtime/bin
      ✓ Created /home/jetson/cira-runtime/blocks
      ✓ Created /home/jetson/cira-runtime/manifests

[5/7] Transferring runtime binary...
      ✓ cira-block-runtime (1.2 MB) [==========] 100%

[6/7] Transferring block libraries...
      ✓ adxl345-v1.0.0.so [==========] 100%
      ✓ sliding_window-v1.0.0.so [==========] 100%
      ✓ channel_merge-v1.0.0.so [==========] 100%
      ✓ gpio_output-v1.0.0.so [==========] 100%

[7/7] Starting runtime...
      ✓ Runtime started successfully
      ✓ PID: 12345

Deployment complete! Runtime is executing on target.
```

## Error Handling

### Connection Errors
```
✗ Failed to connect to 192.168.1.100:22
  Error: Connection timeout

  Suggestions:
  - Check target is powered on
  - Verify network connection
  - Confirm SSH is enabled on target
```

### Missing Block Libraries
```
✗ Deployment failed: Missing block libraries

  Missing blocks:
  - timesnet_onnx-v1.0.0.so

  Search paths:
  - D:\CiRA FES\cira-block-runtime\build\blocks\

  Suggestion:
  - Build the missing blocks first
  - Check CMakeLists.txt for block targets
```

### Architecture Mismatch
```
✗ Deployment failed: Architecture mismatch

  Local binary: x86_64 Windows
  Target platform: aarch64 Linux (Jetson Nano)

  Suggestion:
  - Cross-compile runtime for ARM64
  - Build blocks on target hardware
  - Use Docker for cross-compilation
```

## Success Criteria

- ✅ One-click deployment from Pipeline Builder
- ✅ All required blocks transferred
- ✅ Runtime starts automatically on target
- ✅ Clear progress messages during deployment
- ✅ Helpful error messages on failure
- ✅ Support for both Jetson Nano and Arduino UNO Q
- ✅ Graceful handling of missing blocks
- ✅ Verify remote runtime execution

## Future Enhancements (Post Phase 4.3)

- **Auto-build**: Trigger cross-compilation before deployment
- **Version management**: Automatically update blocks if newer versions available
- **Remote monitoring**: Live stats from remote runtime in UI
- **Log streaming**: Real-time log viewing in deployment dialog
- **Multi-target**: Deploy to multiple devices simultaneously
- **Rollback**: Revert to previous deployment if new one fails
- **Health checks**: Verify runtime is executing correctly after deployment

## Implementation Order

1. ✅ BlockLibraryLocator (find .so/.dll files)
2. ✅ BlockRuntimeDeployer class skeleton
3. ✅ SSH utility extensions
4. ✅ DeployBlockRuntimeThreadFunction implementation
5. ✅ Progress UI updates
6. ✅ Testing with loopback (localhost)
7. ⏳ Testing with Jetson Nano (requires hardware)

---

**Estimated Time**: 4-6 hours
**Complexity**: Medium-High (SSH operations, file transfer, remote execution)
**Dependencies**: libssh, working SSH access to target hardware
