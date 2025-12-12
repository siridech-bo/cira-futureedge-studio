"""
CiRA FutureEdge Studio - Firmware Builder
Generates build files and documentation for embedded firmware compilation
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import json

from loguru import logger


@dataclass
class BuildConfig:
    """Build configuration."""
    platform: str = "cortex-m4"
    optimization: str = "Os"  # Os, O2, O3
    use_float: bool = True
    use_rtos: bool = False
    generate_docs: bool = True


@dataclass
class BuildArtifacts:
    """Generated build artifacts."""
    cmake_file: str
    main_file: str
    readme_file: str
    build_script: str
    platform: str


class FirmwareBuilder:
    """Generate build system for embedded firmware."""

    def __init__(self):
        """Initialize firmware builder."""
        pass

    def generate_build_files(
        self,
        dsp_code_dir: Path,
        config: BuildConfig,
        output_dir: Path
    ) -> BuildArtifacts:
        """
        Generate complete build system.

        Args:
            dsp_code_dir: Directory with generated DSP code
            config: Build configuration
            output_dir: Output directory for build files

        Returns:
            BuildArtifacts with paths to generated files
        """
        logger.info(f"Generating build files for {config.platform}")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate build files
        cmake_file = self._generate_cmake(dsp_code_dir, config, output_dir)
        main_file = self._generate_main(config, output_dir)
        readme = self._generate_readme(config, output_dir)
        build_script = self._generate_build_script(config, output_dir)

        logger.info(f"Generated build system in {output_dir}")

        return BuildArtifacts(
            cmake_file=str(cmake_file),
            main_file=str(main_file),
            readme_file=str(readme),
            build_script=str(build_script),
            platform=config.platform
        )

    def _generate_cmake(self, dsp_dir: Path, config: BuildConfig, output_dir: Path) -> Path:
        """Generate CMakeLists.txt"""
        cmake_path = output_dir / "CMakeLists.txt"

        toolchain_map = {
            "cortex-m4": "arm-none-eabi",
            "cortex-m7": "arm-none-eabi",
            "esp32": "xtensa-esp32-elf",
            "esp32-s3": "xtensa-esp32s3-elf",
            "x86": "gcc"
        }

        toolchain = toolchain_map.get(config.platform, "gcc")

        content = f"""cmake_minimum_required(VERSION 3.15)

# Project
project(CiRAFirmware C CXX)

# Platform: {config.platform}
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR {config.platform})

# Toolchain
set(CMAKE_C_COMPILER {toolchain}-gcc)
set(CMAKE_CXX_COMPILER {toolchain}-g++)
set(CMAKE_SIZE {toolchain}-size)
set(CMAKE_OBJCOPY {toolchain}-objcopy)

# Compiler flags
set(CMAKE_C_FLAGS "-{config.optimization} -Wall -Wextra")
set(CMAKE_CXX_FLAGS "-{config.optimization} -Wall -Wextra -std=c++11")

# Platform-specific flags
if("{config.platform}" MATCHES "cortex-m")
    set(CMAKE_C_FLAGS "${{CMAKE_C_FLAGS}} -mcpu={config.platform} -mthumb -mfloat-abi=soft")
    set(CMAKE_CXX_FLAGS "${{CMAKE_CXX_FLAGS}} -mcpu={config.platform} -mthumb -mfloat-abi=soft")
endif()

# Include directories
include_directories(
    ${{CMAKE_CURRENT_SOURCE_DIR}}
)

# Source files
set(SOURCES
    main.cpp
    anomaly_detector.cpp
    features.cpp
)

# Executable
add_executable(firmware.elf ${{SOURCES}})

# Link options
target_link_libraries(firmware.elf m)

# Generate binary and hex files
add_custom_command(TARGET firmware.elf POST_BUILD
    COMMAND ${{CMAKE_OBJCOPY}} -O binary firmware.elf firmware.bin
    COMMAND ${{CMAKE_OBJCOPY}} -O ihex firmware.elf firmware.hex
    COMMAND ${{CMAKE_SIZE}} firmware.elf
    COMMENT "Generating binary and hex files..."
)
"""
        cmake_path.write_text(content)
        return cmake_path

    def _generate_main(self, config: BuildConfig, output_dir: Path) -> Path:
        """Generate main.cpp application template"""
        main_path = output_dir / "main.cpp"

        content = f"""/**
 * CiRA FutureEdge Studio - Main Application
 * Platform: {config.platform}
 * Generated firmware for anomaly detection
 */

#include "anomaly_detector.h"
#include <stdio.h>

// Sensor data buffer
#define BUFFER_SIZE WINDOW_SIZE
float sensor_buffer[BUFFER_SIZE];
uint16_t buffer_index = 0;

// Feature storage
float features[NUM_FEATURES];

// Results
AnomalyResult result;

/**
 * Initialize hardware (implement based on your platform)
 */
void hardware_init(void) {{
    // Initialize GPIO, ADC, UART, etc.
    // Platform-specific code here
}}

/**
 * Read sensor data (implement based on your sensors)
 */
float read_sensor(void) {{
    // Read from ADC, I2C, SPI, etc.
    // Return sensor value
    return 0.0f;  // Placeholder
}}

/**
 * Send result via communication interface
 */
void send_result(const AnomalyResult* res) {{
    // Send via UART, WiFi, LoRa, etc.
    if (res->is_anomaly) {{
        printf("ANOMALY DETECTED! Score: %.2f\\n", res->anomaly_score);
    }}
}}

/**
 * Main application loop
 */
int main(void) {{
    // Initialize
    hardware_init();
    anomaly_detector_init();

    printf("CiRA Anomaly Detection System\\n");
    printf("Platform: {config.platform}\\n");
    printf("Features: %d\\n", NUM_FEATURES);

    // Main loop
    while (1) {{
        // Read sensor
        float sample = read_sensor();
        sensor_buffer[buffer_index++] = sample;

        // When buffer is full, process
        if (buffer_index >= BUFFER_SIZE) {{
            buffer_index = 0;

            // Extract features
            extract_features(sensor_buffer, BUFFER_SIZE, features);

            // Detect anomaly
            detect_anomaly(features, &result);

            // Handle result
            send_result(&result);
        }}

        // Delay between samples (adjust based on sample rate)
        // delay_ms(1000 / SAMPLE_RATE);
    }}

    return 0;
}}
"""
        main_path.write_text(content)
        return main_path

    def _generate_readme(self, config: BuildConfig, output_dir: Path) -> Path:
        """Generate README with build instructions"""
        readme_path = output_dir / "README.md"

        toolchain_install = {
            "cortex-m4": "ARM GCC: https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm",
            "cortex-m7": "ARM GCC: https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm",
            "esp32": "ESP-IDF: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/",
            "esp32-s3": "ESP-IDF: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/",
            "x86": "GCC: Install via your system package manager"
        }

        flash_instructions = {
            "cortex-m4": "Use ST-Link, J-Link, or OpenOCD to flash firmware.bin",
            "cortex-m7": "Use ST-Link, J-Link, or OpenOCD to flash firmware.bin",
            "esp32": "esptool.py --port /dev/ttyUSB0 write_flash 0x10000 firmware.bin",
            "esp32-s3": "esptool.py --port /dev/ttyUSB0 write_flash 0x10000 firmware.bin",
            "x86": "./firmware.elf (run directly)"
        }

        content = f"""# CiRA Anomaly Detection Firmware

Platform: **{config.platform}**

## Generated Files

- `CMakeLists.txt` - Build configuration
- `main.cpp` - Main application
- `anomaly_detector.h/cpp` - Detection algorithm
- `features.cpp` - Feature extraction
- `config.h` - Platform configuration

## Prerequisites

### Toolchain

{toolchain_install.get(config.platform, "Install appropriate toolchain")}

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

{flash_instructions.get(config.platform, "Refer to your platform's documentation")}

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

- Adjust `-{config.optimization}` flag in CMakeLists.txt
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
"""
        readme_path.write_text(content)
        return readme_path

    def _generate_build_script(self, config: BuildConfig, output_dir: Path) -> Path:
        """Generate build script for easy compilation"""
        if config.platform.startswith("cortex"):
            script_path = output_dir / "build.sh"
            content = """#!/bin/bash
# CiRA Build Script

set -e

echo "Building CiRA Firmware..."

# Create build directory
mkdir -p build
cd build

# Configure
cmake ..

# Build
make -j$(nproc)

echo ""
echo "Build complete!"
echo "Output files:"
ls -lh firmware.*

# Show memory usage
arm-none-eabi-size firmware.elf
"""
            script_path.write_text(content)
            script_path.chmod(0o755)

        else:
            script_path = output_dir / "build.bat"
            content = """@echo off
REM CiRA Build Script

echo Building CiRA Firmware...

REM Create build directory
if not exist build mkdir build
cd build

REM Configure
cmake ..

REM Build
cmake --build . --config Release

echo.
echo Build complete!
dir firmware.*
"""
            script_path.write_text(content)

        return script_path


def generate_firmware_build(
    dsp_code_dir: Path,
    config: BuildConfig,
    output_dir: Path
) -> BuildArtifacts:
    """
    Convenience function to generate firmware build.

    Args:
        dsp_code_dir: DSP code directory
        config: Build configuration
        output_dir: Output directory

    Returns:
        BuildArtifacts object
    """
    builder = FirmwareBuilder()
    return builder.generate_build_files(dsp_code_dir, config, output_dir)
