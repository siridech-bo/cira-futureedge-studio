"""
Edge Impulse JSON/CBOR Data Source Loader
Supports Edge Impulse data acquisition format (JSON and CBOR)
Specification: https://docs.edgeimpulse.com/tools/specifications/data-acquisition/json-cbor
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

try:
    import cbor2
    CBOR_AVAILABLE = True
except ImportError:
    CBOR_AVAILABLE = False
    logging.warning("cbor2 library not available. CBOR format will not be supported.")

from .base import DataSource, DataSourceFactory
from .label_extractor import LabelExtractor

logger = logging.getLogger(__name__)


class EdgeImpulseDataSource(DataSource):
    """
    Data source for Edge Impulse JSON/CBOR format files.

    Format structure:
    {
        "protected": {
            "ver": "v1",
            "alg": "HS256" or "none",
            "iat": timestamp (optional)
        },
        "signature": "signature_string",
        "payload": {
            "device_type": "device_model",
            "device_name": "device_id" (optional),
            "interval_ms": sampling_interval,
            "sensors": [
                {"name": "sensor_name", "units": "unit"}
            ],
            "values": [
                [val1, val2, val3, ...],
                ...
            ]
        }
    }
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.file_path: Optional[Path] = None
        self.format_type: str = "auto"  # "json", "cbor", or "auto"
        self.raw_data: Optional[Dict] = None
        self.metadata: Dict[str, Any] = {}

        # Classification mode support (NEW)
        if config:
            self.extract_labels = config.parameters.get("extract_labels", False)
            self.label_pattern = config.parameters.get("label_pattern", "prefix")
            self.label_separator = config.parameters.get("label_separator", ".")
        else:
            self.extract_labels = False
            self.label_pattern = "prefix"
            self.label_separator = "."
        self.detected_class: Optional[str] = None

    def connect(self) -> bool:
        """Validate file exists and format is supported"""
        if not self.file_path:
            self.last_error = "No file path specified"
            return False

        if not self.file_path.exists():
            self.last_error = f"File not found: {self.file_path}"
            return False

        # Detect format if auto
        if self.format_type == "auto":
            if self.file_path.suffix.lower() == '.json':
                self.format_type = "json"
            elif self.file_path.suffix.lower() == '.cbor' or '.cbor' in self.file_path.name.lower():
                self.format_type = "cbor"
            else:
                # Try to detect by reading first bytes
                try:
                    with open(self.file_path, 'rb') as f:
                        first_byte = f.read(1)
                        if first_byte == b'{':
                            self.format_type = "json"
                        else:
                            self.format_type = "cbor"
                except Exception as e:
                    self.last_error = f"Could not detect format: {str(e)}"
                    return False

        # Check CBOR support
        if self.format_type == "cbor" and not CBOR_AVAILABLE:
            self.last_error = "CBOR format not supported. Install cbor2 library: pip install cbor2"
            return False

        self.is_connected = True
        return True

    def disconnect(self) -> None:
        """Disconnect from the data source (no-op for file-based sources)"""
        self.is_connected = False
        self.raw_data = None
        logger.info(f"Disconnected from {self.file_path}")

    def load_data(self, **kwargs) -> pd.DataFrame:
        """Load and parse Edge Impulse format data"""
        if not self.is_connected:
            if not self.connect():
                raise ValueError(self.last_error)

        try:
            # Load file based on format
            if self.format_type == "json":
                self.raw_data = self._load_json()
            elif self.format_type == "cbor":
                self.raw_data = self._load_cbor()
            else:
                raise ValueError(f"Unsupported format: {self.format_type}")

            # Validate structure
            if not self._validate_structure():
                raise ValueError(f"Invalid Edge Impulse format: {self.last_error}")

            # Extract metadata
            self._extract_metadata()

            # Convert to DataFrame
            df = self._to_dataframe()

            # Extract class label from filename if enabled (NEW)
            if self.extract_labels:
                class_label = self._extract_label_from_filename()
                if class_label:
                    df['class_label'] = class_label
                    self.detected_class = class_label
                    logger.info(f"Assigned class '{class_label}' to {len(df)} samples from {self.file_path.name}")

            logger.info(f"Loaded {len(df)} samples from {self.file_path.name}")
            logger.info(f"Device: {self.metadata.get('device_type', 'Unknown')}, "
                       f"Sampling: {self.metadata.get('interval_ms', 0)}ms, "
                       f"Sensors: {len(self.metadata.get('sensors', []))}")

            return df

        except Exception as e:
            self.last_error = f"Failed to load data: {str(e)}"
            logger.error(self.last_error)
            raise

    def _load_json(self) -> Dict:
        """Load JSON format file"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_cbor(self) -> Dict:
        """Load CBOR format file"""
        with open(self.file_path, 'rb') as f:
            return cbor2.load(f)

    def _validate_structure(self) -> bool:
        """Validate Edge Impulse data structure"""
        if not self.raw_data:
            self.last_error = "No data loaded"
            return False

        # Check required top-level fields
        if 'protected' not in self.raw_data:
            self.last_error = "Missing 'protected' section"
            return False

        if 'payload' not in self.raw_data:
            self.last_error = "Missing 'payload' section"
            return False

        # Check protected section
        protected = self.raw_data['protected']
        if 'ver' not in protected or protected['ver'] != 'v1':
            self.last_error = "Invalid or missing version in 'protected' section"
            return False

        # Check payload
        payload = self.raw_data['payload']
        required_fields = ['interval_ms', 'sensors', 'values']
        for field in required_fields:
            if field not in payload:
                self.last_error = f"Missing required field in payload: {field}"
                return False

        # Validate sensors structure
        sensors = payload['sensors']
        if not isinstance(sensors, list) or len(sensors) == 0:
            self.last_error = "Invalid sensors array"
            return False

        for sensor in sensors:
            if 'name' not in sensor:
                self.last_error = "Sensor missing 'name' field"
                return False

        # Validate values structure
        values = payload['values']
        if not isinstance(values, list) or len(values) == 0:
            self.last_error = "Invalid or empty values array"
            return False

        # Check that each value has correct number of elements
        num_sensors = len(sensors)
        for i, row in enumerate(values):
            if not isinstance(row, list) or len(row) != num_sensors:
                self.last_error = f"Row {i} has {len(row)} values, expected {num_sensors}"
                return False

        return True

    def _extract_metadata(self):
        """Extract metadata from loaded data"""
        payload = self.raw_data['payload']
        protected = self.raw_data['protected']

        self.metadata = {
            'version': protected.get('ver', 'unknown'),
            'algorithm': protected.get('alg', 'none'),
            'timestamp': protected.get('iat', None),
            'device_type': payload.get('device_type', 'Unknown'),
            'device_name': payload.get('device_name', None),
            'interval_ms': payload['interval_ms'],
            'sensors': payload['sensors'],
            'num_samples': len(payload['values']),
            'signature': self.raw_data.get('signature', None)
        }

    def _extract_label_from_filename(self) -> Optional[str]:
        """
        Extract class label from current file path using LabelExtractor.

        Returns:
            Extracted class label or None if extraction fails
        """
        if not self.file_path:
            return None

        label = LabelExtractor.extract_from_filename(
            self.file_path.name,
            pattern=self.label_pattern,
            separator=self.label_separator
        )

        if label:
            logger.debug(f"Extracted label '{label}' from '{self.file_path.name}' using pattern '{self.label_pattern}'")
        else:
            logger.warning(f"Could not extract label from '{self.file_path.name}' using pattern '{self.label_pattern}'")

        return label

    def _to_dataframe(self) -> pd.DataFrame:
        """Convert Edge Impulse data to pandas DataFrame"""
        payload = self.raw_data['payload']

        # Get sensor names
        sensor_names = [sensor['name'] for sensor in payload['sensors']]

        # Convert values to numpy array
        values_array = np.array(payload['values'])

        # Create DataFrame
        df = pd.DataFrame(values_array, columns=sensor_names)

        # Add time column based on interval_ms
        interval_s = payload['interval_ms'] / 1000.0  # Convert to seconds
        df.insert(0, 'time', np.arange(len(df)) * interval_s)

        return df

    def get_sensor_info(self) -> List[Dict[str, str]]:
        """Get detailed sensor information"""
        if not self.metadata or 'sensors' not in self.metadata:
            return []
        return self.metadata['sensors']

    def get_sampling_rate(self) -> Optional[float]:
        """Get sampling rate in Hz"""
        if not self.metadata or 'interval_ms' not in self.metadata:
            return None
        interval_ms = self.metadata['interval_ms']
        if interval_ms > 0:
            return 1000.0 / interval_ms
        return None

    def get_device_info(self) -> Dict[str, str]:
        """Get device information"""
        return {
            'type': self.metadata.get('device_type', 'Unknown'),
            'name': self.metadata.get('device_name', 'N/A'),
        }

    def detect_time_column(self) -> Optional[str]:
        """Return the time column name (always 'time' for Edge Impulse data)"""
        return 'time'

    def detect_sensor_columns(self) -> List[str]:
        """Return list of sensor column names"""
        if not self.metadata or 'sensors' not in self.metadata:
            return []
        return [sensor['name'] for sensor in self.metadata['sensors']]

    def infer_sampling_rate(self) -> Optional[float]:
        """Infer sampling rate from interval_ms"""
        return self.get_sampling_rate()


# Register both JSON and CBOR variants with factory
DataSourceFactory.register("edgeimpulse_json", EdgeImpulseDataSource)
DataSourceFactory.register("edgeimpulse_cbor", EdgeImpulseDataSource)
