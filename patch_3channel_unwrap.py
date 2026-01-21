#!/usr/bin/env python3
"""Patch CiRA CBOR loader to properly unwrap multi-channel windows"""

# Read the file
with open('data_sources/cira_cbor_loader.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the _to_dataframe method
old_method = '''    def _to_dataframe(self) -> pd.DataFrame:
        """Convert CiRA CBOR data to pandas DataFrame

        Each sample contains a window of data (e.g. 300 values).
        We unwrap these windows into a continuous time series.
        """
        samples = self.raw_data['samples']

        # Build DataFrame by unwrapping windows
        rows = []
        time_index = 0.0

        # Calculate time increment per sample within window
        # Estimate based on window intervals
        window_interval_ms = self.metadata.get('interval_ms', 100)
        window_size = len(samples[0]['data']) if samples else 1
        sample_interval_sec = (window_interval_ms / 1000.0) / window_size

        for sample in samples:
            # Get window data
            window_data = sample['data']
            class_name = sample['class_name']

            # Each value in the window becomes a separate row
            for value in window_data:
                row = {
                    'time': time_index,
                    'signal': value,
                    'class_label': class_name
                }
                rows.append(row)
                time_index += sample_interval_sec

        df = pd.DataFrame(rows)

        # Reset time to start from 0
        if len(df) > 0:
            df['time'] = df['time'] - df['time'].iloc[0]

        return df'''

new_method = '''    def _to_dataframe(self) -> pd.DataFrame:
        """Convert CiRA CBOR data to pandas DataFrame

        Each sample contains a window of merged multi-channel data.
        For example: 300 values = 3 channels × 100 samples per channel
        Window layout: [ch0_s0, ch0_s1, ..., ch0_s99, ch1_s0, ..., ch1_s99, ch2_s0, ..., ch2_s99]

        We need to detect number of channels and unwrap accordingly.
        """
        samples = self.raw_data['samples']

        if not samples:
            return pd.DataFrame()

        window_size = len(samples[0]['data'])

        # Try to detect number of channels
        # Common window sizes: 300 (3ch×100), 100 (1ch×100), 600 (3ch×200)
        num_channels = 1
        samples_per_channel = window_size

        # Heuristic: if window size is divisible by 3 and > 100, assume 3 channels
        if window_size >= 300 and window_size % 3 == 0:
            num_channels = 3
            samples_per_channel = window_size // 3
        elif window_size >= 200 and window_size % 2 == 0:
            num_channels = 2
            samples_per_channel = window_size // 2

        logger.info(f"Detected {num_channels} channels, {samples_per_channel} samples per channel")

        # Build DataFrame by unwrapping windows
        rows = []
        time_index = 0.0

        # Calculate time increment per sample within window
        window_interval_ms = self.metadata.get('interval_ms', 100)
        sample_interval_sec = (window_interval_ms / 1000.0) / samples_per_channel

        for sample in samples:
            window_data = sample['data']
            class_name = sample['class_name']

            # Reshape window data: [ch0_samples, ch1_samples, ch2_samples, ...]
            # into rows: [(ch0_val, ch1_val, ch2_val), ...]
            for i in range(samples_per_channel):
                row = {
                    'time': time_index,
                    'class_label': class_name
                }

                # Extract values for each channel at sample position i
                for ch in range(num_channels):
                    channel_offset = ch * samples_per_channel
                    row[f'ch{ch}'] = window_data[channel_offset + i]

                rows.append(row)
                time_index += sample_interval_sec

        df = pd.DataFrame(rows)

        # Reset time to start from 0
        if len(df) > 0:
            df['time'] = df['time'] - df['time'].iloc[0]

        return df'''

if old_method in content:
    content = content.replace(old_method, new_method)
    print("[OK] Patched _to_dataframe to properly unwrap multi-channel windows")
else:
    print("[WARNING] Could not find method to replace")

# Write back
with open('data_sources/cira_cbor_loader.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] CiRA CBOR loader updated for multi-channel support")
