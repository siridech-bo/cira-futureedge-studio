#pragma once

#include "block_interface.hpp"
using namespace CiraBlockRuntime;

class LowPassFilterBlock : public IBlock {
public:
    LowPassFilterBlock();
    ~LowPassFilterBlock() override = default;

    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    std::string GetBlockId() const override { return "low-pass-filter"; }
    std::string GetBlockVersion() const override { return "1.0.0"; }
    std::string GetBlockType() const override { return "processing"; }

    std::vector<Pin> GetInputPins() const override;
    std::vector<Pin> GetOutputPins() const override;

    void SetInput(const std::string& pin_name, const BlockValue& value) override;
    BlockValue GetOutput(const std::string& pin_name) const override;

private:
    float alpha_;
    float input_;
    float output_;
    float prev_output_;
};

extern "C" {
    IBlock* CreateBlock();
    void DestroyBlock(IBlock* block);
}
