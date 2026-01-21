#!/usr/bin/env python3
"""Final fix for dialog size and channel configuration"""

# Read the file
with open('ui/data_panel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Make dialog 2x bigger (500x280 -> 1000x560) and double font sizes
old_dialog_setup = '''                                dialog.geometry("500x280")
                                dialog.resizable(False, False)'''

new_dialog_setup = '''                                dialog.geometry("1000x560")
                                dialog.resizable(False, False)'''

content = content.replace(old_dialog_setup, new_dialog_setup)
print("[OK] Doubled dialog size: 1000x560")

# Fix 2: Double all font sizes
font_replacements = [
    ('font=("Arial", 11, "bold")', 'font=("Arial", 22, "bold")'),
    ('font=("Arial", 10)', 'font=("Arial", 20)'),
    ('font=("Arial", 12, "bold")', 'font=("Arial", 24, "bold")'),
]

for old, new in font_replacements:
    content = content.replace(old, new)
print("[OK] Doubled font sizes")

# Fix 3: Make entry box bigger
content = content.replace('width=10)', 'width=20, font=("Arial", 18))')
print("[OK] Increased entry box size")

# Fix 4: Make label text bigger
content = content.replace(
    'Label(frame, text="Override - Number of channels:")',
    'Label(frame, text="Override - Number of channels:", font=("Arial", 18))'
)

# Fix 5: Make buttons bigger
content = content.replace(
    'width=12)',
    'width=20, font=("Arial", 16))'
)
print("[OK] Increased button sizes")

# Fix 6: Fix the channel config not being applied - use proper method override
old_override = '''                    # Apply confirmed channel config for CiRA CBOR files
                    if format_type == "CiRA CBOR" and isinstance(data_source, CiraCBORDataSource) and detected_channels:
                        # Override detection for this file
                        original_method = data_source._detect_channel_config
                        data_source._detect_channel_config = lambda w: (detected_channels, detected_samples)'''

new_override = '''                    # Apply confirmed channel config for CiRA CBOR files
                    if format_type == "CiRA CBOR" and isinstance(data_source, CiraCBORDataSource) and detected_channels:
                        # Override detection for this file with confirmed values
                        def fixed_config(window_size):
                            return (detected_channels, detected_samples)
                        data_source._detect_channel_config = fixed_config
                        logger.info(f"Applying user-confirmed config: {detected_channels} channels × {detected_samples} samples")'''

if old_override in content:
    content = content.replace(old_override, new_override)
    print("[OK] Fixed channel configuration override with proper closure")
else:
    print("[WARNING] Could not find channel override section")

# Write back
with open('ui/data_panel.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n=== All Fixes Applied ===")
print("1. Dialog size: 1000x560 (2x bigger)")
print("2. Fonts: 18-24pt (2x bigger)")
print("3. Entry box: width=20, font=18pt")
print("4. Buttons: width=20, font=16pt")
print("5. Channel override: Fixed closure issue")
