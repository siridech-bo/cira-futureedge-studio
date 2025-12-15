# CiRA Anomaly Detection Firmware

Platform: **cortex-m4**

## Generated Files

- `CMakeLists.txt` - Build configuration
- `main.cpp` - Main application
- `anomaly_detector.h/cpp` - Detection algorithm
- `features.cpp` - Feature extraction
- `config.h` - Platform configuration

## Prerequisites

### Toolchain

ARM GCC: https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm

### CMake

```bash
# Ubuntu/Debian
sudo apt-get install cmake

# macOS
brew install cmake

# Windows
# Download from https://cmake.org/download/
```

## Build Instructions

### 1. Configure

```bash
mkdir build
cd build
cmake ..
```

### 2. Compile

```bash
make
```

This will generate:
- `firmware.elf` - Executable
- `firmware.bin` - Binary for flashing
- `firmware.hex` - Intel HEX format

### 3. Flash to Device

Use ST-Link, J-Link, or OpenOCD to flash firmware.bin

## Customization

### Sensor Integration

Edit `main.cpp`:
- `hardware_init()` - Initialize your sensors and peripherals
- `read_sensor()` - Read data from your specific sensor(s)
- `send_result()` - Send anomaly alerts via your communication interface

### Platform-Specific Code

Add your platform's startup code, linker script, and HAL drivers to the build.

## Memory Usage

Check memory usage after build:

```bash
arm-none-eabi-size firmware.elf
```

## Optimization

- Adjust `-Os` flag in CMakeLists.txt
- Use fixed-point arithmetic for faster MCU performance
- Reduce WINDOW_SIZE if RAM is limited

## Troubleshooting

### Build Errors

- Ensure toolchain is in PATH
- Check CMake version >= 3.15
- Verify all source files are present

### Runtime Issues

- Check SAMPLE_RATE matches your sensor
- Verify feature extraction produces valid values
- Adjust ANOMALY_THRESHOLD if needed

## Support

For issues or questions, refer to the CiRA FutureEdge Studio documentation.
