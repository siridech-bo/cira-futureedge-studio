#include "../../../include/block_interface.hpp"
#include <iostream>
#include <deque>

namespace CiraBlockRuntime {

class SlidingWindowBlock : public IBlock {
public:
    SlidingWindowBlock()
        : window_size_(100)
        , step_size_(50)
        , sample_count_(0)
        , window_ready_(false)
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

        buffer_.clear();
        sample_count_ = 0;
        window_ready_ = false;

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
        }
    }

    bool Execute() override {
        // Convert input to float (handle different types)
        float sample = 0.0f;
        if (std::holds_alternative<float>(input_value_)) {
            sample = std::get<float>(input_value_);
        } else if (std::holds_alternative<int>(input_value_)) {
            sample = static_cast<float>(std::get<int>(input_value_));
        } else {
            // For other types, use 0
            sample = 0.0f;
        }

        // Add sample to buffer
        buffer_.push_back(sample);
        sample_count_++;

        // Check if we have enough samples
        if (buffer_.size() >= window_size_) {
            // Window is ready
            window_ready_ = true;

            // Copy window to output array
            output_window_.clear();
            output_window_.assign(buffer_.begin(), buffer_.end());

            // Slide the window (remove step_size samples from front)
            if (step_size_ > 0 && step_size_ <= buffer_.size()) {
                buffer_.erase(buffer_.begin(), buffer_.begin() + step_size_);
            } else {
                // If step_size >= window_size, clear buffer
                buffer_.clear();
            }
        } else {
            window_ready_ = false;
        }

        return true;
    }

    BlockValue GetOutput(const std::string& pin_name) const override {
        if (pin_name == "window_out") {
            return output_window_;
        }
        if (pin_name == "ready") {
            return window_ready_;
        }
        return false;
    }

    void Shutdown() override {
        buffer_.clear();
        output_window_.clear();
        std::cout << "Sliding Window shutdown (processed " << sample_count_ << " samples)" << std::endl;
    }

private:
    int window_size_;
    int step_size_;
    int sample_count_;
    bool window_ready_;
    std::deque<float> buffer_;
    std::vector<float> output_window_;
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
