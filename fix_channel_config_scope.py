#!/usr/bin/env python3
"""
Fix channel configuration scope issue.
The detected_channels/detected_samples are inside load_folder() nested function,
so they're not accessible in the outer scope when setting up UI data source.

Fix: Return these values from load_folder and capture them.
"""

import re

def fix_scope():
    with open('ui/data_panel.py', 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Fix 1: Modify return statement of load_folder to include channel config
    old_return = """            # Fix time column
            if 'time' in combined_df.columns:
                combined_df['time'] = range(len(combined_df))

            return combined_df, class_labels, all_files"""

    new_return = """            # Fix time column
            if 'time' in combined_df.columns:
                combined_df['time'] = range(len(combined_df))

            return combined_df, class_labels, all_files, detected_channels, detected_samples"""

    if old_return in content:
        content = content.replace(old_return, new_return)
        print("[OK] Step 1: Modified load_folder return statement")
    else:
        print("[WARNING] Could not find return statement to modify")

    # Fix 2: Update train folder call to capture channel config
    old_train = "        # Load training data\n        train_df, train_classes, train_files = load_folder(train_folder, \"training\")"
    new_train = "        # Load training data\n        train_df, train_classes, train_files, train_detected_ch, train_detected_samp = load_folder(train_folder, \"training\")"

    if old_train in content:
        content = content.replace(old_train, new_train)
        print("[OK] Step 2: Updated train folder call")
    else:
        print("[WARNING] Could not find train folder call")

    # Fix 3: Update test folder call to capture channel config
    old_test = "            test_df, test_classes, test_files = load_folder(test_folder, \"test\")"
    new_test = "            test_df, test_classes, test_files, test_detected_ch, test_detected_samp = load_folder(test_folder, \"test\")"

    if old_test in content:
        content = content.replace(old_test, new_test)
        print("[OK] Step 3: Updated test folder call")
    else:
        print("[WARNING] Could not find test folder call")

    # Fix 4: Replace the UI data source setup to use captured values
    old_ui_setup = """        if format_type == "CiRA CBOR":
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
                self.current_data_source.load_data()"""

    new_ui_setup = """        if format_type == "CiRA CBOR":
            self.current_data_source = CiraCBORDataSource()
            self.current_data_source.file_path = Path(train_files[0])
            if self.current_data_source.connect():
                # Apply the user-confirmed channel configuration (captured from load_folder)
                if train_detected_ch is not None:
                    def fixed_config(window_size):
                        return (train_detected_ch, train_detected_samp)
                    self.current_data_source._detect_channel_config = fixed_config
                    logger.info(f"Applied confirmed config to UI data source: {train_detected_ch} ch × {train_detected_samp} samples")
                else:
                    logger.info("No channel config from this session - using auto-detection for UI preview")
                self.current_data_source.load_data()"""

    if old_ui_setup in content:
        content = content.replace(old_ui_setup, new_ui_setup)
        print("[OK] Step 4: Updated UI data source setup")
    else:
        print("[WARNING] Could not find UI data source setup")

    if content != original:
        with open('ui/data_panel.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("\n=== All fixes applied successfully ===")
        return True
    else:
        print("\n[ERROR] No changes were made")
        return False

if __name__ == "__main__":
    fix_scope()
