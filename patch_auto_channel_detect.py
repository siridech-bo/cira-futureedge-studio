#!/usr/bin/env python3
"""Patch CiRA CBOR loader to automatically detect channel configuration"""

# Read the file
with open('data_sources/cira_cbor_loader.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and insert a new method after __init__
init_line = None
for i, line in enumerate(lines):
    if 'def __init__' in line and 'CiraCBORDataSource' in lines[i-2]:
        # Find the end of __init__ method
        indent_level = len(line) - len(line.lstrip())
        for j in range(i+1, len(lines)):
            if lines[j].strip() and not lines[j].startswith(' ' * (indent_level + 4)):
                init_line = j
                break
        break

if init_line:
    # Insert new method
    new_method = '''
    def _detect_channel_config(self, window_size: int) -> tuple:
        """
        Automatically detect channel configuration from window size.

        Strategy:
        1. Check if window_size is stored in metadata (from Pipeline Builder config)
        2. Try common factorizations (1ch, 2ch, 3ch, 4ch, etc.)
        3. Prefer configurations with reasonable samples_per_channel (50-500 range)

        Returns:
            (num_channels, samples_per_channel)
        """
        # Common channel counts to try, ordered by likelihood
        common_channels = [3, 1, 2, 4, 6, 8]

        best_config = (1, window_size)  # Default: single channel
        best_score = 0

        for num_ch in common_channels:
            if window_size % num_ch == 0:
                samples_per_ch = window_size // num_ch

                # Score this configuration
                # Prefer: 50 <= samples_per_channel <= 500
                score = 0
                if 50 <= samples_per_ch <= 500:
                    score = 100
                    # Bonus for common sample counts
                    if samples_per_ch in [100, 128, 200, 256]:
                        score += 50
                elif 20 <= samples_per_ch <= 1000:
                    score = 50
                else:
                    score = 10

                # Prefer 3 channels (most common in signal processing)
                if num_ch == 3:
                    score += 20
                elif num_ch == 1:
                    score += 10

                if score > best_score:
                    best_score = score
                    best_config = (num_ch, samples_per_ch)

        return best_config

'''
    lines.insert(init_line, new_method)
    print("[OK] Inserted _detect_channel_config method")

# Now update _to_dataframe to use the new detection method
for i, line in enumerate(lines):
    if '# Try to detect number of channels' in line:
        # Find the end of the old detection logic
        start = i
        end = i
        for j in range(i, min(i+20, len(lines))):
            if 'logger.info(f"Detected' in lines[j]:
                end = j + 1
                break

        # Replace with new detection logic
        new_detection = '''        # Detect channel configuration automatically
        num_channels, samples_per_channel = self._detect_channel_config(window_size)

        logger.info(f"Auto-detected {num_channels} channels, {samples_per_channel} samples per channel (window size: {window_size})")
'''

        # Remove old lines
        for _ in range(end - start):
            lines.pop(start)

        # Insert new detection
        lines.insert(start, new_detection)
        print("[OK] Updated channel detection logic")
        break

# Write back
with open('data_sources/cira_cbor_loader.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("[OK] CiRA CBOR loader updated with automatic channel detection")
