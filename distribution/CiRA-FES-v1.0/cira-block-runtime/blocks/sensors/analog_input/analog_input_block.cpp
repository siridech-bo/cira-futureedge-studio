#include "analog_input_block.hpp"
#include <iostream>
#include <fstream>
#include <cmath>

using namespace CiraBlockRuntime;

AnalogInputBlock::AnalogInputBlock()
    : adc_channel_(0)
    , adc_device_("/sys/bus/iio/devices/iio:device0")
    , adc_max_value_(4095)  // 12-bit ADC
    , value_(0.0f)
    , raw_value_(0)
    , is_initialized_(false) {
}

AnalogInputBlock::~AnalogInputBlock() {
    Shutdown();
}

bool AnalogInputBlock::Initialize(const BlockConfig& config) {
    std::cout << "[Analog Input] Initializing..." << std::endl;

    // Load configuration
    if (config.find("adc_channel") != config.end()) {
        adc_channel_ = std::stoi(config.at("adc_channel"));
    }
    if (config.find("adc_device") != config.end()) {
        adc_device_ = config.at("adc_device");
    }
    if (config.find("adc_max_value") != config.end()) {
        adc_max_value_ = std::stoi(config.at("adc_max_value"));
    }

    std::cout << "  ADC Channel: " << adc_channel_ << std::endl;
    std::cout << "  ADC Device: " << adc_device_ << std::endl;
    std::cout << "  Max Value: " << adc_max_value_ << std::endl;

#ifdef _WIN32
    std::cout << "  [Simulation Mode] Analog input initialized" << std::endl;
#endif

    is_initialized_ = true;
    std::cout << "[Analog Input] Initialization complete" << std::endl;
    return true;
}

bool AnalogInputBlock::Execute() {
    if (!is_initialized_) {
        std::cerr << "[Analog Input] Not initialized" << std::endl;
        return false;
    }

#ifdef _WIN32
    // Simulation mode - generate realistic analog signal
    static double time_offset = 0.0;
    time_offset += 0.05;

    // Simulate varying analog input (e.g., potentiometer or sensor)
    raw_value_ = static_cast<int>(adc_max_value_ * 0.5 * (1.0 + 0.8 * std::sin(time_offset)));
    value_ = static_cast<float>(raw_value_) / adc_max_value_;

    std::cout << "[Analog Input] Channel " << adc_channel_ << ": "
              << value_ << " (" << raw_value_ << "/" << adc_max_value_ << ")" << std::endl;
#else
    if (!ReadADC()) {
        return false;
    }
#endif

    return true;
}

void AnalogInputBlock::Shutdown() {
    if (is_initialized_) {
        is_initialized_ = false;
        std::cout << "[Analog Input] Shutdown complete" << std::endl;
    }
}

std::vector<Pin> AnalogInputBlock::GetInputPins() const {
    return {}; // No inputs
}

std::vector<Pin> AnalogInputBlock::GetOutputPins() const {
    return {
        Pin("value", "float", false),
        Pin("raw", "int", false)
    };
}

void AnalogInputBlock::SetInput(const std::string& pin_name, const BlockValue& value) {
    // No inputs
}

BlockValue AnalogInputBlock::GetOutput(const std::string& pin_name) const {
    if (pin_name == "value") {
        return value_;
    } else if (pin_name == "raw") {
        return raw_value_;
    }
    return 0.0f;
}

bool AnalogInputBlock::ReadADC() {
#ifndef _WIN32
    // Read from sysfs ADC interface (Linux IIO subsystem)
    std::string adc_path = adc_device_ + "/in_voltage" + std::to_string(adc_channel_) + "_raw";

    std::ifstream adc_file(adc_path);
    if (!adc_file.is_open()) {
        std::cerr << "[Analog Input] Failed to open ADC device: " << adc_path << std::endl;
        return false;
    }

    adc_file >> raw_value_;
    adc_file.close();

    value_ = static_cast<float>(raw_value_) / adc_max_value_;

    std::cout << "[Analog Input] Channel " << adc_channel_ << ": "
              << value_ << " (" << raw_value_ << "/" << adc_max_value_ << ")" << std::endl;
    return true;
#else
    return true;
#endif
}

// Block factory functions
extern "C" {
    IBlock* CreateBlock() {
        return new AnalogInputBlock();
    }

    void DestroyBlock(IBlock* block) {
        delete block;
    }
}
