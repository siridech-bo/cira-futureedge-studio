#include "../../../include/block_interface.hpp"
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <filesystem>
#include <ctime>

namespace CiraBlockRuntime {

class DataRecorderBlock : public IBlock {
public:
    DataRecorderBlock()
        : is_recording_(false)
        , sample_count_(0)
        , max_samples_(0)
        , recording_duration_ms_(0)
        , output_format_("cbor")
        , save_directory_("/home/user/cira_datasets")
    {
        std::cout << "DataRecorderBlock constructor called" << std::endl;
    }

    ~DataRecorderBlock() {
        if (is_recording_) {
            StopRecording();
        }
    }

    bool Initialize(const BlockConfig& config) override {
        std::cout << "DataRecorderBlock::Initialize()" << std::endl;

        // Parse configuration
        if (config.count("format")) {
            output_format_ = config.at("format");
        }
        if (config.count("save_directory")) {
            save_directory_ = config.at("save_directory");
        }
        if (config.count("max_samples")) {
            max_samples_ = std::stoi(config.at("max_samples"));
        }
        if (config.count("duration_ms")) {
            recording_duration_ms_ = std::stoi(config.at("duration_ms"));
        }

        std::cout << "  Output Format: " << output_format_ << std::endl;
        std::cout << "  Save Directory: " << save_directory_ << std::endl;
        std::cout << "  Max Samples: " << max_samples_ << std::endl;
        std::cout << "  Duration (ms): " << recording_duration_ms_ << std::endl;

        // Create save directory if it doesn't exist
        try {
            std::filesystem::create_directories(save_directory_);
            std::cout << "✓ Data recorder initialized successfully" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "ERROR: Failed to create save directory: " << e.what() << std::endl;
            return false;
        }

        return true;
    }

    std::string GetBlockId() const override {
        return "data-recorder";
    }

    std::string GetBlockVersion() const override {
        return "1.0.0";
    }

    std::string GetBlockType() const override {
        return "output";
    }

    std::vector<PinDefinition> GetInputPins() const override {
        return {
            {"record_trigger", DataType::BOOL, "Start/stop recording trigger"},
            {"data_stream_1", DataType::FLOAT, "Primary data stream to record"},
            {"data_stream_2", DataType::FLOAT_VECTOR, "Secondary data stream (optional)"},
            {"label", DataType::INT, "Ground truth label (optional)"}
        };
    }

    std::vector<PinDefinition> GetOutputPins() const override {
        return {
            {"recording_status", DataType::BOOL, "True when recording is active"},
            {"sample_count", DataType::INT, "Number of samples recorded"}
        };
    }

    void Process(const InputValues& inputs, OutputValues& outputs) override {
        // Check for recording trigger
        if (inputs.count("record_trigger") > 0) {
            bool trigger = std::get<bool>(inputs.at("record_trigger"));

            if (trigger && !is_recording_) {
                StartRecording();
            } else if (!trigger && is_recording_) {
                StopRecording();
            }
        }

        // If recording, collect data
        if (is_recording_) {
            RecordSample(inputs);

            // Check if we should stop based on max_samples or duration
            if (max_samples_ > 0 && sample_count_ >= max_samples_) {
                std::cout << "Max samples reached, stopping recording" << std::endl;
                StopRecording();
            }

            if (recording_duration_ms_ > 0) {
                auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
                    std::chrono::steady_clock::now() - recording_start_time_
                ).count();

                if (elapsed >= recording_duration_ms_) {
                    std::cout << "Recording duration reached, stopping recording" << std::endl;
                    StopRecording();
                }
            }
        }

        // Update outputs
        outputs["recording_status"] = is_recording_;
        outputs["sample_count"] = static_cast<int>(sample_count_);
    }

    void Shutdown() override {
        if (is_recording_) {
            StopRecording();
        }
        std::cout << "DataRecorderBlock shutdown" << std::endl;
    }

private:
    struct DataSample {
        int64_t timestamp_us;
        float data_stream_1;
        std::vector<float> data_stream_2;
        int label;
    };

    bool is_recording_;
    size_t sample_count_;
    size_t max_samples_;
    int64_t recording_duration_ms_;
    std::string output_format_;
    std::string save_directory_;
    std::string current_filename_;

    std::chrono::steady_clock::time_point recording_start_time_;
    std::vector<DataSample> recorded_samples_;

    void StartRecording() {
        std::cout << "Starting data recording..." << std::endl;

        is_recording_ = true;
        sample_count_ = 0;
        recorded_samples_.clear();
        recording_start_time_ = std::chrono::steady_clock::now();

        // Generate filename with timestamp
        auto now = std::chrono::system_clock::now();
        auto time_t_now = std::chrono::system_clock::to_time_t(now);
        std::tm tm_now;

#ifdef _WIN32
        localtime_s(&tm_now, &time_t_now);
#else
        localtime_r(&time_t_now, &tm_now);
#endif

        std::ostringstream oss;
        oss << "dataset_"
            << std::put_time(&tm_now, "%Y%m%d_%H%M%S")
            << "." << output_format_;

        current_filename_ = save_directory_ + "/" + oss.str();

        std::cout << "✓ Recording started: " << current_filename_ << std::endl;
    }

    void RecordSample(const InputValues& inputs) {
        DataSample sample;

        // Get timestamp in microseconds
        auto now = std::chrono::steady_clock::now();
        sample.timestamp_us = std::chrono::duration_cast<std::chrono::microseconds>(
            now - recording_start_time_
        ).count();

        // Record data streams
        if (inputs.count("data_stream_1") > 0) {
            sample.data_stream_1 = std::get<float>(inputs.at("data_stream_1"));
        } else {
            sample.data_stream_1 = 0.0f;
        }

        if (inputs.count("data_stream_2") > 0) {
            sample.data_stream_2 = std::get<std::vector<float>>(inputs.at("data_stream_2"));
        }

        if (inputs.count("label") > 0) {
            sample.label = std::get<int>(inputs.at("label"));
        } else {
            sample.label = -1;  // No label
        }

        recorded_samples_.push_back(sample);
        sample_count_++;
    }

    void StopRecording() {
        if (!is_recording_) return;

        std::cout << "Stopping data recording..." << std::endl;
        std::cout << "  Total samples: " << sample_count_ << std::endl;

        // Save data based on format
        bool success = false;
        if (output_format_ == "csv") {
            success = SaveAsCSV();
        } else if (output_format_ == "json") {
            success = SaveAsJSON();
        } else if (output_format_ == "cbor") {
            success = SaveAsCBOR();
        } else if (output_format_ == "npy") {
            success = SaveAsNumPy();
        } else {
            std::cerr << "ERROR: Unsupported format: " << output_format_ << std::endl;
        }

        if (success) {
            std::cout << "✓ Data saved successfully: " << current_filename_ << std::endl;
        } else {
            std::cerr << "ERROR: Failed to save data" << std::endl;
        }

        is_recording_ = false;
        recorded_samples_.clear();
    }

    bool SaveAsCSV() {
        std::ofstream file(current_filename_);
        if (!file.is_open()) {
            std::cerr << "ERROR: Could not open file for writing: " << current_filename_ << std::endl;
            return false;
        }

        // Write header
        file << "timestamp_us,data_stream_1,";

        // Determine max vector size for data_stream_2
        size_t max_vector_size = 0;
        for (const auto& sample : recorded_samples_) {
            if (sample.data_stream_2.size() > max_vector_size) {
                max_vector_size = sample.data_stream_2.size();
            }
        }

        for (size_t i = 0; i < max_vector_size; ++i) {
            file << "data_stream_2_" << i << ",";
        }

        file << "label\n";

        // Write data
        for (const auto& sample : recorded_samples_) {
            file << sample.timestamp_us << ","
                 << sample.data_stream_1 << ",";

            for (size_t i = 0; i < max_vector_size; ++i) {
                if (i < sample.data_stream_2.size()) {
                    file << sample.data_stream_2[i];
                } else {
                    file << "";
                }
                file << ",";
            }

            file << sample.label << "\n";
        }

        file.close();
        return true;
    }

    bool SaveAsJSON() {
        std::ofstream file(current_filename_);
        if (!file.is_open()) {
            std::cerr << "ERROR: Could not open file for writing: " << current_filename_ << std::endl;
            return false;
        }

        file << "{\n";
        file << "  \"metadata\": {\n";
        file << "    \"sample_count\": " << sample_count_ << ",\n";
        file << "    \"format_version\": \"1.0\"\n";
        file << "  },\n";
        file << "  \"samples\": [\n";

        for (size_t i = 0; i < recorded_samples_.size(); ++i) {
            const auto& sample = recorded_samples_[i];

            file << "    {\n";
            file << "      \"timestamp_us\": " << sample.timestamp_us << ",\n";
            file << "      \"data_stream_1\": " << sample.data_stream_1 << ",\n";
            file << "      \"data_stream_2\": [";

            for (size_t j = 0; j < sample.data_stream_2.size(); ++j) {
                file << sample.data_stream_2[j];
                if (j < sample.data_stream_2.size() - 1) file << ", ";
            }

            file << "],\n";
            file << "      \"label\": " << sample.label << "\n";
            file << "    }";

            if (i < recorded_samples_.size() - 1) {
                file << ",";
            }
            file << "\n";
        }

        file << "  ]\n";
        file << "}\n";

        file.close();
        return true;
    }

    bool SaveAsCBOR() {
        // For now, save as JSON with .cbor extension
        // TODO: Implement actual CBOR encoding
        std::cout << "Warning: CBOR format not yet implemented, saving as JSON" << std::endl;
        return SaveAsJSON();
    }

    bool SaveAsNumPy() {
        // For now, save as CSV with .npy extension
        // TODO: Implement actual NumPy .npy format
        std::cout << "Warning: NPY format not yet implemented, saving as CSV" << std::endl;
        return SaveAsCSV();
    }
};

// Factory function
extern "C" IBlock* CreateBlock() {
    return new DataRecorderBlock();
}

extern "C" void DestroyBlock(IBlock* block) {
    delete block;
}

} // namespace CiraBlockRuntime
