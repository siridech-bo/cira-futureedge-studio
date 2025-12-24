#include "../../../include/block_interface.hpp"
#include <iostream>
#include <fstream>

#ifndef _WIN32
#include <fcntl.h>
#include <unistd.h>
#endif

namespace CiraBlockRuntime {

class GPIOOutputBlock : public IBlock {
public:
    GPIOOutputBlock()
        : pin_number_(18)
        , gpio_fd_(-1)
        , state_(false)
    {
        std::cout << "GPIOOutputBlock constructor called" << std::endl;
    }

    ~GPIOOutputBlock() {
        Shutdown();
    }

    bool Initialize(const BlockConfig& config) override {
        std::cout << "GPIOOutputBlock::Initialize()" << std::endl;

        // Parse configuration
        if (config.count("pin")) {
            pin_number_ = std::stoi(config.at("pin"));
        }

        std::cout << "  GPIO Pin: " << pin_number_ << std::endl;

#ifndef _WIN32
        // Export GPIO pin
        std::ofstream export_file("/sys/class/gpio/export");
        if (export_file.is_open()) {
            export_file << pin_number_;
            export_file.close();
            usleep(100000);  // Wait for sysfs to create files
        }

        // Set direction to output
        std::string direction_path = "/sys/class/gpio/gpio" + std::to_string(pin_number_) + "/direction";
        std::ofstream direction_file(direction_path);
        if (direction_file.is_open()) {
            direction_file << "out";
            direction_file.close();
        } else {
            std::cerr << "Warning: Could not set GPIO direction (may already be exported)" << std::endl;
        }

        // Open value file for writing
        std::string value_path = "/sys/class/gpio/gpio" + std::to_string(pin_number_) + "/value";
        gpio_fd_ = open(value_path.c_str(), O_WRONLY);
        if (gpio_fd_ < 0) {
            std::cerr << "ERROR: Failed to open GPIO value file" << std::endl;
            std::cerr << "       (This is normal on non-Linux systems)" << std::endl;
        } else {
            std::cout << "✓ GPIO output initialized successfully" << std::endl;
        }
#else
        std::cout << "✓ GPIO output initialized (simulation mode - Windows)" << std::endl;
#endif

        return true;
    }

    std::string GetBlockId() const override {
        return "gpio-output";
    }

    std::string GetBlockVersion() const override {
        return "1.0.0";
    }

    std::string GetBlockType() const override {
        return "output";
    }

    std::vector<Pin> GetInputPins() const override {
        return {
            Pin("state", "bool", true)
        };
    }

    std::vector<Pin> GetOutputPins() const override {
        return {};  // No outputs (actuator node)
    }

    void SetInput(const std::string& pin_name, const BlockValue& value) override {
        if (pin_name == "state" && std::holds_alternative<bool>(value)) {
            state_ = std::get<bool>(value);
        }
    }

    bool Execute() override {
#ifndef _WIN32
        if (gpio_fd_ >= 0) {
            // Write state to GPIO
            const char* value_str = state_ ? "1" : "0";
            if (write(gpio_fd_, value_str, 1) != 1) {
                std::cerr << "ERROR: Failed to write GPIO value" << std::endl;
                return false;
            }
            lseek(gpio_fd_, 0, SEEK_SET);  // Reset file position
        } else {
            // Simulation mode
            std::cout << "GPIO Pin " << pin_number_ << ": " << (state_ ? "HIGH" : "LOW") << std::endl;
        }
#else
        // Windows simulation mode
        std::cout << "GPIO Pin " << pin_number_ << ": " << (state_ ? "HIGH" : "LOW") << std::endl;
#endif

        return true;
    }

    BlockValue GetOutput(const std::string& pin_name) const override {
        (void)pin_name;
        return false;
    }

    void Shutdown() override {
#ifndef _WIN32
        if (gpio_fd_ >= 0) {
            // Set GPIO to LOW before closing
            write(gpio_fd_, "0", 1);
            close(gpio_fd_);
            gpio_fd_ = -1;
        }

        // Unexport GPIO
        std::ofstream unexport_file("/sys/class/gpio/unexport");
        if (unexport_file.is_open()) {
            unexport_file << pin_number_;
            unexport_file.close();
        }

        std::cout << "GPIO output shutdown" << std::endl;
#endif
    }

private:
    int pin_number_;
    int gpio_fd_;
    bool state_;
};

} // namespace CiraBlockRuntime

// Export factory functions
extern "C" {
    CiraBlockRuntime::IBlock* CreateBlock() {
        return new CiraBlockRuntime::GPIOOutputBlock();
    }

    void DestroyBlock(CiraBlockRuntime::IBlock* block) {
        delete block;
    }
}
