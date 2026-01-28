#include "../../../include/block_interface.hpp"
#include <iostream>
#include <cstring>
#include <cmath>

#ifndef _WIN32
#include <linux/i2c-dev.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#endif

namespace CiraBlockRuntime {

class ADXL345Block : public IBlock {
public:
    ADXL345Block()
        : i2c_fd_(-1)
        , i2c_address_(0x53)
        , range_(2)  // ±2g default
        , accel_x_(0.0f)
        , accel_y_(0.0f)
        , accel_z_(0.0f)
    {
        std::cout << "ADXL345Block constructor called" << std::endl;
    }

    ~ADXL345Block() {
        Shutdown();
    }

    bool Initialize(const BlockConfig& config) override {
        std::cout << "ADXL345Block::Initialize()" << std::endl;

        // Parse configuration
        if (config.count("i2c_address")) {
            i2c_address_ = std::stoi(config.at("i2c_address"), nullptr, 16);
        }
        if (config.count("range")) {
            range_ = std::stoi(config.at("range"));
        }

        std::cout << "  I2C Address: 0x" << std::hex << i2c_address_ << std::dec << std::endl;
        std::cout << "  Range: ±" << range_ << "g" << std::endl;

#ifndef _WIN32
        // Open I2C device
        const char* i2c_device = "/dev/i2c-1";
        i2c_fd_ = open(i2c_device, O_RDWR);
        if (i2c_fd_ < 0) {
            std::cerr << "ERROR: Failed to open I2C device: " << i2c_device << std::endl;
            std::cerr << "       (This is normal on non-Linux systems)" << std::endl;
            // Don't fail - allow simulation mode
            return true;
        }

        // Set I2C slave address
        if (ioctl(i2c_fd_, I2C_SLAVE, i2c_address_) < 0) {
            std::cerr << "ERROR: Failed to set I2C slave address" << std::endl;
            close(i2c_fd_);
            i2c_fd_ = -1;
            return true;  // Allow simulation mode
        }

        // Initialize ADXL345
        // Power control register - measurement mode
        uint8_t power_ctl[] = {0x2D, 0x08};
        if (write(i2c_fd_, power_ctl, 2) != 2) {
            std::cerr << "ERROR: Failed to write power control" << std::endl;
        }

        // Data format register - set range
        uint8_t range_code = 0;
        switch (range_) {
            case 2:  range_code = 0x00; break;
            case 4:  range_code = 0x01; break;
            case 8:  range_code = 0x02; break;
            case 16: range_code = 0x03; break;
            default: range_code = 0x00; break;
        }
        uint8_t data_format[] = {0x31, range_code};
        if (write(i2c_fd_, data_format, 2) != 2) {
            std::cerr << "ERROR: Failed to write data format" << std::endl;
        }

        std::cout << "✓ ADXL345 initialized successfully" << std::endl;
#else
        std::cout << "✓ ADXL345 initialized (simulation mode - Windows)" << std::endl;
#endif

        return true;
    }

    std::string GetBlockId() const override {
        return "adxl345-sensor";
    }

    std::string GetBlockVersion() const override {
        return "1.0.0";
    }

    std::string GetBlockType() const override {
        return "sensor";
    }

    std::vector<Pin> GetInputPins() const override {
        return {};  // No inputs (sensor node)
    }

    std::vector<Pin> GetOutputPins() const override {
        return {
            Pin("accel_x", "float", false),
            Pin("accel_y", "float", false),
            Pin("accel_z", "float", false)
        };
    }

    void SetInput(const std::string& pin_name, const BlockValue& value) override {
        // No inputs
        (void)pin_name;
        (void)value;
    }

    bool Execute() override {
#ifndef _WIN32
        if (i2c_fd_ >= 0) {
            // Read 6 bytes starting from register 0x32 (DATAX0)
            uint8_t reg = 0x32;
            if (write(i2c_fd_, &reg, 1) != 1) {
                std::cerr << "ERROR: Failed to write register address" << std::endl;
                return false;
            }

            uint8_t buffer[6];
            if (read(i2c_fd_, buffer, 6) != 6) {
                std::cerr << "ERROR: Failed to read acceleration data" << std::endl;
                return false;
            }

            // Combine bytes (little-endian)
            int16_t x = (buffer[1] << 8) | buffer[0];
            int16_t y = (buffer[3] << 8) | buffer[2];
            int16_t z = (buffer[5] << 8) | buffer[4];

            // Convert to g values based on range
            // ±2g: 256 LSB/g
            // ±4g: 128 LSB/g
            // ±8g: 64 LSB/g
            // ±16g: 32 LSB/g
            float scale = 256.0f / range_;
            accel_x_ = x / scale;
            accel_y_ = y / scale;
            accel_z_ = z / scale;
        } else {
            // Simulation mode - generate fake accelerometer data
            static float t = 0.0f;
            t += 0.1f;
            accel_x_ = 0.5f * std::sin(t);
            accel_y_ = 0.3f * std::cos(t * 1.5f);
            accel_z_ = 1.0f + 0.1f * std::sin(t * 0.5f);  // ~1g with variation
        }
#else
        // Windows simulation mode
        static float t = 0.0f;
        t += 0.1f;
        accel_x_ = 0.5f * std::sin(t);
        accel_y_ = 0.3f * std::cos(t * 1.5f);
        accel_z_ = 1.0f + 0.1f * std::sin(t * 0.5f);
#endif

        return true;
    }

    BlockValue GetOutput(const std::string& pin_name) const override {
        if (pin_name == "accel_x") return accel_x_;
        if (pin_name == "accel_y") return accel_y_;
        if (pin_name == "accel_z") return accel_z_;
        return 0.0f;
    }

    void Shutdown() override {
#ifndef _WIN32
        if (i2c_fd_ >= 0) {
            // Put device into standby mode
            uint8_t power_ctl[] = {0x2D, 0x00};
            write(i2c_fd_, power_ctl, 2);

            close(i2c_fd_);
            i2c_fd_ = -1;
            std::cout << "ADXL345 shutdown" << std::endl;
        }
#endif
    }

private:
    int i2c_fd_;
    int i2c_address_;
    int range_;
    float accel_x_;
    float accel_y_;
    float accel_z_;
};

} // namespace CiraBlockRuntime

// Export factory functions (C linkage for dlopen)
extern "C" {
    CiraBlockRuntime::IBlock* CreateBlock() {
        return new CiraBlockRuntime::ADXL345Block();
    }

    void DestroyBlock(CiraBlockRuntime::IBlock* block) {
        delete block;
    }
}
