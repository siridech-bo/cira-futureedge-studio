"""
Frequency Analysis Module for TimesNet Period Configuration

Analyzes time series data to determine dominant frequencies and
recommend optimal period configurations for ONNX deployment.
"""

import numpy as np
import pickle
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from loguru import logger


@dataclass
class FrequencyStats:
    """Statistics for a single class's frequency distribution."""
    class_name: str
    dominant_freq: float  # Hz
    freq_range: Tuple[float, float]  # (min_hz, max_hz)
    spectral_centroid: float  # Hz
    spectral_bandwidth: float  # Hz
    energy_distribution: Dict[str, float]  # {band_name: energy_percentage}
    sample_count: int


@dataclass
class PeriodConfig:
    """Configuration profile for TimesNet periods."""
    id: str  # 'A', 'B', 'C', etc.
    name: str
    periods: List[int]
    description: str
    best_for: str
    freq_range: Tuple[float, float]  # (min_hz, max_hz)
    color: str  # For UI visualization


class FrequencyAnalyzer:
    """Analyzes time series data frequency characteristics."""

    # Pre-defined period configurations
    STANDARD_CONFIGS = {
        'A': PeriodConfig(
            id='A',
            name='Low Frequency',
            periods=[100, 75, 50, 40, 33],
            description='Optimized for slow movements and postural changes',
            best_for='Idle detection, slow gestures, drift monitoring',
            freq_range=(0.1, 1.0),
            color='#3498db'  # Blue
        ),
        'B': PeriodConfig(
            id='B',
            name='Balanced',
            periods=[100, 50, 25, 20, 16],
            description='General-purpose configuration for mixed gestures',
            best_for='Mixed gesture types, general motion classification',
            freq_range=(0.5, 3.0),
            color='#2ecc71'  # Green
        ),
        'C': PeriodConfig(
            id='C',
            name='High Frequency',
            periods=[50, 25, 12, 8, 6],
            description='Optimized for rapid movements and vibrations',
            best_for='Shaking, rapid gestures, high-frequency patterns',
            freq_range=(2.0, 8.0),
            color='#e74c3c'  # Red
        ),
    }

    def __init__(self, sample_rate: float = 100.0):
        """
        Initialize frequency analyzer.

        Args:
            sample_rate: Sampling rate in Hz (default: 100 Hz)
        """
        self.sample_rate = sample_rate

    def analyze_windows(self, windows_file: Path) -> Dict[str, FrequencyStats]:
        """
        Analyze frequency characteristics of windowed data.

        Args:
            windows_file: Path to pickled windows file (train_windows.pkl or test_windows.pkl)

        Returns:
            Dictionary mapping class names to FrequencyStats
        """
        logger.info(f"Analyzing frequency characteristics from {windows_file}")

        # Load windows
        with open(windows_file, 'rb') as f:
            windows = pickle.load(f)

        # Group by class
        class_windows = {}
        for w in windows:
            class_name = w.class_label
            if class_name not in class_windows:
                class_windows[class_name] = []

            # Extract numeric sensor data
            if hasattr(w.data, 'select_dtypes'):
                numeric_cols = w.data.select_dtypes(include=[np.number]).columns.tolist()
                sensor_cols = [col for col in numeric_cols if col.lower() not in ['time', 'timestamp']]
                window_array = w.data[sensor_cols].values.astype(np.float32)
            else:
                window_array = np.array(w.data, dtype=np.float32)

            class_windows[class_name].append(window_array)

        # Analyze each class
        results = {}
        for class_name, windows_list in class_windows.items():
            results[class_name] = self._analyze_class(class_name, windows_list)

        logger.info(f"Analyzed {len(results)} classes, {sum(len(w) for w in class_windows.values())} total samples")
        return results

    def _analyze_class(self, class_name: str, windows: List[np.ndarray]) -> FrequencyStats:
        """Analyze frequency characteristics for a single class."""
        all_freqs = []
        all_powers = []

        for window in windows:
            # Compute FFT for each channel, average across channels
            fft_results = []
            for channel in range(window.shape[1]):
                signal = window[:, channel]
                fft = np.fft.rfft(signal)
                power = np.abs(fft) ** 2
                fft_results.append(power)

            # Average power across channels
            avg_power = np.mean(fft_results, axis=0)

            # Frequency bins
            freqs = np.fft.rfftfreq(len(signal), d=1.0/self.sample_rate)

            all_freqs.append(freqs)
            all_powers.append(avg_power)

        # Average power spectrum across all windows
        avg_power_spectrum = np.mean(all_powers, axis=0)
        freqs = all_freqs[0]  # Same for all windows

        # Compute statistics
        # Skip DC component for dominant frequency
        dominant_idx = np.argmax(avg_power_spectrum[1:]) + 1
        dominant_freq = freqs[dominant_idx]

        # Spectral centroid (weighted mean frequency)
        spectral_centroid = np.sum(freqs * avg_power_spectrum) / np.sum(avg_power_spectrum)

        # Find frequency range (where power > 5% of max)
        threshold = 0.05 * np.max(avg_power_spectrum)
        active_freqs = freqs[avg_power_spectrum > threshold]
        if len(active_freqs) > 0:
            freq_range = (float(active_freqs[0]), float(active_freqs[-1]))
        else:
            freq_range = (0.0, 0.0)

        # Spectral bandwidth
        spectral_bandwidth = freq_range[1] - freq_range[0]

        # Energy distribution in frequency bands
        bands = {
            'Very Low (0-0.5 Hz)': (0.0, 0.5),
            'Low (0.5-1.5 Hz)': (0.5, 1.5),
            'Medium (1.5-3.0 Hz)': (1.5, 3.0),
            'High (3.0-5.0 Hz)': (3.0, 5.0),
            'Very High (5.0+ Hz)': (5.0, np.inf),
        }

        energy_distribution = {}
        total_energy = np.sum(avg_power_spectrum)

        for band_name, (low, high) in bands.items():
            mask = (freqs >= low) & (freqs < high)
            band_energy = np.sum(avg_power_spectrum[mask])
            energy_distribution[band_name] = float((band_energy / total_energy) * 100)

        return FrequencyStats(
            class_name=class_name,
            dominant_freq=float(dominant_freq),
            freq_range=freq_range,
            spectral_centroid=float(spectral_centroid),
            spectral_bandwidth=float(spectral_bandwidth),
            energy_distribution=energy_distribution,
            sample_count=len(windows)
        )

    def recommend_config(self, freq_stats: Dict[str, FrequencyStats]) -> Tuple[str, float]:
        """
        Recommend optimal period configuration based on frequency analysis.

        Args:
            freq_stats: Dictionary of frequency statistics per class

        Returns:
            Tuple of (recommended_config_id, confidence_score)
        """
        # Compute overall frequency range weighted by sample count
        total_samples = sum(stats.sample_count for stats in freq_stats.values())

        weighted_min_freq = 0.0
        weighted_max_freq = 0.0

        for stats in freq_stats.values():
            weight = stats.sample_count / total_samples
            weighted_min_freq += stats.freq_range[0] * weight
            weighted_max_freq += stats.freq_range[1] * weight

        overall_range = (weighted_min_freq, weighted_max_freq)
        overall_centroid = sum(
            stats.spectral_centroid * (stats.sample_count / total_samples)
            for stats in freq_stats.values()
        )

        logger.info(f"Overall frequency range: {overall_range[0]:.2f}-{overall_range[1]:.2f} Hz")
        logger.info(f"Overall spectral centroid: {overall_centroid:.2f} Hz")

        # Score each configuration
        scores = {}
        for config_id, config in self.STANDARD_CONFIGS.items():
            # Check overlap between data range and config range
            overlap_min = max(overall_range[0], config.freq_range[0])
            overlap_max = min(overall_range[1], config.freq_range[1])

            if overlap_max > overlap_min:
                overlap = overlap_max - overlap_min
                config_span = config.freq_range[1] - config.freq_range[0]
                data_span = overall_range[1] - overall_range[0]

                # Overlap score (higher = better)
                overlap_score = overlap / max(config_span, data_span)

                # Centroid score (1.0 if centroid in config range, decays outside)
                if config.freq_range[0] <= overall_centroid <= config.freq_range[1]:
                    centroid_score = 1.0
                else:
                    dist_to_range = min(
                        abs(overall_centroid - config.freq_range[0]),
                        abs(overall_centroid - config.freq_range[1])
                    )
                    centroid_score = np.exp(-dist_to_range)

                # Combined score
                scores[config_id] = 0.6 * overlap_score + 0.4 * centroid_score
            else:
                scores[config_id] = 0.0

        # Get best config
        best_config_id = max(scores, key=scores.get)
        confidence = scores[best_config_id]

        logger.info(f"Recommended config: {best_config_id} (confidence: {confidence*100:.1f}%)")
        for config_id, score in scores.items():
            logger.debug(f"  Config {config_id}: {score*100:.1f}%")

        return best_config_id, confidence

    def get_config(self, config_id: str) -> PeriodConfig:
        """Get period configuration by ID."""
        return self.STANDARD_CONFIGS.get(config_id)

    def get_all_configs(self) -> Dict[str, PeriodConfig]:
        """Get all available period configurations."""
        return self.STANDARD_CONFIGS.copy()


def generate_frequency_report(
    windows_file: Path,
    sample_rate: float = 100.0
) -> Tuple[Dict[str, FrequencyStats], str, float]:
    """
    Generate frequency analysis report for windowed data.

    Args:
        windows_file: Path to pickled windows file
        sample_rate: Sampling rate in Hz

    Returns:
        Tuple of (freq_stats, recommended_config_id, confidence)
    """
    analyzer = FrequencyAnalyzer(sample_rate=sample_rate)
    freq_stats = analyzer.analyze_windows(windows_file)
    recommended_config, confidence = analyzer.recommend_config(freq_stats)

    return freq_stats, recommended_config, confidence
