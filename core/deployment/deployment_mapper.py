"""
CiRA FutureEdge Studio - Deployment Signal Mapper
Intelligently maps model inputs/outputs to hardware I/O
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
from loguru import logger


class DeploymentMapper:
    """Maps trained model I/O to hardware sensors and actuators."""

    # Sensor detection rules
    SENSOR_PATTERNS = {
        "mpu6050": {
            "signals": ["accX", "accY", "accZ", "gyroX", "gyroY", "gyroZ"],
            "min_match": 3,
            "name": "MPU6050",
            "description": "6-axis IMU (Accelerometer + Gyroscope)",
            "interface": "I2C",
            "default_config": {
                "i2c_address": "0x68",
                "sda_pin": 21,
                "scl_pin": 22,
                "sample_rate": 100
            }
        },
        "adxl345": {
            "signals": ["accX", "accY", "accZ"],
            "min_match": 3,
            "name": "ADXL345",
            "description": "3-axis Accelerometer",
            "interface": "I2C",
            "default_config": {
                "i2c_address": "0x53",
                "sda_pin": 21,
                "scl_pin": 22,
                "sample_rate": 100
            }
        },
        "bme280": {
            "signals": ["temperature", "humidity", "pressure"],
            "min_match": 2,
            "name": "BME280",
            "description": "Environmental Sensor",
            "interface": "I2C",
            "default_config": {
                "i2c_address": "0x76",
                "sda_pin": 21,
                "scl_pin": 22,
                "sample_rate": 1
            }
        }
    }

    # Platform-specific pin mappings
    PLATFORM_PINS = {
        "esp32": {
            "i2c_sda": 21,
            "i2c_scl": 22,
            "led_pins": [2, 4, 5, 18, 19],
            "pwm_pins": [16, 17, 25, 26, 27]
        },
        "jetson": {
            "i2c_bus": "/dev/i2c-1",
            "gpio_base": 0,
            "led_pins": [7, 11, 12, 13, 15]
        },
        "nano33": {
            "builtin_imu": True,
            "led_builtin": 13,
            "led_pins": [2, 3, 4, 5, 6]
        }
    }

    def __init__(self):
        """Initialize deployment mapper."""
        pass

    def load_project_metadata(self, project_file: Path) -> Dict:
        """
        Load model metadata from .ciraproject file.

        Args:
            project_file: Path to .ciraproject file

        Returns:
            Dictionary with model metadata
        """
        logger.info(f"Loading project: {project_file}")

        with open(project_file, 'r') as f:
            project = json.load(f)

        # Extract relevant info
        metadata = {
            "project_name": project.get("name", "unknown"),
            "sensor_columns": project["data"].get("sensor_columns", []),
            "window_size": project["data"].get("window_size", 100),
            "sampling_rate": project["data"].get("sampling_rate", 100),
            "class_names": project["model"].get("class_names", []),
            "num_classes": project["model"].get("num_classes", 0),
            "model_type": project["model"].get("model_type", "classifier"),
            "onnx_path": project["model"].get("onnx_model_path"),
            "input_channels": project["model"]["dl_config"]["model_info"].get("input_channels", 3),
            "seq_len": project["model"]["dl_config"]["model_info"].get("seq_len", 100)
        }

        logger.info(f"Loaded metadata: {metadata['project_name']}")
        logger.info(f"Input: {metadata['input_channels']} channels, window={metadata['window_size']}")
        logger.info(f"Output: {metadata['num_classes']} classes: {metadata['class_names']}")

        return metadata

    def suggest_sensor(self, sensor_columns: List[str]) -> Optional[Dict]:
        """
        Auto-detect appropriate sensor based on signal names.

        Args:
            sensor_columns: List of sensor signal names from model

        Returns:
            Suggested sensor configuration or None
        """
        logger.info(f"Detecting sensor for signals: {sensor_columns}")

        # Normalize signal names (lowercase)
        signals_lower = [s.lower() for s in sensor_columns]

        # Try to match against known sensors
        best_match = None
        best_score = 0

        for sensor_id, sensor_info in self.SENSOR_PATTERNS.items():
            # Count matching signals
            pattern_signals_lower = [s.lower() for s in sensor_info["signals"]]
            matches = sum(1 for s in signals_lower if s in pattern_signals_lower)

            if matches >= sensor_info["min_match"] and matches > best_score:
                best_score = matches
                best_match = {
                    "sensor_id": sensor_id,
                    "name": sensor_info["name"],
                    "description": sensor_info["description"],
                    "interface": sensor_info["interface"],
                    "config": sensor_info["default_config"],
                    "confidence": matches / len(sensor_columns),
                    "matched_signals": [s for s in sensor_columns if s.lower() in pattern_signals_lower]
                }

        if best_match:
            logger.info(f"Suggested sensor: {best_match['name']} (confidence: {best_match['confidence']:.1%})")
        else:
            logger.warning("Could not auto-detect sensor from signal names")

        return best_match

    def suggest_actions(self, class_names: List[str], platform: str = "esp32") -> List[Dict]:
        """
        Suggest default output actions for each class.

        Args:
            class_names: List of classification labels
            platform: Target platform (esp32, jetson, nano33)

        Returns:
            List of suggested actions
        """
        logger.info(f"Suggesting actions for {len(class_names)} classes on {platform}")

        actions = []
        platform_config = self.PLATFORM_PINS.get(platform, self.PLATFORM_PINS["esp32"])

        # Assign LED to each class (excluding idle/normal)
        led_pins = platform_config.get("led_pins", [2, 4, 5, 18, 19])
        led_idx = 0

        for class_idx, class_name in enumerate(class_names):
            class_lower = class_name.lower()

            # Skip idle/normal classes for LED indication
            if class_lower in ["idle", "normal", "none", "background"]:
                actions.append({
                    "class_name": class_name,
                    "class_index": class_idx,
                    "type": "none",
                    "description": f"No action for {class_name}"
                })
            else:
                # Assign LED
                if led_idx < len(led_pins):
                    actions.append({
                        "class_name": class_name,
                        "class_index": class_idx,
                        "type": "led",
                        "pin": led_pins[led_idx],
                        "duration_ms": 2000,
                        "description": f"LED on pin {led_pins[led_idx]} for {class_name}"
                    })
                    led_idx += 1
                else:
                    # Serial output if no more LEDs
                    actions.append({
                        "class_name": class_name,
                        "class_index": class_idx,
                        "type": "serial",
                        "message": f"Detected: {class_name}",
                        "description": f"Serial output for {class_name}"
                    })

        # Always add serial logging for all classes
        for action in actions:
            if "serial_log" not in action:
                action["serial_log"] = True

        logger.info(f"Suggested {len(actions)} actions")
        return actions

    def create_deployment_config(
        self,
        project_file: Path,
        platform: str = "esp32",
        user_sensor_override: Optional[Dict] = None,
        user_actions_override: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Create complete deployment configuration.

        Args:
            project_file: Path to .ciraproject
            platform: Target platform
            user_sensor_override: User-specified sensor config (overrides auto-detect)
            user_actions_override: User-specified actions (overrides suggestions)

        Returns:
            Complete deployment configuration
        """
        logger.info("Creating deployment configuration...")

        # Load project metadata
        metadata = self.load_project_metadata(project_file)

        # Detect or use user-specified sensor
        if user_sensor_override:
            sensor_config = user_sensor_override
            logger.info(f"Using user-specified sensor: {sensor_config.get('name')}")
        else:
            sensor_config = self.suggest_sensor(metadata["sensor_columns"])
            if not sensor_config:
                # Fallback to manual selection required
                sensor_config = {
                    "sensor_id": "unknown",
                    "name": "Manual Selection Required",
                    "description": "Could not auto-detect sensor",
                    "interface": "Unknown",
                    "config": {}
                }

        # Generate or use user-specified actions
        if user_actions_override:
            actions = user_actions_override
            logger.info(f"Using {len(actions)} user-specified actions")
        else:
            actions = self.suggest_actions(metadata["class_names"], platform)

        # Build complete config
        deployment_config = {
            "project_name": metadata["project_name"],
            "platform": platform,
            "model": {
                "onnx_path": metadata["onnx_path"],
                "input_shape": [metadata["window_size"], metadata["input_channels"]],
                "num_classes": metadata["num_classes"],
                "class_names": metadata["class_names"]
            },
            "input": {
                "sensor": sensor_config,
                "window_size": metadata["window_size"],
                "sampling_rate": metadata["sampling_rate"],
                "signal_mapping": {
                    col: i for i, col in enumerate(metadata["sensor_columns"])
                }
            },
            "output": {
                "actions": actions
            }
        }

        logger.info("✓ Deployment configuration created")
        return deployment_config

    def validate_config(self, config: Dict) -> Tuple[bool, List[str]]:
        """
        Validate deployment configuration.

        Args:
            config: Deployment configuration

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        if not config.get("model", {}).get("onnx_path"):
            errors.append("Missing ONNX model path")

        if config.get("input", {}).get("sensor", {}).get("sensor_id") == "unknown":
            errors.append("Sensor not configured")

        if not config.get("output", {}).get("actions"):
            errors.append("No output actions defined")

        # Check pin conflicts
        used_pins = set()
        for action in config.get("output", {}).get("actions", []):
            if action.get("type") == "led":
                pin = action.get("pin")
                if pin in used_pins:
                    errors.append(f"Pin {pin} used multiple times")
                used_pins.add(pin)

        is_valid = len(errors) == 0

        if is_valid:
            logger.info("✓ Configuration is valid")
        else:
            logger.error(f"✗ Configuration has {len(errors)} errors")
            for err in errors:
                logger.error(f"  - {err}")

        return is_valid, errors


# Example usage
if __name__ == "__main__":
    mapper = DeploymentMapper()

    # Load project
    project_file = Path("D:/CiRA FES/output/ts3/ts3.ciraproject")

    # Create deployment config with auto-detection
    config = mapper.create_deployment_config(
        project_file=project_file,
        platform="esp32"
    )

    # Validate
    is_valid, errors = mapper.validate_config(config)

    if is_valid:
        print("✓ Ready to generate firmware!")
        print(json.dumps(config, indent=2))
