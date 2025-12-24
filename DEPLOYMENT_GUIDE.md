# CiRA FES - Complete Deployment Guide

## Overview

This guide walks you through deploying and testing all 16 blocks on your Jetson Nano.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows Development PC                    │
│                                                              │
│  ┌────────────────────┐         ┌──────────────────────┐   │
│  │ Pipeline Builder   │────────>│  CiRA Block Runtime  │   │
│  │   (GUI Editor)     │         │   (16 Blocks Built)  │   │
│  └────────────────────┘         └──────────────────────┘   │
│           │                                │                │
│           │ SSH Deployment                 │ SFTP Transfer │
│           ▼                                ▼                │
└───────────┼────────────────────────────────┼────────────────┘
            │                                │
    ════════╪════════════════════════════════╪════════════════
            │         Network (SSH)          │
    ════════╪════════════════════════════════╪════════════════
            │                                │
            ▼                                ▼
┌───────────┴────────────────────────────────┴────────────────┐
│                      Jetson Nano                             │
│                                                              │
│  ~/cira-runtime/                                            │
│    ├── bin/                                                 │
│    │   └── cira_block_runtime                              │
│    ├── blocks/                                              │
│    │   ├── adxl345-sensor-v1.0.0.so                        │
│    │   ├── bme280-sensor-v1.0.0.so                         │
│    │   ├── ... (14 more blocks)                            │
│    │   └── websocket-v1.0.0.so                             │
│    ├── manifests/                                           │
│    │   └── test_all_blocks.json                            │
│    └── logs/                                                │
│        └── runtime.log                                      │
│                                                              │
│  Hardware Connected:                                        │
│    - ADXL345 → I2C-1 (0x53)                                │
│    - BME280  → I2C-1 (0x76)                                │
│    - OLED    → I2C-1 (0x3C)                                │
│    - GPIO Pin 17 (Input)                                   │
│    - GPIO Pin 18 (Output)                                  │
│    - PWM Channel 0                                          │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### On Windows Development PC

- ✅ Visual Studio 2019+ (already installed)
- ✅ CMake 3.15+ (already installed)
- ✅ Pipeline Builder compiled
- ✅ All 16 blocks compiled

### On Jetson Nano

```bash
# Install required packages
sudo apt update
sudo apt install -y \
    build-essential \
    cmake \
    git \
    i2c-tools \
    libi2c-dev \
    openssh-server

# Enable I2C
sudo modprobe i2c-dev
sudo usermod -a -G i2c $USER

# Verify I2C devices
i2cdetect -y 1
```

## Method 1: Deploy via Pipeline Builder GUI (Recommended)

### Step 1: Open Pipeline Builder

```bash
# On Windows
cd "D:\CiRA FES\pipeline_builder\build"
.\pipeline_builder.exe
```

### Step 2: Create or Load Project

1. **File → New Pipeline** or **File → Open .ciraproject**
2. Drag blocks from Block Library panel onto canvas
3. Connect blocks by dragging between pins

### Step 3: Configure Deployment

1. **Deploy → Configure Target**
2. Select target: **Jetson Nano**
3. Enter SSH details:
   - Host: `192.168.1.100` (your Jetson IP)
   - Port: `22`
   - Username: `jetson`
   - Password: `yourpassword`
4. Click **Save**

### Step 4: Deploy Block Runtime

1. **Deploy → Block Runtime**
2. Wait for deployment progress:
   - ✓ Connecting to target
   - ✓ Setting up directories
   - ✓ Transferring runtime binary
   - ✓ Transferring blocks (16 files)
   - ✓ Transferring manifest
   - ✓ Starting runtime
3. Check deployment log for success

### Step 5: Monitor Execution

```bash
# SSH into Jetson
ssh jetson@192.168.1.100

# Check runtime is running
ps aux | grep cira_block_runtime

# View logs
tail -f ~/cira-runtime/logs/runtime.log

# Stop runtime
pkill cira_block_runtime
```

## Method 2: Manual Deployment

### Step 1: Build for ARM64 on Jetson

```bash
# On Jetson Nano
git clone <your-repo-url>
cd cira-block-runtime

# Build all blocks
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4

# Verify blocks built
python3 tests/verify_blocks.py
```

### Step 2: Setup Runtime Environment

```bash
mkdir -p ~/cira-runtime/{bin,blocks,manifests,logs}

# Copy runtime binary
cp build/cira_block_runtime ~/cira-runtime/bin/

# Copy all block libraries
find build/blocks -name "*.so" -exec cp {} ~/cira-runtime/blocks/ \;

# Verify
ls -lh ~/cira-runtime/blocks/
# Should show 16 .so files
```

### Step 3: Create Test Manifest

```bash
# Copy test manifest
cp manifests/test_all_blocks.json ~/cira-runtime/manifests/

# Or create custom manifest
nano ~/cira-runtime/manifests/my_test.json
```

### Step 4: Run Block Runtime

```bash
cd ~/cira-runtime

# Run with manifest
./bin/cira_block_runtime --manifest manifests/test_all_blocks.json

# Run in background
nohup ./bin/cira_block_runtime --manifest manifests/test_all_blocks.json > logs/runtime.log 2>&1 &

# Check logs
tail -f logs/runtime.log
```

## Method 3: Cross-Compilation (Advanced)

### On Windows with WSL2

```bash
# Install ARM64 cross-compiler
sudo apt install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

# Configure for cross-compilation
cmake -B build-arm64 \
  -DCMAKE_SYSTEM_NAME=Linux \
  -DCMAKE_SYSTEM_PROCESSOR=aarch64 \
  -DCMAKE_C_COMPILER=aarch64-linux-gnu-gcc \
  -DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++

# Build
cmake --build build-arm64

# Copy to Jetson
scp -r build-arm64/blocks/*.so jetson@192.168.1.100:~/cira-runtime/blocks/
```

## Testing Each Block Category

### Sensor Blocks

```bash
# Test ADXL345
i2cdetect -y 1  # Should show device at 0x53

# Test BME280
i2cdetect -y 1  # Should show device at 0x76

# Test GPIO Input
cat /sys/class/gpio/gpio17/value

# Test Analog Input
cat /sys/bus/iio/devices/iio:device0/in_voltage0_raw
```

### Processing Blocks

Create a simple pipeline manifest:

```json
{
  "blocks": [
    {
      "id": "test_lpf",
      "type": "low-pass-filter",
      "version": "1.0.0",
      "config": {"alpha": "0.3"}
    }
  ]
}
```

### AI/Model Blocks

```bash
# Test TimesNet ONNX
# Requires ONNX model file
./bin/cira_block_runtime --manifest manifests/test_timesnet.json

# Test Decision Tree
# Uses built-in simple tree
./bin/cira_block_runtime --manifest manifests/test_tree.json
```

### Output Blocks

```bash
# Test OLED Display
i2cdetect -y 1  # Should show device at 0x3C

# Test GPIO Output
cat /sys/class/gpio/gpio18/value

# Test PWM Output
cat /sys/class/pwm/pwmchip0/pwm0/duty_cycle

# Test MQTT Publisher
# Requires mosquitto broker
mosquitto_sub -h localhost -t "sensor/data"

# Test HTTP POST
# Monitor with server logs

# Test WebSocket
# Connect with client: wscat -c ws://localhost:8080/ws
```

## Troubleshooting

### Block Loading Errors

```bash
# Check library dependencies
ldd ~/cira-runtime/blocks/adxl345-sensor-v1.0.0.so

# Check symbols
nm -D ~/cira-runtime/blocks/adxl345-sensor-v1.0.0.so | grep CreateBlock
```

### I2C Errors

```bash
# Check permissions
sudo usermod -a -G i2c jetson
# Logout and login again

# Check devices
i2cdetect -y 1

# Check kernel module
lsmod | grep i2c
```

### GPIO Errors

```bash
# Check permissions
ls -l /sys/class/gpio/

# Export GPIO manually
echo 17 > /sys/class/gpio/export
echo in > /sys/class/gpio/gpio17/direction
```

### Runtime Crashes

```bash
# Enable debug logging
export CIRA_DEBUG=1
./bin/cira_block_runtime --manifest manifests/test.json --verbose

# Check system logs
dmesg | tail -50

# Check for memory issues
free -h
top
```

## Performance Monitoring

```bash
# CPU usage
htop

# GPU usage (Jetson specific)
tegrastats

# Memory usage
watch -n 1 free -h

# Block execution timing
# Check logs for execution times
grep "Execute time" logs/runtime.log
```

## Complete Test Workflow

### 1. Verify Hardware

```bash
# I2C devices
i2cdetect -y 1
# Expected: 0x3C (OLED), 0x53 (ADXL345), 0x76 (BME280)

# GPIO
ls /sys/class/gpio/

# PWM
ls /sys/class/pwm/
```

### 2. Deploy All Blocks

Use Pipeline Builder GUI or manual deployment

### 3. Run Comprehensive Test

```bash
cd ~/cira-runtime
./bin/cira_block_runtime --manifest manifests/test_all_blocks.json
```

### 4. Verify Output

Check console output for each block:
- `[ADXL345] x=..., y=..., z=...`
- `[BME280] T=...°C, H=...%, P=... hPa`
- `[OLED] Line 0: ...`
- `[GPIO Output] Pin 18: HIGH/LOW`
- `[PWM Output] Channel 0: ...% duty cycle`
- `[MQTT Publisher] Publishing to 'sensor/data': ...`
- `[HTTP POST] POST http://...`
- `[WebSocket] Sending: ...`

### 5. Performance Test

```bash
# Run for 1 hour
timeout 3600 ./bin/cira_block_runtime --manifest manifests/test_all_blocks.json

# Analyze logs
grep "Execute time" logs/runtime.log | awk '{sum+=$3; count++} END {print "Avg:", sum/count, "ms"}'
```

## Production Deployment

### 1. Systemd Service

Create `/etc/systemd/system/cira-runtime.service`:

```ini
[Unit]
Description=CiRA Block Runtime
After=network.target

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/cira-runtime
ExecStart=/home/jetson/cira-runtime/bin/cira_block_runtime --manifest /home/jetson/cira-runtime/manifests/production.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable cira-runtime
sudo systemctl start cira-runtime
sudo systemctl status cira-runtime
```

### 2. Auto-Update Script

```bash
#!/bin/bash
# update_blocks.sh

REMOTE_URL="windows-pc:D:/CiRA\ FES/cira-block-runtime/build/blocks"
LOCAL_PATH="~/cira-runtime/blocks"

# Stop runtime
sudo systemctl stop cira-runtime

# Backup current blocks
cp -r $LOCAL_PATH $LOCAL_PATH.backup

# Download new blocks
rsync -avz $REMOTE_URL/ $LOCAL_PATH/

# Restart runtime
sudo systemctl start cira-runtime
```

## Next Steps

1. ✅ Verify all 16 blocks compiled (DONE)
2. ✅ Test deployment to Jetson Nano
3. Connect real hardware sensors
4. Create production pipelines
5. Optimize block execution
6. Add monitoring and alerts

## Support

For issues:
1. Check logs: `~/cira-runtime/logs/runtime.log`
2. Enable debug: `export CIRA_DEBUG=1`
3. Test blocks individually
4. Check hardware connections
5. Review manifest JSON syntax

**All 16 blocks are ready for deployment! 🚀**
