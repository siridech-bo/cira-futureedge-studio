# Dataset Upload Guide for Synthetic Signal Generator

## Overview
The Synthetic Signal Generator block requires dataset files to be present on the Jetson device. This guide explains how to upload and manage dataset files.

## Quick Answer to Your Questions

### 1. Why Can't I Connect Multiple Wires?

**You CAN connect multiple wires from one output pin!** This is called "fanout" or "broadcast" mode.

**How to do it:**
1. Click and drag from the output pin (e.g., `channel_0`)
2. Connect to first input pin (e.g., Channel Merge → `input_0`)
3. **Click and drag from the SAME output pin again**
4. Connect to another input pin

**Example - Broadcasting X-axis to multiple destinations:**
```
Synthetic Signal Generator
  ├─ channel_0 ──→ [Low Pass Filter] input
  ├─ channel_0 ──→ [Normalize] input
  └─ channel_0 ──→ [OLED Display] value
```

This allows you to:
- Send same signal to multiple processing blocks
- Display data while also processing it
- Create parallel processing pipelines

### 2. Do I Need to Upload the Dataset?

**YES**, dataset files must be manually uploaded to the Jetson device.

## Methods to Upload Datasets

### Method 1: SCP (Secure Copy) - Recommended

**From Windows:**
```bash
# Using scp (install Git for Windows to get scp)
scp accelerometer_dataset.json jetson@192.168.1.100:/home/jetson/test_data/

# Upload all test datasets
scp cira-block-runtime/test_datasets/*.json jetson@192.168.1.100:/home/jetson/test_data/
scp cira-block-runtime/test_datasets/*.csv jetson@192.168.1.100:/home/jetson/test_data/
scp cira-block-runtime/test_datasets/*.cbor jetson@192.168.1.100:/home/jetson/test_data/
```

**From Linux/Mac:**
```bash
scp /path/to/dataset.json jetson@jetson-ip:/home/jetson/test_data/
```

### Method 2: SFTP (Graphical Interface)

**Using WinSCP (Windows):**
1. Download and install [WinSCP](https://winscp.net/)
2. Connect to Jetson:
   - Host: Your Jetson IP (e.g., 192.168.1.100)
   - Username: jetson
   - Password: your password
3. Navigate to `/home/jetson/test_data/`
4. Drag and drop dataset files

**Using FileZilla:**
1. Download [FileZilla](https://filezilla-project.org/)
2. Use SFTP protocol
3. Upload files to `/home/jetson/test_data/`

### Method 3: Direct SSH + Paste (Small Files)

```bash
# Connect to Jetson
ssh jetson@192.168.1.100

# Create directory
mkdir -p /home/jetson/test_data

# Create dataset file
nano /home/jetson/test_data/accelerometer_dataset.json

# Paste JSON content, then Ctrl+X, Y, Enter
```

### Method 4: USB Drive (Physical Access)

1. Copy datasets to USB drive
2. Insert USB into Jetson
3. Mount and copy:
```bash
sudo mkdir -p /mnt/usb
sudo mount /dev/sda1 /mnt/usb
cp /mnt/usb/*.json /home/jetson/test_data/
sudo umount /mnt/usb
```

## Dataset Directory Setup

### Create Required Directories on Jetson

```bash
# SSH into Jetson
ssh jetson@<jetson-ip>

# Create dataset directories
mkdir -p /home/jetson/test_data
mkdir -p /home/jetson/datasets/har  # Human Activity Recognition
mkdir -p /home/jetson/datasets/gestures
mkdir -p /home/jetson/models
```

### Recommended Directory Structure

```
/home/jetson/
├── test_data/              # Test/demo datasets
│   ├── accelerometer_dataset.json
│   ├── accelerometer_dataset.csv
│   └── accelerometer_dataset.cbor
├── datasets/               # Production datasets
│   ├── har/                # Human Activity Recognition
│   │   ├── training.json
│   │   └── validation.json
│   └── gestures/
│       └── gestures.json
└── models/                 # ONNX model files
    └── activity_recognition.onnx
```

## Updating Dataset Paths in Pipeline Builder

After uploading datasets, update the configuration in Pipeline Builder:

1. Click on **Synthetic Signal Generator** node
2. In **Properties** panel, find **dataset_path**
3. Update path to match uploaded location:
   ```
   /home/jetson/test_data/accelerometer_dataset.json
   ```
4. Click **Edit Configuration** or **Revert to Defaults** as needed

## Verifying Dataset Upload

### Check if File Exists
```bash
ssh jetson@<jetson-ip>
ls -lh /home/jetson/test_data/
cat /home/jetson/test_data/accelerometer_dataset.json | head -20
```

### Test Dataset Loading
```bash
# Test JSON validity
python3 -m json.tool /home/jetson/test_data/accelerometer_dataset.json

# Check file permissions
chmod 644 /home/jetson/test_data/*.json
```

## Example Upload Script

Create `upload_datasets.sh`:
```bash
#!/bin/bash
JETSON_IP="192.168.1.100"
JETSON_USER="jetson"
LOCAL_PATH="cira-block-runtime/test_datasets"
REMOTE_PATH="/home/jetson/test_data"

echo "Creating remote directory..."
ssh ${JETSON_USER}@${JETSON_IP} "mkdir -p ${REMOTE_PATH}"

echo "Uploading JSON datasets..."
scp ${LOCAL_PATH}/*.json ${JETSON_USER}@${JETSON_IP}:${REMOTE_PATH}/

echo "Uploading CSV datasets..."
scp ${LOCAL_PATH}/*.csv ${JETSON_USER}@${JETSON_IP}:${REMOTE_PATH}/

echo "Uploading CBOR datasets..."
scp ${LOCAL_PATH}/*.cbor ${JETSON_USER}@${JETSON_IP}:${REMOTE_PATH}/

echo "Verifying upload..."
ssh ${JETSON_USER}@${JETSON_IP} "ls -lh ${REMOTE_PATH}"

echo "Done!"
```

Run with:
```bash
chmod +x upload_datasets.sh
./upload_datasets.sh
```

## Dataset File Formats

### JSON Format (Recommended for Editing)
- Human-readable
- Easy to edit and debug
- Larger file size
- Example: `accelerometer_dataset.json`

### CBOR Format (Recommended for Production)
- Binary compact format
- Smaller file size (~40-60% of JSON)
- Faster parsing
- Generate from JSON:
  ```bash
  python3 cira-block-runtime/test_datasets/generate_cbor.py
  ```

### CSV Format (Simple Data)
- Widely compatible
- Good for simple tabular data
- No metadata (sample rate, channel names)
- Example: `accelerometer_dataset.csv`

## Troubleshooting

### "Failed to open dataset file" Error
```bash
# Check file exists
ssh jetson@<ip> "ls -l /home/jetson/test_data/"

# Check permissions
ssh jetson@<ip> "chmod 644 /home/jetson/test_data/*.json"

# Verify path in manifest matches actual path
```

### "JSON parsing failed" Error
```bash
# Validate JSON syntax
ssh jetson@<ip> "python3 -m json.tool /path/to/dataset.json"

# Check for UTF-8 encoding issues
ssh jetson@<ip> "file /path/to/dataset.json"
```

### Large Dataset Transfer Fails
```bash
# Use compression
scp -C large_dataset.json jetson@<ip>:/home/jetson/test_data/

# Or compress first
gzip large_dataset.json
scp large_dataset.json.gz jetson@<ip>:/home/jetson/test_data/
ssh jetson@<ip> "gunzip /home/jetson/test_data/large_dataset.json.gz"
```

## Future Enhancement: Automatic Dataset Upload

**Currently NOT implemented**, but could be added to deployment system:

```cpp
// Future feature in BlockRuntimeDeployer
bool UploadDatasets(const std::vector<std::string>& dataset_paths) {
    for (const auto& local_path : dataset_paths) {
        std::string remote_path = "/home/jetson/datasets/" +
                                  fs::path(local_path).filename().string();
        if (!TransferFile(local_path, remote_path)) {
            return false;
        }
    }
    return true;
}
```

This would allow Pipeline Builder to automatically upload datasets during deployment.

## Best Practices

1. **Version Control**: Keep datasets in Git LFS or separate repository
2. **Naming Convention**: Use descriptive names (e.g., `walking_100hz_500samples.json`)
3. **Documentation**: Include dataset metadata (sample rate, units, classes)
4. **Backup**: Keep copies of original datasets before converting to CBOR
5. **Size Limits**: Keep datasets under 100MB for fast upload (use compression for larger)

## Summary

| Method | Use Case | Difficulty |
|--------|----------|-----------|
| SCP | Automated upload | Easy |
| WinSCP/FileZilla | GUI file transfer | Very Easy |
| Direct SSH | Small files, quick edits | Medium |
| USB Drive | No network access | Easy |

**Recommendation**: Use **SCP** for regular uploads and **WinSCP** for occasional file management.
