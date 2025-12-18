"""
CiRA FutureEdge Studio - Deployment Wizard
5-step wizard for deploying trained models to embedded hardware
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path
from typing import Optional, Dict, List
import json
from loguru import logger

from core.deployment.deployment_mapper import DeploymentMapper


class DeploymentWizard(ctk.CTkToplevel):
    """
    5-step deployment wizard for hardware deployment.

    Steps:
    1. Platform Selection (ESP32, Jetson, Arduino Nano 33)
    2. Sensor Configuration (auto-detected + manual override)
    3. Pin Configuration (I2C, sampling rate)
    4. Output Actions (LED, Serial, MQTT, etc.)
    5. Generate & Review
    """

    def __init__(self, parent, project_file: Path):
        """
        Initialize deployment wizard.

        Args:
            parent: Parent window
            project_file: Path to .ciraproject file
        """
        super().__init__(parent)

        self.title("Deploy to Hardware - Step 1 of 5")
        self.geometry("800x600")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self.project_file = project_file
        self.mapper = DeploymentMapper()
        self.current_step = 1
        self.max_steps = 5

        # Load project metadata
        try:
            self.project_metadata = self.mapper.load_project_metadata(project_file)
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            messagebox.showerror("Error", f"Failed to load project:\n{e}")
            self.destroy()
            return

        # User configuration (accumulated through wizard steps)
        self.config = {
            'platform': 'esp32',  # Default
            'sensor': None,
            'sensor_config': {},
            'actions': [],
            'project_name': self.project_metadata['project_name']
        }

        # Auto-detect sensor
        self.suggested_sensor = self.mapper.suggest_sensor(
            self.project_metadata['sensor_columns']
        )

        # Create UI
        self._create_ui()
        self._show_step(1)

    def _create_ui(self):
        """Create wizard UI structure."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header = ctk.CTkLabel(
            self,
            text="Deploy to Hardware - Step 1 of 5",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Content frame (changes per step)
        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Progress bar
        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.progress.set(0.2)  # Step 1 of 5

        # Navigation buttons
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        nav_frame.grid_columnconfigure(1, weight=1)

        self.back_btn = ctk.CTkButton(
            nav_frame,
            text="← Back",
            command=self._previous_step,
            width=120
        )
        self.back_btn.grid(row=0, column=0, padx=(0, 10))

        self.next_btn = ctk.CTkButton(
            nav_frame,
            text="Next →",
            command=self._next_step,
            width=120
        )
        self.next_btn.grid(row=0, column=2)

        self.cancel_btn = ctk.CTkButton(
            nav_frame,
            text="Cancel",
            command=self.destroy,
            width=120,
            fg_color="gray40",
            hover_color="gray30"
        )
        self.cancel_btn.grid(row=0, column=3, padx=(10, 0))

    def _show_step(self, step: int):
        """Display content for specific step."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.current_step = step
        self.header.configure(text=f"Deploy to Hardware - Step {step} of {self.max_steps}")
        self.progress.set(step / self.max_steps)

        # Show appropriate step content
        if step == 1:
            self._create_step1_platform()
        elif step == 2:
            self._create_step2_sensor()
        elif step == 3:
            self._create_step3_pins()
        elif step == 4:
            self._create_step4_actions()
        elif step == 5:
            self._create_step5_review()

        # Update button states
        self.back_btn.configure(state="normal" if step > 1 else "disabled")
        self.next_btn.configure(
            text="Generate Firmware" if step == self.max_steps else "Next →"
        )

    def _create_step1_platform(self):
        """Step 1: Platform selection."""
        ctk.CTkLabel(
            self.content_frame,
            text="Select Target Hardware Platform",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, pady=(0, 20), sticky="w")

        # Platform options
        platforms = [
            {
                "id": "esp32",
                "name": "ESP32 DevKit",
                "icon": "⚡",
                "specs": "240MHz Dual-core, WiFi/BT, 520KB RAM",
                "price": "$10",
                "best_for": "IoT projects, wireless connectivity"
            },
            {
                "id": "jetson",
                "name": "NVIDIA Jetson Nano",
                "icon": "🚀",
                "specs": "Quad-core ARM, 128-core GPU, 4GB RAM",
                "price": "$99",
                "best_for": "Computer vision, complex ML models"
            },
            {
                "id": "nano33",
                "name": "Arduino Nano 33 BLE",
                "icon": "🔋",
                "specs": "64MHz ARM, Built-in IMU, BLE 5.0",
                "price": "$33",
                "best_for": "Low power, built-in sensors"
            }
        ]

        self.platform_var = ctk.StringVar(value=self.config['platform'])

        for i, platform in enumerate(platforms):
            frame = ctk.CTkFrame(self.content_frame)
            frame.grid(row=i+1, column=0, sticky="ew", pady=5)
            frame.grid_columnconfigure(1, weight=1)

            # Radio button with icon
            radio = ctk.CTkRadioButton(
                frame,
                text=f"{platform['icon']} {platform['name']}",
                variable=self.platform_var,
                value=platform['id'],
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda p=platform['id']: self._on_platform_change(p)
            )
            radio.grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 5), sticky="w")

            # Specs
            ctk.CTkLabel(
                frame,
                text=f"Specs: {platform['specs']}",
                font=ctk.CTkFont(size=11),
                text_color="gray60"
            ).grid(row=1, column=0, columnspan=2, padx=35, sticky="w")

            # Best for
            ctk.CTkLabel(
                frame,
                text=f"Best for: {platform['best_for']}",
                font=ctk.CTkFont(size=11),
                text_color="gray60"
            ).grid(row=2, column=0, columnspan=2, padx=35, pady=(0, 10), sticky="w")

            # Price badge
            price_label = ctk.CTkLabel(
                frame,
                text=platform['price'],
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="green"
            )
            price_label.grid(row=0, column=2, padx=15, pady=10, sticky="e")

    def _create_step2_sensor(self):
        """Step 2: Sensor configuration."""
        ctk.CTkLabel(
            self.content_frame,
            text="Configure Input Sensor",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, pady=(0, 10), sticky="w")

        # Show model requirements
        info_frame = ctk.CTkFrame(self.content_frame, fg_color=("gray85", "gray20"))
        info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        info_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            info_frame,
            text="Your Model Requires:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        sensor_info = f"• {self.project_metadata['input_channels']} sensor channels: " + \
                     ", ".join(self.project_metadata['sensor_columns'])
        ctk.CTkLabel(
            info_frame,
            text=sensor_info,
            font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, padx=15, sticky="w")

        window_info = f"• Window size: {self.project_metadata['window_size']} samples"
        ctk.CTkLabel(
            info_frame,
            text=window_info,
            font=ctk.CTkFont(size=12)
        ).grid(row=2, column=0, padx=15, pady=(0, 10), sticky="w")

        # Auto-detected sensor
        if self.suggested_sensor:
            ctk.CTkLabel(
                self.content_frame,
                text="✓ Auto-detected Sensor (Recommended)",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="green"
            ).grid(row=2, column=0, pady=(10, 5), sticky="w")

            sensor_frame = ctk.CTkFrame(self.content_frame, fg_color=("gray90", "gray15"))
            sensor_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
            sensor_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                sensor_frame,
                text=self.suggested_sensor['name'],
                font=ctk.CTkFont(size=15, weight="bold")
            ).grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

            ctk.CTkLabel(
                sensor_frame,
                text=self.suggested_sensor['description'],
                font=ctk.CTkFont(size=12),
                text_color="gray60"
            ).grid(row=1, column=0, padx=15, sticky="w")

            ctk.CTkLabel(
                sensor_frame,
                text=f"Interface: {self.suggested_sensor['interface']}",
                font=ctk.CTkFont(size=12),
                text_color="gray60"
            ).grid(row=2, column=0, padx=15, sticky="w")

            ctk.CTkLabel(
                sensor_frame,
                text=f"Confidence: {self.suggested_sensor['confidence']:.0%}",
                font=ctk.CTkFont(size=12),
                text_color="green"
            ).grid(row=3, column=0, padx=15, pady=(0, 10), sticky="w")

            # Use this sensor button
            use_btn = ctk.CTkButton(
                sensor_frame,
                text="✓ Use This Sensor",
                command=self._use_suggested_sensor,
                fg_color="green",
                hover_color="darkgreen"
            )
            use_btn.grid(row=0, column=1, rowspan=4, padx=15, pady=10)

        # Manual sensor selection
        ctk.CTkLabel(
            self.content_frame,
            text="Or Select Sensor Manually:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=4, column=0, pady=(10, 10), sticky="w")

        # Sensor options
        sensors = [
            ("MPU6050", "6-axis IMU (Accelerometer + Gyroscope)", "I2C", "0x68"),
            ("ADXL345", "3-axis Accelerometer", "I2C", "0x53"),
            ("BME280", "Environmental Sensor (Temp/Humidity/Pressure)", "I2C", "0x76"),
            ("Built-in IMU", "Arduino Nano 33 BLE only", "Built-in", "N/A")
        ]

        self.sensor_var = ctk.StringVar(value="auto")

        for i, (name, desc, interface, addr) in enumerate(sensors):
            frame = ctk.CTkFrame(self.content_frame)
            frame.grid(row=5+i, column=0, sticky="ew", pady=3)
            frame.grid_columnconfigure(1, weight=1)

            radio = ctk.CTkRadioButton(
                frame,
                text=name,
                variable=self.sensor_var,
                value=name.lower().replace(" ", "_"),
                font=ctk.CTkFont(size=13)
            )
            radio.grid(row=0, column=0, padx=15, pady=8, sticky="w")

            ctk.CTkLabel(
                frame,
                text=desc,
                font=ctk.CTkFont(size=11),
                text_color="gray60"
            ).grid(row=0, column=1, padx=10, pady=8, sticky="w")

    def _create_step3_pins(self):
        """Step 3: Pin configuration."""
        ctk.CTkLabel(
            self.content_frame,
            text="Pin Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, pady=(0, 20), sticky="w")

        # Get selected sensor config
        sensor_config = self.config.get('sensor_config', {})
        if not sensor_config and self.suggested_sensor:
            sensor_config = self.suggested_sensor['config']

        # I2C Configuration
        if sensor_config.get('i2c_address'):
            i2c_frame = ctk.CTkFrame(self.content_frame)
            i2c_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
            i2c_frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                i2c_frame,
                text="I2C Configuration",
                font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 10), sticky="w")

            # SDA Pin
            ctk.CTkLabel(i2c_frame, text="SDA Pin:").grid(row=1, column=0, padx=15, pady=5, sticky="w")
            self.sda_entry = ctk.CTkEntry(i2c_frame, width=100)
            self.sda_entry.insert(0, str(sensor_config.get('sda_pin', 21)))
            self.sda_entry.grid(row=1, column=1, padx=15, pady=5, sticky="w")

            # SCL Pin
            ctk.CTkLabel(i2c_frame, text="SCL Pin:").grid(row=2, column=0, padx=15, pady=5, sticky="w")
            self.scl_entry = ctk.CTkEntry(i2c_frame, width=100)
            self.scl_entry.insert(0, str(sensor_config.get('scl_pin', 22)))
            self.scl_entry.grid(row=2, column=1, padx=15, pady=5, sticky="w")

            # I2C Address
            ctk.CTkLabel(i2c_frame, text="I2C Address:").grid(row=3, column=0, padx=15, pady=5, sticky="w")
            self.addr_entry = ctk.CTkEntry(i2c_frame, width=100)
            self.addr_entry.insert(0, sensor_config.get('i2c_address', '0x68'))
            self.addr_entry.grid(row=3, column=1, padx=15, pady=(5, 15), sticky="w")

        # Sampling Configuration
        sample_frame = ctk.CTkFrame(self.content_frame)
        sample_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        sample_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            sample_frame,
            text="Sampling Configuration",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 10), sticky="w")

        # Sample Rate
        ctk.CTkLabel(sample_frame, text="Sample Rate (Hz):").grid(row=1, column=0, padx=15, pady=5, sticky="w")
        self.rate_entry = ctk.CTkEntry(sample_frame, width=100)
        default_rate = self.project_metadata.get('sampling_rate', 100)
        self.rate_entry.insert(0, str(default_rate))
        self.rate_entry.grid(row=1, column=1, padx=15, pady=(5, 15), sticky="w")

        # Help text
        help_frame = ctk.CTkFrame(self.content_frame, fg_color=("gray85", "gray20"))
        help_frame.grid(row=3, column=0, sticky="ew")
        help_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            help_frame,
            text="💡 Pin Configuration Tips:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        tips = [
            f"• ESP32 default I2C: SDA=21, SCL=22",
            f"• Arduino Nano 33: SDA=A4, SCL=A5",
            f"• Jetson Nano: Uses /dev/i2c-1",
            f"• Sample rate should match training data ({default_rate}Hz recommended)"
        ]

        for i, tip in enumerate(tips):
            ctk.CTkLabel(
                help_frame,
                text=tip,
                font=ctk.CTkFont(size=11),
                text_color="gray60"
            ).grid(row=i+1, column=0, padx=15, pady=2, sticky="w")

        ctk.CTkLabel(help_frame, text="").grid(row=len(tips)+1, column=0, pady=5)

    def _create_step4_actions(self):
        """Step 4: Output actions configuration."""
        ctk.CTkLabel(
            self.content_frame,
            text="Configure Output Actions",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, pady=(0, 10), sticky="w")

        # Show model output classes
        info_frame = ctk.CTkFrame(self.content_frame, fg_color=("gray85", "gray20"))
        info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        ctk.CTkLabel(
            info_frame,
            text=f"Your Model Predicts {self.project_metadata['num_classes']} Classes:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        classes_text = ", ".join(self.project_metadata['class_names'])
        ctk.CTkLabel(
            info_frame,
            text=classes_text,
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        ).grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        # Get suggested actions
        suggested_actions = self.mapper.suggest_actions(
            self.project_metadata['class_names'],
            self.config['platform']
        )

        # Action configuration for each class
        self.action_vars = {}

        row = 2
        for action in suggested_actions:
            class_name = action['class_name']
            class_idx = action['class_index']

            # Class frame
            class_frame = ctk.CTkFrame(self.content_frame)
            class_frame.grid(row=row, column=0, sticky="ew", pady=5)
            class_frame.grid_columnconfigure(1, weight=1)

            # Class label
            ctk.CTkLabel(
                class_frame,
                text=f"When '{class_name}' detected:",
                font=ctk.CTkFont(size=13, weight="bold")
            ).grid(row=0, column=0, columnspan=3, padx=15, pady=(10, 5), sticky="w")

            # LED action checkbox
            led_var = ctk.BooleanVar(value=(action['type'] == 'led'))
            led_check = ctk.CTkCheckBox(
                class_frame,
                text="Turn on LED",
                variable=led_var
            )
            led_check.grid(row=1, column=0, padx=(30, 10), pady=5, sticky="w")

            # LED pin entry
            led_pin_entry = ctk.CTkEntry(class_frame, width=60, placeholder_text="Pin")
            if action['type'] == 'led':
                led_pin_entry.insert(0, str(action['pin']))
            led_pin_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

            # LED duration
            led_dur_entry = ctk.CTkEntry(class_frame, width=60, placeholder_text="ms")
            if action['type'] == 'led':
                led_dur_entry.insert(0, str(action.get('duration_ms', 2000)))
            led_dur_entry.grid(row=1, column=2, padx=(5, 15), pady=5, sticky="w")

            # Serial action checkbox
            serial_var = ctk.BooleanVar(value=True)
            serial_check = ctk.CTkCheckBox(
                class_frame,
                text="Send Serial message",
                variable=serial_var
            )
            serial_check.grid(row=2, column=0, columnspan=3, padx=(30, 15), pady=5, sticky="w")

            # MQTT action checkbox (optional)
            mqtt_var = ctk.BooleanVar(value=False)
            mqtt_check = ctk.CTkCheckBox(
                class_frame,
                text="Send MQTT message",
                variable=mqtt_var
            )
            mqtt_check.grid(row=3, column=0, columnspan=3, padx=(30, 15), pady=(5, 10), sticky="w")

            # Store references
            self.action_vars[class_name] = {
                'index': class_idx,
                'led_enabled': led_var,
                'led_pin': led_pin_entry,
                'led_duration': led_dur_entry,
                'serial_enabled': serial_var,
                'mqtt_enabled': mqtt_var
            }

            row += 1

    def _create_step5_review(self):
        """Step 5: Review and generate."""
        ctk.CTkLabel(
            self.content_frame,
            text="Review Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, pady=(0, 20), sticky="w")

        # Build final configuration
        final_config = self._build_final_config()

        # Display review
        review_frame = ctk.CTkFrame(self.content_frame, fg_color=("gray90", "gray15"))
        review_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        review_frame.grid_columnconfigure(0, weight=1)

        sections = [
            ("Project", [
                f"Name: {final_config['project_name']}",
                f"Platform: {final_config['platform'].upper()}"
            ]),
            ("Model", [
                f"Input: {final_config['model']['input_shape']}",
                f"Classes: {', '.join(final_config['model']['class_names'])}"
            ]),
            ("Input Sensor", [
                f"Sensor: {final_config['input']['sensor']['name']}",
                f"Interface: {final_config['input']['sensor']['interface']}",
                f"Sampling: {final_config['input']['sampling_rate']} Hz"
            ]),
            ("Output Actions", [
                f"{len(final_config['output']['actions'])} actions configured"
            ])
        ]

        row = 0
        for section_title, items in sections:
            ctk.CTkLabel(
                review_frame,
                text=section_title,
                font=ctk.CTkFont(size=13, weight="bold")
            ).grid(row=row, column=0, padx=15, pady=(10, 5), sticky="w")
            row += 1

            for item in items:
                ctk.CTkLabel(
                    review_frame,
                    text=f"  • {item}",
                    font=ctk.CTkFont(size=12),
                    text_color="gray60"
                ).grid(row=row, column=0, padx=15, pady=2, sticky="w")
                row += 1

        ctk.CTkLabel(review_frame, text="").grid(row=row, column=0, pady=5)

        # Project name entry
        name_frame = ctk.CTkFrame(self.content_frame)
        name_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        name_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            name_frame,
            text="Firmware Project Name:",
            font=ctk.CTkFont(size=13)
        ).grid(row=0, column=0, padx=15, pady=15, sticky="w")

        self.project_name_entry = ctk.CTkEntry(name_frame)
        default_name = f"{final_config['project_name']}_{final_config['platform']}_fw"
        self.project_name_entry.insert(0, default_name)
        self.project_name_entry.grid(row=0, column=1, padx=(10, 15), pady=15, sticky="ew")

        # Generate button
        generate_btn = ctk.CTkButton(
            self.content_frame,
            text="🚀 Generate Firmware",
            command=self._generate_firmware,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        generate_btn.grid(row=3, column=0, pady=20)

    def _on_platform_change(self, platform_id: str):
        """Handle platform selection change."""
        self.config['platform'] = platform_id
        logger.info(f"Platform selected: {platform_id}")

    def _use_suggested_sensor(self):
        """Use the auto-detected sensor."""
        self.config['sensor'] = self.suggested_sensor['sensor_id']
        self.config['sensor_config'] = self.suggested_sensor['config']
        logger.info(f"Using suggested sensor: {self.suggested_sensor['name']}")
        messagebox.showinfo("Sensor Selected",
                          f"Selected: {self.suggested_sensor['name']}\n\n"
                          "Click 'Next' to configure pins.")

    def _build_final_config(self) -> Dict:
        """Build final deployment configuration from wizard steps."""
        # Gather sensor config from step 3
        sensor_config = self.config.get('sensor_config', {})
        if hasattr(self, 'sda_entry'):
            sensor_config['sda_pin'] = int(self.sda_entry.get())
            sensor_config['scl_pin'] = int(self.scl_entry.get())
            sensor_config['i2c_address'] = self.addr_entry.get()

        if hasattr(self, 'rate_entry'):
            sampling_rate = float(self.rate_entry.get())
        else:
            sampling_rate = self.project_metadata.get('sampling_rate', 100)

        # Gather actions from step 4
        actions = []
        if hasattr(self, 'action_vars'):
            for class_name, vars_dict in self.action_vars.items():
                action_list = []

                # LED action
                if vars_dict['led_enabled'].get():
                    try:
                        pin = int(vars_dict['led_pin'].get())
                        duration = int(vars_dict['led_duration'].get())
                        action_list.append({
                            'type': 'led',
                            'pin': pin,
                            'duration_ms': duration
                        })
                    except ValueError:
                        pass

                # Serial action
                if vars_dict['serial_enabled'].get():
                    action_list.append({
                        'type': 'serial',
                        'message': f"Detected: {class_name}"
                    })

                # MQTT action
                if vars_dict['mqtt_enabled'].get():
                    action_list.append({
                        'type': 'mqtt',
                        'topic': f"device/prediction",
                        'message': class_name
                    })

                actions.append({
                    'class_name': class_name,
                    'class_index': vars_dict['index'],
                    'actions': action_list
                })

        # Use sensor from config or suggested
        sensor_info = self.config.get('sensor')
        if not sensor_info and self.suggested_sensor:
            sensor_info = self.suggested_sensor

        # Build final config
        return {
            'project_name': self.config['project_name'],
            'platform': self.config['platform'],
            'model': {
                'onnx_path': self.project_metadata['onnx_path'],
                'input_shape': [self.project_metadata['window_size'],
                              self.project_metadata['input_channels']],
                'num_classes': self.project_metadata['num_classes'],
                'class_names': self.project_metadata['class_names']
            },
            'input': {
                'sensor': sensor_info if isinstance(sensor_info, dict) else self.suggested_sensor,
                'window_size': self.project_metadata['window_size'],
                'sampling_rate': sampling_rate,
                'sensor_config': sensor_config
            },
            'output': {
                'actions': actions
            }
        }

    def _next_step(self):
        """Move to next wizard step."""
        if self.current_step < self.max_steps:
            # Validate current step before proceeding
            if self._validate_step(self.current_step):
                self._show_step(self.current_step + 1)
        else:
            # Last step - generate firmware
            self._generate_firmware()

    def _previous_step(self):
        """Move to previous wizard step."""
        if self.current_step > 1:
            self._show_step(self.current_step - 1)

    def _validate_step(self, step: int) -> bool:
        """Validate current step before proceeding."""
        if step == 2:
            # Ensure sensor is selected
            if not self.config.get('sensor') and not self.suggested_sensor:
                messagebox.showwarning("Sensor Required",
                                     "Please select a sensor or use the suggested one.")
                return False

        return True

    def _generate_firmware(self):
        """Generate firmware code."""
        try:
            # Build final configuration
            final_config = self._build_final_config()

            # Get project name
            if hasattr(self, 'project_name_entry'):
                firmware_name = self.project_name_entry.get()
            else:
                firmware_name = f"{final_config['project_name']}_{final_config['platform']}_fw"

            # Save configuration
            output_dir = Path("output") / "firmware" / firmware_name
            output_dir.mkdir(parents=True, exist_ok=True)

            config_file = output_dir / "deployment_config.json"
            with open(config_file, 'w') as f:
                json.dump(final_config, f, indent=2)

            logger.info(f"Deployment configuration saved: {config_file}")

            # Show success message
            messagebox.showinfo(
                "Configuration Saved",
                f"Deployment configuration saved!\n\n"
                f"Location: {output_dir}\n\n"
                f"Next step: Firmware code generation\n"
                f"(Will be implemented with code generator)"
            )

            self.destroy()

        except Exception as e:
            logger.error(f"Failed to generate firmware: {e}")
            messagebox.showerror("Error", f"Failed to generate firmware:\n{e}")


# Test the wizard
if __name__ == "__main__":
    import sys

    app = ctk.CTk()
    app.geometry("400x300")
    app.title("Test Deployment Wizard")

    def open_wizard():
        project_file = Path("output/ts3/ts3.ciraproject")
        if project_file.exists():
            wizard = DeploymentWizard(app, project_file)
        else:
            messagebox.showerror("Error", f"Project file not found:\n{project_file}")

    btn = ctk.CTkButton(app, text="Open Deployment Wizard", command=open_wizard)
    btn.pack(pady=100)

    app.mainloop()
