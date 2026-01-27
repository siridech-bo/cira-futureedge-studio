# CiRA FutureEdge Studio - Troubleshooting Guide

Common issues and solutions for CiRA FES v1.0

## Table of Contents

- [Connection Issues](#connection-issues)
- [Deployment Issues](#deployment-issues)
- [Performance Issues](#performance-issues)
- [Training Issues](#training-issues)
- [License Issues](#license-issues)
- [Runtime Errors](#runtime-errors)

---

## Connection Issues

### Cannot Connect to Jetson via SSH

**Symptoms**:
- "Connection refused" error in Pipeline Builder
- Setup Device fails immediately
- "Could not resolve hostname" error

**Solutions**:

1. **Verify Jetson is reachable**:
   ```bash
   ping 192.168.1.200
   ```
   If ping fails, check network connectivity.

2. **Check SSH is enabled on Jetson**:
   ```bash
   ssh user@192.168.1.200
   # If you can connect manually, SSH is working
   ```

3. **Verify SSH service is running**:
   ```bash
   sudo systemctl status ssh
   # Should show "active (running)"
   ```

   If not running:
   ```bash
   sudo systemctl start ssh
   sudo systemctl enable ssh
   ```

4. **Check firewall settings**:
   ```bash
   sudo ufw status
   # If active, ensure port 22 is allowed
   sudo ufw allow 22
   ```

5. **Verify credentials**:
   - Default Jetson username is often `nvidia` or `jetson`
   - Try both if unsure
   - Ensure password is correct (case-sensitive)

### SSH Connection Timeout

**Symptoms**:
- Deployment hangs at "Connecting to device..."
- Long delay before "Connection timeout" error

**Solutions**:

1. **Check network latency**:
   ```bash
   ping -c 10 192.168.1.200
   # Look for high latency or packet loss
   ```

2. **Use wired connection** instead of WiFi (more stable for deployment)

3. **Increase timeout** (advanced):
   - Edit Pipeline Builder SSH settings
   - Increase connection timeout to 30 seconds

### Permission Denied (publickey)

**Symptoms**:
- "Permission denied (publickey)" error
- Asked for password but authentication fails

**Solutions**:

1. **Use password authentication**:
   - Ensure Jetson allows password auth
   - Edit `/etc/ssh/sshd_config`:
     ```
     PasswordAuthentication yes
     ```
   - Restart SSH: `sudo systemctl restart ssh`

2. **Check sudo privileges**:
   ```bash
   sudo -v
   # Should not ask for password if user has NOPASSWD sudo
   ```

---

## Deployment Issues

### Setup Device Fails

**Symptoms**:
- "Failed to install dependencies" error
- Compilation errors during setup
- "cmake: command not found"

**Solutions**:

1. **Update package lists**:
   ```bash
   sudo apt update
   ```

2. **Install missing dependencies manually**:
   ```bash
   sudo apt install -y cmake build-essential curl git
   sudo apt install -y libssl-dev libssh-dev libixwebsocket-dev
   ```

3. **Check disk space**:
   ```bash
   df -h
   # Ensure at least 1GB free on /home partition
   ```

4. **For Jetson Nano (limited resources)**:
   - Use precompiled binaries (automatically downloaded)
   - Ensure internet connection for first-time setup

### Deployment Hangs at "Uploading pipeline..."

**Symptoms**:
- Deployment stuck at upload stage
- No error message, just hangs

**Solutions**:

1. **Check network stability**:
   - Use wired connection if possible
   - Avoid WiFi with high packet loss

2. **Reduce pipeline size**:
   - Large ONNX models can take 30+ seconds to upload
   - Be patient for first deployment

3. **Check Jetson disk space**:
   ```bash
   df -h /home
   # Ensure sufficient space for pipeline and models
   ```

### Runtime Fails to Start

**Symptoms**:
- Deployment succeeds but runtime doesn't start
- "Failed to start runtime" error
- Dashboard shows "Disconnected"

**Solutions**:

1. **Check runtime logs on Jetson**:
   ```bash
   ssh user@192.168.1.200
   cd ~/cira_projects/<project_name>/bin
   tail -f runtime.log
   ```

2. **Common log errors**:

   **"Failed to load model: No such file"**:
   - Model path in TimesNet block is incorrect
   - Verify model was uploaded (check `models/` directory)

   **"Port 8080 already in use"**:
   - Another runtime is running
   - Kill old process: `pkill cira-block-runtime`
   - Or change port in deployment settings

   **"Segmentation fault"**:
   - Check ONNX model compatibility
   - Re-export model from CiRA Studio
   - Verify Jetson has enough RAM (check with `free -h`)

3. **Manually start runtime** (for debugging):
   ```bash
   cd ~/cira_projects/<project>/bin
   ./cira-block-runtime --config pipeline.json --rate 100
   ```

---

## Performance Issues

### Slow Execution Rate (<10 Hz)

**Symptoms**:
- Web Dashboard shows execution rate much lower than expected
- "Execution time: 500ms" in logs (should be 10-100ms)

**Solutions**:

1. **Check Jetson power mode**:
   ```bash
   sudo nvpmodel -q
   # Should show maximum performance mode (mode 0 or 2)
   ```

   Set max performance:
   ```bash
   sudo nvpmodel -m 0  # Maximum performance
   sudo jetson_clocks   # Lock clocks to max frequency
   ```

2. **Reduce execution rate** in deployment settings:
   - If 100 Hz is too fast, try 50 Hz or 10 Hz
   - Match execution rate to your actual application needs

3. **Optimize model**:
   - Use TensorRT optimization (enable in CiRA Studio during training)
   - Reduce model size (fewer layers, smaller d_model)

4. **Check CPU usage**:
   ```bash
   htop  # or top
   # If CPU is at 100%, pipeline is too complex for current power mode
   ```

### Recording is Very Slow

**Symptoms**:
- Recording takes 30+ seconds per window
- Expected 3 seconds per window at 100 Hz

**Solutions**:

1. **This is normal behavior**:
   - Recording involves disk I/O (writing CBOR files)
   - Execution rate drops to ~30 Hz during recording
   - After recording stops, rate returns to normal

2. **Improve recording speed**:
   - Use faster storage (eMMC is faster than SD card on Jetson Nano)
   - Reduce `max_windows` (record fewer windows per file)
   - Increase execution rate (if Jetson can handle it)

3. **Verify execution rate is configured**:
   - Check deployment settings: Execution Rate should be 100 Hz
   - If still at default 10 Hz, recording will be 10× slower

### Web Dashboard Not Responding During Recording

**Symptoms**:
- Dashboard freezes or updates very slowly
- Graphs stop updating

**Solutions**:

1. **This is expected behavior**:
   - Broadcast throttling reduces UI updates during recording
   - Numeric outputs throttled by 100× (only every 100th value sent to UI)
   - Helps maintain execution performance

2. **Check "Recording in progress" indicator**:
   - Web LED or other outputs should show recording state
   - Dashboard resumes normal updates when recording stops

3. **String outputs still update**:
   - Class names and status messages update immediately
   - Only numeric data is throttled

---

## Training Issues

### Out of Memory During Training

**Symptoms**:
- "CUDA out of memory" error
- "RuntimeError: unable to allocate tensor"
- System freezes during training

**Solutions**:

1. **Reduce batch size**:
   - Default is 32, try 16 or 8
   - Smaller batch = less memory, slightly slower training

2. **Reduce model size**:
   - Decrease `d_model` (64 → 32)
   - Reduce `num_layers` (2 → 1)

3. **Use CPU training**:
   - If GPU has insufficient memory
   - Slower but works with limited VRAM

4. **Close other applications**:
   - Free up system RAM
   - Close browser tabs, other Python processes

### Training is Very Slow

**Symptoms**:
- 1+ hour for 50 epochs
- Expected: 5-15 minutes

**Solutions**:

1. **Check if GPU is being used**:
   - CiRA Studio should auto-detect GPU
   - Look for "Using device: cuda:0" in training log
   - If shows "Using device: cpu", GPU not detected

2. **Install/update PyTorch with CUDA**:
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Verify GPU is available**:
   ```python
   import torch
   print(torch.cuda.is_available())  # Should be True
   ```

4. **Reduce dataset size** (for testing):
   - Use fewer windows to verify training works
   - Then train on full dataset

### Cannot Load Dataset

**Symptoms**:
- "No files could be loaded from training folder"
- "Failed to read CBOR file"
- "Format error" when loading dataset

**Solutions**:

1. **Verify file format**:
   - CiRA CBOR vs Edge Impulse CBOR are different
   - Select correct format in Data Sources tab

2. **Check file structure**:
   ```bash
   # Expected structure:
   Dataset/
   ├── train/
   │   ├── class0_001.cbor
   │   ├── class1_001.cbor
   │   └── ...
   └── test/
       └── ...
   ```

3. **Validate CBOR files**:
   - Use provided `validate_dataset.py` script
   - Checks format and content

4. **Re-record dataset** if files are corrupted

---

## License Issues

### "Trial limit reached" Error

**Symptoms**:
- "Trial limit reached (100/100)" when starting training
- Cannot train new models

**Solutions**:

1. **Check current usage**:
   - CiRA Studio → Settings → License Info
   - Shows: "DL Training: 95/100" (example)

2. **Upgrade to PRO**:
   - Unlimited trainings and LLM usage
   - Contact: support@cira-fes.com

3. **License count doesn't reset**:
   - FREE tier is cumulative (not monthly)
   - Each training counts toward 100 lifetime limit

### License Activation Failed

**Symptoms**:
- "Could not validate license" error on startup
- App works but shows "Unlicensed" status

**Solutions**:

1. **Check internet connection** (first launch requires validation)

2. **Firewall blocking connection**:
   - Allow CiRA Studio through Windows Firewall

3. **For offline activation**:
   - Contact support for manual activation

---

## Runtime Errors

### Broadcast Errors in Logs

**Symptoms**:
- "WebSocket send failed" in runtime logs
- "Broadcast queue full" warnings

**Solutions**:

1. **This is usually harmless**:
   - Warnings occur when dashboard is not connected
   - Runtime continues executing normally

2. **If affecting performance**:
   - Restart runtime: `pkill cira-block-runtime && ./cira-block-runtime ...`

### Model Inference Errors

**Symptoms**:
- "ONNXRuntime error: invalid tensor shape"
- "Mismatched input dimensions"
- "Segmentation fault" during inference

**Solutions**:

1. **Verify model configuration matches training**:
   - `seq_len` in TimesNet block = seq_len during training
   - `input_channels` matches dataset channels
   - `num_classes` matches number of classes in dataset

2. **Check Sliding Window output**:
   - window_size must match model's seq_len
   - Number of channels must match model's input_channels

3. **Re-export model**:
   - Sometimes ONNX export has issues
   - Re-export from CiRA Studio and redeploy

### "Block execution failed" Errors

**Symptoms**:
- Runtime stops with "Block execution failed" error
- Specific block name in error message

**Solutions**:

1. **Check block configuration**:
   - Verify all required parameters are set
   - Look for invalid values (negative numbers, out of range, etc.)

2. **Check input connections**:
   - Ensure all input pins are connected
   - Missing inputs cause execution failures

3. **Review runtime logs**:
   - Detailed error message shows root cause
   - Look for "Exception:" or "Error:" lines

---

## Getting Help

If you've tried the above solutions and still have issues:

1. **Check runtime logs**:
   ```bash
   ssh user@<jetson-ip>
   cat ~/cira_projects/<project>/bin/runtime.log
   ```

2. **Collect information**:
   - Exact error message
   - Steps to reproduce
   - Jetson model (Nano/Xavier/Orin)
   - Pipeline configuration (JSON file)

3. **Contact support**:
   - Email: support@cira-fes.com
   - GitHub Issues: [your-repo-url]
   - Include logs and error messages

4. **Community**:
   - Discord: [invite-link]
   - Forums: [forum-url]

---

## Known Issues

### Version 1.0 Known Limitations

1. **Single pipeline per project**:
   - Workaround: Create multiple projects for multiple pipelines

2. **No auto-reconnect** after Jetson reboot:
   - Workaround: Manually redeploy or restart runtime

3. **Large ONNX models (>100 MB)** slow to upload:
   - Workaround: Be patient, first upload takes longest

4. **Windows Defender false positive** (sometimes flags .exe):
   - Workaround: Add exception in Windows Security

These will be addressed in future releases.

---

**Still stuck?** Contact support with detailed logs and we'll help you resolve the issue!
