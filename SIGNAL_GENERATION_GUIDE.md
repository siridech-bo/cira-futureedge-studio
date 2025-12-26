# Signal Generation Mode - Quick Start Guide

## Overview

The Synthetic Signal Generator now supports **built-in signal generation** - no dataset files needed!

Perfect for:
- Quick pipeline testing
- Demonstrating signal processing
- Debugging connections
- Validating block behavior

## Signal Types

### 1. Sine Wave
Smooth periodic oscillation: `y = A × sin(2πft + φ) + offset`

**Configuration:**
```json
{
  "signal_type": "sine",
  "frequency": "2.0",      // Hz
  "amplitude": "1.0",      // Peak value
  "offset": "0.0",         // DC offset
  "phase": "0.0",          // Phase shift (radians)
  "num_channels": "3"
}
```

**Use Case:** Test filters, visualize smooth waveforms

---

### 2. Square Wave
Digital on/off signal

**Configuration:**
```json
{
  "signal_type": "square",
  "frequency": "1.0",
  "amplitude": "1.0",
  "num_channels": "3"
}
```

**Use Case:** Test digital outputs, GPIO blocks

---

### 3. Triangular Wave
Linear ramp up/down

**Configuration:**
```json
{
  "signal_type": "triangular",
  "frequency": "1.0",
  "amplitude": "1.0",
  "num_channels": "3"
}
```

**Use Case:** Test linear processing, ramp detection

---

### 4. Sawtooth Wave
Linear ramp with instant reset

**Configuration:**
```json
{
  "signal_type": "sawtooth",
  "frequency": "1.0",
  "amplitude": "1.0",
  "num_channels": "3"
}
```

**Use Case:** Scanning applications, counters

---

### 5. Random Noise
White noise within amplitude range

**Configuration:**
```json
{
  "signal_type": "noise",
  "amplitude": "0.5",      // ±0.5 random values
  "offset": "0.0",
  "num_channels": "3"
}
```

**Use Case:** Test noise filters, robustness testing

---

### 6. Constant Value
Fixed DC level

**Configuration:**
```json
{
  "signal_type": "constant",
  "amplitude": "5.0",      // Output value
  "num_channels": "3"
}
```

**Use Case:** Test thresholds, calibration

---

## Quick Examples

### Example 1: Sine Wave Pipeline
```json
{
  "blocks": [{
    "type": "synthetic-signal-generator",
    "config": {
      "signal_type": "sine",
      "frequency": "2.0",
      "amplitude": "1.0",
      "num_channels": "3",
      "sample_rate": "100"
    }
  }]
}
```

### Example 2: Noise → Filter
```json
{
  "blocks": [
    {
      "id": "noise",
      "type": "synthetic-signal-generator",
      "config": {
        "signal_type": "noise",
        "amplitude": "1.0",
        "num_channels": "1"
      }
    },
    {
      "id": "lpf",
      "type": "low-pass-filter",
      "config": {"alpha": "0.3"}
    }
  ],
  "connections": [{
    "from_block": "noise",
    "from_pin": "channel_0",
    "to_block": "lpf",
    "to_pin": "input"
  }]
}
```

---

## Configuration Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `signal_type` | string | "dataset" | Signal type: "sine", "square", "triangular", "sawtooth", "noise", "constant", "dataset" |
| `frequency` | float | 1.0 | Frequency in Hz (periodic signals only) |
| `amplitude` | float | 1.0 | Peak amplitude / output value |
| `offset` | float | 0.0 | DC offset added to signal |
| `phase` | float | 0.0 | Phase shift in radians (periodic signals) |
| `num_channels` | int | 3 | Number of output channels |
| `sample_rate` | float | 100 | Sampling rate in Hz |

---

## Pipeline Builder Usage

### In Properties Panel:

1. Add **Synthetic Signal Generator** to canvas
2. Click node to open Properties
3. Set **signal_type**: Choose from dropdown
4. Set **frequency**: Adjust Hz (1.0 = 1 cycle/second)
5. Set **amplitude**: Peak value
6. Set **num_channels**: Match your pipeline needs

### Example Settings:

**Test Low-Pass Filter:**
- signal_type: `noise`
- amplitude: `1.0`
- Connect to Low Pass Filter

**Test Sliding Window:**
- signal_type: `sine`
- frequency: `2.0`
- Connect to Sliding Window

---

## Comparison: Signal Generation vs Dataset

| Feature | Signal Generation | Dataset Replay |
|---------|------------------|----------------|
| Setup Time | ⚡ Instant | 📁 Need dataset file |
| File Upload | ❌ Not needed | ✅ Required (or inline) |
| Flexibility | 🔄 Real-time adjust | 📊 Fixed patterns |
| Use Case | Quick testing | Realistic data |
| Signal Types | 6 built-in types | Unlimited custom |

---

## Tips & Tricks

### 1. Quick Connectivity Test
```json
{"signal_type": "constant", "amplitude": "1.0"}
```
Generates steady output - perfect for testing connections

### 2. Filter Verification
```json
{"signal_type": "noise", "amplitude": "1.0"}
```
Feed noise to filter, verify smoothing

### 3. Frequency Response
```json
{"signal_type": "sine", "frequency": "0.5"}  // 0.5 Hz
{"signal_type": "sine", "frequency": "5.0"}  // 5.0 Hz
```
Test with different frequencies

### 4. Multi-Channel Testing
```json
{"signal_type": "sine", "num_channels": "10"}
```
Generate many channels for stress testing

---

## Switching Between Modes

**Signal Generation Mode:**
```json
{
  "signal_type": "sine",
  "frequency": "2.0",
  "num_channels": "3"
}
```

**Dataset Mode:**
```json
{
  "signal_type": "dataset",
  "dataset_inline": "{...json...}"
}
```

Or simply omit `signal_type` to default to dataset mode.

---

## Example Manifests

Created for you:
- [test_signal_sine.json](manifests/test_signal_sine.json) - Sine wave example
- [test_signal_noise.json](manifests/test_signal_noise.json) - Noise filtering
- [test_all_signals.json](manifests/test_all_signals.json) - All 6 signal types

---

## Build & Deploy

### Rebuild Block Runtime
```bash
cd cira-block-runtime/build
cmake --build . --target synthetic-signal-generator-v1.0.0
```

### Deploy
```bash
# Setup device (one-time)
Deploy → Setup Device

# Deploy signal generation pipeline
Deploy → test_signal_sine.json
```

---

## Troubleshooting

### Signal outputs all zeros
- Check `is_playing` is true (default)
- Verify `signal_type` is not "dataset"
- Check `amplitude` is non-zero

### Unexpected signal shape
- Verify `signal_type` spelling
- Check `frequency` (too high = aliasing)
- Verify `sample_rate` > 2 × frequency

### No output on some channels
- Check `num_channels` matches connections
- Verify pin connections in manifest

---

## Phase 1 Complete! ✅

**Implemented:**
- ✅ Sine wave generation
- ✅ Square wave generation
- ✅ Triangular wave generation
- ✅ Sawtooth wave generation
- ✅ Random noise generation
- ✅ Constant value generation
- ✅ Pipeline Builder integration
- ✅ Example manifests

**Ready for Phase 2:** Web UI Button & LED Widgets

---

## Next: Testing

1. Rebuild Pipeline Builder
2. Rebuild Block Runtime
3. Test in UI:
   - Add Synthetic Signal Generator
   - Set signal_type = "sine"
   - Connect to OLED Display
   - Deploy and verify
