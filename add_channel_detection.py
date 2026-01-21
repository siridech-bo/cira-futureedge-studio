#!/usr/bin/env python3
"""Add _detect_channel_config method to CiRA CBOR loader"""

# Read the file
with open('data_sources/cira_cbor_loader.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new method
new_method = '''
    def _detect_channel_config(self, window_size: int) -> tuple:
        """
        Automatically detect channel configuration from window size.

        Strategy:
        1. Try common factorizations (1ch, 2ch, 3ch, 4ch, etc.)
        2. Prefer configurations with reasonable samples_per_channel (50-500 range)
        3. Use scoring to pick the most likely configuration

        Returns:
            (num_channels, samples_per_channel)
        """
        # Common channel counts to try, ordered by likelihood
        common_channels = [3, 1, 2, 4, 6, 8, 12, 16]

        best_config = (1, window_size)  # Default: single channel
        best_score = 0

        for num_ch in common_channels:
            if window_size % num_ch == 0:
                samples_per_ch = window_size // num_ch

                # Score this configuration
                score = 0

                # Prefer: 50 <= samples_per_channel <= 500
                if 50 <= samples_per_ch <= 500:
                    score = 100
                    # Bonus for common sample counts (powers of 2, multiples of 50/100)
                    if samples_per_ch in [50, 100, 128, 150, 200, 256, 300, 400, 500]:
                        score += 50
                elif 20 <= samples_per_ch <= 1000:
                    score = 50
                else:
                    score = 10

                # Prefer common channel counts
                if num_ch == 3:  # Most common in accelerometer/gyro (x,y,z)
                    score += 20
                elif num_ch == 1:  # Single sensor
                    score += 10
                elif num_ch == 6:  # IMU (accel + gyro)
                    score += 15
                elif num_ch in [2, 4, 8]:  # Common powers of 2
                    score += 5

                if score > best_score:
                    best_score = score
                    best_config = (num_ch, samples_per_ch)

        return best_config
'''

# Find where to insert (before _to_dataframe method)
insert_marker = '    def _to_dataframe(self) -> pd.DataFrame:'
if insert_marker in content:
    content = content.replace(insert_marker, new_method + '\n' + insert_marker)
    print("[OK] Added _detect_channel_config method")
else:
    print("[ERROR] Could not find insertion point")

# Write back
with open('data_sources/cira_cbor_loader.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Channel detection method added successfully")
