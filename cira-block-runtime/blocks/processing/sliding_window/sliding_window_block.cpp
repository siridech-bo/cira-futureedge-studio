#include "../../../include/block_interface.hpp"
#include <iostream>
#include <deque>
#include <vector>

namespace CiraBlockRuntime {

class SlidingWindowBlock : public IBlock {
public:
    SlidingWindowBlock()
        : window_size_(100)
        , step_size_(50)
        , sample_count_(0)
        , window_ready_(false)
        , is_vector_input_(false)
        , vector_size_(1)
        , has_new_input_(false)
    {
        std::cout << "SlidingWindowBlock constructor called" << std::endl;
    }

    bool Initialize(const BlockConfig& config) override {
        std::cout << "SlidingWindowBlock::Initialize()" << std::endl;

        // Parse configuration
        if (config.count("window_size")) {
            window_size_ = std::stoi(config.at("window_size"));
        }
        if (config.count("step_size")) {
            step_size_ = std::stoi(config.at("step_size"));
        }

        std::cout << "  Window size: " << window_size_ << std::endl;
        std::cout << "  Step size: " << step_size_ << std::endl;

        vector_buffer_.clear();
        sample_count_ = 0;
        window_ready_ = false;
        is_vector_input_ = false;
        vector_size_ = 1;

        std::cout << "✓ Sliding Window initialized successfully" << std::endl;
        return true;
    }

    std::string GetBlockId() const override {
        return "sliding-window";
    }

    std::string GetBlockVersion() const override {
        return "1.0.0";
    }

    std::string GetBlockType() const override {
        return "processing";
    }

    std::vector<Pin> GetInputPins() const override {
        return {
            Pin("input", "any", true)
        };
    }

    std::vector<Pin> GetOutputPins() const override {
        return {
            Pin("window_out", "array", false),
            Pin("ready", "bool", false)
        };
    }

    void SetInput(const std::string& pin_name, const BlockValue& value) override {
        if (pin_name == "input") {
            input_value_ = value;
            has_new_input_ = true;  // Mark that we have new data
        }
    }

    bool Execute() override {
        static int exec_count = 0;
        // Log every execution when buffer is close to window_size to see sliding
        if (exec_count % 10 == 0 || vector_buffer_.size() >= static_cast<size_t>(window_size_) - 10) {
            std::cout << "[Sliding Window] Execute() called, vector_buffer_.size()=" << vector_buffer_.size()
                      << ", output_window_.size()=" << output_window_.size()
                      << ", has_new_input_=" << has_new_input_ << std::endl;
        }
        exec_count++;

        // Only process if we have new input data
        if (!has_new_input_) {
            return true;  // Skip processing if no new data
        }
        has_new_input_ = false;  // Reset flag

        // Handle vector input (from Channel Merge)
        if (std::holds_alternative<std::vector<float>>(input_value_)) {
            const auto& vec = std::get<std::vector<float>>(input_value_);

            // Detect vector input mode on first vector
            if (!is_vector_input_ && !vec.empty()) {
                is_vector_input_ = true;
                vector_size_ = vec.size();
                std::cout << "[Sliding Window] Vector input detected, size=" << vector_size_
                          << " (window_size=" << window_size_ << " will buffer "
                          << window_size_ << " vectors = " << (window_size_ * vector_size_) << " floats)" << std::endl;
            }

            // Debug: Log incoming data periodically
            static int input_count = 0;
            if (input_count % 100 == 0 && !vec.empty()) {
                std::cout << "[Sliding Window] Incoming vector [" << input_count << "]: size=" << vec.size()
                          << ", first 3 values: [" << vec[0];
                if (vec.size() > 1) std::cout << ", " << vec[1];
                if (vec.size() > 2) std::cout << ", " << vec[2];
                std::cout << "]" << std::endl;
            }
            input_count++;

            // Store the entire vector as one sample
            vector_buffer_.push_back(vec);
            sample_count_++;
        } else {
            // Convert single value input to float and store as 1-element vector
            float sample = 0.0f;
            if (std::holds_alternative<float>(input_value_)) {
                sample = std::get<float>(input_value_);
            } else if (std::holds_alternative<int>(input_value_)) {
                sample = static_cast<float>(std::get<int>(input_value_));
            } else {
                // For other types, use 0
                sample = 0.0f;
            }

            // Store as single-element vector
            vector_buffer_.push_back({sample});
            sample_count_++;

            if (!is_vector_input_) {
                is_vector_input_ = false;
                vector_size_ = 1;
            }
        }

        // Check if we have enough vector samples (not individual float elements)
        if (vector_buffer_.size() >= static_cast<size_t>(window_size_)) {
            // Window is ready
            window_ready_ = true;

            // Flatten exactly window_size_ vectors into output array
            output_window_.clear();
            for (int i = 0; i < window_size_; i++) {
                const auto& vec = vector_buffer_[i];
                output_window_.insert(output_window_.end(), vec.begin(), vec.end());
            }

            // Debug log
            static int output_count = 0;
            if (output_count % 100 == 0) {
                std::cout << "[Sliding Window] Output window ready: " << window_size_
                          << " vectors × " << vector_size_ << " elements = "
                          << output_window_.size() << " floats" << std::endl;
                // Print first 10 values of the output window
                std::cout << "[Sliding Window] First 10 output values: [";
                for (size_t i = 0; i < std::min(size_t(10), output_window_.size()); i++) {
                    std::cout << output_window_[i];
                    if (i < 9 && i < output_window_.size() - 1) std::cout << ", ";
                }
                std::cout << "]" << std::endl;
            }
            output_count++;

            // Slide the window (remove step_size vector samples from front)
            if (step_size_ > 0 && static_cast<size_t>(step_size_) <= vector_buffer_.size()) {
                vector_buffer_.erase(vector_buffer_.begin(), vector_buffer_.begin() + step_size_);
                // Mark as not ready, but keep output_window_ valid until next window
                window_ready_ = false;
            } else {
                // If step_size >= window_size, clear everything
                vector_buffer_.clear();
                output_window_.clear();
                window_ready_ = false;
            }
        } else {
            // Buffer not full yet - window not ready
            window_ready_ = false;
        }

        return true;
    }

    BlockValue GetOutput(const std::string& pin_name) const override {
        if (pin_name == "window_out") {
            static int get_count = 0;
            if (get_count % 100 == 0) {
                std::cout << "[Sliding Window] GetOutput('window_out') called, returning vector size="
                          << output_window_.size() << ", window_ready=" << window_ready_ << std::endl;
            }
            get_count++;
            return output_window_;
        }
        if (pin_name == "ready") {
            return window_ready_;
        }
        return false;
    }

    void Shutdown() override {
        vector_buffer_.clear();
        output_window_.clear();
        std::cout << "Sliding Window shutdown (processed " << sample_count_ << " samples)" << std::endl;
    }

private:
    int window_size_;
    int step_size_;
    int sample_count_;
    bool window_ready_;
    bool is_vector_input_;
    size_t vector_size_;
    bool has_new_input_;                            // Flag to track if SetInput was called
    std::deque<std::vector<float>> vector_buffer_;  // Buffer of vector samples
    std::vector<float> output_window_;              // Flattened output
    BlockValue input_value_;
};

} // namespace CiraBlockRuntime

// Export factory functions
extern "C" {
    CiraBlockRuntime::IBlock* CreateBlock() {
        return new CiraBlockRuntime::SlidingWindowBlock();
    }

    void DestroyBlock(CiraBlockRuntime::IBlock* block) {
        delete block;
    }
}
