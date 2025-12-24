#pragma once

#include "block_interface.hpp"
using namespace CiraBlockRuntime;
#include <string>
#include <cstdint>

/**
 * @brief BME280 Environmental Sensor Block
 *
 * Reads temperature, humidity, and pressure from BME280 sensor via I2C.
 *
 * Block ID: bme280-sensor
 * Version: 1.0.0
 *
 * Inputs:
 *   - None (sensor reads automatically)
 *
 * Outputs:
 *   - temperature (float): Temperature in Celsius
 *   - humidity (float): Relative humidity in %
 *   - pressure (float): Atmospheric pressure in hPa
 */
class BME280Block : public IBlock {
public:
    BME280Block();
    ~BME280Block() override;

    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    std::string GetBlockId() const override { return "bme280-sensor"; }
    std::string GetBlockVersion() const override { return "1.0.0"; }
    std::string GetBlockType() const override { return "sensor"; }

    std::vector<Pin> GetInputPins() const override;
    std::vector<Pin> GetOutputPins() const override;

    void SetInput(const std::string& pin_name, const BlockValue& value) override;
    BlockValue GetOutput(const std::string& pin_name) const override;

private:
    // Configuration
    std::string i2c_device_;
    uint8_t i2c_address_;

    // Output values
    float temperature_;
    float humidity_;
    float pressure_;

    // I2C file descriptor
    int i2c_fd_;
    bool is_initialized_;

    // Hardware interface
    bool OpenI2C();
    void CloseI2C();
    bool ReadSensor();
};

// Block factory functions
extern "C" {
    IBlock* CreateBlock();
    void DestroyBlock(IBlock* block);
}
