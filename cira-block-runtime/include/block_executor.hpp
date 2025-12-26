#pragma once

#include "block_interface.hpp"
#include "manifest_parser.hpp"
#include "block_loader.hpp"
#include <map>
#include <vector>
#include <memory>
#include <cstdint>

namespace CiraBlockRuntime {

// Node instance in execution graph
struct ExecutionNode {
    int node_id;
    std::string node_type;
    IBlock* block;
    BlockConfig config;
    std::map<std::string, BlockValue> input_values;
    std::map<std::string, BlockValue> output_values;
};

// Execution graph - manages pipeline execution
class BlockExecutor {
public:
    BlockExecutor();
    ~BlockExecutor();

    // Build execution graph from manifest
    bool BuildFromManifest(const BlockManifest& manifest, BlockLoader& loader);

    // Initialize all blocks
    bool Initialize();

    // Execute one iteration of the pipeline
    // Returns true if successful, false on error
    bool Execute();

    // Shutdown all blocks
    void Shutdown();

    // Get execution statistics
    struct Stats {
        uint64_t total_executions;
        uint64_t total_errors;
        double avg_execution_time_ms;
    };
    Stats GetStats() const { return stats_; }

    // Get error message
    const std::string& GetError() const { return error_; }

    // Get all nodes (for dashboard display)
    const std::map<int, ExecutionNode>& GetNodes() const { return nodes_; }

    // Get specific node output value
    bool GetNodeOutputValue(int node_id, const std::string& pin_name, BlockValue& value) const;

    // Get all output values for a node
    std::map<std::string, BlockValue> GetNodeOutputValues(int node_id) const;

private:
    std::map<int, ExecutionNode> nodes_;
    std::vector<Connection> connections_;
    std::vector<int> execution_order_;  // Topologically sorted node IDs
    Stats stats_;
    std::string error_;

    // Build topological sort for execution order
    bool BuildExecutionOrder();

    // Transfer data between connected nodes
    void TransferData();

    // Check for cycles in graph
    bool HasCycle() const;
};

} // namespace CiraBlockRuntime
