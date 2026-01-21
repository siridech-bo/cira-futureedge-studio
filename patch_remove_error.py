#!/usr/bin/env python3
"""Fix data source reference to prevent error message"""

# Read the file
with open('ui/data_panel.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and replace lines 1563-1568
found = False
for i in range(len(lines)):
    if i == 1563 and '# Store data source reference' in lines[i]:
        # Replace the next 5 lines
        lines[1563] = '        # Store data source reference - use appropriate loader based on format\n'
        lines[1564] = '        if format_type == "CiRA CBOR":\n'
        lines[1565] = '            self.current_data_source = CiraCBORDataSource()\n'
        lines[1566] = '            self.current_data_source.file_path = Path(train_files[0])\n'
        lines[1567] = '            if self.current_data_source.connect():\n'
        lines[1568] = '                self.current_data_source.load_data()\n'
        # Insert new lines for else block
        lines.insert(1569, '        else:\n')
        lines.insert(1570, '            self.current_data_source = EdgeImpulseDataSource()\n')
        lines.insert(1571, '            self.current_data_source.file_path = Path(train_files[0])\n')
        lines.insert(1572, '            self.current_data_source.format_type = internal_format\n')
        lines.insert(1573, '            if self.current_data_source.connect():\n')
        lines.insert(1574, '                self.current_data_source.load_data()\n')
        found = True
        print("[OK] Fixed data source reference to prevent error")
        break

if not found:
    print("[WARNING] Could not find target lines to patch")

# Write back
with open('ui/data_panel.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("[OK] Patched ui/data_panel.py to remove error message")
