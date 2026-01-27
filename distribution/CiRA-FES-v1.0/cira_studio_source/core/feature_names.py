"""
Feature Name Decoder

Provides human-readable explanations for tsfresh feature names.
Based on tsfresh documentation: https://tsfresh.readthedocs.io/en/latest/text/list_of_features.html
"""

from typing import Dict, Optional
import re


class FeatureNameDecoder:
    """Decode tsfresh feature names to human-readable descriptions."""

    # Feature calculators and their descriptions
    FEATURE_DESCRIPTIONS = {
        # Statistical features
        "mean": "Mean (average) value of the time series",
        "median": "Median value of the time series",
        "std": "Standard deviation - measures spread/variability",
        "variance": "Variance - squared standard deviation",
        "min": "Minimum value",
        "max": "Maximum value",
        "sum": "Sum of all values",
        "abs_energy": "Absolute energy - sum of squared values",
        "mean_abs_change": "Mean of absolute differences between consecutive values",
        "mean_change": "Mean of differences between consecutive values (trend)",
        "mean_second_derivative_central": "Mean of second derivative (acceleration/curvature)",

        # Count features
        "count_above_mean": "Number of values above the mean",
        "count_below_mean": "Number of values below the mean",
        "length": "Length of the time series (number of data points)",
        "range_count": "Number of values within a specified range",
        "value_count": "Count of specific value occurrences",

        # Percentile features
        "quantile": "Quantile value (percentile)",
        "first_location_of_maximum": "Index of first occurrence of maximum value",
        "first_location_of_minimum": "Index of first occurrence of minimum value",
        "last_location_of_maximum": "Index of last occurrence of maximum value",
        "last_location_of_minimum": "Index of last occurrence of minimum value",
        "percentage_of_reoccurring_datapoints_to_all_datapoints": "Percentage of repeated values",
        "percentage_of_reoccurring_values_to_all_values": "Percentage of unique repeated values",
        "sum_of_reoccurring_data_points": "Sum of all values that occur more than once",
        "sum_of_reoccurring_values": "Sum of unique values that occur more than once",
        "ratio_value_number_to_time_series_length": "Ratio of unique values to series length",

        # Frequency domain features
        "fft_coefficient": "Fast Fourier Transform coefficient - frequency domain representation",
        "fft_aggregated": "Aggregated FFT features (mean, variance, etc. of FFT coefficients)",
        "spectral_centroid": "Center of mass of the spectrum - indicates dominant frequency",
        "spectral_rolloff": "Frequency below which a percentage of total energy is contained",
        "spectral_entropy": "Entropy of power spectral density - measures complexity",

        # Autocorrelation features
        "autocorrelation": "Correlation of signal with itself at different time lags",
        "partial_autocorrelation": "Partial autocorrelation controlling for intermediate lags",
        "c3": "Measure of non-linearity in the time series",

        # Complexity features
        "cid_ce": "Complexity-Invariant Distance - measures complexity",
        "approximate_entropy": "Approximate entropy - measures regularity/unpredictability",
        "sample_entropy": "Sample entropy - improved version of approximate entropy",
        "permutation_entropy": "Permutation entropy - based on ordinal patterns",

        # Linear trend features
        "linear_trend": "Linear least-squares regression parameters",
        "agg_linear_trend": "Aggregated linear trend features",
        "linear_trend_timewise": "Time-wise linear trend",

        # AR model features
        "ar_coefficient": "Autoregressive model coefficients",
        "augmented_dickey_fuller": "ADF test statistic - tests for stationarity",

        # Energy features
        "abs_energy": "Absolute energy - sum of squared values",
        "absolute_sum_of_changes": "Sum of absolute differences between consecutive values",
        "benford_correlation": "Correlation to Benford's Law distribution",

        # Peak features
        "number_peaks": "Number of peaks in the time series",
        "number_cwt_peaks": "Number of peaks found using continuous wavelet transform",

        # Binned features
        "binned_entropy": "Entropy calculated from binned values",
        "index_mass_quantile": "Relative index where a quantile of the mass is reached",

        # Change point features
        "mean_n_absolute_max": "Mean of n absolute maximum values",
        "number_crossing_m": "Number of times series crosses the mean",

        # Advanced features
        "change_quantiles": "Changes in quantiles between consecutive segments",
        "cwt_coefficients": "Continuous Wavelet Transform coefficients",
        "energy_ratio_by_chunks": "Ratio of energy in chunks to total energy",
        "friedrich_coefficients": "Coefficients of Friedrich polynomial approximation",
        "large_standard_deviation": "Boolean if std is larger than r * (max - min)",
        "last_location_of_maximum": "Relative position of last maximum",
        "longest_strike_above_mean": "Longest consecutive sequence above mean",
        "longest_strike_below_mean": "Longest consecutive sequence below mean",
        "matrix_profile": "Matrix profile features - finds motifs and discords",
        "max_langevin_fixed_point": "Maximum fixed point of Langevin model",
        "mean_abs_change": "Mean over absolute differences between consecutive values",
        "mean_change": "Mean over differences between consecutive values",
        "number_crossing_m": "Number of crossings of mean",
        "ratio_beyond_r_sigma": "Ratio of values beyond r standard deviations from mean",
        "spkt_welch_density": "Power spectral density using Welch's method",
        "time_reversal_asymmetry_statistic": "Measure of time series asymmetry",
        "variation_coefficient": "Coefficient of variation - std/mean (normalized volatility)",
    }

    @staticmethod
    def decode_feature_name(feature_name: str) -> Dict[str, str]:
        """
        Decode a tsfresh feature name into components and description.

        Args:
            feature_name: Feature name (e.g., "audio__mean" or "x__fft_coefficient__attr_\"real\"__coeff_0")

        Returns:
            Dictionary with:
                - sensor: Sensor/column name
                - calculator: Feature calculator name
                - params: Parameter string (if any)
                - description: Human-readable description
                - full_description: Complete description with parameters
        """
        # Split by double underscore to get sensor and feature
        parts = feature_name.split("__", 1)

        if len(parts) == 1:
            # No double underscore, might be a simple feature
            return {
                "sensor": "unknown",
                "calculator": parts[0],
                "params": "",
                "description": FeatureNameDecoder.FEATURE_DESCRIPTIONS.get(parts[0], "Unknown feature"),
                "full_description": parts[0]
            }

        sensor = parts[0]
        feature_part = parts[1]

        # Find the calculator name (first part before parameters)
        calculator = feature_part
        params = ""

        # Extract calculator and parameters
        for calc_name in FeatureNameDecoder.FEATURE_DESCRIPTIONS.keys():
            if feature_part.startswith(calc_name):
                calculator = calc_name
                # Get everything after the calculator name
                if len(feature_part) > len(calc_name):
                    params = feature_part[len(calc_name):]
                    if params.startswith("__"):
                        params = params[2:]  # Remove leading __
                break

        # Get base description
        description = FeatureNameDecoder.FEATURE_DESCRIPTIONS.get(
            calculator,
            "Unknown feature calculator"
        )

        # Build full description with parameters
        full_desc = f"{sensor.upper()}: {description}"

        if params:
            # Parse common parameter patterns
            param_desc = FeatureNameDecoder._parse_parameters(params)
            if param_desc:
                full_desc += f" ({param_desc})"

        return {
            "sensor": sensor,
            "calculator": calculator,
            "params": params,
            "description": description,
            "full_description": full_desc
        }

    @staticmethod
    def _parse_parameters(params: str) -> str:
        """Parse parameter string into human-readable format."""
        param_parts = []

        # Common parameter patterns
        patterns = {
            r"coeff_(\d+)": lambda m: f"coefficient {m.group(1)}",
            r"m_(\d+)": lambda m: f"m={m.group(1)}",
            r"r_(\d+)": lambda m: f"r={m.group(1)}",
            r"attr_\"(\w+)\"": lambda m: f"attribute: {m.group(1)}",
            r"lag_(\d+)": lambda m: f"lag={m.group(1)}",
            r"q_([0-9.]+)": lambda m: f"quantile={m.group(1)}",
            r"chunk_len_(\d+)": lambda m: f"chunk length={m.group(1)}",
            r"f_agg_\"(\w+)\"": lambda m: f"aggregation: {m.group(1)}",
            r"max_(\d+)": lambda m: f"max={m.group(1)}",
            r"min_(-?\d+)": lambda m: f"min={m.group(1)}",
            r"n_(\d+)": lambda m: f"n={m.group(1)}",
            r"param_(\d+)": lambda m: f"param {m.group(1)}",
        }

        for pattern, formatter in patterns.items():
            matches = re.finditer(pattern, params)
            for match in matches:
                param_parts.append(formatter(match))

        return ", ".join(param_parts) if param_parts else params

    @staticmethod
    def get_short_description(feature_name: str) -> str:
        """Get a short one-line description of the feature."""
        info = FeatureNameDecoder.decode_feature_name(feature_name)
        return info["full_description"]

    @staticmethod
    def explain_feature(feature_name: str, verbose: bool = False) -> str:
        """
        Get detailed explanation of a feature.

        Args:
            feature_name: Feature name
            verbose: If True, include technical details

        Returns:
            Formatted explanation string
        """
        info = FeatureNameDecoder.decode_feature_name(feature_name)

        explanation = f"Feature: {feature_name}\n"
        explanation += f"Sensor: {info['sensor']}\n"
        explanation += f"Calculator: {info['calculator']}\n"

        if info['params']:
            explanation += f"Parameters: {info['params']}\n"

        explanation += f"\nDescription:\n{info['description']}\n"

        if verbose:
            explanation += f"\nFull: {info['full_description']}\n"

        return explanation


# Example usage and tests
if __name__ == "__main__":
    decoder = FeatureNameDecoder()

    # Test examples
    test_features = [
        "audio__friedrich_coefficients__coeff_0__m_3__r_30",
        "x__range_count__max_1__min_-1",
        "audio__variation_coefficient",
        "y__fft_coefficient__attr_\"real\"__coeff_4",
        "accX__mean",
        "gyroZ__autocorrelation__lag_5",
    ]

    print("Feature Name Decoder Examples")
    print("=" * 80)

    for feature in test_features:
        print(f"\n{feature}")
        print("-" * 80)
        print(decoder.get_short_description(feature))
        print()
