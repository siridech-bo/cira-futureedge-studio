#include "normalize_block.hpp"
#include <iostream>
#include <algorithm>

using namespace CiraBlockRuntime;

NormalizeBlock::NormalizeBlock()
    : input_min_(0.0f)
    , input_max_(1.0f)
    , output_min_(0.0f)
    , output_max_(1.0f)
    , input_(0.0f)
    , output_(0.0f) {
}

bool NormalizeBlock::Initialize(const BlockConfig& config) {
    if (config.find("input_min") != config.end()) {
        input_min_ = std::stof(config.at("input_min"));
    }
    if (config.find("input_max") != config.end()) {
        input_max_ = std::stof(config.at("input_max"));
    }
    if (config.find("output_min") != config.end()) {
        output_min_ = std::stof(config.at("output_min"));
    }
    if (config.find("output_max") != config.end()) {
        output_max_ = std::stof(config.at("output_max"));
    }

    std::cout << "[Normalize] Initialized: [" << input_min_ << ", " << input_max_
              << "] -> [" << output_min_ << ", " << output_max_ << "]" << std::endl;
    return true;
}

bool NormalizeBlock::Execute() {
    // Normalize input to [0, 1] range
    float normalized = (input_ - input_min_) / (input_max_ - input_min_);

    // Clamp to [0, 1]
    normalized = std::max(0.0f, std::min(1.0f, normalized));

    // Scale to output range
    output_ = output_min_ + normalized * (output_max_ - output_min_);

    return true;
}

void NormalizeBlock::Shutdown() {}

std::vector<Pin> NormalizeBlock::GetInputPins() const {
    return {Pin("input", "float", true)};
}

std::vector<Pin> NormalizeBlock::GetOutputPins() const {
    return {Pin("output", "float", false)};
}

void NormalizeBlock::SetInput(const std::string& pin_name, const BlockValue& value) {
    if (pin_name == "input") {
        input_ = std::get<float>(value);
    }
}

BlockValue NormalizeBlock::GetOutput(const std::string& pin_name) const {
    return output_;
}

extern "C" {
    IBlock* CreateBlock() { return new NormalizeBlock(); }
    void DestroyBlock(IBlock* block) { delete block; }
}
