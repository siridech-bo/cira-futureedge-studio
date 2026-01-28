#pragma once

#include "block_interface.hpp"
using namespace CiraBlockRuntime;
#include <string>
#include <cstdint>

/**
 * @brief Analog Input Block
 *
 * Reads analog input from ADC pin.
 *
 * Block ID: analog-input
 * Version: 1.0.0
 *
 * Inputs:
 *   - None (reads from hardware)
 *
 * Outputs:
 *   - value (float): Analog value (0.0 - 1.0 normalized)
 *   - raw (int): Raw ADC value
 */
class AnalogInputBlock : public IBlock {
public:
    AnalogInputBlock();
    ~AnalogInputBlock() override;

    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    std::string GetBlockId() const override { return "analog-input"; }
    std::string GetBlockVersion() const override { return "1.0.0"; }
    std::string GetBlockType() const override { return "sensor"; }

    std::vector<Pin> GetInputPins() const override;
    std::vector<Pin> GetOutputPins() const override;

    void SetInput(const std::string& pin_name, const BlockValue& value) override;
    BlockValue GetOutput(const std::string& pin_name) const override;

private:
    // Configuration
    int adc_channel_;
    std::string adc_device_;
    int adc_max_value_;  // Max ADC value (e.g., 1023 for 10-bit, 4095 for 12-bit)

    // Output values
    float value_;
    int raw_value_;

    bool is_initialized_;

    // Hardware interface
    bool ReadADC();
};

// Block factory functions
extern "C" {
    IBlock* CreateBlock();
    void DestroyBlock(IBlock* block);
}
