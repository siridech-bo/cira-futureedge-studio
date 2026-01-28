#pragma once

#include "block_interface.hpp"
using namespace CiraBlockRuntime;
#include <string>
#include <cstdint>

/**
 * @brief GPIO Input Block
 *
 * Reads digital input from GPIO pin.
 *
 * Block ID: gpio-input
 * Version: 1.0.0
 *
 * Inputs:
 *   - None (reads from hardware)
 *
 * Outputs:
 *   - state (bool): GPIO pin state (true = HIGH, false = LOW)
 */
class GPIOInputBlock : public IBlock {
public:
    GPIOInputBlock();
    ~GPIOInputBlock() override;

    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    std::string GetBlockId() const override { return "gpio-input"; }
    std::string GetBlockVersion() const override { return "1.0.0"; }
    std::string GetBlockType() const override { return "sensor"; }

    std::vector<Pin> GetInputPins() const override;
    std::vector<Pin> GetOutputPins() const override;

    void SetInput(const std::string& pin_name, const BlockValue& value) override;
    BlockValue GetOutput(const std::string& pin_name) const override;

private:
    // Configuration
    int gpio_pin_;
    bool pull_up_;

    // Output values
    bool state_;

    // GPIO file descriptor
    int gpio_fd_;
    bool is_initialized_;

    // Hardware interface
    bool InitGPIO();
    void CloseGPIO();
    bool ReadGPIO();
};

// Block factory functions
extern "C" {
    IBlock* CreateBlock();
    void DestroyBlock(IBlock* block);
}
