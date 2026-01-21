#!/usr/bin/env python3
"""Add channel configuration confirmation dialog to data panel"""

# Read the file
with open('ui/data_panel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import for simpledialog at the top
import_section = '''from tkinter import filedialog, messagebox'''
new_import = '''from tkinter import filedialog, messagebox, simpledialog'''

if import_section in content and 'simpledialog' not in content:
    content = content.replace(import_section, new_import)
    print("[OK] Added simpledialog import")

# Find the load_folder function in _load_edgeimpulse_train_test
# We need to add dialog after detection but before loading

old_code = '''            for file_path in all_files:
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
                                continue'''

new_code = '''            # Auto-detect channel configuration from first CBOR file
            channel_config_confirmed = False
            detected_channels = None
            detected_samples = None

            for idx, file_path in enumerate(all_files):
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
                            # First CBOR file with CiRA format - detect and confirm
                            if not channel_config_confirmed and isinstance(data_source, CiraCBORDataSource):
                                # Load just to get window size
                                import cbor2
                                with open(file_path, 'rb') as f:
                                    cbor_data = cbor2.load(f)
                                window_size = len(cbor_data['samples'][0]['data'])

                                # Auto-detect
                                num_ch, samples_per_ch = data_source._detect_channel_config(window_size)

                                # Show confirmation dialog
                                from tkinter import Toplevel, Label, Entry, Button, StringVar

                                dialog = Toplevel(self)
                                dialog.title("Confirm Channel Configuration")
                                dialog.geometry("450x200")
                                dialog.transient(self)
                                dialog.grab_set()

                                Label(dialog, text=f"Detected Window Size: {window_size} values",
                                      font=("Arial", 11, "bold")).pack(pady=10)
                                Label(dialog, text=f"Auto-detected Configuration:",
                                      font=("Arial", 10)).pack(pady=5)
                                Label(dialog, text=f"{num_ch} channel(s) × {samples_per_ch} samples per channel",
                                      font=("Arial", 12, "bold"), fg="blue").pack(pady=5)

                                # Manual override option
                                frame = ctk.CTkFrame(dialog)
                                frame.pack(pady=10)

                                Label(frame, text="Override - Number of channels:").grid(row=0, column=0, padx=5, pady=5)
                                channels_var = StringVar(value=str(num_ch))
                                channels_entry = Entry(frame, textvariable=channels_var, width=10)
                                channels_entry.grid(row=0, column=1, padx=5, pady=5)

                                confirmed = [False]
                                user_channels = [num_ch]

                                def on_confirm():
                                    try:
                                        user_ch = int(channels_var.get())
                                        if user_ch < 1 or user_ch > 32:
                                            messagebox.showerror("Invalid Input", "Number of channels must be between 1 and 32")
                                            return
                                        if window_size % user_ch != 0:
                                            messagebox.showerror("Invalid Input",
                                                f"Window size {window_size} is not divisible by {user_ch} channels")
                                            return
                                        user_channels[0] = user_ch
                                        confirmed[0] = True
                                        dialog.destroy()
                                    except ValueError:
                                        messagebox.showerror("Invalid Input", "Please enter a valid number")

                                def on_cancel():
                                    dialog.destroy()

                                btn_frame = ctk.CTkFrame(dialog)
                                btn_frame.pack(pady=10)
                                Button(btn_frame, text="✓ Confirm", command=on_confirm,
                                       bg="green", fg="white", width=12).grid(row=0, column=0, padx=5)
                                Button(btn_frame, text="✗ Cancel", command=on_cancel,
                                       bg="red", fg="white", width=12).grid(row=0, column=1, padx=5)

                                dialog.wait_window()

                                if not confirmed[0]:
                                    logger.info("User cancelled channel configuration")
                                    return pd.DataFrame(), set(), []

                                detected_channels = user_channels[0]
                                detected_samples = window_size // detected_channels
                                channel_config_confirmed = True

                                logger.info(f"User confirmed: {detected_channels} channels × {detected_samples} samples")

                                # Override the detection method for this session
                                original_detect = data_source._detect_channel_config
                                data_source._detect_channel_config = lambda w: (detected_channels, detected_samples)'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("[OK] Added channel configuration confirmation dialog")
else:
    print("[WARNING] Could not find code section to patch")

# Write back
with open('ui/data_panel.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Channel configuration dialog added")
