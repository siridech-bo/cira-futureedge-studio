#include "block_executor.hpp"
#include <iostream>
#include <algorithm>
#include <set>
#include <chrono>

namespace CiraBlockRuntime {

BlockExecutor::BlockExecutor()
    : stats_{0, 0, 0.0}
{
}

BlockExecutor::~BlockExecutor() {
    Shutdown();
}

bool BlockExecutor::BuildFromManifest(const BlockManifest& manifest, BlockLoader& loader) {
    std::cout << "\n=== Building Execution Graph ===" << std::endl;

    // Map node types to block IDs
    std::map<std::string, std::string> node_type_to_block_id;
    for (const auto& block : manifest.blocks) {
        // Map block ID to itself for lookup
        // e.g., "adxl345-sensor" -> "adxl345-sensor"
        node_type_to_block_id[block.id] = block.id;
    }

    // Helper: Convert node type to block ID
    // e.g., "input.accelerometer.adxl345" -> "adxl345-sensor"
    auto get_block_id = [&](const std::string& node_type) -> std::string {
        // Try direct mapping first
        for (const auto& block : manifest.blocks) {
            // Check if node type contains block ID
            if (node_type.find(block.id) != std::string::npos) {
                return block.id;
            }
        }

        // Handle specific mappings
        if (node_type.find("adxl345") != std::string::npos) return "adxl345-sensor";
        if (node_type.find("bme280") != std::string::npos) return "bme280-sensor";
        if (node_type.find("sliding_window") != std::string::npos) return "sliding-window";
        if (node_type.find("lowpass") != std::string::npos ||
            node_type.find("low_pass") != std::string::npos) return "low-pass-filter";
        if (node_type.find("channel_merge") != std::string::npos) return "channel-merge";
        if (node_type.find("timesnet") != std::string::npos) return "timesnet";
        if (node_type.find("gpio") != std::string::npos &&
            node_type.find("output") != std::string::npos) return "gpio-output";
        if (node_type.find("oled") != std::string::npos) return "oled-display";
        if (node_type.find("mqtt") != std::string::npos) return "mqtt-publisher";

        return "";
    };

    // Load blocks for each node
    for (const auto& node : manifest.nodes) {
        std::string block_id = get_block_id(node.type);
        if (block_id.empty()) {
            error_ = "Unknown node type: " + node.type;
            std::cerr << error_ << std::endl;
            continue;  // Skip unknown blocks for now
        }

        // Find block version from manifest
        std::string version = "1.0.0";  // Default
        for (const auto& block : manifest.blocks) {
            if (block.id == block_id) {
                version = block.version;
                break;
            }
        }

        // Load block
        IBlock* block = loader.LoadBlock(block_id, version);
        if (!block) {
            std::cerr << "Warning: Failed to load block: " << block_id
                     << " (needed by node " << node.id << ")" << std::endl;
            continue;  // Skip missing blocks
        }

        // Create execution node
        ExecutionNode exec_node;
        exec_node.node_id = node.id;
        exec_node.node_type = node.type;
        exec_node.block = block;
        exec_node.config = node.config;

        nodes_[node.id] = exec_node;

        std::cout << "  Node " << node.id << ": " << node.type
                 << " -> Block: " << block_id << " v" << version << std::endl;
    }

    // Store connections
    connections_ = manifest.connections;
    std::cout << "  Connections: " << connections_.size() << std::endl;

    // Build execution order
    if (!BuildExecutionOrder()) {
        return false;
    }

    std::cout << "  Execution order: ";
    for (int node_id : execution_order_) {
        std::cout << node_id << " ";
    }
    std::cout << std::endl;

    std::cout << "✓ Execution graph built successfully" << std::endl;
    return true;
}

bool BlockExecutor::Initialize() {
    std::cout << "\n=== Initializing Blocks ===" << std::endl;

    bool all_success = true;
    std::vector<int> failed_nodes;

    for (auto& [node_id, node] : nodes_) {
        if (!node.block) continue;

        std::cout << "  Initializing node " << node_id << "..." << std::endl;
        if (!node.block->Initialize(node.config)) {
            std::cerr << "  WARNING: Failed to initialize node " << node_id << std::endl;
            failed_nodes.push_back(node_id);
            all_success = false;
            // Continue initializing other blocks
        }
    }

    if (all_success) {
        std::cout << "✓ All blocks initialized successfully" << std::endl;
    } else {
        std::cout << "⚠ Blocks initialized with " << failed_nodes.size() << " failure(s)" << std::endl;
        std::cout << "  Failed nodes: ";
        for (size_t i = 0; i < failed_nodes.size(); i++) {
            std::cout << failed_nodes[i];
            if (i < failed_nodes.size() - 1) std::cout << ", ";
        }
        std::cout << std::endl;
        error_ = "Some blocks failed to initialize (hardware may not be connected)";
    }

    return all_success;
}

bool BlockExecutor::Execute() {
    auto start = std::chrono::high_resolution_clock::now();

    // Execute nodes in topological order
    for (int node_id : execution_order_) {
        auto it = nodes_.find(node_id);
        if (it == nodes_.end() || !it->second.block) {
            continue;
        }

        ExecutionNode& node = it->second;

        // Transfer input data from connected upstream nodes
        TransferData();

        // Execute block (continue even if it fails)
        if (!node.block->Execute()) {
            std::cerr << "  WARNING: Block execution failed for node " << node_id << std::endl;
            error_ = "Block execution failed for node " + std::to_string(node_id);
            stats_.total_errors++;
            // Don't return false - continue with other blocks
            continue;
        }

        // Read output values from block
        auto output_pins = node.block->GetOutputPins();
        for (const auto& pin : output_pins) {
            node.output_values[pin.name] = node.block->GetOutput(pin.name);
        }
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    stats_.total_executions++;
    stats_.avg_execution_time_ms =
        (stats_.avg_execution_time_ms * (stats_.total_executions - 1) + duration.count() / 1000.0)
        / stats_.total_executions;

    return true;
}

void BlockExecutor::Shutdown() {
    std::cout << "\n=== Shutting Down Blocks ===" << std::endl;

    for (auto& [node_id, node] : nodes_) {
        if (node.block) {
            node.block->Shutdown();
            std::cout << "  Shutdown node " << node_id << std::endl;
        }
    }

    nodes_.clear();
    connections_.clear();
    execution_order_.clear();

    std::cout << "✓ All blocks shut down" << std::endl;
}

void BlockExecutor::TransferData() {
    // Transfer data along connections
    for (const auto& conn : connections_) {
        auto from_it = nodes_.find(conn.from_node_id);
        auto to_it = nodes_.find(conn.to_node_id);

        if (from_it == nodes_.end() || to_it == nodes_.end()) {
            continue;
        }

        ExecutionNode& from_node = from_it->second;
        ExecutionNode& to_node = to_it->second;

        if (!from_node.block || !to_node.block) {
            continue;
        }

        // Get value from output pin of source node
        auto output_it = from_node.output_values.find(conn.from_pin);
        if (output_it == from_node.output_values.end()) {
            // Output not yet available, skip
            continue;
        }

        // Set value to input pin of destination node
        to_node.input_values[conn.to_pin] = output_it->second;
        to_node.block->SetInput(conn.to_pin, output_it->second);
    }
}

bool BlockExecutor::BuildExecutionOrder() {
    // Simple topological sort using Kahn's algorithm
    std::map<int, int> in_degree;
    std::map<int, std::vector<int>> adj_list;

    // Initialize in-degrees
    for (const auto& [node_id, node] : nodes_) {
        in_degree[node_id] = 0;
    }

    // Build adjacency list and calculate in-degrees
    for (const auto& conn : connections_) {
        adj_list[conn.from_node_id].push_back(conn.to_node_id);
        in_degree[conn.to_node_id]++;
    }

    // Find nodes with no incoming edges
    std::vector<int> queue;
    for (const auto& [node_id, degree] : in_degree) {
        if (degree == 0) {
            queue.push_back(node_id);
        }
    }

    execution_order_.clear();

    while (!queue.empty()) {
        int current = queue.back();
        queue.pop_back();
        execution_order_.push_back(current);

        // Process neighbors
        if (adj_list.count(current)) {
            for (int neighbor : adj_list[current]) {
                in_degree[neighbor]--;
                if (in_degree[neighbor] == 0) {
                    queue.push_back(neighbor);
                }
            }
        }
    }

    // Check if all nodes were processed (no cycles)
    if (execution_order_.size() != nodes_.size()) {
        error_ = "Cycle detected in execution graph";
        return false;
    }

    return true;
}

bool BlockExecutor::HasCycle() const {
    // Check if execution order contains all nodes
    return execution_order_.size() != nodes_.size();
}

bool BlockExecutor::GetNodeOutputValue(int node_id, const std::string& pin_name, BlockValue& value) const {
    auto it = nodes_.find(node_id);
    if (it == nodes_.end()) {
        return false;
    }

    const auto& outputs = it->second.output_values;
    auto pin_it = outputs.find(pin_name);
    if (pin_it == outputs.end()) {
        return false;
    }

    value = pin_it->second;
    return true;
}

std::map<std::string, BlockValue> BlockExecutor::GetNodeOutputValues(int node_id) const {
    auto it = nodes_.find(node_id);
    if (it == nodes_.end()) {
        return {};
    }

    return it->second.output_values;
}

} // namespace CiraBlockRuntime
