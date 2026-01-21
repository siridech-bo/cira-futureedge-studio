#!/usr/bin/env python3
"""
Fix windowing to use sensor columns from pickle data instead of UI data source.

The bug: When windowing, it detects sensor columns from self.current_data_source
(which loads a fresh CBOR file with 300-value windows), but then applies those
columns to the pickle file (which has 3 channels).

The fix: Detect sensor columns from the actual pickle data being windowed.
"""

def fix_windowing():
    with open('ui/data_panel.py', 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Fix: Detect sensor columns from pickle data instead of UI data source
    old_code = """            # Check if we have separate train/test data
            project = self.project_manager.current_project
            if project and project.data.train_test_split_type == "manual":
                # Load and window train/test data separately
                import pickle

                self.progress_label.configure(text="Windowing training data...")
                self.progress_bar.set(0.4)
                self.update_idletasks()

                # Window training data
                with open(project.data.train_data_file, 'rb') as f:
                    train_data = pickle.load(f)

                train_windows = self.windowing_engine.segment_data(
                    train_data,
                    sensor_columns=sensor_columns,
                    time_column=time_column,
                    label_column=label_column
                )"""

    new_code = """            # Check if we have separate train/test data
            project = self.project_manager.current_project
            if project and project.data.train_test_split_type == "manual":
                # Load and window train/test data separately
                import pickle

                self.progress_label.configure(text="Windowing training data...")
                self.progress_bar.set(0.4)
                self.update_idletasks()

                # Window training data
                with open(project.data.train_data_file, 'rb') as f:
                    train_data = pickle.load(f)

                # For manual train/test split, detect sensor columns from the actual pickle data
                # instead of from UI data source (which may have pre-windowed data)
                actual_sensor_columns = [col for col in train_data.columns
                                        if col not in ['time', 'label', 'class_label', 'timestamp', '_source_file']]
                logger.info(f"Detected {len(actual_sensor_columns)} sensor columns from pickle data: {actual_sensor_columns}")

                train_windows = self.windowing_engine.segment_data(
                    train_data,
                    sensor_columns=actual_sensor_columns,
                    time_column=time_column,
                    label_column=label_column
                )"""

    if old_code in content:
        content = content.replace(old_code, new_code)
        print("[OK] Fixed train windowing to use pickle data columns")
    else:
        print("[WARNING] Could not find train windowing code")

    # Also fix test windowing
    old_test = """                # Window test data if available
                test_windows = []
                if project.data.test_data_file:
                    with open(project.data.test_data_file, 'rb') as f:
                        test_data = pickle.load(f)

                    test_windows = self.windowing_engine.segment_data(
                        test_data,
                        sensor_columns=sensor_columns,
                        time_column=time_column,
                        label_column=label_column
                    )"""

    new_test = """                # Window test data if available
                test_windows = []
                if project.data.test_data_file:
                    with open(project.data.test_data_file, 'rb') as f:
                        test_data = pickle.load(f)

                    # Use same sensor columns from pickle data
                    test_sensor_columns = [col for col in test_data.columns
                                          if col not in ['time', 'label', 'class_label', 'timestamp', '_source_file']]

                    test_windows = self.windowing_engine.segment_data(
                        test_data,
                        sensor_columns=test_sensor_columns,
                        time_column=time_column,
                        label_column=label_column
                    )"""

    if old_test in content:
        content = content.replace(old_test, new_test)
        print("[OK] Fixed test windowing to use pickle data columns")
    else:
        print("[WARNING] Could not find test windowing code")

    if content != original:
        with open('ui/data_panel.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("\n=== Windowing fix applied ===")
        return True
    else:
        print("\n[ERROR] No changes made")
        return False

if __name__ == "__main__":
    fix_windowing()
