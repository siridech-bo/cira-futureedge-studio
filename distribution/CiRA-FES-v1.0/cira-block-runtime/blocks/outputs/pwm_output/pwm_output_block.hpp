#pragma once

#include "block_interface.hpp"
using namespace CiraBlockRuntime;
#include <string>
#include <cstdint>

/**
 * @brief PWM Output Block
 *
 * Outputs PWM signal to control motors, servos, LEDs, etc.
 *
 * Block ID: pwm-output
 * Version: 1.0.0
 *
 * Inputs:
 *   - duty_cycle (float): PWM duty cycle (0.0 - 1.0)
 *
 * Outputs:
 *   - None (hardware output only)
 */
class PWMOutputBlock : public IBlock {
public:
    PWMOutputBlock();
    ~PWMOutputBlock() override;

    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    std::string GetBlockId() const override { return "pwm-output"; }
    std::string GetBlockVersion() const override { return "1.0.0"; }
    std::string GetBlockType() const override { return "output"; }

    std::vector<Pin> GetInputPins() const override;
    std::vector<Pin> GetOutputPins() const override;

    void SetInput(const std::string& pin_name, const BlockValue& value) override;
    BlockValue GetOutput(const std::string& pin_name) const override;

private:
    // Configuration
    int pwm_chip_;
    int pwm_channel_;
    int frequency_;  // PWM frequency in Hz
    std::string pwm_device_;

    // Input values
    float duty_cycle_;

    bool is_initialized_;

    // Hardware interface
    bool InitPWM();
    void ClosePWM();
    bool SetPWMDutyCycle(float duty_cycle);
};

// Block factory functions
extern "C" {
    IBlock* CreateBlock();
    void DestroyBlock(IBlock* block);
}
