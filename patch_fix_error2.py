#!/usr/bin/env python3
"""Fix data source reference to prevent error message - version 2"""

# Read the file
with open('ui/data_panel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the problematic section
old_code = '''        # Store data source reference
        self.current_data_source = EdgeImpulseDataSource()
        self.current_data_source.file_path = Path(train_files[0])
        self.current_data_source.format_type = internal_format  # Use internal format
        self.current_data_source.connect()
        self.current_data_source.load_data()'''

new_code = '''        # Store data source reference - use appropriate loader based on format
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

if old_code in content:
    content = content.replace(old_code, new_code)
    print("[OK] Fixed data source reference to use correct loader")
else:
    print("[WARNING] Could not find exact code to replace")

# Write back
with open('ui/data_panel.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Patch applied successfully")
