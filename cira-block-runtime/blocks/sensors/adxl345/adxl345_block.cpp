/**
 * @file      adxl345_block.cpp
 * @brief     ADXL345 Accelerometer Block using libdriver
 * @version   2.0.0
 * @date      2024
 *
 * This block provides a high-level interface to the ADXL345 accelerometer
 * using the libdriver library for robust hardware communication.
 * Supports both I2C and SPI interfaces.
 */

#include "../../../include/block_interface.hpp"
#include <iostream>
#include <cstring>
#include <cmath>

#ifndef _WIN32
extern "C" {
#include "libdriver/src/driver_adxl345.h"
#include "libdriver/interface/driver_adxl345_interface.h"
}

// External interface configuration functions (defined in driver_adxl345_interface_linux.c)
extern "C" {
    void adxl345_interface_set_i2c_device(const char *device);
    void adxl345_interface_set_spi_device(const char *device);
    void adxl345_interface_set_spi_speed(uint32_t speed);
    void adxl345_interface_set_debug(int enable);
}
#endif

namespace CiraBlockRuntime {

class ADXL345Block : public IBlock {
public:
    ADXL345Block()
        : initialized_(false)
        , use_spi_(false)
        , i2c_address_(0x53)
        , range_(RANGE_2G)
        , rate_(RATE_100HZ)
        , accel_x_(0.0f)
        , accel_y_(0.0f)
        , accel_z_(0.0f)
        , tap_detected_(false)
        , freefall_detected_(false)
        , activity_detected_(false)
    {
        std::cout << "ADXL345Block constructor (libdriver v2.0)" << std::endl;
#ifndef _WIN32
        memset(&handle_, 0, sizeof(handle_));
#endif
    }

    ~ADXL345Block() {
        Shutdown();
    }

    bool Initialize(const BlockConfig& config) override {
        std::cout << "ADXL345Block::Initialize()" << std::endl;

        // Parse configuration
        if (config.count("interface")) {
            std::string iface = config.at("interface");
            use_spi_ = (iface == "spi" || iface == "SPI");
        }

        if (config.count("i2c_address")) {
            i2c_address_ = std::stoi(config.at("i2c_address"), nullptr, 16);
        }

        if (config.count("i2c_device")) {
#ifndef _WIN32
            adxl345_interface_set_i2c_device(config.at("i2c_device").c_str());
#endif
        }

        if (config.count("spi_device")) {
#ifndef _WIN32
            adxl345_interface_set_spi_device(config.at("spi_device").c_str());
#endif
        }

        if (config.count("spi_speed")) {
#ifndef _WIN32
            uint32_t speed = std::stoul(config.at("spi_speed"));
            adxl345_interface_set_spi_speed(speed);
#endif
        }

        if (config.count("range")) {
            int r = std::stoi(config.at("range"));
            switch (r) {
                case 2:  range_ = RANGE_2G; break;
                case 4:  range_ = RANGE_4G; break;
                case 8:  range_ = RANGE_8G; break;
                case 16: range_ = RANGE_16G; break;
                default: range_ = RANGE_2G; break;
            }
        }

        if (config.count("rate")) {
            int r = std::stoi(config.at("rate"));
            switch (r) {
                case 25:   rate_ = RATE_25HZ; break;
                case 50:   rate_ = RATE_50HZ; break;
                case 100:  rate_ = RATE_100HZ; break;
                case 200:  rate_ = RATE_200HZ; break;
                case 400:  rate_ = RATE_400HZ; break;
                case 800:  rate_ = RATE_800HZ; break;
                case 1600: rate_ = RATE_1600HZ; break;
                case 3200: rate_ = RATE_3200HZ; break;
                default:   rate_ = RATE_100HZ; break;
            }
        }

        bool debug = true;
        if (config.count("debug")) {
            debug = (config.at("debug") == "true" || config.at("debug") == "1");
        }

        std::cout << "  Interface: " << (use_spi_ ? "SPI" : "I2C") << std::endl;
        if (!use_spi_) {
            std::cout << "  I2C Address: 0x" << std::hex << i2c_address_ << std::dec << std::endl;
        }
        std::cout << "  Range: " << GetRangeString() << std::endl;
        std::cout << "  Rate: " << GetRateString() << std::endl;

#ifndef _WIN32
        adxl345_interface_set_debug(debug ? 1 : 0);

        // Initialize libdriver handle
        DRIVER_ADXL345_LINK_INIT(&handle_, adxl345_handle_t);
        DRIVER_ADXL345_LINK_IIC_INIT(&handle_, adxl345_interface_iic_init);
        DRIVER_ADXL345_LINK_IIC_DEINIT(&handle_, adxl345_interface_iic_deinit);
        DRIVER_ADXL345_LINK_IIC_READ(&handle_, adxl345_interface_iic_read);
        DRIVER_ADXL345_LINK_IIC_WRITE(&handle_, adxl345_interface_iic_write);
        DRIVER_ADXL345_LINK_SPI_INIT(&handle_, adxl345_interface_spi_init);
        DRIVER_ADXL345_LINK_SPI_DEINIT(&handle_, adxl345_interface_spi_deinit);
        DRIVER_ADXL345_LINK_SPI_READ(&handle_, adxl345_interface_spi_read);
        DRIVER_ADXL345_LINK_SPI_WRITE(&handle_, adxl345_interface_spi_write);
        DRIVER_ADXL345_LINK_DELAY_MS(&handle_, adxl345_interface_delay_ms);
        DRIVER_ADXL345_LINK_DEBUG_PRINT(&handle_, adxl345_interface_debug_print);
        DRIVER_ADXL345_LINK_RECEIVE_CALLBACK(&handle_, adxl345_interface_receive_callback);

        // Set interface type
        if (use_spi_) {
            if (adxl345_set_interface(&handle_, ADXL345_INTERFACE_SPI) != 0) {
                std::cerr << "ERROR: Failed to set SPI interface" << std::endl;
                return false;
            }
        } else {
            if (adxl345_set_interface(&handle_, ADXL345_INTERFACE_IIC) != 0) {
                std::cerr << "ERROR: Failed to set I2C interface" << std::endl;
                return false;
            }

            // Set I2C address
            adxl345_address_t addr = (i2c_address_ == 0x1D) ?
                ADXL345_ADDRESS_ALT_1 : ADXL345_ADDRESS_ALT_0;
            if (adxl345_set_addr_pin(&handle_, addr) != 0) {
                std::cerr << "ERROR: Failed to set I2C address" << std::endl;
                return false;
            }
        }

        // Initialize the sensor
        uint8_t res = adxl345_init(&handle_);
        if (res != 0) {
            std::cerr << "ERROR: Failed to initialize ADXL345 (error code: " << (int)res << ")" << std::endl;
            std::cerr << "       Possible causes:" << std::endl;
            std::cerr << "       - Device not connected" << std::endl;
            std::cerr << "       - Wrong I2C address (try 0x1D instead of 0x53)" << std::endl;
            std::cerr << "       - I2C/SPI bus not available" << std::endl;
            return false;
        }

        // Configure measurement range
        adxl345_range_t libdriver_range;
        switch (range_) {
            case RANGE_2G:  libdriver_range = ADXL345_RANGE_2G; break;
            case RANGE_4G:  libdriver_range = ADXL345_RANGE_4G; break;
            case RANGE_8G:  libdriver_range = ADXL345_RANGE_8G; break;
            case RANGE_16G: libdriver_range = ADXL345_RANGE_16G; break;
            default:        libdriver_range = ADXL345_RANGE_2G; break;
        }
        if (adxl345_set_range(&handle_, libdriver_range) != 0) {
            std::cerr << "WARNING: Failed to set range" << std::endl;
        }

        // Enable full resolution for best accuracy
        if (adxl345_set_full_resolution(&handle_, ADXL345_BOOL_TRUE) != 0) {
            std::cerr << "WARNING: Failed to enable full resolution" << std::endl;
        }

        // Configure sample rate
        adxl345_rate_t libdriver_rate;
        switch (rate_) {
            case RATE_25HZ:   libdriver_rate = ADXL345_RATE_25; break;
            case RATE_50HZ:   libdriver_rate = ADXL345_RATE_50; break;
            case RATE_100HZ:  libdriver_rate = ADXL345_RATE_100; break;
            case RATE_200HZ:  libdriver_rate = ADXL345_RATE_200; break;
            case RATE_400HZ:  libdriver_rate = ADXL345_RATE_400; break;
            case RATE_800HZ:  libdriver_rate = ADXL345_RATE_800; break;
            case RATE_1600HZ: libdriver_rate = ADXL345_RATE_1600; break;
            case RATE_3200HZ: libdriver_rate = ADXL345_RATE_3200; break;
            default:          libdriver_rate = ADXL345_RATE_100; break;
        }
        if (adxl345_set_rate(&handle_, libdriver_rate) != 0) {
            std::cerr << "WARNING: Failed to set rate" << std::endl;
        }

        // Enable measurement mode
        if (adxl345_set_measure(&handle_, ADXL345_BOOL_TRUE) != 0) {
            std::cerr << "ERROR: Failed to enable measurement mode" << std::endl;
            adxl345_deinit(&handle_);
            return false;
        }

        initialized_ = true;
        std::cout << "ADXL345 initialized successfully with libdriver" << std::endl;
        return true;
#else
        std::cout << "ADXL345 initialized (simulation mode - Windows)" << std::endl;
        initialized_ = true;
        return true;
#endif
    }

    std::string GetBlockId() const override {
        return "adxl345-sensor";
    }

    std::string GetBlockVersion() const override {
        return "2.0.0";
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
            Pin("accel_z", "float", false),
            Pin("tap_detected", "bool", false),
            Pin("freefall_detected", "bool", false),
            Pin("activity_detected", "bool", false)
        };
    }

    void SetInput(const std::string& pin_name, const BlockValue& value) override {
        (void)pin_name;
        (void)value;
    }

    bool Execute() override {
#ifndef _WIN32
        if (!initialized_) {
            return false;
        }

        // Read acceleration data using libdriver
        int16_t raw[1][3];
        float g[1][3];
        uint16_t len = 1;

        if (adxl345_read(&handle_, raw, g, &len) != 0) {
            std::cerr << "ERROR: Failed to read acceleration data" << std::endl;
            return false;
        }

        accel_x_ = g[0][0];
        accel_y_ = g[0][1];
        accel_z_ = g[0][2];

        // Check interrupt sources for events
        uint8_t source = 0;
        if (adxl345_get_interrupt_source(&handle_, &source) == 0) {
            tap_detected_ = (source & (1 << ADXL345_INTERRUPT_SINGLE_TAP)) ||
                           (source & (1 << ADXL345_INTERRUPT_DOUBLE_TAP));
            freefall_detected_ = (source & (1 << ADXL345_INTERRUPT_FREE_FALL));
            activity_detected_ = (source & (1 << ADXL345_INTERRUPT_ACTIVITY));
        }

        return true;
#else
        // Windows simulation mode
        static float t = 0.0f;
        t += 0.1f;
        accel_x_ = 0.5f * std::sin(t);
        accel_y_ = 0.3f * std::cos(t * 1.5f);
        accel_z_ = 1.0f + 0.1f * std::sin(t * 0.5f);
        tap_detected_ = false;
        freefall_detected_ = false;
        activity_detected_ = false;
        return true;
#endif
    }

    BlockValue GetOutput(const std::string& pin_name) const override {
        if (pin_name == "accel_x") return accel_x_;
        if (pin_name == "accel_y") return accel_y_;
        if (pin_name == "accel_z") return accel_z_;
        if (pin_name == "tap_detected") return tap_detected_;
        if (pin_name == "freefall_detected") return freefall_detected_;
        if (pin_name == "activity_detected") return activity_detected_;
        return 0.0f;
    }

    void Shutdown() override {
#ifndef _WIN32
        if (initialized_) {
            adxl345_set_measure(&handle_, ADXL345_BOOL_FALSE);
            adxl345_deinit(&handle_);
            initialized_ = false;
            std::cout << "ADXL345 shutdown" << std::endl;
        }
#endif
    }

private:
    enum Range { RANGE_2G, RANGE_4G, RANGE_8G, RANGE_16G };
    enum Rate { RATE_25HZ, RATE_50HZ, RATE_100HZ, RATE_200HZ, RATE_400HZ, RATE_800HZ, RATE_1600HZ, RATE_3200HZ };

    std::string GetRangeString() const {
        switch (range_) {
            case RANGE_2G:  return "+-2g";
            case RANGE_4G:  return "+-4g";
            case RANGE_8G:  return "+-8g";
            case RANGE_16G: return "+-16g";
            default:        return "unknown";
        }
    }

    std::string GetRateString() const {
        switch (rate_) {
            case RATE_25HZ:   return "25Hz";
            case RATE_50HZ:   return "50Hz";
            case RATE_100HZ:  return "100Hz";
            case RATE_200HZ:  return "200Hz";
            case RATE_400HZ:  return "400Hz";
            case RATE_800HZ:  return "800Hz";
            case RATE_1600HZ: return "1600Hz";
            case RATE_3200HZ: return "3200Hz";
            default:          return "unknown";
        }
    }

#ifndef _WIN32
    adxl345_handle_t handle_;
#endif
    bool initialized_;
    bool use_spi_;
    int i2c_address_;
    Range range_;
    Rate rate_;
    float accel_x_;
    float accel_y_;
    float accel_z_;
    bool tap_detected_;
    bool freefall_detected_;
    bool activity_detected_;
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
