#include "../../../include/block_interface.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <ctime>
#include <vector>

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

        std::cout << "  Max samples: " << max_samples_ << std::endl;
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
            bool new_trigger = std::get<bool>(value);
            if (new_trigger && !record_trigger_) {
                StartRecording();
            } else if (!new_trigger && record_trigger_) {
                StopRecording();
            }
            record_trigger_ = new_trigger;
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
                      << ", sample_count=" << sample_count_ << std::endl;
        }
        exec_count++;

        if (is_recording_ && !signal_data_.empty()) {
            Sample sample;
            sample.timestamp = std::chrono::system_clock::now();
            sample.data = signal_data_;
            sample.class_name = current_class_name_;
            sample.class_id = current_class_id_;

            samples_.push_back(sample);
            sample_count_ = static_cast<int>(samples_.size());

            if (sample_count_ >= max_samples_) {
                std::cout << "Max samples reached, stopping recording" << std::endl;
                StopRecording();
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
        sample_count_ = 0;
        is_recording_ = true;
        std::cout << "Recording started" << std::endl;
    }

    void StopRecording() {
        is_recording_ = false;
        std::cout << "Recording stopped with " << sample_count_ << " samples" << std::endl;

        if (!samples_.empty()) {
            if (output_format_ == "csv") {
                SaveAsCSV();
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
