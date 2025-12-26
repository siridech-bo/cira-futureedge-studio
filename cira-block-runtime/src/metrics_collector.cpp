#include "metrics_collector.hpp"
#include <fstream>
#include <sstream>

#ifdef _WIN32
#include <windows.h>
#include <psapi.h>
#else
#include <unistd.h>
#include <sys/sysinfo.h>
#endif

namespace CiraBlockRuntime {

MetricsCollector::MetricsCollector()
    : start_time_(std::chrono::steady_clock::now()) {
}

void MetricsCollector::RecordBlockExecution(const std::string& block_id, double latency_ms) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto& metrics = block_metrics_[block_id];
    metrics.block_id = block_id;
    metrics.execution_count++;
    metrics.total_latency_ms += latency_ms;
    metrics.avg_latency_ms = metrics.total_latency_ms / metrics.execution_count;
    metrics.last_execution_time = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
}

void MetricsCollector::RecordBlockOutput(const std::string& block_id,
                                         const std::string& pin_name,
                                         const std::string& value,
                                         const std::string& type) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto& metrics = block_metrics_[block_id];
    metrics.block_id = block_id;
    metrics.last_output_value = value;
    metrics.last_output_type = type;
}

std::vector<BlockMetrics> MetricsCollector::GetAllBlockMetrics() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<BlockMetrics> result;
    result.reserve(block_metrics_.size());

    for (const auto& pair : block_metrics_) {
        result.push_back(pair.second);
    }

    return result;
}

BlockMetrics MetricsCollector::GetBlockMetrics(const std::string& block_id) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = block_metrics_.find(block_id);
    if (it != block_metrics_.end()) {
        return it->second;
    }

    BlockMetrics empty;
    empty.block_id = block_id;
    return empty;
}

SystemMetrics MetricsCollector::GetSystemMetrics() const {
    // Update system metrics (non-const workaround)
    const_cast<MetricsCollector*>(this)->UpdateSystemMetrics();

    std::lock_guard<std::mutex> lock(mutex_);
    return system_metrics_;
}

void MetricsCollector::UpdateSystemMetrics() {
    auto now = std::chrono::steady_clock::now();
    system_metrics_.uptime_seconds = std::chrono::duration_cast<std::chrono::seconds>(
        now - start_time_
    ).count();

#ifdef _WIN32
    // Windows: Get memory info
    MEMORYSTATUSEX memInfo;
    memInfo.dwLength = sizeof(MEMORYSTATUSEX);
    GlobalMemoryStatusEx(&memInfo);

    system_metrics_.memory_total_mb = memInfo.ullTotalPhys / (1024 * 1024);
    system_metrics_.memory_used_mb = (memInfo.ullTotalPhys - memInfo.ullAvailPhys) / (1024 * 1024);

    // Simple CPU usage estimation (not accurate on Windows without more complex tracking)
    system_metrics_.cpu_usage_percent = 0.0;  // TODO: Implement proper CPU tracking

#else
    // Linux: Get memory info
    struct sysinfo info;
    if (sysinfo(&info) == 0) {
        system_metrics_.memory_total_mb = info.totalram / (1024 * 1024);
        system_metrics_.memory_used_mb = (info.totalram - info.freeram) / (1024 * 1024);
    }

    // Linux: Get CPU usage from /proc/stat
    std::ifstream stat_file("/proc/stat");
    if (stat_file.is_open()) {
        std::string line;
        std::getline(stat_file, line);

        // Parse "cpu  user nice system idle iowait irq softirq"
        std::istringstream iss(line);
        std::string cpu;
        uint64_t user, nice, system, idle;
        iss >> cpu >> user >> nice >> system >> idle;

        static uint64_t prev_idle = 0, prev_total = 0;
        uint64_t total = user + nice + system + idle;

        if (prev_total > 0) {
            uint64_t total_diff = total - prev_total;
            uint64_t idle_diff = idle - prev_idle;
            system_metrics_.cpu_usage_percent = total_diff > 0
                ? 100.0 * (1.0 - (double)idle_diff / total_diff)
                : 0.0;
        }

        prev_idle = idle;
        prev_total = total;
    }
#endif
}

void MetricsCollector::Reset() {
    std::lock_guard<std::mutex> lock(mutex_);
    block_metrics_.clear();
    start_time_ = std::chrono::steady_clock::now();
}

void MetricsCollector::ResetBlock(const std::string& block_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    block_metrics_.erase(block_id);
}

nlohmann::json MetricsCollector::ToJson() const {
    std::lock_guard<std::mutex> lock(mutex_);

    nlohmann::json blocks = nlohmann::json::array();
    for (const auto& pair : block_metrics_) {
        blocks.push_back(pair.second.ToJson());
    }

    return {
        {"blocks", blocks},
        {"system", system_metrics_.ToJson()},
        {"timestamp", std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()
        ).count()}
    };
}

} // namespace CiraBlockRuntime
