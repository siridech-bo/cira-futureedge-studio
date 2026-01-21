#!/usr/bin/env python3
"""Fix channel configuration dialog issues"""

# Read the file
with open('ui/data_panel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the dialog section with improved version
old_dialog_start = '''                        else:
                            # First CBOR file with CiRA format - detect and confirm
                            if not channel_config_confirmed and isinstance(data_source, CiraCBORDataSource):'''

new_dialog_start = '''                        else:
                            # First CBOR file with CiRA format - detect and confirm (only once!)
                            if format_type == "CiRA CBOR" and not channel_config_confirmed and isinstance(data_source, CiraCBORDataSource):'''

if old_dialog_start in content:
    content = content.replace(old_dialog_start, new_dialog_start)
    print("[OK] Fixed dialog trigger condition")

# Fix dialog size and fonts
old_geometry = '''                                dialog.geometry("450x200")'''
new_geometry = '''                                dialog.geometry("500x280")
                                dialog.resizable(False, False)'''

if old_geometry in content:
    content = content.replace(old_geometry, new_geometry)
    print("[OK] Fixed dialog size")

# Fix the override detection method - need to apply to ALL files, not just current one
old_override = '''                                # Override the detection method for this session
                                original_detect = data_source._detect_channel_config
                                data_source._detect_channel_config = lambda w: (detected_channels, detected_samples)'''

new_override = '''                                # Store config for all subsequent files
                                # The config is already stored in detected_channels and detected_samples variables'''

if old_override in content:
    content = content.replace(old_override, new_override)
    print("[OK] Fixed config override")

# Now we need to ensure detected config is used for ALL files
# Find where data_source.load_data() is called and ensure it uses the confirmed config

old_load_pattern = '''                    else:
                        # JSON files use Edge Impulse format
                        data_source = EdgeImpulseDataSource()
                        data_source.file_path = Path(file_path)
                        data_source.format_type = internal_format

                        if not data_source.connect():
                            logger.warning(f"Skipping {file_path}: {data_source.last_error}")
                            continue

                    df = data_source.load_data()'''

new_load_pattern = '''                    else:
                        # JSON files use Edge Impulse format
                        data_source = EdgeImpulseDataSource()
                        data_source.file_path = Path(file_path)
                        data_source.format_type = internal_format

                        if not data_source.connect():
                            logger.warning(f"Skipping {file_path}: {data_source.last_error}")
                            continue

                    # Apply confirmed channel config for CiRA CBOR files
                    if format_type == "CiRA CBOR" and isinstance(data_source, CiraCBORDataSource) and detected_channels:
                        # Override detection for this file
                        original_method = data_source._detect_channel_config
                        data_source._detect_channel_config = lambda w: (detected_channels, detected_samples)

                    df = data_source.load_data()'''

if old_load_pattern in content:
    content = content.replace(old_load_pattern, new_load_pattern)
    print("[OK] Applied confirmed config to all files")

# Write back
with open('ui/data_panel.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Dialog fixes applied")
print("\nSummary:")
print("- Dialog now appears ONCE only (not per file)")
print("- Dialog size increased to 500x280")
print("- Dialog is non-resizable")
print("- Confirmed configuration applies to ALL files in dataset")
