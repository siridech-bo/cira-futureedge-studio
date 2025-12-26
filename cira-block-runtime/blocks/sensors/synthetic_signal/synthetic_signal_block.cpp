#include "../../../include/block_interface.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <cstring>
#include <vector>
#include <map>
#include <algorithm>
#include <cmath>

// JSON parsing
#include <nlohmann/json.hpp>

#ifndef _WIN32
// For file format detection and loading
#include <sys/stat.h>
#endif

namespace CiraBlockRuntime {

// Helper struct to store dataset information
struct DatasetClass {
    std::string name;
    std::vector<std::vector<float>> samples;  // Each sample is a multi-channel data point
    size_t current_index;

    DatasetClass() : current_index(0) {}
};

class SyntheticSignalBlock : public IBlock {
public:
    SyntheticSignalBlock()
        : num_channels_(3)
        , sample_rate_(100.0f)
        , loop_mode_(true)
        , current_class_index_(0)
        , is_playing_(false)
        , sequential_mode_(true)
        , signal_type_("dataset")
        , frequency_(1.0f)
        , amplitude_(1.0f)
        , offset_(0.0f)
        , phase_(0.0f)
        , time_(0.0f)
    {
        std::cout << "SyntheticSignalBlock constructor called" << std::endl;
    }

    ~SyntheticSignalBlock() {
        Shutdown();
    }

    bool Initialize(const BlockConfig& config) override {
        std::cout << "SyntheticSignalBlock::Initialize()" << std::endl;

        // Store config for later use
        config_ = config;

        // Parse configuration
        // NEW: Support signal generation mode
        if (config.count("signal_type")) {
            signal_type_ = config.at("signal_type");
        }

        if (config.count("frequency")) {
            frequency_ = std::stof(config.at("frequency"));
        }

        if (config.count("amplitude")) {
            amplitude_ = std::stof(config.at("amplitude"));
        }

        if (config.count("offset")) {
            offset_ = std::stof(config.at("offset"));
        }

        if (config.count("phase")) {
            phase_ = std::stof(config.at("phase"));
        }

        // Support inline dataset (no file upload needed!)
        if (config.count("dataset_inline")) {
            inline_dataset_ = config.at("dataset_inline");
            std::cout << "  Using inline embedded dataset (" << inline_dataset_.size() << " bytes)" << std::endl;
        } else if (config.count("dataset_path")) {
            dataset_path_ = config.at("dataset_path");
            std::cout << "  Dataset Path: " << dataset_path_ << std::endl;
        }

        if (config.count("sample_rate")) {
            sample_rate_ = std::stof(config.at("sample_rate"));
        }

        if (config.count("num_channels")) {
            num_channels_ = std::stoul(config.at("num_channels"));
        }

        if (config.count("loop_mode")) {
            loop_mode_ = (config.at("loop_mode") == "true" || config.at("loop_mode") == "1");
        }

        if (config.count("sequential_mode")) {
            sequential_mode_ = (config.at("sequential_mode") == "true" || config.at("sequential_mode") == "1");
        }

        if (config.count("selected_classes")) {
            std::string classes_str = config.at("selected_classes");
            std::istringstream iss(classes_str);
            std::string class_name;
            while (std::getline(iss, class_name, ',')) {
                selected_classes_.push_back(class_name);
            }
        }

        std::cout << "  Sample Rate: " << sample_rate_ << " Hz" << std::endl;
        std::cout << "  Loop Mode: " << (loop_mode_ ? "enabled" : "disabled") << std::endl;
        std::cout << "  Sequential Mode: " << (sequential_mode_ ? "enabled" : "disabled") << std::endl;

        // Choose mode: Signal Generation OR Dataset Replay
        if (!signal_type_.empty() && signal_type_ != "dataset") {
            // Signal generation mode
            std::cout << "  Mode: Signal Generation" << std::endl;
            std::cout << "  Signal Type: " << signal_type_ << std::endl;
            std::cout << "  Frequency: " << frequency_ << " Hz" << std::endl;
            std::cout << "  Amplitude: " << amplitude_ << std::endl;
            std::cout << "  Offset: " << offset_ << std::endl;
            std::cout << "  Channels: " << num_channels_ << std::endl;

            // Initialize output buffer
            current_output_.resize(num_channels_, 0.0f);

            std::cout << "✓ SyntheticSignalBlock initialized in signal generation mode" << std::endl;
        } else {
            // Dataset replay mode
            std::cout << "  Mode: Dataset Replay" << std::endl;

            if (!LoadDataset()) {
                std::cerr << "ERROR: Failed to load dataset" << std::endl;
                return false;
            }

            std::cout << "✓ SyntheticSignalBlock initialized with " << num_channels_ << " channels" << std::endl;
            std::cout << "  Loaded " << classes_.size() << " classes:" << std::endl;
            for (const auto& cls : classes_) {
                std::cout << "    - " << cls.name << ": " << cls.samples.size() << " samples" << std::endl;
            }
        }

        is_playing_ = true;
        return true;
    }

    std::string GetBlockId() const override {
        return "synthetic-signal-generator";
    }

    std::string GetBlockVersion() const override {
        return "1.0.0";
    }

    std::string GetBlockType() const override {
        return "sensor";
    }

    std::vector<Pin> GetInputPins() const override {
        return {
            Pin("play", "bool", true),      // Control playback
            Pin("reset", "bool", true),     // Reset to beginning
            Pin("next_class", "bool", true) // Skip to next class
        };
    }

    std::vector<Pin> GetOutputPins() const override {
        std::vector<Pin> pins;

        // Dynamic output pins based on number of channels
        for (size_t i = 0; i < num_channels_; ++i) {
            pins.push_back(Pin("channel_" + std::to_string(i), "float", false));
        }

        // Additional output: current class name
        pins.push_back(Pin("class_name", "string", false));

        return pins;
    }

    void SetInput(const std::string& pin_name, const BlockValue& value) override {
        if (pin_name == "play") {
            if (std::holds_alternative<bool>(value)) {
                is_playing_ = std::get<bool>(value);
            } else if (std::holds_alternative<int>(value)) {
                is_playing_ = (std::get<int>(value) != 0);
            }
        } else if (pin_name == "reset") {
            if (std::holds_alternative<bool>(value) && std::get<bool>(value)) {
                ResetPlayback();
            } else if (std::holds_alternative<int>(value) && std::get<int>(value) != 0) {
                ResetPlayback();
            }
        } else if (pin_name == "next_class") {
            if (std::holds_alternative<bool>(value) && std::get<bool>(value)) {
                NextClass();
            } else if (std::holds_alternative<int>(value) && std::get<int>(value) != 0) {
                NextClass();
            }
        }
    }

    bool Execute() override {
        if (!is_playing_) {
            return true;  // Idle state
        }

        // NEW: Signal generation mode
        if (!signal_type_.empty() && signal_type_ != "dataset") {
            GenerateSignalSample();
            return true;
        }

        // Dataset replay mode
        if (classes_.empty()) {
            return true;  // No dataset loaded
        }

        // Get current class
        DatasetClass& current_class = classes_[current_class_index_];

        // Check if we've reached the end of current class
        if (current_class.current_index >= current_class.samples.size()) {
            if (sequential_mode_) {
                // Move to next class
                current_class.current_index = 0;
                current_class_index_ = (current_class_index_ + 1) % classes_.size();
                current_class = classes_[current_class_index_];
            } else if (loop_mode_) {
                // Loop current class
                current_class.current_index = 0;
            } else {
                // Stop playback
                is_playing_ = false;
                return true;
            }
        }

        // Get current sample
        const std::vector<float>& sample = current_class.samples[current_class.current_index];

        // Update output values
        current_output_.clear();
        for (size_t i = 0; i < num_channels_ && i < sample.size(); ++i) {
            current_output_.push_back(sample[i]);
        }

        // Pad with zeros if sample has fewer channels than expected
        while (current_output_.size() < num_channels_) {
            current_output_.push_back(0.0f);
        }

        current_class_name_ = current_class.name;

        // Advance to next sample
        current_class.current_index++;

        return true;
    }

    BlockValue GetOutput(const std::string& pin_name) const override {
        if (pin_name == "class_name") {
            return current_class_name_;
        }

        // Check for channel outputs
        if (pin_name.substr(0, 8) == "channel_") {
            size_t channel_idx = std::stoul(pin_name.substr(8));
            if (channel_idx < current_output_.size()) {
                return current_output_[channel_idx];
            }
        }

        return 0.0f;
    }

    void Shutdown() override {
        is_playing_ = false;
        classes_.clear();
        current_output_.clear();
        std::cout << "SyntheticSignalBlock shutdown" << std::endl;
    }

private:
    bool LoadDataset() {
        // NEW: Check for inline dataset first (no file I/O needed!)
        if (!inline_dataset_.empty()) {
            return LoadInlineDataset();
        }

        // Fall back to file loading
        std::string ext = GetFileExtension(dataset_path_);

        if (ext == ".json") {
            return LoadJSON();
        } else if (ext == ".cbor") {
            return LoadCBOR();
        } else if (ext == ".csv") {
            return LoadCSV();
        } else if (ext == ".npy") {
            return LoadNPY();
        } else if (ext == ".mat") {
            return LoadMAT();
        } else {
            std::cerr << "ERROR: Unsupported file format: " << ext << std::endl;
            return false;
        }
    }

    bool LoadInlineDataset() {
        try {
            nlohmann::json j = nlohmann::json::parse(inline_dataset_);

            // Parse same as LoadJSON() but from string instead of file
            if (j.contains("sample_rate")) {
                sample_rate_ = j["sample_rate"].get<float>();
            }

            if (j.contains("channels")) {
                auto channels = j["channels"];
                num_channels_ = channels.size();
            }

            if (!j.contains("classes")) {
                std::cerr << "ERROR: Inline dataset does not contain 'classes' field" << std::endl;
                return false;
            }

            auto classes_json = j["classes"];
            for (auto it = classes_json.begin(); it != classes_json.end(); ++it) {
                DatasetClass cls;
                cls.name = it.key();

                auto samples = it.value();
                for (const auto& sample : samples) {
                    std::vector<float> sample_data;
                    for (const auto& val : sample) {
                        sample_data.push_back(val.get<float>());
                    }

                    if (num_channels_ == 0 && !sample_data.empty()) {
                        num_channels_ = sample_data.size();
                    }

                    cls.samples.push_back(sample_data);
                }

                if (selected_classes_.empty() ||
                    std::find(selected_classes_.begin(), selected_classes_.end(), cls.name) != selected_classes_.end()) {
                    classes_.push_back(cls);
                }
            }

            return !classes_.empty();
        } catch (const std::exception& e) {
            std::cerr << "ERROR: Inline dataset parsing failed: " << e.what() << std::endl;
            return false;
        }
    }

    std::string GetFileExtension(const std::string& path) const {
        size_t dot_pos = path.find_last_of('.');
        if (dot_pos == std::string::npos) {
            return "";
        }
        std::string ext = path.substr(dot_pos);
        std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
        return ext;
    }

    bool LoadJSON() {
        try {
            std::ifstream file(dataset_path_);
            if (!file.is_open()) {
                std::cerr << "ERROR: Failed to open JSON file: " << dataset_path_ << std::endl;
                return false;
            }

            nlohmann::json j;
            file >> j;
            file.close();

            // Parse sample rate if present
            if (j.contains("sample_rate")) {
                sample_rate_ = j["sample_rate"].get<float>();
            }

            // Parse channel names if present
            if (j.contains("channels")) {
                auto channels = j["channels"];
                num_channels_ = channels.size();
            }

            // Parse classes
            if (!j.contains("classes")) {
                std::cerr << "ERROR: JSON does not contain 'classes' field" << std::endl;
                return false;
            }

            auto classes_json = j["classes"];
            for (auto it = classes_json.begin(); it != classes_json.end(); ++it) {
                DatasetClass cls;
                cls.name = it.key();

                auto samples = it.value();
                for (const auto& sample : samples) {
                    std::vector<float> sample_data;
                    for (const auto& val : sample) {
                        sample_data.push_back(val.get<float>());
                    }

                    // Infer number of channels from first sample if not set
                    if (num_channels_ == 0 && !sample_data.empty()) {
                        num_channels_ = sample_data.size();
                    }

                    cls.samples.push_back(sample_data);
                }

                // Filter by selected classes if specified
                if (selected_classes_.empty() ||
                    std::find(selected_classes_.begin(), selected_classes_.end(), cls.name) != selected_classes_.end()) {
                    classes_.push_back(cls);
                }
            }

            return !classes_.empty();
        } catch (const std::exception& e) {
            std::cerr << "ERROR: JSON parsing failed: " << e.what() << std::endl;
            return false;
        }
    }

    bool LoadCBOR() {
        try {
            std::ifstream file(dataset_path_, std::ios::binary);
            if (!file.is_open()) {
                std::cerr << "ERROR: Failed to open CBOR file: " << dataset_path_ << std::endl;
                return false;
            }

            std::vector<uint8_t> cbor_data((std::istreambuf_iterator<char>(file)),
                                           std::istreambuf_iterator<char>());
            file.close();

            nlohmann::json j = nlohmann::json::from_cbor(cbor_data);

            // Parse same as JSON
            if (j.contains("sample_rate")) {
                sample_rate_ = j["sample_rate"].get<float>();
            }

            if (j.contains("channels")) {
                auto channels = j["channels"];
                num_channels_ = channels.size();
            }

            if (!j.contains("classes")) {
                std::cerr << "ERROR: CBOR does not contain 'classes' field" << std::endl;
                return false;
            }

            auto classes_json = j["classes"];
            for (auto it = classes_json.begin(); it != classes_json.end(); ++it) {
                DatasetClass cls;
                cls.name = it.key();

                auto samples = it.value();
                for (const auto& sample : samples) {
                    std::vector<float> sample_data;
                    for (const auto& val : sample) {
                        sample_data.push_back(val.get<float>());
                    }

                    if (num_channels_ == 0 && !sample_data.empty()) {
                        num_channels_ = sample_data.size();
                    }

                    cls.samples.push_back(sample_data);
                }

                if (selected_classes_.empty() ||
                    std::find(selected_classes_.begin(), selected_classes_.end(), cls.name) != selected_classes_.end()) {
                    classes_.push_back(cls);
                }
            }

            return !classes_.empty();
        } catch (const std::exception& e) {
            std::cerr << "ERROR: CBOR parsing failed: " << e.what() << std::endl;
            return false;
        }
    }

    bool LoadCSV() {
        std::ifstream file(dataset_path_);
        if (!file.is_open()) {
            std::cerr << "ERROR: Failed to open CSV file: " << dataset_path_ << std::endl;
            return false;
        }

        std::string line;
        bool header_parsed = false;
        std::map<std::string, DatasetClass> class_map;

        while (std::getline(file, line)) {
            if (line.empty()) continue;

            std::istringstream iss(line);
            std::string token;
            std::vector<std::string> tokens;

            while (std::getline(iss, token, ',')) {
                tokens.push_back(token);
            }

            if (!header_parsed) {
                // First line is header - determine number of channels
                // Expected format: class,channel_0,channel_1,...,channel_N
                if (tokens.size() < 2) {
                    std::cerr << "ERROR: Invalid CSV header format" << std::endl;
                    return false;
                }
                num_channels_ = tokens.size() - 1;  // Exclude class column
                header_parsed = true;
                continue;
            }

            // Parse data line
            if (tokens.size() < num_channels_ + 1) {
                continue;  // Skip invalid lines
            }

            std::string class_name = tokens[0];
            std::vector<float> sample_data;

            for (size_t i = 1; i < tokens.size(); ++i) {
                try {
                    sample_data.push_back(std::stof(tokens[i]));
                } catch (...) {
                    sample_data.push_back(0.0f);
                }
            }

            class_map[class_name].name = class_name;
            class_map[class_name].samples.push_back(sample_data);
        }

        file.close();

        // Convert map to vector
        for (auto& pair : class_map) {
            if (selected_classes_.empty() ||
                std::find(selected_classes_.begin(), selected_classes_.end(), pair.first) != selected_classes_.end()) {
                classes_.push_back(pair.second);
            }
        }

        return !classes_.empty();
    }

    bool LoadNPY() {
        std::cerr << "ERROR: NPY format not yet implemented" << std::endl;
        // TODO: Implement NPY parser
        return false;
    }

    bool LoadMAT() {
        std::cerr << "ERROR: MAT format not yet implemented" << std::endl;
        // TODO: Implement MAT parser (requires matio library)
        return false;
    }

    void ResetPlayback() {
        current_class_index_ = 0;
        for (auto& cls : classes_) {
            cls.current_index = 0;
        }
        std::cout << "Playback reset" << std::endl;
    }

    void NextClass() {
        if (!classes_.empty()) {
            classes_[current_class_index_].current_index = 0;
            current_class_index_ = (current_class_index_ + 1) % classes_.size();
            std::cout << "Switched to class: " << classes_[current_class_index_].name << std::endl;
        }
    }

    // NEW: Signal generation functions
    void GenerateSignalSample() {
        if (signal_type_ == "sine") {
            GenerateSine();
        } else if (signal_type_ == "square") {
            GenerateSquare();
        } else if (signal_type_ == "triangular" || signal_type_ == "triangle") {
            GenerateTriangular();
        } else if (signal_type_ == "sawtooth") {
            GenerateSawtooth();
        } else if (signal_type_ == "noise") {
            GenerateNoise();
        } else if (signal_type_ == "constant") {
            GenerateConstant();
        } else {
            // Unknown signal type, generate zeros
            for (size_t i = 0; i < num_channels_; ++i) {
                current_output_[i] = 0.0f;
            }
        }

        // Update time
        time_ += 1.0f / sample_rate_;
    }

    void GenerateSine() {
        float value = amplitude_ * std::sin(2.0f * M_PI * frequency_ * time_ + phase_) + offset_;
        for (size_t i = 0; i < num_channels_; ++i) {
            current_output_[i] = value;
        }
    }

    void GenerateSquare() {
        float phase_value = std::fmod(frequency_ * time_ + phase_ / (2.0f * M_PI), 1.0f);
        float value = (phase_value < 0.5f) ? amplitude_ : -amplitude_;
        value += offset_;
        for (size_t i = 0; i < num_channels_; ++i) {
            current_output_[i] = value;
        }
    }

    void GenerateTriangular() {
        float phase_value = std::fmod(frequency_ * time_ + phase_ / (2.0f * M_PI), 1.0f);
        float value = amplitude_ * (2.0f * std::abs(2.0f * phase_value - 1.0f) - 1.0f) + offset_;
        for (size_t i = 0; i < num_channels_; ++i) {
            current_output_[i] = value;
        }
    }

    void GenerateSawtooth() {
        float phase_value = std::fmod(frequency_ * time_ + phase_ / (2.0f * M_PI), 1.0f);
        float value = amplitude_ * (2.0f * phase_value - 1.0f) + offset_;
        for (size_t i = 0; i < num_channels_; ++i) {
            current_output_[i] = value;
        }
    }

    void GenerateNoise() {
        for (size_t i = 0; i < num_channels_; ++i) {
            // Generate random noise between -amplitude and +amplitude
            float random = static_cast<float>(rand()) / static_cast<float>(RAND_MAX);
            current_output_[i] = (2.0f * random - 1.0f) * amplitude_ + offset_;
        }
    }

    void GenerateConstant() {
        for (size_t i = 0; i < num_channels_; ++i) {
            current_output_[i] = amplitude_ + offset_;
        }
    }

    // Member variables
    BlockConfig config_;               // Store config for reference
    std::string dataset_path_;
    std::string inline_dataset_;       // Inline embedded dataset (JSON string)

    // Signal generation parameters
    std::string signal_type_;          // "sine", "square", "triangular", "sawtooth", "noise", "constant", "dataset"
    float frequency_;                  // Frequency in Hz (for periodic signals)
    float amplitude_;                  // Amplitude/peak value
    float offset_;                     // DC offset
    float phase_;                      // Phase offset in radians
    float time_;                       // Current time for signal generation

    float sample_rate_;
    bool loop_mode_;
    bool sequential_mode_;
    bool is_playing_;

    size_t num_channels_;
    std::vector<std::string> selected_classes_;

    std::vector<DatasetClass> classes_;
    size_t current_class_index_;

    std::vector<float> current_output_;
    std::string current_class_name_;
};

} // namespace CiraBlockRuntime

// Export factory functions (C linkage for dlopen)
extern "C" {
    CiraBlockRuntime::IBlock* CreateBlock() {
        return new CiraBlockRuntime::SyntheticSignalBlock();
    }

    void DestroyBlock(CiraBlockRuntime::IBlock* block) {
        delete block;
    }
}
