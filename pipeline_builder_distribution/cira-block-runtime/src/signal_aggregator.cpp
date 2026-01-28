#include "signal_aggregator.hpp"
#include <algorithm>
#include <cmath>
#include <chrono>
#include <iostream>

namespace CiraBlockRuntime {

SignalAggregator::SignalAggregator(size_t buffer_size)
    : buffer_size_(buffer_size)
{
    std::cout << "[SignalAggregator] Initialized with buffer size: " << buffer_size << std::endl;
}

SignalAggregator::~SignalAggregator() {
    std::lock_guard<std::mutex> lock(mutex_);
    buffers_.clear();
}

void SignalAggregator::PushSample(const std::string& node_id,
                                 const std::string& pin_name,
                                 const BlockValue& value) {
    std::string signal_id = MakeSignalId(node_id, pin_name);
    float float_value = ExtractFloatValue(value);

    std::lock_guard<std::mutex> lock(mutex_);

    // Create buffer if it doesn't exist
    if (buffers_.find(signal_id) == buffers_.end()) {
        buffers_[signal_id] = std::make_unique<CircularBuffer<float>>(buffer_size_);
        std::cout << "[SignalAggregator] Created buffer for signal: " << signal_id << std::endl;
    }

    // Push sample to circular buffer
    buffers_[signal_id]->Push(float_value);

    // Update statistics
    auto& stats = stats_[signal_id];
    stats.sample_count++;

    if (stats.sample_count == 1) {
        stats.min_value = float_value;
        stats.max_value = float_value;
        stats.avg_value = float_value;
    } else {
        stats.min_value = std::min(stats.min_value, float_value);
        stats.max_value = std::max(stats.max_value, float_value);
        // Running average (simple exponential moving average)
        stats.avg_value = stats.avg_value * 0.99f + float_value * 0.01f;
    }
}

WaveformChunk SignalAggregator::GetWaveformChunk(const std::string& signal_id,
                                                int target_samples) {
    std::lock_guard<std::mutex> lock(mutex_);

    WaveformChunk chunk;
    chunk.signal_id = signal_id;

    // Get current timestamp
    auto now = std::chrono::system_clock::now();
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()
    );
    chunk.timestamp = ms.count();

    // Check if signal exists
    auto it = buffers_.find(signal_id);
    if (it == buffers_.end() || it->second->IsEmpty()) {
        chunk.original_sample_count = 0;
        chunk.min_value = 0.0f;
        chunk.max_value = 0.0f;
        chunk.avg_value = 0.0f;
        return chunk;
    }

    // Get all available samples
    std::vector<float> raw_samples = it->second->GetAll();
    chunk.original_sample_count = raw_samples.size();

    // Get statistics
    auto stats_it = stats_.find(signal_id);
    if (stats_it != stats_.end()) {
        chunk.min_value = stats_it->second.min_value;
        chunk.max_value = stats_it->second.max_value;
        chunk.avg_value = stats_it->second.avg_value;
    }

    // Downsample if necessary
    if (raw_samples.size() > static_cast<size_t>(target_samples)) {
        chunk.samples = DownsampleMinMaxAvg(raw_samples, target_samples);
    } else {
        chunk.samples = raw_samples;
    }

    return chunk;
}

std::vector<float> SignalAggregator::GetRawSamples(const std::string& signal_id,
                                                   int max_samples) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = buffers_.find(signal_id);
    if (it == buffers_.end() || it->second->IsEmpty()) {
        return {};
    }

    return it->second->GetLatest(max_samples);
}

void SignalAggregator::ClearSignal(const std::string& signal_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = buffers_.find(signal_id);
    if (it != buffers_.end()) {
        it->second->Clear();
    }

    stats_.erase(signal_id);
}

void SignalAggregator::ClearAll() {
    std::lock_guard<std::mutex> lock(mutex_);

    for (auto& [id, buffer] : buffers_) {
        buffer->Clear();
    }

    stats_.clear();
}

size_t SignalAggregator::GetSignalCount() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return buffers_.size();
}

size_t SignalAggregator::GetBufferSize(const std::string& signal_id) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = buffers_.find(signal_id);
    if (it != buffers_.end()) {
        return it->second->Size();
    }

    return 0;
}

std::vector<float> SignalAggregator::DownsampleMinMaxAvg(
    const std::vector<float>& input,
    int target_samples
) {
    if (input.empty() || target_samples <= 0) {
        return {};
    }

    if (input.size() <= static_cast<size_t>(target_samples)) {
        return input;
    }

    std::vector<float> output;
    output.reserve(target_samples);

    // Calculate bucket size
    float bucket_size = static_cast<float>(input.size()) / target_samples;

    for (int i = 0; i < target_samples; ++i) {
        size_t start_idx = static_cast<size_t>(i * bucket_size);
        size_t end_idx = static_cast<size_t>((i + 1) * bucket_size);

        if (end_idx > input.size()) {
            end_idx = input.size();
        }

        // For each bucket, find min, max, and avg
        // This preserves peaks and valleys (like professional scopes)
        float min_val = input[start_idx];
        float max_val = input[start_idx];
        float sum = 0.0f;
        size_t count = 0;

        for (size_t j = start_idx; j < end_idx; ++j) {
            min_val = std::min(min_val, input[j]);
            max_val = std::max(max_val, input[j]);
            sum += input[j];
            count++;
        }

        float avg_val = count > 0 ? sum / count : 0.0f;

        // Store average (could also alternate min/max for better peak preservation)
        output.push_back(avg_val);
    }

    return output;
}

std::string SignalAggregator::MakeSignalId(const std::string& node_id,
                                          const std::string& pin_name) const {
    return node_id + ":" + pin_name;
}

float SignalAggregator::ExtractFloatValue(const BlockValue& value) const {
    if (std::holds_alternative<float>(value)) {
        return std::get<float>(value);
    } else if (std::holds_alternative<int>(value)) {
        return static_cast<float>(std::get<int>(value));
    } else if (std::holds_alternative<bool>(value)) {
        return std::get<bool>(value) ? 1.0f : 0.0f;
    } else if (std::holds_alternative<std::vector<float>>(value)) {
        const auto& vec = std::get<std::vector<float>>(value);
        return vec.empty() ? 0.0f : vec[0];
    }

    return 0.0f;
}

} // namespace CiraBlockRuntime
