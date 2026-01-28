#include "manifest_parser.hpp"
#include "../third_party/json.hpp"
#include <fstream>
#include <iostream>

using json = nlohmann::json;

namespace CiraBlockRuntime {

bool ManifestParser::LoadFromFile(const std::string& filepath) {
    try {
        // Read file
        std::ifstream file(filepath);
        if (!file.is_open()) {
            error_ = "Failed to open manifest file: " + filepath;
            return false;
        }

        // Parse JSON
        json j;
        file >> j;

        // Parse format version
        if (j.contains("format_version")) {
            manifest_.format_version = j["format_version"].get<std::string>();
        }

        // Parse pipeline name
        if (j.contains("pipeline_name")) {
            manifest_.pipeline_name = j["pipeline_name"].get<std::string>();
        }

        // Parse target platform
        if (j.contains("target_platform")) {
            manifest_.target_platform = j["target_platform"].get<std::string>();
        }

        // Parse blocks
        if (j.contains("blocks") && j["blocks"].is_array()) {
            for (const auto& block_json : j["blocks"]) {
                BlockReference block;
                block.id = block_json["id"].get<std::string>();
                block.version = block_json["version"].get<std::string>();
                block.type = block_json["type"].get<std::string>();

                if (block_json.contains("dependencies") && block_json["dependencies"].is_array()) {
                    for (const auto& dep : block_json["dependencies"]) {
                        block.dependencies.push_back(dep.get<std::string>());
                    }
                }

                manifest_.blocks.push_back(block);
            }
        }

        // Parse nodes
        if (j.contains("pipeline") && j["pipeline"].contains("nodes")) {
            for (const auto& node_json : j["pipeline"]["nodes"]) {
                NodeInstance node;
                node.id = node_json["id"].get<int>();
                node.type = node_json["type"].get<std::string>();

                // Parse position
                if (node_json.contains("position")) {
                    node.position.x = node_json["position"]["x"].get<float>();
                    node.position.y = node_json["position"]["y"].get<float>();
                }

                // Parse config
                if (node_json.contains("config")) {
                    for (auto& [key, value] : node_json["config"].items()) {
                        if (value.is_string()) {
                            node.config[key] = value.get<std::string>();
                        } else {
                            node.config[key] = value.dump();
                        }
                    }
                }

                manifest_.nodes.push_back(node);
            }
        }

        // Parse connections
        if (j.contains("pipeline") && j["pipeline"].contains("connections")) {
            for (const auto& conn_json : j["pipeline"]["connections"]) {
                Connection conn;
                conn.from_node_id = conn_json["from_node_id"].get<int>();
                conn.from_pin = conn_json["from_pin"].get<std::string>();
                conn.to_node_id = conn_json["to_node_id"].get<int>();
                conn.to_pin = conn_json["to_pin"].get<std::string>();

                manifest_.connections.push_back(conn);
            }
        }

        std::cout << "Manifest loaded successfully:" << std::endl;
        std::cout << "  Pipeline: " << manifest_.pipeline_name << std::endl;
        std::cout << "  Platform: " << manifest_.target_platform << std::endl;
        std::cout << "  Blocks: " << manifest_.blocks.size() << std::endl;
        std::cout << "  Nodes: " << manifest_.nodes.size() << std::endl;
        std::cout << "  Connections: " << manifest_.connections.size() << std::endl;

        return true;

    } catch (const json::exception& e) {
        error_ = std::string("JSON parse error: ") + e.what();
        return false;
    } catch (const std::exception& e) {
        error_ = std::string("Error loading manifest: ") + e.what();
        return false;
    }
}

} // namespace CiraBlockRuntime
