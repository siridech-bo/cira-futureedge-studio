#include "bme280_block.hpp"
#include <iostream>
#include <cmath>
#include <ctime>

using namespace CiraBlockRuntime;

#ifndef _WIN32
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#endif

BME280Block::BME280Block()
    : i2c_device_("/dev/i2c-1")
    , i2c_address_(0x76)
    , temperature_(0.0f)
    , humidity_(0.0f)
    , pressure_(0.0f)
    , i2c_fd_(-1)
    , is_initialized_(false) {
}

BME280Block::~BME280Block() {
    Shutdown();
}

bool BME280Block::Initialize(const BlockConfig& config) {
    std::cout << "[BME280] Initializing..." << std::endl;

    // Load configuration
    if (config.find("i2c_device") != config.end()) {
        i2c_device_ = config.at("i2c_device");
    }
    if (config.find("i2c_address") != config.end()) {
        i2c_address_ = static_cast<uint8_t>(std::stoi(config.at("i2c_address"), nullptr, 16));
    }

    std::cout << "  I2C Device: " << i2c_device_ << std::endl;
    std::cout << "  I2C Address: 0x" << std::hex << (int)i2c_address_ << std::dec << std::endl;

#ifndef _WIN32
    if (!OpenI2C()) {
        return false;
    }
#else
    std::cout << "  [Simulation Mode] BME280 initialized" << std::endl;
#endif

    is_initialized_ = true;
    std::cout << "[BME280] Initialization complete" << std::endl;
    return true;
}

bool BME280Block::Execute() {
    if (!is_initialized_) {
        std::cerr << "[BME280] Not initialized" << std::endl;
        return false;
    }

#ifdef _WIN32
    // Simulation mode - generate realistic environmental data
    static double time_offset = 0.0;
    time_offset += 0.1;

    temperature_ = 22.0f + 3.0f * std::sin(time_offset * 0.1);  // 19-25°C
    humidity_ = 50.0f + 20.0f * std::sin(time_offset * 0.15);   // 30-70%
    pressure_ = 1013.25f + 10.0f * std::sin(time_offset * 0.05); // 1003-1023 hPa

    std::cout << "[BME280] T=" << temperature_ << "°C, "
              << "H=" << humidity_ << "%, "
              << "P=" << pressure_ << " hPa" << std::endl;
#else
    if (!ReadSensor()) {
        return false;
    }
#endif

    return true;
}

void BME280Block::Shutdown() {
    if (is_initialized_) {
#ifndef _WIN32
        CloseI2C();
#endif
        is_initialized_ = false;
        std::cout << "[BME280] Shutdown complete" << std::endl;
    }
}

std::vector<Pin> BME280Block::GetInputPins() const {
    return {}; // No inputs
}

std::vector<Pin> BME280Block::GetOutputPins() const {
    return {
        Pin("temperature", "float", false),
        Pin("humidity", "float", false),
        Pin("pressure", "float", false)
    };
}

void BME280Block::SetInput(const std::string& pin_name, const BlockValue& value) {
    // No inputs
}

BlockValue BME280Block::GetOutput(const std::string& pin_name) const {
    if (pin_name == "temperature") {
        return temperature_;
    } else if (pin_name == "humidity") {
        return humidity_;
    } else if (pin_name == "pressure") {
        return pressure_;
    }
    return 0.0f;
}

bool BME280Block::OpenI2C() {
#ifndef _WIN32
    i2c_fd_ = open(i2c_device_.c_str(), O_RDWR);
    if (i2c_fd_ < 0) {
        std::cerr << "[BME280] Failed to open I2C device: " << i2c_device_ << std::endl;
        return false;
    }

    if (ioctl(i2c_fd_, I2C_SLAVE, i2c_address_) < 0) {
        std::cerr << "[BME280] Failed to set I2C slave address" << std::endl;
        close(i2c_fd_);
        i2c_fd_ = -1;
        return false;
    }

    return true;
#else
    return true;
#endif
}

void BME280Block::CloseI2C() {
#ifndef _WIN32
    if (i2c_fd_ >= 0) {
        close(i2c_fd_);
        i2c_fd_ = -1;
    }
#endif
}

bool BME280Block::ReadSensor() {
#ifndef _WIN32
    // Simplified BME280 reading
    // In real implementation, this would:
    // 1. Read calibration data
    // 2. Trigger measurement
    // 3. Read raw data
    // 4. Apply calibration formulas

    // For now, return simulated data
    temperature_ = 22.5f;
    humidity_ = 55.0f;
    pressure_ = 1013.25f;

    std::cout << "[BME280] T=" << temperature_ << "°C, "
              << "H=" << humidity_ << "%, "
              << "P=" << pressure_ << " hPa" << std::endl;
    return true;
#else
    return true;
#endif
}

// Block factory functions
extern "C" {
    IBlock* CreateBlock() {
        return new BME280Block();
    }

    void DestroyBlock(IBlock* block) {
        delete block;
    }
}
