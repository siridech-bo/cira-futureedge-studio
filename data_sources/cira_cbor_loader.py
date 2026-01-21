"""
CiRA CBOR Data Source Loader
Supports CiRA Dataset Recorder CBOR format
Format: {"samples": [{"timestamp": ms, "class_name": str, "class_id": int, "data": [floats]}]}
"""

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


class CiraCBORDataSource(DataSource):
    """
    Data source for CiRA Dataset Recorder CBOR format files.

    Format structure:
    {
        "samples": [
            {
                "timestamp": milliseconds_since_epoch,
                "class_name": "class_label",
                "class_id": numeric_id,
                "data": [val1, val2, val3, ...]
            },
            ...
        ]
    }
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.file_path: Optional[Path] = None
        self.raw_data: Optional[Dict] = None
        self.metadata: Dict[str, Any] = {}
        self.detected_class: Optional[str] = None

    def connect(self) -> bool:
        """Validate file exists and CBOR library is available"""
        if not self.file_path:
            self.last_error = "No file path specified"
            return False

        if not self.file_path.exists():
            self.last_error = f"File not found: {self.file_path}"
            return False

        if not CBOR_AVAILABLE:
            self.last_error = "CBOR format not supported. Install cbor2 library: pip install cbor2"
            return False

        self.is_connected = True
        return True

    def disconnect(self) -> None:
        """Disconnect from the data source"""
        self.is_connected = False
        self.raw_data = None
        logger.info(f"Disconnected from {self.file_path}")

    def load_data(self, **kwargs) -> pd.DataFrame:
        """Load and parse CiRA CBOR format data"""
        if not self.is_connected:
            if not self.connect():
                raise ValueError(self.last_error)

        try:
            # Load CBOR file
            with open(self.file_path, 'rb') as f:
                self.raw_data = cbor2.load(f)

            # Validate structure
            if not self._validate_structure():
                raise ValueError(f"Invalid CiRA CBOR format: {self.last_error}")

            # Extract metadata
            self._extract_metadata()

            # Convert to DataFrame
            df = self._to_dataframe()

            logger.info(f"Loaded {len(df)} samples from {self.file_path.name}")
            logger.info(f"Class: {self.detected_class}, "
                       f"Channels: {self.metadata.get('num_channels', 0)}, "
                       f"Samples: {self.metadata.get('num_samples', 0)}")

            return df

        except Exception as e:
            self.last_error = f"Failed to load data: {str(e)}"
            logger.error(self.last_error)
            raise

    def _validate_structure(self) -> bool:
        """Validate CiRA CBOR data structure"""
        if not self.raw_data:
            self.last_error = "No data loaded"
            return False

        # Check for samples array
        if 'samples' not in self.raw_data:
            self.last_error = "Missing 'samples' array"
            return False

        samples = self.raw_data['samples']
        if not isinstance(samples, list) or len(samples) == 0:
            self.last_error = "Invalid or empty samples array"
            return False

        # Check first sample structure
        first_sample = samples[0]
        required_fields = ['timestamp', 'class_name', 'class_id', 'data']
        for field in required_fields:
            if field not in first_sample:
                self.last_error = f"Sample missing required field: {field}"
                return False

        # Validate data is array
        if not isinstance(first_sample['data'], list):
            self.last_error = "Sample 'data' field must be an array"
            return False

        return True

    def _extract_metadata(self):
        """Extract metadata from loaded data"""
        samples = self.raw_data['samples']

        # Get dominant class
        class_counts = {}
        for sample in samples:
            class_name = sample.get('class_name', 'unknown')
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

        dominant_class = max(class_counts, key=class_counts.get) if class_counts else 'unknown'
        self.detected_class = dominant_class

        # Calculate sampling interval
        avg_interval_ms = 0.0
        if len(samples) > 1:
            first_ts = samples[0]['timestamp']
            last_ts = samples[-1]['timestamp']
            avg_interval_ms = (last_ts - first_ts) / (len(samples) - 1)

        # Detect actual number of channels by unwrapping the window
        window_size = len(samples[0]['data']) if samples else 0
        num_channels, samples_per_channel = self._detect_channel_config(window_size) if window_size > 0 else (0, 0)

        self.metadata = {
            'num_samples': len(samples),
            'window_size': window_size,
            'num_channels': num_channels,
            'samples_per_channel': samples_per_channel,
            'class_name': dominant_class,
            'class_counts': class_counts,
            'interval_ms': avg_interval_ms,
            'sampling_rate_hz': 1000.0 / avg_interval_ms if avg_interval_ms > 0 else None,
            'filename': self.file_path.name if self.file_path else 'unknown'
        }


    def _detect_channel_config(self, window_size: int) -> tuple:
        """
        Automatically detect channel configuration from window size.

        Strategy:
        1. Try common factorizations (1ch, 2ch, 3ch, 4ch, etc.)
        2. Prefer configurations with reasonable samples_per_channel (50-500 range)
        3. Use scoring to pick the most likely configuration

        Returns:
            (num_channels, samples_per_channel)
        """
        # Common channel counts to try, ordered by likelihood
        common_channels = [3, 1, 2, 4, 6, 8, 12, 16]

        best_config = (1, window_size)  # Default: single channel
        best_score = 0

        for num_ch in common_channels:
            if window_size % num_ch == 0:
                samples_per_ch = window_size // num_ch

                # Score this configuration
                score = 0

                # Prefer: 50 <= samples_per_channel <= 500
                if 50 <= samples_per_ch <= 500:
                    score = 100
                    # Bonus for common sample counts (powers of 2, multiples of 50/100)
                    if samples_per_ch in [50, 100, 128, 150, 200, 256, 300, 400, 500]:
                        score += 50
                elif 20 <= samples_per_ch <= 1000:
                    score = 50
                else:
                    score = 10

                # Prefer common channel counts
                if num_ch == 3:  # Most common in accelerometer/gyro (x,y,z)
                    score += 20
                elif num_ch == 1:  # Single sensor
                    score += 10
                elif num_ch == 6:  # IMU (accel + gyro)
                    score += 15
                elif num_ch in [2, 4, 8]:  # Common powers of 2
                    score += 5

                if score > best_score:
                    best_score = score
                    best_config = (num_ch, samples_per_ch)

        return best_config

    def _to_dataframe(self) -> pd.DataFrame:
        """Convert CiRA CBOR data to pandas DataFrame

        Each sample contains a window of merged multi-channel data.
        For example: 300 values = 3 channels × 100 samples per channel
        Window layout: [ch0_s0, ch0_s1, ..., ch0_s99, ch1_s0, ..., ch1_s99, ch2_s0, ..., ch2_s99]

        We need to detect number of channels and unwrap accordingly.
        """
        samples = self.raw_data['samples']

        if not samples:
            return pd.DataFrame()

        window_size = len(samples[0]['data'])

        # Detect channel configuration automatically
        num_channels, samples_per_channel = self._detect_channel_config(window_size)

        logger.info(f"Auto-detected {num_channels} channels, {samples_per_channel} samples per channel (window size: {window_size})")

        # Build DataFrame by unwrapping windows
        rows = []
        time_index = 0.0

        # Calculate time increment per sample within window
        window_interval_ms = self.metadata.get('interval_ms', 100)
        sample_interval_sec = (window_interval_ms / 1000.0) / samples_per_channel

        for sample in samples:
            window_data = sample['data']
            class_name = sample['class_name']

            # Reshape window data: [ch0_samples, ch1_samples, ch2_samples, ...]
            # into rows: [(ch0_val, ch1_val, ch2_val), ...]
            for i in range(samples_per_channel):
                row = {
                    'time': time_index,
                    'class_label': class_name
                }

                # Extract values for each channel at sample position i
                for ch in range(num_channels):
                    channel_offset = ch * samples_per_channel
                    row[f'ch{ch}'] = window_data[channel_offset + i]

                rows.append(row)
                time_index += sample_interval_sec

        df = pd.DataFrame(rows)

        # Reset time to start from 0
        if len(df) > 0:
            df['time'] = df['time'] - df['time'].iloc[0]

        return df

    def detect_time_column(self) -> Optional[str]:
        """Return the time column name"""
        return 'time'

    def detect_sensor_columns(self) -> List[str]:
        """Return list of sensor column names"""
        if not self.metadata or 'num_channels' not in self.metadata:
            return []

        num_channels = self.metadata['num_channels']
        if num_channels == 1:
            return ['signal']
        else:
            return [f'ch{i}' for i in range(num_channels)]

    def infer_sampling_rate(self) -> Optional[float]:
        """Infer sampling rate from metadata"""
        return self.metadata.get('sampling_rate_hz')


# Register with factory
DataSourceFactory.register("cira_cbor", CiraCBORDataSource)
