#include "low_pass_filter_block.hpp"
#include <iostream>

using namespace CiraBlockRuntime;

LowPassFilterBlock::LowPassFilterBlock()
    : alpha_(0.1f), input_(0.0f), output_(0.0f), prev_output_(0.0f) {}

bool LowPassFilterBlock::Initialize(const BlockConfig& config) {
    if (config.find("alpha") != config.end()) {
        alpha_ = std::stof(config.at("alpha"));
    }
    std::cout << "[Low Pass Filter] Initialized with alpha=" << alpha_ << std::endl;
    return true;
}

bool LowPassFilterBlock::Execute() {
    output_ = alpha_ * input_ + (1.0f - alpha_) * prev_output_;
    prev_output_ = output_;
    return true;
}

void LowPassFilterBlock::Shutdown() {}

std::vector<Pin> LowPassFilterBlock::GetInputPins() const {
    return {Pin("input", "float", true)};
}

std::vector<Pin> LowPassFilterBlock::GetOutputPins() const {
    return {Pin("output", "float", false)};
}

void LowPassFilterBlock::SetInput(const std::string& pin_name, const BlockValue& value) {
    if (pin_name == "input") input_ = std::get<float>(value);
}

BlockValue LowPassFilterBlock::GetOutput(const std::string& pin_name) const {
    return output_;
}

extern "C" {
    IBlock* CreateBlock() { return new LowPassFilterBlock(); }
    void DestroyBlock(IBlock* block) { delete block; }
}
