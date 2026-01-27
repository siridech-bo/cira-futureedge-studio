#pragma once

#include "block_interface.hpp"
using namespace CiraBlockRuntime;
#include <string>
#include <memory>
#include <cstdint>

/**
 * @brief OLED Display Block (SSD1306 128x64 I2C)
 *
 * Displays text on an OLED screen via I2C.
 *
 * Block ID: oled-display
 * Version: 1.1.0
 *
 * Inputs:
 *   - text (string): Text to display on screen
 *   - value (float): Numeric value to display
 *
 * Outputs:
 *   - None (visual output only)
 */
class OledDisplayBlock : public IBlock {
public:
    OledDisplayBlock();
    ~OledDisplayBlock() override;

    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    std::string GetBlockId() const override { return "oled-display"; }
    std::string GetBlockVersion() const override { return "1.1.0"; }
    std::string GetBlockType() const override { return "output"; }

    std::vector<Pin> GetInputPins() const override;
    std::vector<Pin> GetOutputPins() const override;

    void SetInput(const std::string& pin_name, const BlockValue& value) override;
    BlockValue GetOutput(const std::string& pin_name) const override;

private:
    // Configuration
    std::string i2c_device_;
    uint8_t i2c_address_;
    int screen_width_;
    int screen_height_;

    // Input values
    std::string text_;
    float value_;

    // I2C file descriptor
    int i2c_fd_;
    bool is_initialized_;

    // Hardware interface methods
    bool OpenI2C();
    void CloseI2C();
    bool InitializeDisplay();
    void ClearDisplay();
    void DisplayText(const std::string& text, int line);
    void DisplayValue(float value, int line);

    // Low-level I2C communication
    bool WriteCommand(uint8_t cmd);
    bool WriteData(uint8_t data);
};

// Block factory functions
extern "C" {
    IBlock* CreateBlock();
    void DestroyBlock(IBlock* block);
}
