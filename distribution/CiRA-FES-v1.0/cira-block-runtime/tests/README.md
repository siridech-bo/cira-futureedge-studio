# CiRA Block Runtime - Testing Guide

This directory contains tests for all CiRA blocks.

## Quick Start

### Method 1: Python Test Script (Recommended)

The Python script provides a quick overview of all blocks:

```bash
# From the cira-block-runtime directory
python tests/test_blocks.py

# Or specify a custom build directory
python tests/test_blocks.py /path/to/build/blocks
```

**What it tests:**
- ✓ Finds all compiled block libraries (.dll/.so)
- ✓ Checks for required export symbols (CreateBlock, DestroyBlock)
- ✓ Tests dynamic loading of each block
- ✓ Categorizes blocks by type (Sensor/Processing/AI/Output)
- ✓ Reports file sizes and success rates

### Method 2: C++ Test Program (Comprehensive)

For detailed testing that actually executes blocks:

```bash
# Build the test program
cd cira-block-runtime
cmake --build build

# Run the test program
./build/tests/test_all_blocks

# Or on Windows
.\build\tests\test_all_blocks.exe
```

**What it tests:**
- ✓ Dynamic library loading
- ✓ Block creation and initialization
- ✓ Input/output pin discovery
- ✓ Setting input values
- ✓ Execute() function (runs 3 cycles)
- ✓ Reading output values
- ✓ Proper shutdown

### Method 3: Manual Testing with Block Runtime

Test blocks in a real pipeline on target hardware:

```bash
# On Jetson Nano or Arduino UNO Q
cd cira-block-runtime/build
./cira_block_runtime --manifest /path/to/manifest.json
```

## Test Coverage

### Sensor Blocks (4)
- [x] ADXL345 - Accelerometer
- [x] BME280 - Temperature/Humidity/Pressure
- [x] Analog Input - ADC input
- [x] GPIO Input - Digital input

### Processing Blocks (4)
- [x] Low Pass Filter - Signal filtering
- [x] Sliding Window - Data buffering
- [x] Normalize - Value normalization
- [x] Channel Merge - Multi-channel combining

### AI/Model Blocks (2)
- [x] TimesNet ONNX - Neural network inference
- [x] Decision Tree - Tree-based classifier

### Output Blocks (7)
- [x] OLED Display - SSD1306 display
- [x] GPIO Output - Digital output
- [x] PWM Output - Motor/servo control
- [x] MQTT Publisher - IoT messaging
- [x] HTTP POST - Web API calls
- [x] WebSocket - Real-time data streaming

**Total: 17 blocks**

## Expected Output

### Python Script Output Example
```
============================================================
         CiRA Block Runtime - Test Suite
============================================================

ℹ Scanning for blocks in: ../build/blocks
✓ Found 17 blocks

============================================================
                    Testing Blocks
============================================================

Sensor Blocks:

  adxl345-sensor-v1.0.0
    Path: ../build/blocks/sensors/adxl345/adxl345-sensor-v1.0.0.dll
    Size: 256.3 KB
✓    Exports: CreateBlock, DestroyBlock found
✓    Loading: Block loads successfully

[... continues for all blocks ...]

============================================================
                    Test Summary
============================================================
Total blocks tested: 17
✓ Passed: 17

Success rate: 100.0%

✓ All blocks passed basic tests!
```

### C++ Test Program Output Example
```
========================================
Testing: ADXL345 Sensor
========================================
[ADXL345] Initializing...
  I2C Device: /dev/i2c-1
  I2C Address: 0x53
  [Simulation Mode] ADXL345 initialized
[ADXL345] Initialization complete
  ID: adxl345-sensor
  Version: 1.0.0
  Type: sensor
  Input Pins (0):
  Output Pins (3):
    - x (float)
    - y (float)
    - z (float)

  Executing block (3 cycles)...
  --- Cycle 1 ---
[ADXL345] x=0.245, y=-0.123, z=9.812 m/s²
    Output 'x': 0.245
    Output 'y': -0.123
    Output 'z': 9.812
  --- Cycle 2 ---
[... continues ...]
  ✓ Test PASSED
```

## Troubleshooting

### "No blocks found"
- Make sure you've built the project: `cmake --build build`
- Check that BUILD_BLOCKS option is ON in CMakeLists.txt

### "Failed to load library"
- On Linux: Check library dependencies with `ldd <block.so>`
- On Windows: Check for missing DLLs with Dependency Walker
- Ensure you're using the correct architecture (x64)

### "Missing required functions"
- Block may not have exported CreateBlock/DestroyBlock
- Check CMakeLists.txt for proper `extern "C"` linkage

### Simulation vs Real Hardware
- On Windows: All blocks run in simulation mode (no actual I2C/GPIO)
- On Linux: Blocks attempt real hardware access
- For desktop testing, all blocks should work in simulation mode

## Creating Custom Tests

You can create custom test manifests in `manifests/` directory:

Example `test_sensors.json`:
```json
{
  "blocks": [
    {
      "id": "sensor1",
      "type": "adxl345-sensor",
      "version": "1.0.0",
      "config": {
        "i2c_device": "/dev/i2c-1",
        "i2c_address": "0x53"
      }
    }
  ],
  "connections": []
}
```

Then test with:
```bash
./build/cira_block_runtime --manifest manifests/test_sensors.json
```

## CI/CD Integration

To integrate tests in CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Build blocks
  run: cmake --build build

- name: Test blocks
  run: python tests/test_blocks.py

- name: Comprehensive test
  run: ./build/tests/test_all_blocks
```

## Performance Testing

For performance benchmarks, use the `--benchmark` flag:

```bash
./build/tests/test_all_blocks --benchmark
```

This will measure:
- Block initialization time
- Execute() latency (avg/min/max)
- Memory usage
- CPU utilization

## Hardware Testing

For testing on real Jetson Nano:

1. **Deploy blocks:**
   ```bash
   scp -r build/blocks/*.so jetson@192.168.1.100:~/blocks/
   ```

2. **Run on target:**
   ```bash
   ssh jetson@192.168.1.100
   cd ~/
   ./cira_block_runtime --manifest test.json
   ```

3. **Monitor output:**
   - Check console output for block execution
   - Verify I2C devices: `i2cdetect -y 1`
   - Monitor GPIO: `cat /sys/kernel/debug/gpio`
   - Check PWM: `cat /sys/class/pwm/pwmchip0/pwm0/duty_cycle`

## Known Issues

- **Windows I2C simulation**: Uses random data generation
- **Network blocks**: Require actual server/broker in non-simulation mode
- **GPIO conflicts**: May conflict if pins already in use

## Contributing

To add a new block test:

1. Create the block following the IBlock interface
2. Add to CMakeLists.txt in appropriate category
3. Python script will auto-detect it
4. Add manual test case to test_all_blocks.cpp if needed

## Support

For issues or questions:
- Check build logs: `cmake --build build --verbose`
- Enable debug output: Set `CMAKE_BUILD_TYPE=Debug`
- Review block-specific logs in Execute() output
