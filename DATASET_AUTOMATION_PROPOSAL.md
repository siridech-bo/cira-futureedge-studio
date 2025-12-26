# Dataset Automation Proposal

## Problem
Currently, users must manually upload dataset files to Jetson device before testing synthetic signal pipelines. This is complex and error-prone.

## Solutions (3 Options)

### Option 1: Embedded Datasets in Manifest (RECOMMENDED)
**Idea**: Embed small datasets directly in the JSON manifest as base64 or inline data.

**Advantages:**
- ✅ Single file deployment
- ✅ No manual upload needed
- ✅ Works with existing deployment system
- ✅ Version control friendly

**Implementation:**
```json
{
  "blocks": [
    {
      "id": "synth_gen",
      "type": "synthetic-signal-generator",
      "config": {
        "dataset_inline": "{\"classes\": {\"walking\": [[0.1, 0.2, 9.8]]}}",
        "sample_rate": "100"
      }
    }
  ]
}
```

**Changes needed:**
1. Modify `synthetic_signal_block.cpp` to check for `dataset_inline` config
2. Parse inline JSON instead of loading file
3. Pipeline Builder UI: Add "Embed Dataset" button

### Option 2: Automatic Upload During Deployment
**Idea**: Deployment system detects dataset paths and uploads them automatically.

**Advantages:**
- ✅ Supports large datasets
- ✅ Separate files for easier editing
- ✅ One-click deployment

**Implementation:**
```cpp
// In BlockRuntimeDeployer::Deploy()
bool DeployDatasets() {
    // Parse manifest for dataset_path configs
    for (auto& block : manifest["blocks"]) {
        if (block.contains("config") &&
            block["config"].contains("dataset_path")) {

            std::string local_path = block["config"]["dataset_path"];
            std::string remote_path = "/home/jetson/datasets/" +
                                     fs::path(local_path).filename();

            // Upload file via SFTP
            TransferFile(local_path, remote_path);

            // Update manifest with remote path
            block["config"]["dataset_path"] = remote_path;
        }
    }
}
```

**Changes needed:**
1. Add dataset detection in `BlockRuntimeDeployer`
2. Upload files before deploying runtime
3. Update manifest paths automatically

### Option 3: Dataset Library Manager
**Idea**: Central dataset library with upload/browse UI in Pipeline Builder.

**Advantages:**
- ✅ Professional UX
- ✅ Dataset reuse across projects
- ✅ Version management

**Implementation:**
- Add "Dataset Manager" dialog in Pipeline Builder
- List local and remote datasets
- Sync button to upload/download
- Select from library when configuring block

**Changes needed:**
1. New UI panel for dataset management
2. Dataset metadata tracking
3. SSH/SFTP integration in Pipeline Builder

## Recommended Implementation: Hybrid Approach

Combine Option 1 and Option 2:

### Phase 1: Inline Datasets (Quick Win)
For small test datasets, support inline JSON:

```cpp
// In synthetic_signal_block.cpp Initialize()
if (config.count("dataset_inline")) {
    // Parse inline JSON directly
    std::string inline_data = config.at("dataset_inline");
    nlohmann::json j = nlohmann::json::parse(inline_data);
    // ... parse classes
} else if (config.count("dataset_path")) {
    // Load from file (existing code)
    std::ifstream file(dataset_path_);
    // ...
}
```

### Phase 2: Automatic Upload (Better UX)
For production datasets, auto-upload during deployment:

```cpp
// In BlockRuntimeDeployer.cpp
bool BlockRuntimeDeployer::DeployWithDatasets() {
    // 1. Parse manifest for dataset references
    auto datasets = ExtractDatasetPaths(manifest_);

    // 2. Upload each dataset
    for (const auto& [block_id, local_path] : datasets) {
        ReportProgress("Uploading dataset: " + local_path, progress);

        std::string remote_path = "/home/jetson/datasets/" +
                                 fs::path(local_path).filename().string();

        if (!TransferFile(local_path, remote_path)) {
            return false;
        }

        // 3. Update manifest reference
        UpdateManifestPath(block_id, "dataset_path", remote_path);
    }

    // 4. Deploy runtime with updated manifest
    return DeployManifest();
}
```

## Quick Implementation (Option 1 Only)

Minimal changes to support inline datasets:

### File: `synthetic_signal_block.cpp`

```cpp
bool LoadDataset() {
    // Check for inline dataset first
    if (config.count("dataset_inline")) {
        return LoadInlineDataset();
    }

    // Fall back to file loading
    std::string ext = GetFileExtension(dataset_path_);
    // ... existing code
}

bool LoadInlineDataset() {
    try {
        std::string inline_data = config.at("dataset_inline");
        nlohmann::json j = nlohmann::json::parse(inline_data);

        // Same parsing logic as LoadJSON()
        if (j.contains("sample_rate")) {
            sample_rate_ = j["sample_rate"].get<float>();
        }
        // ... rest of JSON parsing

        return !classes_.empty();
    } catch (const std::exception& e) {
        std::cerr << "ERROR: Inline dataset parsing failed: " << e.what() << std::endl;
        return false;
    }
}
```

### File: Pipeline Builder UI

Add checkbox in properties panel:
```cpp
// In PropertiesPanel::RenderConfigFields()
if (node_type == "synthetic-signal-generator") {
    ImGui::Checkbox("Embed Dataset", &embed_dataset);

    if (embed_dataset) {
        // Show file picker
        if (ImGui::Button("Select Dataset File")) {
            // Open file dialog
            std::string path = FileDialog::Open("JSON files", "*.json");
            if (!path.empty()) {
                // Read file and embed
                std::ifstream f(path);
                std::string content((std::istreambuf_iterator<char>(f)),
                                   std::istreambuf_iterator<char>());

                // Minify JSON (remove whitespace)
                auto j = nlohmann::json::parse(content);
                config["dataset_inline"] = j.dump();
                config.erase("dataset_path");
            }
        }
    } else {
        // Show path input (existing behavior)
        ImGui::InputText("dataset_path", ...);
    }
}
```

## Size Considerations

**Inline Dataset Limits:**
- Small test datasets (< 10KB): Perfect for inline
- Medium datasets (10-100KB): Acceptable if minified
- Large datasets (> 100KB): Should use file upload

**Example sizes:**
- 30 samples × 3 channels × 3 classes = ~2KB JSON (✅ inline)
- 1000 samples × 3 channels × 5 classes = ~150KB (⚠️ upload)

## Migration Path

1. **Week 1**: Implement inline dataset support (2 hours)
   - Modify `synthetic_signal_block.cpp`
   - Test with small datasets

2. **Week 2**: Add UI for embedding (4 hours)
   - File picker in properties panel
   - JSON minification
   - Preview embedded size

3. **Week 3**: Add auto-upload (8 hours)
   - Detect dataset paths in manifest
   - Upload via existing SFTP
   - Update paths automatically

4. **Future**: Dataset library manager (20 hours)
   - Full UI for dataset management
   - Remote browsing
   - Version control

## Recommendation

**For now**: Implement **Option 1 (Inline Datasets)** with the quick implementation above.

**Why:**
- Solves your immediate problem
- Minimal code changes (~50 lines)
- No deployment system changes
- Works with existing test datasets
- Can add auto-upload later if needed

**Next steps:**
1. I can implement inline dataset support right now
2. Test with your accelerometer dataset
3. Add UI checkbox later if you want

Would you like me to implement Option 1 now?
