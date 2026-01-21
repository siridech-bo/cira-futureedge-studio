#!/usr/bin/env python3
"""Fix variable scope and project reload issues"""

# Read the file
with open('ui/data_panel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Move variable declarations OUTSIDE the for loop
old_loop_start = '''            # Auto-detect channel configuration from first CBOR file
            channel_config_confirmed = False
            detected_channels = None
            detected_samples = None

            for idx, file_path in enumerate(all_files):'''

# Already correct, but let's ensure the application section uses proper checks

# Fix 2: Check if variables are defined before using them
old_application = '''        # Store data source reference - use appropriate loader based on format
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
                self.current_data_source.load_data()'''

new_application = '''        # Store data source reference - use appropriate loader based on format
        if format_type == "CiRA CBOR":
            self.current_data_source = CiraCBORDataSource()
            self.current_data_source.file_path = Path(train_files[0])
            if self.current_data_source.connect():
                # Apply the user-confirmed channel configuration (if available from this session)
                if 'detected_channels' in locals() and detected_channels:
                    def fixed_config(window_size):
                        return (detected_channels, detected_samples)
                    self.current_data_source._detect_channel_config = fixed_config
                    logger.info(f"Applied confirmed config to UI data source: {detected_channels} ch × {detected_samples} samples")
                else:
                    logger.info("No channel config from this session - using auto-detection for UI preview")
                self.current_data_source.load_data()'''

if old_application in content:
    content = content.replace(old_application, new_application)
    print("[OK] Fixed variable scope check for detected_channels")
else:
    print("[WARNING] Could not find application section")

# Fix 3: When reloading project, detect format correctly
old_reload = '''        # Detect format from file extension
        source_files = []
        if os.path.isdir(project.data.train_folder_path):
            source_files = [f for f in os.listdir(project.data.train_folder_path)
                          if f.endswith(('.json', '.cbor'))]

        if source_files:
            # Use first file to detect format
            first_file = source_files[0]
            if first_file.endswith('.json'):
                format_type = "json"
            else:  # .cbor
                format_type = "cbor"
            logger.info(f"Detected source format from file extension: {format_type}")'''

new_reload = '''        # Detect format from file extension and project settings
        source_files = []
        if os.path.isdir(project.data.train_folder_path):
            source_files = [f for f in os.listdir(project.data.train_folder_path)
                          if f.endswith(('.json', '.cbor'))]

        if source_files:
            # Check if project has source_type saved (from initial load)
            if hasattr(project.data, 'source_type') and project.data.source_type:
                format_type = project.data.source_type
                logger.info(f"Using saved source format from project: {format_type}")
            else:
                # Use first file to detect format
                first_file = source_files[0]
                if first_file.endswith('.json'):
                    format_type = "Edge Impulse JSON"
                else:  # .cbor - default to CiRA CBOR for better compatibility
                    format_type = "CiRA CBOR"
                logger.info(f"Detected source format from file extension: {format_type}")'''

if old_reload in content:
    content = content.replace(old_reload, new_reload)
    print("[OK] Fixed project reload format detection")
else:
    print("[WARNING] Could not find reload section")

# Write back
with open('ui/data_panel.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n=== Fixes Applied ===")
print("1. Added scope check for detected_channels variable")
print("2. Project reload now uses saved source_type from project")
print("3. Falls back to 'CiRA CBOR' for .cbor files on reload")
