#include "oled_display_block.hpp"
#include <iostream>
#include <sstream>
#include <iomanip>
#include <cstring>

using namespace CiraBlockRuntime;

#ifndef _WIN32
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#endif

// SSD1306 Commands
#define SSD1306_SETCONTRAST 0x81
#define SSD1306_DISPLAYALLON_RESUME 0xA4
#define SSD1306_DISPLAYALLON 0xA5
#define SSD1306_NORMALDISPLAY 0xA6
#define SSD1306_INVERTDISPLAY 0xA7
#define SSD1306_DISPLAYOFF 0xAE
#define SSD1306_DISPLAYON 0xAF
#define SSD1306_SETDISPLAYOFFSET 0xD3
#define SSD1306_SETCOMPINS 0xDA
#define SSD1306_SETVCOMDETECT 0xDB
#define SSD1306_SETDISPLAYCLOCKDIV 0xD5
#define SSD1306_SETPRECHARGE 0xD9
#define SSD1306_SETMULTIPLEX 0xA8
#define SSD1306_SETLOWCOLUMN 0x00
#define SSD1306_SETHIGHCOLUMN 0x10
#define SSD1306_SETSTARTLINE 0x40
#define SSD1306_MEMORYMODE 0x20
#define SSD1306_COLUMNADDR 0x21
#define SSD1306_PAGEADDR 0x22
#define SSD1306_COMSCANINC 0xC0
#define SSD1306_COMSCANDEC 0xC8
#define SSD1306_SEGREMAP 0xA0
#define SSD1306_CHARGEPUMP 0x8D

OledDisplayBlock::OledDisplayBlock()
    : i2c_device_("/dev/i2c-1")
    , i2c_address_(0x3C)
    , screen_width_(128)
    , screen_height_(64)
    , text_("")
    , value_(0.0f)
    , i2c_fd_(-1)
    , is_initialized_(false) {
}

OledDisplayBlock::~OledDisplayBlock() {
    Shutdown();
}

bool OledDisplayBlock::Initialize(const BlockConfig& config) {
    std::cout << "[OLED Display] Initializing..." << std::endl;

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
    // Open I2C and initialize display
    if (!OpenI2C()) {
        return false;
    }

    if (!InitializeDisplay()) {
        CloseI2C();
        return false;
    }

    ClearDisplay();
#else
    std::cout << "  [Simulation Mode] OLED display initialized" << std::endl;
#endif

    is_initialized_ = true;
    std::cout << "[OLED Display] Initialization complete" << std::endl;
    return true;
}

bool OledDisplayBlock::Execute() {
    if (!is_initialized_) {
        std::cerr << "[OLED Display] Not initialized" << std::endl;
        return false;
    }

#ifdef _WIN32
    // Simulation mode - print to console
    std::cout << "\n╔════════════════════════════╗" << std::endl;
    std::cout << "║     OLED DISPLAY (SIM)     ║" << std::endl;
    std::cout << "╠════════════════════════════╣" << std::endl;

    if (!text_.empty()) {
        std::cout << "║ " << std::left << std::setw(26) << text_ << " ║" << std::endl;
    }

    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2) << value_;
    std::cout << "║ Value: " << std::left << std::setw(18) << oss.str() << " ║" << std::endl;
    std::cout << "╚════════════════════════════╝" << std::endl;
#else
    // Real hardware - update display
    ClearDisplay();

    if (!text_.empty()) {
        DisplayText(text_, 0);
    }

    DisplayValue(value_, 2);
#endif

    return true;
}

void OledDisplayBlock::Shutdown() {
    if (is_initialized_) {
#ifndef _WIN32
        ClearDisplay();
        CloseI2C();
#else
        std::cout << "[OLED Display] Shutdown (simulation)" << std::endl;
#endif
        is_initialized_ = false;
    }
}

std::vector<Pin> OledDisplayBlock::GetInputPins() const {
    return {
        Pin("text", "string", true),
        Pin("value", "float", true)
    };
}

std::vector<Pin> OledDisplayBlock::GetOutputPins() const {
    return {}; // No outputs
}

void OledDisplayBlock::SetInput(const std::string& pin_name, const BlockValue& value) {
    if (pin_name == "text") {
        text_ = std::get<std::string>(value);
    } else if (pin_name == "value") {
        value_ = std::get<float>(value);
    }
}

BlockValue OledDisplayBlock::GetOutput(const std::string& pin_name) const {
    return 0.0f; // No outputs
}

bool OledDisplayBlock::OpenI2C() {
#ifndef _WIN32
    i2c_fd_ = open(i2c_device_.c_str(), O_RDWR);
    if (i2c_fd_ < 0) {
        std::cerr << "[OLED Display] Failed to open I2C device: " << i2c_device_ << std::endl;
        return false;
    }

    if (ioctl(i2c_fd_, I2C_SLAVE, i2c_address_) < 0) {
        std::cerr << "[OLED Display] Failed to set I2C slave address" << std::endl;
        close(i2c_fd_);
        i2c_fd_ = -1;
        return false;
    }

    return true;
#else
    return true; // Simulation
#endif
}

void OledDisplayBlock::CloseI2C() {
#ifndef _WIN32
    if (i2c_fd_ >= 0) {
        close(i2c_fd_);
        i2c_fd_ = -1;
    }
#endif
}

bool OledDisplayBlock::InitializeDisplay() {
#ifndef _WIN32
    // SSD1306 initialization sequence
    WriteCommand(SSD1306_DISPLAYOFF);
    WriteCommand(SSD1306_SETDISPLAYCLOCKDIV);
    WriteCommand(0x80);
    WriteCommand(SSD1306_SETMULTIPLEX);
    WriteCommand(0x3F);
    WriteCommand(SSD1306_SETDISPLAYOFFSET);
    WriteCommand(0x0);
    WriteCommand(SSD1306_SETSTARTLINE | 0x0);
    WriteCommand(SSD1306_CHARGEPUMP);
    WriteCommand(0x14);
    WriteCommand(SSD1306_MEMORYMODE);
    WriteCommand(0x00);
    WriteCommand(SSD1306_SEGREMAP | 0x1);
    WriteCommand(SSD1306_COMSCANDEC);
    WriteCommand(SSD1306_SETCOMPINS);
    WriteCommand(0x12);
    WriteCommand(SSD1306_SETCONTRAST);
    WriteCommand(0xCF);
    WriteCommand(SSD1306_SETPRECHARGE);
    WriteCommand(0xF1);
    WriteCommand(SSD1306_SETVCOMDETECT);
    WriteCommand(0x40);
    WriteCommand(SSD1306_DISPLAYALLON_RESUME);
    WriteCommand(SSD1306_NORMALDISPLAY);
    WriteCommand(SSD1306_DISPLAYON);
    return true;
#else
    return true; // Simulation
#endif
}

void OledDisplayBlock::ClearDisplay() {
#ifndef _WIN32
    WriteCommand(SSD1306_COLUMNADDR);
    WriteCommand(0);
    WriteCommand(127);
    WriteCommand(SSD1306_PAGEADDR);
    WriteCommand(0);
    WriteCommand(7);

    // Clear all pages
    for (int i = 0; i < 1024; i++) {
        WriteData(0x00);
    }
#endif
}

void OledDisplayBlock::DisplayText(const std::string& text, int line) {
    // Simplified - just print to console in real mode too for now
    std::cout << "[OLED] Line " << line << ": " << text << std::endl;
}

void OledDisplayBlock::DisplayValue(float value, int line) {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2) << value;
    std::cout << "[OLED] Line " << line << ": " << oss.str() << std::endl;
}

bool OledDisplayBlock::WriteCommand(uint8_t cmd) {
#ifndef _WIN32
    uint8_t buffer[2] = {0x00, cmd}; // Control byte + command
    return write(i2c_fd_, buffer, 2) == 2;
#else
    return true;
#endif
}

bool OledDisplayBlock::WriteData(uint8_t data) {
#ifndef _WIN32
    uint8_t buffer[2] = {0x40, data}; // Data byte
    return write(i2c_fd_, buffer, 2) == 2;
#else
    return true;
#endif
}

// Block factory functions
extern "C" {
    IBlock* CreateBlock() {
        return new OledDisplayBlock();
    }

    void DestroyBlock(IBlock* block) {
        delete block;
    }
}
