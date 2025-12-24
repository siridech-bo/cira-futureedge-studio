#include "../../../include/block_interface.hpp"
#include "../../../include/data_types.hpp"
#include <iostream>

namespace CiraBlockRuntime {

class ChannelMergeBlock : public IBlock {
public:
    ChannelMergeBlock()
        : num_channels_(3)
        , channel_0_(0.0f)
        , channel_1_(0.0f)
        , channel_2_(0.0f)
    {
        std::cout << "ChannelMergeBlock constructor called" << std::endl;
    }

    bool Initialize(const BlockConfig& config) override {
        std::cout << "ChannelMergeBlock::Initialize()" << std::endl;

        // Parse configuration
        if (config.count("num_channels")) {
            num_channels_ = std::stoi(config.at("num_channels"));
        }

        std::cout << "  Number of channels: " << num_channels_ << std::endl;
        std::cout << "✓ Channel Merge initialized successfully" << std::endl;
        return true;
    }

    std::string GetBlockId() const override {
        return "channel-merge";
    }

    std::string GetBlockVersion() const override {
        return "1.0.0";
    }

    std::string GetBlockType() const override {
        return "processing";
    }

    std::vector<Pin> GetInputPins() const override {
        return {
            Pin("channel_0", "float", true),
            Pin("channel_1", "float", true),
            Pin("channel_2", "float", true)
        };
    }

    std::vector<Pin> GetOutputPins() const override {
        return {
            Pin("merged_out", "vector3", false)
        };
    }

    void SetInput(const std::string& pin_name, const BlockValue& value) override {
        if (pin_name == "channel_0" && std::holds_alternative<float>(value)) {
            channel_0_ = std::get<float>(value);
        } else if (pin_name == "channel_1" && std::holds_alternative<float>(value)) {
            channel_1_ = std::get<float>(value);
        } else if (pin_name == "channel_2" && std::holds_alternative<float>(value)) {
            channel_2_ = std::get<float>(value);
        }
    }

    bool Execute() override {
        // Merge channels into Vector3
        merged_output_.x = channel_0_;
        merged_output_.y = channel_1_;
        merged_output_.z = channel_2_;
        return true;
    }

    BlockValue GetOutput(const std::string& pin_name) const override {
        if (pin_name == "merged_out") {
            // Return as vector of floats (since BlockValue doesn't have Vector3)
            std::vector<float> vec = {merged_output_.x, merged_output_.y, merged_output_.z};
            return vec;
        }
        return 0.0f;
    }

    void Shutdown() override {
        std::cout << "Channel Merge shutdown" << std::endl;
    }

private:
    int num_channels_;
    float channel_0_;
    float channel_1_;
    float channel_2_;
    Vector3 merged_output_;
};

} // namespace CiraBlockRuntime

// Export factory functions
extern "C" {
    CiraBlockRuntime::IBlock* CreateBlock() {
        return new CiraBlockRuntime::ChannelMergeBlock();
    }

    void DestroyBlock(CiraBlockRuntime::IBlock* block) {
        delete block;
    }
}
