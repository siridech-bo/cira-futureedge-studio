#include "gpio_input_block.hpp"
#include <iostream>
#include <fstream>
#include <cmath>

#ifndef _WIN32
#include <fcntl.h>
#include <unistd.h>
#endif

using namespace CiraBlockRuntime;

GPIOInputBlock::GPIOInputBlock()
    : gpio_pin_(17)
    , pull_up_(true)
    , state_(false)
    , gpio_fd_(-1)
    , is_initialized_(false) {
}

GPIOInputBlock::~GPIOInputBlock() {
    Shutdown();
}

bool GPIOInputBlock::Initialize(const BlockConfig& config) {
    std::cout << "[GPIO Input] Initializing..." << std::endl;

    // Load configuration
    if (config.find("gpio_pin") != config.end()) {
        gpio_pin_ = std::stoi(config.at("gpio_pin"));
    }
    if (config.find("pull_up") != config.end()) {
        pull_up_ = (config.at("pull_up") == "true" || config.at("pull_up") == "1");
    }

    std::cout << "  GPIO Pin: " << gpio_pin_ << std::endl;
    std::cout << "  Pull-up: " << (pull_up_ ? "enabled" : "disabled") << std::endl;

#ifndef _WIN32
    if (!InitGPIO()) {
        return false;
    }
#else
    std::cout << "  [Simulation Mode] GPIO input initialized" << std::endl;
#endif

    is_initialized_ = true;
    std::cout << "[GPIO Input] Initialization complete" << std::endl;
    return true;
}

bool GPIOInputBlock::Execute() {
    if (!is_initialized_) {
        std::cerr << "[GPIO Input] Not initialized" << std::endl;
        return false;
    }

#ifdef _WIN32
    // Simulation mode - toggle state periodically
    static int counter = 0;
    counter++;
    state_ = (counter / 10) % 2 == 0;

    std::cout << "[GPIO Input] Pin " << gpio_pin_ << ": " << (state_ ? "HIGH" : "LOW") << std::endl;
#else
    if (!ReadGPIO()) {
        return false;
    }
#endif

    return true;
}

void GPIOInputBlock::Shutdown() {
    if (is_initialized_) {
#ifndef _WIN32
        CloseGPIO();
#endif
        is_initialized_ = false;
        std::cout << "[GPIO Input] Shutdown complete" << std::endl;
    }
}

std::vector<Pin> GPIOInputBlock::GetInputPins() const {
    return {}; // No inputs
}

std::vector<Pin> GPIOInputBlock::GetOutputPins() const {
    return {
        Pin("state", "bool", false)
    };
}

void GPIOInputBlock::SetInput(const std::string& pin_name, const BlockValue& value) {
    // No inputs
}

BlockValue GPIOInputBlock::GetOutput(const std::string& pin_name) const {
    if (pin_name == "state") {
        return state_;
    }
    return false;
}

bool GPIOInputBlock::InitGPIO() {
#ifndef _WIN32
    // Export GPIO pin
    std::ofstream export_file("/sys/class/gpio/export");
    if (export_file.is_open()) {
        export_file << gpio_pin_;
        export_file.close();
    }

    // Set direction to input
    std::string direction_path = "/sys/class/gpio/gpio" + std::to_string(gpio_pin_) + "/direction";
    std::ofstream direction_file(direction_path);
    if (!direction_file.is_open()) {
        std::cerr << "[GPIO Input] Failed to set direction" << std::endl;
        return false;
    }
    direction_file << "in";
    direction_file.close();

    // Open value file
    std::string value_path = "/sys/class/gpio/gpio" + std::to_string(gpio_pin_) + "/value";
    gpio_fd_ = open(value_path.c_str(), O_RDONLY);
    if (gpio_fd_ < 0) {
        std::cerr << "[GPIO Input] Failed to open GPIO value file" << std::endl;
        return false;
    }

    return true;
#else
    return true;
#endif
}

void GPIOInputBlock::CloseGPIO() {
#ifndef _WIN32
    if (gpio_fd_ >= 0) {
        close(gpio_fd_);
        gpio_fd_ = -1;
    }

    // Unexport GPIO
    std::ofstream unexport_file("/sys/class/gpio/unexport");
    if (unexport_file.is_open()) {
        unexport_file << gpio_pin_;
        unexport_file.close();
    }
#endif
}

bool GPIOInputBlock::ReadGPIO() {
#ifndef _WIN32
    char value_char;
    lseek(gpio_fd_, 0, SEEK_SET);
    if (read(gpio_fd_, &value_char, 1) != 1) {
        std::cerr << "[GPIO Input] Failed to read GPIO value" << std::endl;
        return false;
    }

    state_ = (value_char == '1');
    std::cout << "[GPIO Input] Pin " << gpio_pin_ << ": " << (state_ ? "HIGH" : "LOW") << std::endl;
    return true;
#else
    return true;
#endif
}

// Block factory functions
extern "C" {
    IBlock* CreateBlock() {
        return new GPIOInputBlock();
    }

    void DestroyBlock(IBlock* block) {
        delete block;
    }
}
