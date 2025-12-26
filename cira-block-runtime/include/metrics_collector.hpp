#pragma once

#include <string>
#include <map>
#include <vector>
#include <mutex>
#include <chrono>
#include "nlohmann/json.hpp"

namespace CiraBlockRuntime {

struct BlockMetrics {
    std::string block_id;
    uint64_t execution_count = 0;
    double avg_latency_ms = 0.0;
    double total_latency_ms = 0.0;
    std::string last_output_value;
    std::string last_output_type;
    uint64_t last_execution_time = 0;

    nlohmann::json ToJson() const {
        return {
            {"block_id", block_id},
            {"execution_count", execution_count},
            {"avg_latency_ms", avg_latency_ms},
            {"last_output_value", last_output_value},
            {"last_output_type", last_output_type},
            {"last_execution_time", last_execution_time}
        };
    }
};

struct SystemMetrics {
    double cpu_usage_percent = 0.0;
    uint64_t memory_used_mb = 0;
    uint64_t memory_total_mb = 0;
    uint64_t uptime_seconds = 0;

    nlohmann::json ToJson() const {
        return {
            {"cpu_usage", cpu_usage_percent},
            {"memory_used_mb", memory_used_mb},
            {"memory_total_mb", memory_total_mb},
            {"uptime_seconds", uptime_seconds}
        };
    }
};

class MetricsCollector {
public:
    MetricsCollector();

    // Record block execution
    void RecordBlockExecution(const std::string& block_id, double latency_ms);

    // Record block output for monitoring
    void RecordBlockOutput(const std::string& block_id, const std::string& pin_name,
                          const std::string& value, const std::string& type);

    // Get metrics
    std::vector<BlockMetrics> GetAllBlockMetrics() const;
    BlockMetrics GetBlockMetrics(const std::string& block_id) const;
    SystemMetrics GetSystemMetrics() const;

    // Reset metrics
    void Reset();
    void ResetBlock(const std::string& block_id);

    // Export to JSON
    nlohmann::json ToJson() const;

private:
    mutable std::mutex mutex_;
    std::map<std::string, BlockMetrics> block_metrics_;
    std::chrono::steady_clock::time_point start_time_;

    // Helper to update system metrics
    void UpdateSystemMetrics();
    SystemMetrics system_metrics_;
};

} // namespace CiraBlockRuntime
