# CiRA FES - Quick Reference Card

## 🚀 Quick Start Commands

### Build Everything
```bash
# Build blocks (Windows)
cd "D:\CiRA FES\cira-block-runtime"
cmake --build build

# Build Pipeline Builder (Windows)
cd "D:\CiRA FES\pipeline_builder"
cmake --build build

# Build blocks (Jetson Nano)
cd cira-block-runtime
cmake -B build && cmake --build build -j4
```

### Verify Blocks
```bash
# Quick verification
python tests/verify_blocks.py

# Should output: 16/16 blocks (100%)
```

### Run Pipeline Builder
```bash
cd "D:\CiRA FES\pipeline_builder\build"
.\pipeline_builder.exe
```

### Deploy to Jetson
```
GUI Method:
  Pipeline Builder → Deploy → Block Runtime

Manual Method:
  scp -r build/blocks/*.so jetson@<IP>:~/blocks/
```

---

## 📦 All 16 Blocks

| Category | Block Name | ID | Features |
|----------|-----------|-----|----------|
| **Sensors** | ADXL345 | `adxl345-sensor` | 3-axis accelerometer |
| | BME280 | `bme280-sensor` | Temp/Humid/Press |
| | Analog Input | `analog-input` | ADC reader |
| | GPIO Input | `gpio-input` | Digital input |
| **Processing** | Low Pass Filter | `low-pass-filter` | IIR filtering |
| | Sliding Window | `sliding-window` | Data buffering |
| | Normalize | `normalize` | Value scaling |
| | Channel Merge | `channel-merge` | Multi-channel |
| **AI/Models** | TimesNet ONNX | `timesnet` | Neural network |
| | Decision Tree | `decision-tree` | Classifier |
| **Outputs** | OLED Display | `oled-display` | SSD1306 I2C |
| | GPIO Output | `gpio-output` | Digital output |
| | PWM Output | `pwm-output` | Motor control |
| | MQTT Publisher | `mqtt-publisher` | IoT messaging |
| | HTTP POST | `http-post` | Web API |
| | WebSocket | `websocket` | Real-time data |

---

## 🔌 Hardware Connections (Jetson Nano)

```
I2C-1 (/dev/i2c-1):
  Pin 3 (SDA), Pin 5 (SCL)
  ├── 0x53: ADXL345
  ├── 0x76: BME280
  └── 0x3C: OLED SSD1306

GPIO:
  Pin 11 (GPIO 17): Input
  Pin 12 (GPIO 18): Output

PWM:
  PWM0: Motor/Servo control
```

---

## 📁 Key File Locations

```
D:\CiRA FES\
├── cira-block-runtime/
│   ├── build/blocks/          ← 16 compiled blocks (.dll)
│   ├── tests/                 ← Test scripts
│   └── manifests/             ← Test configurations
│
├── pipeline_builder/
│   ├── build/                 ← Pipeline Builder executable
│   └── manifests/             ← Pipeline definitions
│
├── DEPLOYMENT_GUIDE.md        ← Full deployment instructions
├── SESSION_COMPLETE.md        ← Implementation summary
└── QUICK_REFERENCE.md         ← This file
```

---

## 🧪 Testing

### Verify Build
```bash
python cira-block-runtime/tests/verify_blocks.py
```

### Test on Jetson
```bash
# Check I2C devices
i2cdetect -y 1

# Run test manifest
./cira_block_runtime --manifest test_all_blocks.json

# Monitor logs
tail -f ~/cira-runtime/logs/runtime.log
```

---

## 🐛 Troubleshooting

### Build Issues
```bash
# Clean build
rm -rf build/
cmake -B build && cmake --build build

# Check dependencies
ldd build/blocks/sensor/*.so
```

### Deployment Issues
```bash
# Test SSH connection
ssh jetson@<IP>

# Check file permissions
ls -l ~/cira-runtime/bin/

# Manual deployment
scp -r build/blocks/*.so jetson@<IP>:~/cira-runtime/blocks/
```

### Runtime Issues
```bash
# Enable debug output
export CIRA_DEBUG=1
./cira_block_runtime --manifest test.json --verbose

# Check I2C
i2cdetect -y 1

# Check GPIO
cat /sys/class/gpio/gpio17/value
```

---

## 📊 Manifest Example

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
    },
    {
      "id": "filter1",
      "type": "low-pass-filter",
      "version": "1.0.0",
      "config": {
        "alpha": "0.3"
      }
    }
  ],
  "connections": [
    {
      "from_block": "sensor1",
      "from_pin": "x",
      "to_block": "filter1",
      "to_pin": "input"
    }
  ]
}
```

---

## 🎯 Common Tasks

### Deploy New Pipeline
```
1. Pipeline Builder → File → New Pipeline
2. Drag blocks onto canvas
3. Connect blocks
4. File → Save As → my_pipeline.ciraproject
5. Deploy → Block Runtime
```

### Update Blocks on Jetson
```bash
# Rebuild blocks
cmake --build build

# Copy to Jetson
scp -r build/blocks/*.so jetson@<IP>:~/cira-runtime/blocks/

# Restart runtime
ssh jetson@<IP>
pkill cira_block_runtime
./cira-runtime/bin/cira_block_runtime --manifest manifests/my_pipeline.json
```

### Add New Block
```bash
# 1. Create block files
blocks/<category>/<name>/
  ├── <name>_block.hpp
  ├── <name>_block.cpp
  └── CMakeLists.txt

# 2. Update main CMakeLists.txt
add_subdirectory(blocks/<category>/<name>)

# 3. Rebuild
cmake --build build

# 4. Verify
python tests/verify_blocks.py
```

---

## 📈 Performance Tips

### Optimize Execution
```bash
# Check execution frequency
grep "Execute time" logs/runtime.log

# Reduce frequency in manifest
"execution": {
  "frequency_hz": 10  # Lower = less CPU
}

# Monitor CPU usage
htop
tegrastats  # Jetson only
```

### Reduce Memory
```bash
# Use smaller window sizes
"window_size": "50"  # Instead of 100

# Disable unused outputs
# Remove MQTT/HTTP/WebSocket if not needed
```

---

## 🔐 Security Notes

### SSH Access
```bash
# Use SSH keys instead of passwords
ssh-keygen
ssh-copy-id jetson@<IP>

# Update deployment config to use key
```

### Production Deployment
```bash
# Create systemd service
sudo nano /etc/systemd/system/cira-runtime.service

# Enable and start
sudo systemctl enable cira-runtime
sudo systemctl start cira-runtime
```

---

## 📚 Documentation Links

- **Full Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Session Summary**: `SESSION_COMPLETE.md`
- **Test Guide**: `cira-block-runtime/tests/README.md`
- **Pipeline Builder Docs**: `pipeline_builder/README.md`

---

## ✅ Checklist

### Before Deployment
- [ ] All blocks compiled (16/16)
- [ ] Tests pass (`verify_blocks.py`)
- [ ] Jetson Nano accessible via SSH
- [ ] I2C devices detected
- [ ] Pipeline Builder opens

### First Deployment
- [ ] SSH credentials configured
- [ ] Test manifest created
- [ ] Deployment successful
- [ ] Runtime starts without errors
- [ ] Logs show block execution

### Production Ready
- [ ] Hardware sensors connected
- [ ] Pipeline tested end-to-end
- [ ] Performance acceptable
- [ ] Systemd service configured
- [ ] Monitoring in place

---

## 🆘 Getting Help

1. Check logs: `~/cira-runtime/logs/runtime.log`
2. Enable debug: `export CIRA_DEBUG=1`
3. Review `DEPLOYMENT_GUIDE.md`
4. Test blocks individually
5. Verify hardware connections

---

*Quick Reference v1.0 - Last updated: 2024-12-24*
