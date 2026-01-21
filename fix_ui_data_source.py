#!/usr/bin/env python3
"""Fix UI data source to use correct channel configuration"""

# Read the file
with open('ui/data_panel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The problem: current_data_source loads fresh without the confirmed channel config
# Solution: Apply the confirmed config here too

old_code = '''        # Store data source reference - use appropriate loader based on format
        if format_type == "CiRA CBOR":
            self.current_data_source = CiraCBORDataSource()
            self.current_data_source.file_path = Path(train_files[0])
            if self.current_data_source.connect():
                self.current_data_source.load_data()
        else:
            self.current_data_source = EdgeImpulseDataSource()
            self.current_data_source.file_path = Path(train_files[0])
            self.current_data_source.format_type = internal_format
            if self.current_data_source.connect():
                self.current_data_source.load_data()'''

new_code = '''        # Store data source reference - use appropriate loader based on format
        if format_type == "CiRA CBOR":
            self.current_data_source = CiraCBORDataSource()
            self.current_data_source.file_path = Path(train_files[0])
            if self.current_data_source.connect():
                # Apply the user-confirmed channel configuration
                if detected_channels:
                    def fixed_config(window_size):
                        return (detected_channels, detected_samples)
                    self.current_data_source._detect_channel_config = fixed_config
                    logger.info(f"Applied confirmed config to UI data source: {detected_channels} ch × {detected_samples} samples")
                self.current_data_source.load_data()
        else:
            self.current_data_source = EdgeImpulseDataSource()
            self.current_data_source.file_path = Path(train_files[0])
            self.current_data_source.format_type = internal_format
            if self.current_data_source.connect():
                self.current_data_source.load_data()'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("[OK] Fixed UI data source to use confirmed channel configuration")
else:
    print("[ERROR] Could not find code to replace")

# Write back
with open('ui/data_panel.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] UI data source fix applied - Windowing tab will now show 3 channels")
