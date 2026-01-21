#!/usr/bin/env python3
"""Patch data_panel.py to support CiRA CBOR format"""

import re

# Read the file
with open('ui/data_panel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the loader logic
old_pattern = r'''            for file_path in all_files:
                try:
                    data_source = EdgeImpulseDataSource\(\)
                    data_source\.file_path = Path\(file_path\)
                    data_source\.format_type = internal_format

                    if not data_source\.connect\(\):
                        logger\.warning\(f"Skipping \{file_path\}: \{data_source\.last_error\}"\)
                        continue

                    df = data_source\.load_data\(\)'''

new_code = '''            for file_path in all_files:
                try:
                    # Try CiRA CBOR format first for CBOR files, fallback to Edge Impulse
                    if file_path.endswith('.cbor'):
                        data_source = CiraCBORDataSource()
                        data_source.file_path = Path(file_path)

                        if not data_source.connect():
                            # Try Edge Impulse format as fallback
                            data_source = EdgeImpulseDataSource()
                            data_source.file_path = Path(file_path)
                            data_source.format_type = 'cbor'

                            if not data_source.connect():
                                logger.warning(f"Skipping {file_path}: {data_source.last_error}")
                                continue
                    else:
                        # JSON files use Edge Impulse format
                        data_source = EdgeImpulseDataSource()
                        data_source.file_path = Path(file_path)
                        data_source.format_type = internal_format

                        if not data_source.connect():
                            logger.warning(f"Skipping {file_path}: {data_source.last_error}")
                            continue

                    df = data_source.load_data()'''

# Replace
content = re.sub(old_pattern, new_code, content, flags=re.MULTILINE)

# Write back
with open('ui/data_panel.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Patched ui/data_panel.py to support CiRA CBOR format")
