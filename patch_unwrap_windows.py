#!/usr/bin/env python3
"""Patch CiRA CBOR loader to unwrap windows into time series"""

# Read the file
with open('data_sources/cira_cbor_loader.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the _to_dataframe method
old_method = '''    def _to_dataframe(self) -> pd.DataFrame:
        """Convert CiRA CBOR data to pandas DataFrame"""
        samples = self.raw_data['samples']

        # Build DataFrame
        rows = []
        for sample in samples:
            row = {}

            # Add timestamp (convert ms to seconds)
            row['time'] = sample['timestamp'] / 1000.0

            # Add class label
            row['class_label'] = sample['class_name']

            # Add data channels
            data = sample['data']
            if len(data) == 1:
                # Single channel
                row['signal'] = data[0]
            else:
                # Multiple channels
                for i, val in enumerate(data):
                    row[f'ch{i}'] = val

            rows.append(row)

        df = pd.DataFrame(rows)

        # Reset time to start from 0
        if 'time' in df.columns:
            df['time'] = df['time'] - df['time'].iloc[0]

        return df'''

new_method = '''    def _to_dataframe(self) -> pd.DataFrame:
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

if old_method in content:
    content = content.replace(old_method, new_method)
    print("[OK] Patched _to_dataframe to unwrap windows")
else:
    print("[WARNING] Could not find method to replace")

# Write back
with open('data_sources/cira_cbor_loader.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] CiRA CBOR loader updated to unwrap windows into time series")
