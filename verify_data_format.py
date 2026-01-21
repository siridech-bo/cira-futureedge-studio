"""
Verify the hypothesis: CBOR files have interleaved format but loader expects channel-by-channel format.

Test both interpretations and see which produces correct waveform patterns.
"""

import cbor2
import numpy as np
import matplotlib.pyplot as plt

# Load a sine wave CBOR file
with open('Dataset/StandardWave/train/sine.1.cbor.6960fa8f.user-desktop.cbor', 'rb') as f:
    data = cbor2.load(f)

# Get first sample window
window = np.array(data['samples'][0]['data'])
print(f"Window size: {len(window)}")
print(f"First 30 values: {window[:30]}")

# Test two interpretations:

# Interpretation 1: Channel-by-channel (what loader expects)
# Format: [ch0_s0, ch0_s1, ..., ch0_s99, ch1_s0, ..., ch1_s99, ch2_s0, ..., ch2_s99]
num_channels = 3
samples_per_channel = len(window) // num_channels  # 300 / 3 = 100

ch0_format1 = window[0:samples_per_channel]
ch1_format1 = window[samples_per_channel:2*samples_per_channel]
ch2_format1 = window[2*samples_per_channel:3*samples_per_channel]

# Interpretation 2: Interleaved (what Dataset Recorder actually saves)
# Format: [ch0_s0, ch1_s0, ch2_s0, ch0_s1, ch1_s1, ch2_s1, ...]
ch0_format2 = window[0::3]  # Every 3rd element starting at 0
ch1_format2 = window[1::3]  # Every 3rd element starting at 1
ch2_format2 = window[2::3]  # Every 3rd element starting at 2

print(f"\n{'='*80}")
print("Interpretation 1: Channel-by-channel format")
print(f"{'='*80}")
print(f"Samples per channel: {samples_per_channel}")
print(f"Ch0 first 20: {ch0_format1[:20]}")
print(f"Ch0 range: [{ch0_format1.min():.3f}, {ch0_format1.max():.3f}]")
print(f"Ch0 mean: {ch0_format1.mean():.3f}")

# Check if it's a sine wave (should oscillate smoothly)
def is_smooth_sine(signal):
    """Check if signal looks like a smooth sine wave"""
    # Check for smooth transitions (no big jumps)
    diffs = np.abs(np.diff(signal))
    max_diff = np.max(diffs)
    avg_diff = np.mean(diffs)

    # Sine wave should have small, consistent differences
    # and values should span negative to positive
    has_range = (signal.max() > 0.5) and (signal.min() < -0.5)
    is_smooth = avg_diff < 0.5

    return has_range and is_smooth, avg_diff, max_diff

smooth1, avg_diff1, max_diff1 = is_smooth_sine(ch0_format1)
print(f"Is smooth sine? {smooth1}")
print(f"  Avg consecutive diff: {avg_diff1:.3f}, Max diff: {max_diff1:.3f}")

print(f"\n{'='*80}")
print("Interpretation 2: Interleaved format")
print(f"{'='*80}")
print(f"Samples per channel: {len(ch0_format2)}")
print(f"Ch0 first 20: {ch0_format2[:20]}")
print(f"Ch0 range: [{ch0_format2.min():.3f}, {ch0_format2.max():.3f}]")
print(f"Ch0 mean: {ch0_format2.mean():.3f}")

smooth2, avg_diff2, max_diff2 = is_smooth_sine(ch0_format2)
print(f"Is smooth sine? {smooth2}")
print(f"  Avg consecutive diff: {avg_diff2:.3f}, Max diff: {max_diff2:.3f}")

print(f"\n{'='*80}")
print("VERDICT:")
print(f"{'='*80}")

if smooth2 and not smooth1:
    print("✓ Hypothesis CONFIRMED: Data is in INTERLEAVED format")
    print("  - Interpretation 2 produces smooth sine wave")
    print("  - Interpretation 1 produces noisy/stepped signal")
    print("\nConclusion: CBOR loader is reading data incorrectly!")
elif smooth1 and not smooth2:
    print("✗ Hypothesis REJECTED: Data is in channel-by-channel format")
    print("  - Interpretation 1 produces smooth sine wave")
    print("  - Interpretation 2 produces noisy/stepped signal")
    print("\nConclusion: CBOR loader is correct. Problem elsewhere.")
else:
    print("? Inconclusive - both or neither look like sine waves")
    print(f"  Interpretation 1: smooth={smooth1}, avg_diff={avg_diff1:.3f}")
    print(f"  Interpretation 2: smooth={smooth2}, avg_diff={avg_diff2:.3f}")

# Plot both interpretations
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

axes[0].plot(ch0_format1[:100], label='Ch0', alpha=0.7)
axes[0].set_title('Interpretation 1: Channel-by-channel (what loader expects)')
axes[0].set_xlabel('Sample')
axes[0].set_ylabel('Value')
axes[0].grid(True, alpha=0.3)
axes[0].legend()

axes[1].plot(ch0_format2[:100], label='Ch0', alpha=0.7)
axes[1].set_title('Interpretation 2: Interleaved (hypothesis)')
axes[1].set_xlabel('Sample')
axes[1].set_ylabel('Value')
axes[1].grid(True, alpha=0.3)
axes[1].legend()

plt.tight_layout()
plt.savefig('data_format_comparison.png', dpi=150, bbox_inches='tight')
print(f"\n✓ Plot saved to: data_format_comparison.png")
print("  Open this file to visually compare the two interpretations.")
