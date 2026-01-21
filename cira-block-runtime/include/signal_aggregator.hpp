#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <memory>
#include <deque>
#include "block_interface.hpp"

namespace CiraBlockRuntime {

/**
 * Circular buffer for efficient signal storage
 * Lock-free single-producer, single-consumer
 */
template<typename T>
class CircularBuffer {
public:
    explicit CircularBuffer(size_t capacity)
        : capacity_(capacity)
        , buffer_(capacity)
        , write_pos_(0)
        , read_pos_(0)
        , size_(0)
    {}

    // Add sample to buffer
    void Push(T value) {
        buffer_[write_pos_] = value;
        write_pos_ = (write_pos_ + 1) % capacity_;

        if (size_ < capacity_) {
            size_++;
        } else {
            // Buffer full, move read position
            read_pos_ = (read_pos_ + 1) % capacity_;
        }
    }

    // Get latest N samples
    std::vector<T> GetLatest(size_t n) const {
        if (n > size_) {
            n = size_;
        }

        std::vector<T> result;
        result.reserve(n);

        size_t start_pos = (write_pos_ + capacity_ - n) % capacity_;
        for (size_t i = 0; i < n; ++i) {
            result.push_back(buffer_[(start_pos + i) % capacity_]);
        }

        return result;
    }

    // Get all samples
    std::vector<T> GetAll() const {
        return GetLatest(size_);
    }

    size_t Size() const { return size_; }
    size_t Capacity() const { return capacity_; }
    bool IsEmpty() const { return size_ == 0; }
    bool IsFull() const { return size_ == capacity_; }

    void Clear() {
        write_pos_ = 0;
        read_pos_ = 0;
        size_ = 0;
    }

private:
    size_t capacity_;
    std::vector<T> buffer_;
    size_t write_pos_;
    size_t read_pos_;
    size_t size_;
};

/**
 * Downsampled waveform chunk ready for transmission
 */
struct WaveformChunk {
    std::string signal_id;          // "node_id:pin_name"
    uint64_t timestamp;             // Milliseconds since epoch
    std::vector<float> samples;     // Downsampled samples
    int original_sample_count;      // Original number of samples
    float min_value;                // Min value in chunk
    float max_value;                // Max value in chunk
    float avg_value;                // Average value
    std::string string_value;       // For string-type signals (e.g., class names)
    bool is_string = false;         // Flag to indicate this is a string value
};

/**
 * Signal aggregation and downsampling engine
 * Optimized for oscilloscope display
 */
class SignalAggregator {
public:
    SignalAggregator(size_t buffer_size = 10000);
    ~SignalAggregator();

    /**
     * Push a new sample to the buffer
     * Called by runtime when blocks produce output
     */
    void PushSample(const std::string& node_id,
                   const std::string& pin_name,
                   const BlockValue& value);

    /**
     * Get downsampled waveform chunk for display
     * @param signal_id Format: "node_id:pin_name"
     * @param target_samples Number of samples client wants
     * @return Downsampled waveform chunk
     */
    WaveformChunk GetWaveformChunk(const std::string& signal_id,
                                   int target_samples = 1000);

    /**
     * Get raw samples (no downsampling)
     * Used for debugging or when client wants full resolution
     */
    std::vector<float> GetRawSamples(const std::string& signal_id,
                                    int max_samples = 1000);

    /**
     * Clear buffer for specific signal
     */
    void ClearSignal(const std::string& signal_id);

    /**
     * Clear all buffers
     */
    void ClearAll();

    /**
     * Get statistics
     */
    size_t GetSignalCount() const;
    size_t GetBufferSize(const std::string& signal_id) const;

    /**
     * Downsample using Min/Max/Avg algorithm
     * Professional oscilloscopes use this to preserve peaks
     */
    static std::vector<float> DownsampleMinMaxAvg(
        const std::vector<float>& input,
        int target_samples
    );

private:
    std::string MakeSignalId(const std::string& node_id,
                            const std::string& pin_name) const;

    float ExtractFloatValue(const BlockValue& value) const;

    size_t buffer_size_;
    mutable std::mutex mutex_;

    // Signal buffers: "node_id:pin_name" -> CircularBuffer
    std::unordered_map<std::string, std::unique_ptr<CircularBuffer<float>>> buffers_;

    // Signal statistics for measurements
    struct SignalStats {
        float min_value = 0.0f;
        float max_value = 0.0f;
        float avg_value = 0.0f;
        uint64_t sample_count = 0;
    };
    std::unordered_map<std::string, SignalStats> stats_;
};

} // namespace CiraBlockRuntime
