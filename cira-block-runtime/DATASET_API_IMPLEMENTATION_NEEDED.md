# Dataset API Implementation - Remaining Work

## Status: Routes Added, Handlers Need Implementation

### ✅ Completed:
1. Dataset routes added to `SetupRoutes()` in web_server.cpp (lines 285-311)
2. Handler declarations added to web_server.hpp (lines 41-43)
3. Data recorder block fully implemented
4. Web widget fully implemented (recorder-widget.js)
5. CSS styles added
6. Widget added to palette

### ⚠️ Remaining: Implement 3 Handler Methods

Add these methods to the END of `src/web_server.cpp` (after line 706):

```cpp
void WebServer::HandleListDatasets(const httplib::Request& req, httplib::Response& res) {
    try {
        std::string datasets_dir = "/home/user/cira_datasets";

        nlohmann::json response;
        response["datasets"] = nlohmann::json::array();

        // Check if directory exists
        if (!fs::exists(datasets_dir)) {
            res.set_content(response.dump(), "application/json");
            return;
        }

        // Iterate through files in directory
        for (const auto& entry : fs::directory_iterator(datasets_dir)) {
            if (entry.is_regular_file()) {
                nlohmann::json dataset_info;

                std::string filename = entry.path().filename().string();
                dataset_info["filename"] = filename;

                // Get file size in KB
                std::uintmax_t size_bytes = fs::file_size(entry.path());
                dataset_info["size_kb"] = static_cast<int>(size_bytes / 1024);

                // Get modification time
                auto ftime = fs::last_write_time(entry.path());
                auto sctp = std::chrono::time_point_cast<std::chrono::system_clock::duration>(
                    ftime - fs::file_time_type::clock::now() + std::chrono::system_clock::now()
                );
                auto time_t_now = std::chrono::system_clock::to_time_t(sctp);

                std::tm tm_now;
                #ifdef _WIN32
                localtime_s(&tm_now, &time_t_now);
                #else
                localtime_r(&time_t_now, &tm_now);
                #endif

                char timestamp_str[64];
                std::strftime(timestamp_str, sizeof(timestamp_str), "%Y-%m-%d %H:%M:%S", &tm_now);
                dataset_info["timestamp"] = std::string(timestamp_str);

                response["datasets"].push_back(dataset_info);
            }
        }

        res.set_content(response.dump(), "application/json");

    } catch (const std::exception& e) {
        std::cerr << "[WebServer] HandleListDatasets error: " << e.what() << std::endl;
        res.status = 500;
        res.set_content("{\"error\":\"Internal server error\"}", "application/json");
    }
}

void WebServer::HandleDownloadDataset(const httplib::Request& req, httplib::Response& res) {
    try {
        // Extract filename from URL path
        std::string filename = req.matches[1];

        // Sanitize filename - prevent directory traversal
        if (filename.find("..") != std::string::npos ||
            filename.find("/") != std::string::npos ||
            filename.find("\\") != std::string::npos) {
            res.status = 400;
            res.set_content("{\"error\":\"Invalid filename\"}", "application/json");
            return;
        }

        std::string datasets_dir = "/home/user/cira_datasets";
        std::string filepath = datasets_dir + "/" + filename;

        // Check if file exists
        if (!fs::exists(filepath)) {
            res.status = 404;
            res.set_content("{\"error\":\"File not found\"}", "application/json");
            return;
        }

        // Read file content
        std::ifstream file(filepath, std::ios::binary);
        if (!file.is_open()) {
            res.status = 500;
            res.set_content("{\"error\":\"Failed to open file\"}", "application/json");
            return;
        }

        std::stringstream buffer;
        buffer << file.rdbuf();
        std::string content = buffer.str();

        // Determine content type based on file extension
        std::string content_type = "application/octet-stream";
        if (filename.find(".json") != std::string::npos) {
            content_type = "application/json";
        } else if (filename.find(".csv") != std::string::npos) {
            content_type = "text/csv";
        } else if (filename.find(".cbor") != std::string::npos) {
            content_type = "application/cbor";
        }

        // Set download headers
        res.set_header("Content-Disposition", "attachment; filename=\"" + filename + "\"");
        res.set_content(content, content_type.c_str());

        AddLog("INFO", "Dataset downloaded: " + filename);

    } catch (const std::exception& e) {
        std::cerr << "[WebServer] HandleDownloadDataset error: " << e.what() << std::endl;
        res.status = 500;
        res.set_content("{\"error\":\"Internal server error\"}", "application/json");
    }
}

void WebServer::HandleDeleteDataset(const httplib::Request& req, httplib::Response& res) {
    try {
        // Extract filename from URL path
        std::string filename = req.matches[1];

        // Sanitize filename - prevent directory traversal
        if (filename.find("..") != std::string::npos ||
            filename.find("/") != std::string::npos ||
            filename.find("\\") != std::string::npos) {
            res.status = 400;
            res.set_content("{\"error\":\"Invalid filename\"}", "application/json");
            return;
        }

        std::string datasets_dir = "/home/user/cira_datasets";
        std::string filepath = datasets_dir + "/" + filename;

        // Check if file exists
        if (!fs::exists(filepath)) {
            res.status = 404;
            res.set_content("{\"error\":\"File not found\"}", "application/json");
            return;
        }

        // Delete the file
        if (fs::remove(filepath)) {
            nlohmann::json response;
            response["success"] = true;
            response["message"] = "Dataset deleted";
            res.set_content(response.dump(), "application/json");

            AddLog("INFO", "Dataset deleted: " + filename);
        } else {
            res.status = 500;
            res.set_content("{\"error\":\"Failed to delete file\"}", "application/json");
        }

    } catch (const std::exception& e) {
        std::cerr << "[WebServer] HandleDeleteDataset error: " << e.what() << std::endl;
        res.status = 500;
        res.set_content("{\"error\":\"Internal server error\"}", "application/json");
    }
}
```

## WebSocket Command Handlers

Also need to add handling for `start_recording` and `stop_recording` commands in `HandleWebSocketMessage()`.

Find the section around line 595 where it handles `button_press` and add:

```cpp
        // Handle start_recording command
        } else if (command == "start_recording") {
            if (!message.contains("node_id")) {
                std::cerr << "[WebServer] start_recording missing node_id" << std::endl;
                return;
            }

            int node_id = message["node_id"];

            if (!executor_) {
                std::cerr << "[WebServer] Executor not available" << std::endl;
                return;
            }

            // Find the DataRecorderBlock
            auto block = executor_->GetBlock(node_id);
            if (block) {
                block->SetInput("record_trigger", true);
                AddLog("INFO", "Recording started on node " + std::to_string(node_id));
            }

        // Handle stop_recording command
        } else if (command == "stop_recording") {
            if (!message.contains("node_id")) {
                std::cerr << "[WebServer] stop_recording missing node_id" << std::endl;
                return;
            }

            int node_id = message["node_id"];

            if (!executor_) {
                std::cerr << "[WebServer] Executor not available" << std::endl;
                return;
            }

            // Find the DataRecorderBlock
            auto block = executor_->GetBlock(node_id);
            if (block) {
                block->SetInput("record_trigger", false);
                AddLog("INFO", "Recording stopped on node " + std::to_string(node_id));
            }
        }
```

## Testing Steps

1. **Build cira-block-runtime:**
   ```bash
   cd cira-block-runtime/build
   cmake ..
   make
   ```

2. **Create test pipeline with recorder block**

3. **Deploy to Jetson**

4. **Test Web UI:**
   - Add recorder widget to dashboard
   - Click Start Recording
   - Wait for samples
   - Click Stop
   - Verify dataset appears in list
   - Click Download
   - Verify file downloads

5. **Test retraining loop:**
   - Use downloaded dataset to retrain model
   - Deploy new model
   - Test predictions

## File Locations

- Block: `blocks/outputs/data_recorder/data_recorder_block.cpp`
- Widget: `web/js/recorder-widget.js`
- CSS: `web/css/dashboard.css` (lines 1159-1414)
- Routes: `src/web_server.cpp` (lines 285-311)
- Handlers: **NEED TO ADD** to end of `src/web_server.cpp`
- WebSocket commands: **NEED TO ADD** to `HandleWebSocketMessage()`

## Estimated Time to Complete

- Add 3 handler methods: 5 minutes
- Add WebSocket commands: 5 minutes
- Build and test: 15 minutes
- **Total: 25 minutes**
