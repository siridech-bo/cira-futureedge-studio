#pragma once

#include "block_interface.hpp"
using namespace CiraBlockRuntime;

/**
 * @brief Normalize Block
 *
 * Normalizes input values to a specified range.
 *
 * Block ID: normalize
 * Version: 1.0.0
 *
 * Inputs:
 *   - input (float): Input value to normalize
 *
 * Outputs:
 *   - output (float): Normalized output value
 */
class NormalizeBlock : public IBlock {
public:
    NormalizeBlock();
    ~NormalizeBlock() override = default;

    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    std::string GetBlockId() const override { return "normalize"; }
    std::string GetBlockVersion() const override { return "1.0.0"; }
    std::string GetBlockType() const override { return "processing"; }

    std::vector<Pin> GetInputPins() const override;
    std::vector<Pin> GetOutputPins() const override;

    void SetInput(const std::string& pin_name, const BlockValue& value) override;
    BlockValue GetOutput(const std::string& pin_name) const override;

private:
    // Configuration
    float input_min_;
    float input_max_;
    float output_min_;
    float output_max_;

    // Values
    float input_;
    float output_;
};

extern "C" {
    IBlock* CreateBlock();
    void DestroyBlock(IBlock* block);
}
