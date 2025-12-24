#include "pwm_output_block.hpp"
#include <iostream>
#include <fstream>
#include <cmath>

using namespace CiraBlockRuntime;

PWMOutputBlock::PWMOutputBlock()
    : pwm_chip_(0)
    , pwm_channel_(0)
    , frequency_(1000)  // 1 kHz default
    , pwm_device_("/sys/class/pwm/pwmchip0")
    , duty_cycle_(0.0f)
    , is_initialized_(false) {
}

PWMOutputBlock::~PWMOutputBlock() {
    Shutdown();
}

bool PWMOutputBlock::Initialize(const BlockConfig& config) {
    std::cout << "[PWM Output] Initializing..." << std::endl;

    // Load configuration
    if (config.find("pwm_chip") != config.end()) {
        pwm_chip_ = std::stoi(config.at("pwm_chip"));
    }
    if (config.find("pwm_channel") != config.end()) {
        pwm_channel_ = std::stoi(config.at("pwm_channel"));
    }
    if (config.find("frequency") != config.end()) {
        frequency_ = std::stoi(config.at("frequency"));
    }
    if (config.find("pwm_device") != config.end()) {
        pwm_device_ = config.at("pwm_device");
    }

    std::cout << "  PWM Chip: " << pwm_chip_ << std::endl;
    std::cout << "  PWM Channel: " << pwm_channel_ << std::endl;
    std::cout << "  Frequency: " << frequency_ << " Hz" << std::endl;

#ifndef _WIN32
    if (!InitPWM()) {
        return false;
    }
#else
    std::cout << "  [Simulation Mode] PWM output initialized" << std::endl;
#endif

    is_initialized_ = true;
    std::cout << "[PWM Output] Initialization complete" << std::endl;
    return true;
}

bool PWMOutputBlock::Execute() {
    if (!is_initialized_) {
        std::cerr << "[PWM Output] Not initialized" << std::endl;
        return false;
    }

#ifdef _WIN32
    // Simulation mode - print PWM duty cycle
    std::cout << "[PWM Output] Channel " << pwm_channel_ << ": "
              << (duty_cycle_ * 100.0f) << "% duty cycle" << std::endl;
#else
    if (!SetPWMDutyCycle(duty_cycle_)) {
        return false;
    }
#endif

    return true;
}

void PWMOutputBlock::Shutdown() {
    if (is_initialized_) {
#ifndef _WIN32
        SetPWMDutyCycle(0.0f);  // Turn off PWM
        ClosePWM();
#endif
        is_initialized_ = false;
        std::cout << "[PWM Output] Shutdown complete" << std::endl;
    }
}

std::vector<Pin> PWMOutputBlock::GetInputPins() const {
    return {
        Pin("duty_cycle", "float", true)
    };
}

std::vector<Pin> PWMOutputBlock::GetOutputPins() const {
    return {}; // No outputs
}

void PWMOutputBlock::SetInput(const std::string& pin_name, const BlockValue& value) {
    if (pin_name == "duty_cycle") {
        duty_cycle_ = std::get<float>(value);
        // Clamp to [0, 1]
        if (duty_cycle_ < 0.0f) duty_cycle_ = 0.0f;
        if (duty_cycle_ > 1.0f) duty_cycle_ = 1.0f;
    }
}

BlockValue PWMOutputBlock::GetOutput(const std::string& pin_name) const {
    return 0.0f; // No outputs
}

bool PWMOutputBlock::InitPWM() {
#ifndef _WIN32
    // Export PWM channel
    std::string export_path = pwm_device_ + "/export";
    std::ofstream export_file(export_path);
    if (export_file.is_open()) {
        export_file << pwm_channel_;
        export_file.close();
    }

    // Set period (inverse of frequency)
    int period_ns = 1000000000 / frequency_;  // nanoseconds
    std::string period_path = pwm_device_ + "/pwm" + std::to_string(pwm_channel_) + "/period";
    std::ofstream period_file(period_path);
    if (!period_file.is_open()) {
        std::cerr << "[PWM Output] Failed to set period" << std::endl;
        return false;
    }
    period_file << period_ns;
    period_file.close();

    // Enable PWM
    std::string enable_path = pwm_device_ + "/pwm" + std::to_string(pwm_channel_) + "/enable";
    std::ofstream enable_file(enable_path);
    if (!enable_file.is_open()) {
        std::cerr << "[PWM Output] Failed to enable PWM" << std::endl;
        return false;
    }
    enable_file << "1";
    enable_file.close();

    return true;
#else
    return true;
#endif
}

void PWMOutputBlock::ClosePWM() {
#ifndef _WIN32
    // Disable PWM
    std::string enable_path = pwm_device_ + "/pwm" + std::to_string(pwm_channel_) + "/enable";
    std::ofstream enable_file(enable_path);
    if (enable_file.is_open()) {
        enable_file << "0";
        enable_file.close();
    }

    // Unexport PWM
    std::string unexport_path = pwm_device_ + "/unexport";
    std::ofstream unexport_file(unexport_path);
    if (unexport_file.is_open()) {
        unexport_file << pwm_channel_;
        unexport_file.close();
    }
#endif
}

bool PWMOutputBlock::SetPWMDutyCycle(float duty_cycle) {
#ifndef _WIN32
    // Calculate duty cycle in nanoseconds
    int period_ns = 1000000000 / frequency_;
    int duty_cycle_ns = static_cast<int>(period_ns * duty_cycle);

    std::string duty_cycle_path = pwm_device_ + "/pwm" + std::to_string(pwm_channel_) + "/duty_cycle";
    std::ofstream duty_cycle_file(duty_cycle_path);
    if (!duty_cycle_file.is_open()) {
        std::cerr << "[PWM Output] Failed to set duty cycle" << std::endl;
        return false;
    }
    duty_cycle_file << duty_cycle_ns;
    duty_cycle_file.close();

    std::cout << "[PWM Output] Channel " << pwm_channel_ << ": "
              << (duty_cycle * 100.0f) << "% duty cycle" << std::endl;
    return true;
#else
    return true;
#endif
}

// Block factory functions
extern "C" {
    IBlock* CreateBlock() {
        return new PWMOutputBlock();
    }

    void DestroyBlock(IBlock* block) {
        delete block;
    }
}
