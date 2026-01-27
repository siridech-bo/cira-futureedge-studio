#pragma once

#include <string>
#include <vector>
#include <map>
#include <memory>

namespace CiraBlockRuntime {

// Block reference from manifest
struct BlockReference {
    std::string id;          // e.g., "adxl345-sensor"
    std::string version;     // e.g., "1.0.0"
    std::string type;        // e.g., "i2c-device", "native", "onnx-runtime"
    std::vector<std::string> dependencies;
};

// Node instance from manifest
struct NodeInstance {
    int id;
    std::string type;  // e.g., "input.accelerometer.adxl345"
    std::map<std::string, std::string> config;
    struct Position {
        float x;
        float y;
    } position;
};

// Connection from manifest
struct Connection {
    int from_node_id;
    std::string from_pin;
    int to_node_id;
    std::string to_pin;
};

// Complete manifest structure
struct BlockManifest {
    std::string format_version;
    std::string pipeline_name;
    std::string target_platform;
    std::vector<BlockReference> blocks;
    std::vector<NodeInstance> nodes;
    std::vector<Connection> connections;
};

// Parser class
class ManifestParser {
public:
    ManifestParser() = default;
    ~ManifestParser() = default;

    // Load and parse manifest from file
    bool LoadFromFile(const std::string& filepath);

    // Get parsed manifest
    const BlockManifest& GetManifest() const { return manifest_; }

    // Get error message if parsing failed
    const std::string& GetError() const { return error_; }

private:
    BlockManifest manifest_;
    std::string error_;
};

} // namespace CiraBlockRuntime
