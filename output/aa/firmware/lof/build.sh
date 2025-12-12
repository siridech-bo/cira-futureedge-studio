#!/bin/bash
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
