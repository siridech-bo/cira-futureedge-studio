#include "../../../include/block_interface.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <ctime>
#include <vector>
#include <map>
#include <unistd.h>  // for gethostname
#include "../../../third_party/json.hpp"

// Use experimental filesystem for older compilers (GCC < 8)
#if __has_include(<filesystem>)
    #include <filesystem>
    namespace fs = std::filesystem;
#else
    #include <experimental/filesystem>
    namespace fs = std::experimental::filesystem;
#endif

namespace CiraBlockRuntime {

struct Sample {
    std::chrono::system_clock::time_point timestamp;
    std::vector<float> data;
    std::string class_name;
    int class_id;
};

class DataRecorderBlock : public IBlock {
public:
    DataRecorderBlock()
        : record_trigger_(false)
        , is_recording_(false)
        , sample_count_(0)
        , max_samples_(10000)
        , output_format_("csv")
        , output_dir_("/home/user/cira_datasets")
        , current_class_name_("")
        , current_class_id_(0)
        , window_size_(300)
        , num_channels_(3)
        , window_count_(0)
    {
        std::cout << "DataRecorderBlock constructor called" << std::endl;
    }

    ~DataRecorderBlock() {
        Shutdown();
    }

    bool Initialize(const BlockConfig& config) override {
        std::cout << "DataRecorderBlock::Initialize()" << std::endl;

        if (config.count("max_samples")) {
            max_samples_ = std::stoi(config.at("max_samples"));
        }
        if (config.count("output_format")) {
            output_format_ = config.at("output_format");
        }
        if (config.count("output_dir")) {
            output_dir_ = config.at("output_dir");
        }
        if (config.count("window_size")) {
            window_size_ = std::stoi(config.at("window_size"));
        }
        if (config.count("num_channels")) {
            num_channels_ = std::stoi(config.at("num_channels"));
        }

        std::cout << "  Max samples (windows): " << max_samples_ << std::endl;
        std::cout << "  Window size: " << window_size_ << std::endl;
        std::cout << "  Num channels: " << num_channels_ << std::endl;
        std::cout << "  Output format: " << output_format_ << std::endl;
        std::cout << "  Output directory: " << output_dir_ << std::endl;

        try {
            if (!fs::exists(output_dir_)) {
                fs::create_directories(output_dir_);
                std::cout << "✓ Created output directory" << std::endl;
            }
        } catch (const std::exception& e) {
            std::cerr << "ERROR: Failed to create output directory: " << e.what() << std::endl;
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

    std::vector<Pin> GetInputPins() const override {
        return {
            Pin("record_trigger", "bool", true),
            Pin("stop_trigger", "bool", true),
            Pin("signal_data", "array", true),
            Pin("class_name", "string", true),
            Pin("class_id", "int", true)
        };
    }

    std::vector<Pin> GetOutputPins() const override {
        return {
            Pin("recording_status", "bool", false),
            Pin("sample_count", "int", false)
        };
    }

    void SetInput(const std::string& pin_name, const BlockValue& value) override {
        if (pin_name == "record_trigger" && std::holds_alternative<bool>(value)) {
            bool trigger = std::get<bool>(value);

            // Original working logic: level-based trigger
            if (trigger && !is_recording_) {
                // Trigger HIGH and not recording → START
                std::cout << "[DataRecorder] Start recording (trigger=HIGH)" << std::endl;
                StartRecording();
            } else if (!trigger && is_recording_) {
                // Trigger LOW and IS recording → STOP and save
                std::cout << "[DataRecorder] Stop recording (trigger=LOW, windows=" << window_count_ << ")" << std::endl;
                StopRecording();
            }
        }
        else if (pin_name == "signal_data" && std::holds_alternative<std::vector<float>>(value)) {
            signal_data_ = std::get<std::vector<float>>(value);
            static int input_count = 0;
            if (input_count % 100 == 0) {
                std::cout << "[DataRecorder] SetInput signal_data, size=" << signal_data_.size() << ", is_recording=" << is_recording_ << std::endl;
            }
            input_count++;
        }
        else if (pin_name == "class_name" && std::holds_alternative<std::string>(value)) {
            current_class_name_ = std::get<std::string>(value);
        }
        else if (pin_name == "class_id" && std::holds_alternative<int>(value)) {
            current_class_id_ = std::get<int>(value);
        }
    }

    bool Execute() override {
        static int exec_count = 0;
        if (exec_count % 100 == 0 && is_recording_) {
            std::cout << "[DataRecorder] Execute() - is_recording=" << is_recording_
                      << ", signal_data_.size()=" << signal_data_.size()
                      << ", window_buffer_.size()=" << window_buffer_.size()
                      << "/" << window_size_ << ", windows=" << window_count_ << std::endl;
        }
        exec_count++;

        if (is_recording_ && !signal_data_.empty()) {
            // Verify signal_data has correct number of channels
            if (signal_data_.size() != static_cast<size_t>(num_channels_)) {
                std::cerr << "[DataRecorder] WARNING: Expected " << num_channels_
                          << " channels but got " << signal_data_.size() << std::endl;
            }

            // Add this sample to the window buffer
            window_buffer_.push_back(signal_data_);

            // Check if we've accumulated enough samples for a complete window
            if (static_cast<int>(window_buffer_.size()) >= window_size_) {
                // Flatten buffer into channel-by-channel format
                std::vector<float> windowed_data;
                windowed_data.reserve(window_size_ * num_channels_);

                // Reshape: [ch0_all_samples, ch1_all_samples, ch2_all_samples, ...]
                for (int ch = 0; ch < num_channels_; ++ch) {
                    for (int sample_idx = 0; sample_idx < window_size_; ++sample_idx) {
                        if (ch < static_cast<int>(window_buffer_[sample_idx].size())) {
                            windowed_data.push_back(window_buffer_[sample_idx][ch]);
                        } else {
                            windowed_data.push_back(0.0f); // Pad if needed
                        }
                    }
                }

                // Create window sample
                Sample window_sample;
                window_sample.timestamp = std::chrono::system_clock::now();
                window_sample.data = windowed_data;
                window_sample.class_name = current_class_name_;
                window_sample.class_id = current_class_id_;

                samples_.push_back(window_sample);
                window_count_++;
                sample_count_ = window_count_;

                // Progress logging - show every window for easy monitoring
                std::cout << "=== [DataRecorder] Window " << window_count_ << "/" << max_samples_
                          << " completed (class: " << current_class_name_ << ", id: " << current_class_id_ << ") ===" << std::endl;

                // Clear buffer for next window
                window_buffer_.clear();

                // Check if we've reached max windows - auto-save and continue
                if (window_count_ >= max_samples_) {
                    std::cout << "\n╔════════════════════════════════════════════════════════════╗" << std::endl;
                    std::cout << "║  AUTO-SAVE: " << max_samples_ << " windows completed!                    ║" << std::endl;
                    std::cout << "║  Saving batch and continuing recording...                 ║" << std::endl;
                    std::cout << "╚════════════════════════════════════════════════════════════╝\n" << std::endl;

                    // Save current batch
                    if (!samples_.empty()) {
                        if (output_format_ == "cbor") {
                            SaveAsCBOR();
                        } else if (output_format_ == "csv") {
                            SaveAsCSV();
                        } else {
                            SaveAsJSON();
                        }
                    }

                    // Clear samples and reset counter to continue recording next batch
                    samples_.clear();
                    window_count_ = 0;
                    std::cout << "=== Recording continues - next batch starting... ===" << std::endl;
                }
            }
        }
        return true;
    }

    BlockValue GetOutput(const std::string& pin_name) const override {
        if (pin_name == "recording_status") {
            return is_recording_;
        }
        else if (pin_name == "sample_count") {
            return sample_count_;
        }
        return false;
    }

    void Shutdown() override {
        if (is_recording_) {
            StopRecording();
        }
        std::cout << "DataRecorderBlock shutdown" << std::endl;
    }

private:
    void StartRecording() {
        samples_.clear();
        window_buffer_.clear();
        sample_count_ = 0;
        window_count_ = 0;
        is_recording_ = true;
        std::cout << "Recording started (windowed mode: " << window_size_
                  << " samples × " << num_channels_ << " channels)" << std::endl;
    }

    void StopRecording() {
        is_recording_ = false;
        std::cout << "Recording stopped with " << window_count_ << " windows" << std::endl;

        // If there's a partial window in the buffer, warn but don't save it
        if (!window_buffer_.empty()) {
            std::cout << "  WARNING: Discarding partial window with "
                      << window_buffer_.size() << "/" << window_size_ << " samples" << std::endl;
        }

        if (!samples_.empty()) {
            if (output_format_ == "csv") {
                SaveAsCSV();
            } else if (output_format_ == "cbor") {
                SaveAsCBOR();
            } else {
                SaveAsJSON();
            }
        }
    }

    void SaveAsCSV() {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        std::stringstream ss;
        ss << output_dir_ << "/recording_"
           << std::put_time(std::localtime(&time_t), "%Y%m%d_%H%M%S")
           << ".csv";

        std::ofstream file(ss.str());
        if (!file.is_open()) {
            std::cerr << "ERROR: Failed to open CSV file: " << ss.str() << std::endl;
            return;
        }

        file << "timestamp,class_name,class_id";
        if (!samples_.empty() && !samples_[0].data.empty()) {
            for (size_t i = 0; i < samples_[0].data.size(); i++) {
                file << ",value_" << i;
            }
        }
        file << "\n";

        for (const auto& sample : samples_) {
            auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                sample.timestamp.time_since_epoch()).count();
            file << ms << "," << sample.class_name << "," << sample.class_id;
            for (float val : sample.data) {
                file << "," << val;
            }
            file << "\n";
        }

        file.close();
        std::cout << "✓ Saved " << samples_.size() << " samples to " << ss.str() << std::endl;
    }

    void SaveAsJSON() {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        std::stringstream ss;
        ss << output_dir_ << "/recording_"
           << std::put_time(std::localtime(&time_t), "%Y%m%d_%H%M%S")
           << ".json";

        std::ofstream file(ss.str());
        if (!file.is_open()) {
            std::cerr << "ERROR: Failed to open JSON file: " << ss.str() << std::endl;
            return;
        }

        file << "{\n";
        file << "  \"samples\": [\n";

        for (size_t i = 0; i < samples_.size(); i++) {
            const auto& sample = samples_[i];
            auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                sample.timestamp.time_since_epoch()).count();

            file << "    {\n";
            file << "      \"timestamp\": " << ms << ",\n";
            file << "      \"class_name\": \"" << sample.class_name << "\",\n";
            file << "      \"class_id\": " << sample.class_id << ",\n";
            file << "      \"data\": [";
            for (size_t j = 0; j < sample.data.size(); j++) {
                file << sample.data[j];
                if (j < sample.data.size() - 1) file << ", ";
            }
            file << "]\n";
            file << "    }";
            if (i < samples_.size() - 1) file << ",";
            file << "\n";
        }

        file << "  ]\n";
        file << "}\n";

        file.close();
        std::cout << "✓ Saved " << samples_.size() << " samples to " << ss.str() << std::endl;
    }

    void SaveAsCBOR() {
        using json = nlohmann::json;

        // Determine dominant class name from samples
        std::map<std::string, int> class_counts;
        for (const auto& sample : samples_) {
            if (!sample.class_name.empty()) {
                class_counts[sample.class_name]++;
            }
        }

        std::string dominant_class = "unknown";
        int max_count = 0;
        for (const auto& pair : class_counts) {
            if (pair.second > max_count) {
                max_count = pair.second;
                dominant_class = pair.first;
            }
        }

        // Generate filename: {class_name}.{sequence}.cbor.{unique_id}.{device_id}.cbor
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);

        // Get sequence number (count existing files for this class)
        int sequence_num = 1;
        for (const auto& entry : fs::directory_iterator(output_dir_)) {
            if (entry.path().filename().string().find(dominant_class + ".") == 0) {
                sequence_num++;
            }
        }

        // Generate unique ID (timestamp-based)
        std::stringstream unique_id;
        unique_id << std::hex << time_t;

        // Device ID (hostname or "jetson")
        std::string device_id = "jetson";
        #ifdef __linux__
            char hostname[256];
            if (gethostname(hostname, sizeof(hostname)) == 0) {
                device_id = hostname;
            }
        #endif

        // Build filename
        std::stringstream ss;
        ss << output_dir_ << "/" << dominant_class << "." << sequence_num
           << ".cbor." << unique_id.str() << "." << device_id << ".cbor";

        // Build JSON structure
        json j;
        j["samples"] = json::array();

        for (const auto& sample : samples_) {
            auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                sample.timestamp.time_since_epoch()).count();

            json sample_obj;
            sample_obj["timestamp"] = ms;
            sample_obj["class_name"] = sample.class_name;
            sample_obj["class_id"] = sample.class_id;
            sample_obj["data"] = sample.data;

            j["samples"].push_back(sample_obj);
        }

        // Convert to CBOR binary format
        std::vector<uint8_t> cbor_data = json::to_cbor(j);

        // Write binary data to file
        std::ofstream file(ss.str(), std::ios::binary);
        if (!file.is_open()) {
            std::cerr << "ERROR: Failed to open CBOR file: " << ss.str() << std::endl;
            return;
        }

        file.write(reinterpret_cast<const char*>(cbor_data.data()), cbor_data.size());
        file.close();

        std::cout << "✓ Saved " << samples_.size() << " samples to " << ss.str()
                  << " (" << cbor_data.size() << " bytes)" << std::endl;
    }

    bool record_trigger_;
    bool is_recording_;
    int sample_count_;
    int max_samples_;
    std::string output_format_;
    std::string output_dir_;
    std::string current_class_name_;
    int current_class_id_;
    std::vector<float> signal_data_;
    std::vector<Sample> samples_;

    // Windowing parameters
    int window_size_;
    int num_channels_;
    int window_count_;
    std::vector<std::vector<float>> window_buffer_;  // Buffer to accumulate samples for current window
};

} // namespace CiraBlockRuntime

// Export factory functions
extern "C" {
    CiraBlockRuntime::IBlock* CreateBlock() {
        return new CiraBlockRuntime::DataRecorderBlock();
    }

    void DestroyBlock(CiraBlockRuntime::IBlock* block) {
        delete block;
    }
}
