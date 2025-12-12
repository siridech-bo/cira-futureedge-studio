"""
CiRA FutureEdge Studio - DSP Code Generator
Converts trained Python models to optimized C++ code for embedded deployment
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pickle
import json
import numpy as np

from loguru import logger


@dataclass
class DSPConfig:
    """Configuration for DSP code generation."""
    target_platform: str = "cortex-m4"  # cortex-m4, esp32, x86
    use_fixed_point: bool = True  # Use fixed-point arithmetic
    fixed_point_bits: int = 16  # Q15 format
    optimize_size: bool = True  # Optimize for code size vs speed
    window_size: int = 128  # Samples per window
    sample_rate: int = 1000  # Hz
    memory_limit_kb: int = 64  # RAM budget


@dataclass
class GeneratedCode:
    """Generated C++ code files."""
    header_file: str  # anomaly_detector.h
    source_file: str  # anomaly_detector.cpp
    features_file: str  # features.cpp
    config_file: str  # config.h

    # Metadata
    algorithm: str
    num_features: int
    feature_names: List[str]
    code_size_estimate: int  # Bytes
    ram_usage_estimate: int  # Bytes


class DSPGenerator:
    """Generate embedded C++ code from trained models."""

    def __init__(self):
        """Initialize the DSP generator."""
        self.config = None
        self.model = None
        self.scaler = None

    def generate(
        self,
        model_path: Path,
        scaler_path: Path,
        selected_features: List[str],
        config: DSPConfig,
        output_dir: Path
    ) -> GeneratedCode:
        """
        Generate C++ code from trained model.

        Args:
            model_path: Path to trained model pickle
            scaler_path: Path to scaler pickle
            selected_features: List of selected feature names
            config: DSP generation configuration
            output_dir: Directory to save generated files

        Returns:
            GeneratedCode with file paths and metadata
        """
        logger.info(f"Generating DSP code for {model_path.stem}")
        self.config = config

        # Load model and scaler
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

        if scaler_path and scaler_path.exists():
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine algorithm type
        algorithm = model_path.stem.replace('_model', '')
        logger.info(f"Detected algorithm: {algorithm}")

        # Generate files
        header = self._generate_header(algorithm, selected_features)
        source = self._generate_source(algorithm, selected_features)
        features = self._generate_features(selected_features)
        config_h = self._generate_config()

        # Write files
        header_path = output_dir / "anomaly_detector.h"
        source_path = output_dir / "anomaly_detector.cpp"
        features_path = output_dir / "features.cpp"
        config_path = output_dir / "config.h"

        header_path.write_text(header)
        source_path.write_text(source)
        features_path.write_text(features)
        config_path.write_text(config_h)

        logger.info(f"Generated 4 files in {output_dir}")

        # Estimate sizes
        code_size = len(header) + len(source) + len(features) + len(config_h)
        ram_usage = self._estimate_ram_usage(selected_features)

        return GeneratedCode(
            header_file=str(header_path),
            source_file=str(source_path),
            features_file=str(features_path),
            config_file=str(config_path),
            algorithm=algorithm,
            num_features=len(selected_features),
            feature_names=selected_features,
            code_size_estimate=code_size,
            ram_usage_estimate=ram_usage
        )

    def _generate_header(self, algorithm: str, features: List[str]) -> str:
        """Generate anomaly_detector.h header file."""
        code = f"""/**
 * CiRA FutureEdge Studio - Anomaly Detector
 * Generated for {self.config.target_platform}
 * Algorithm: {algorithm.upper()}
 */

#ifndef ANOMALY_DETECTOR_H
#define ANOMALY_DETECTOR_H

#include <stdint.h>
#include "config.h"

#ifdef __cplusplus
extern "C" {{
#endif

// Feature vector size
#define NUM_FEATURES {len(features)}

// Model parameters
"""

        # Add model-specific parameters
        if algorithm == 'knn':
            k = self.model.n_neighbors
            code += f"#define KNN_K {k}\n"
        elif algorithm == 'lof':
            k = self.model.n_neighbors
            code += f"#define LOF_K {k}\n"

        code += """
// Data types
typedef struct {
    float features[NUM_FEATURES];
    float anomaly_score;
    uint8_t is_anomaly;
} AnomalyResult;

// Functions
void anomaly_detector_init(void);
void extract_features(const float* window, uint16_t window_size, float* features);
void detect_anomaly(const float* features, AnomalyResult* result);
float normalize_feature(float value, float mean, float std);

#ifdef __cplusplus
}
#endif

#endif // ANOMALY_DETECTOR_H
"""
        return code

    def _generate_source(self, algorithm: str, features: List[str]) -> str:
        """Generate anomaly_detector.cpp source file."""
        code = f"""/**
 * CiRA FutureEdge Studio - Anomaly Detector Implementation
 * Algorithm: {algorithm.upper()}
 */

#include "anomaly_detector.h"
#include <math.h>
#include <string.h>

// Scaler parameters (mean and std for each feature)
"""

        # Generate scaler parameters
        if self.scaler:
            means = self.scaler.mean_
            stds = self.scaler.scale_

            code += f"static const float feature_means[NUM_FEATURES] = {{\n"
            for i, mean in enumerate(means):
                code += f"    {mean:.6f}f{',' if i < len(means)-1 else ''}\n"
            code += "};\n\n"

            code += f"static const float feature_stds[NUM_FEATURES] = {{\n"
            for i, std in enumerate(stds):
                code += f"    {std:.6f}f{',' if i < len(stds)-1 else ''}\n"
            code += "};\n\n"

        # Generate algorithm-specific code
        if algorithm == 'knn':
            code += self._generate_knn_code()
        elif algorithm == 'lof':
            code += self._generate_lof_code()
        elif algorithm == 'iforest':
            code += self._generate_iforest_code()
        elif algorithm in ['copod', 'ecod']:
            code += self._generate_copod_code()
        else:
            code += self._generate_generic_code()

        # Common functions
        code += """
void anomaly_detector_init(void) {
    // Initialize any required state
}

float normalize_feature(float value, float mean, float std) {
    return (value - mean) / std;
}

void detect_anomaly(const float* features, AnomalyResult* result) {
    // Normalize features
    float normalized[NUM_FEATURES];
    for (int i = 0; i < NUM_FEATURES; i++) {
        normalized[i] = normalize_feature(features[i], feature_means[i], feature_stds[i]);
    }

    // Compute anomaly score
    result->anomaly_score = compute_anomaly_score(normalized);

    // Threshold (typically set to 90th percentile during training)
    result->is_anomaly = (result->anomaly_score > ANOMALY_THRESHOLD);
}
"""
        return code

    def _generate_knn_code(self) -> str:
        """Generate KNN-specific code."""
        # Get training data from model
        # PyOD KNN stores training data in different attributes depending on version
        if hasattr(self.model, '_fit_X'):
            X_train = self.model._fit_X
        elif hasattr(self.model, 'X_train_'):
            X_train = self.model.X_train_
        elif hasattr(self.model, 'fit_X_'):
            X_train = self.model.fit_X_
        else:
            # Fallback to generic implementation if training data not available
            return self._generate_generic_code()

        k = self.model.n_neighbors

        code = f"""// KNN Model - Training data ({len(X_train)} samples)
#define TRAIN_SAMPLES {len(X_train)}
#define ANOMALY_THRESHOLD 2.5f

static const float training_data[TRAIN_SAMPLES][NUM_FEATURES] = {{
"""
        # Include subset of training data (or all if small)
        max_samples = min(len(X_train), 500)  # Limit for memory
        for i in range(max_samples):
            code += "    {"
            for j, val in enumerate(X_train[i]):
                code += f"{val:.6f}f"
                if j < len(X_train[i]) - 1:
                    code += ", "
            code += "},\n"
        code += "};\n\n"

        code += f"""float compute_anomaly_score(const float* features) {{
    // Find K nearest neighbors
    float distances[TRAIN_SAMPLES];

    // Calculate distances to all training samples
    for (int i = 0; i < TRAIN_SAMPLES; i++) {{
        float dist = 0.0f;
        for (int j = 0; j < NUM_FEATURES; j++) {{
            float diff = features[j] - training_data[i][j];
            dist += diff * diff;
        }}
        distances[i] = sqrtf(dist);
    }}

    // Find K largest distances (outlier score)
    float knn_distances[KNN_K];
    memset(knn_distances, 0, sizeof(knn_distances));

    // Simple selection of K largest
    for (int i = 0; i < TRAIN_SAMPLES; i++) {{
        for (int k = 0; k < KNN_K; k++) {{
            if (distances[i] > knn_distances[k]) {{
                // Shift and insert
                for (int j = KNN_K - 1; j > k; j--) {{
                    knn_distances[j] = knn_distances[j-1];
                }}
                knn_distances[k] = distances[i];
                break;
            }}
        }}
    }}

    // Return mean of K largest distances
    float sum = 0.0f;
    for (int i = 0; i < KNN_K; i++) {{
        sum += knn_distances[i];
    }}
    return sum / KNN_K;
}}
"""
        return code

    def _generate_lof_code(self) -> str:
        """Generate LOF-specific code (simplified)."""
        return """#define ANOMALY_THRESHOLD 1.5f

float compute_anomaly_score(const float* features) {
    // Simplified LOF - compute distance to centroid
    static const float centroid[NUM_FEATURES] = {0};  // TODO: Compute from training

    float dist = 0.0f;
    for (int i = 0; i < NUM_FEATURES; i++) {
        float diff = features[i] - centroid[i];
        dist += diff * diff;
    }
    return sqrtf(dist);
}
"""

    def _generate_iforest_code(self) -> str:
        """Generate Isolation Forest code."""
        return """#define ANOMALY_THRESHOLD 0.5f
#define NUM_TREES 10
#define MAX_DEPTH 8

float compute_anomaly_score(const float* features) {
    // Isolation Forest: average path length across trees
    // This is a simplified version - full implementation would include tree structures
    float avg_path_length = 0.0f;

    // TODO: Implement tree traversal
    // For now, return placeholder
    return avg_path_length / NUM_TREES;
}
"""

    def _generate_copod_code(self) -> str:
        """Generate COPOD/ECOD code."""
        return """#define ANOMALY_THRESHOLD 3.0f

float compute_anomaly_score(const float* features) {
    // COPOD: Product of marginal outlier scores
    float score = 1.0f;

    for (int i = 0; i < NUM_FEATURES; i++) {
        // Simple z-score based outlier score
        float z = fabsf(features[i]);
        score *= (1.0f + z);
    }

    return score;
}
"""

    def _generate_generic_code(self) -> str:
        """Generate generic anomaly detection code."""
        return """#define ANOMALY_THRESHOLD 2.0f

float compute_anomaly_score(const float* features) {
    // Generic: Euclidean distance from origin (after normalization)
    float dist = 0.0f;
    for (int i = 0; i < NUM_FEATURES; i++) {
        dist += features[i] * features[i];
    }
    return sqrtf(dist);
}
"""

    def _generate_features(self, features: List[str]) -> str:
        """Generate features.cpp with feature extraction code."""
        code = """/**
 * CiRA FutureEdge Studio - Feature Extraction
 * Implements selected tsfresh features
 */

#include "anomaly_detector.h"
#include <math.h>

void extract_features(const float* window, uint16_t window_size, float* features) {
    int feat_idx = 0;

"""

        # Parse feature names and generate corresponding C++ code
        for feat_name in features:
            code += f"    // Feature: {feat_name}\n"
            code += self._generate_feature_code(feat_name, "    ")
            code += f"    features[feat_idx++] = {self._get_feature_var_name(feat_name)};\n\n"

        code += "}\n"
        return code

    def _generate_feature_code(self, feature_name: str, indent: str = "") -> str:
        """Generate C++ code for a specific feature."""
        # Parse feature name (e.g., "x__length", "x__mean", "x__fft_coefficient__attr_'angle'__coeff_3")
        parts = feature_name.split("__")
        sensor = parts[0] if parts else "x"

        if "length" in feature_name:
            return f"{indent}float {self._get_feature_var_name(feature_name)} = (float)window_size;\n"

        elif "mean" in feature_name or "average" in feature_name:
            return f"""{indent}float sum = 0.0f;
{indent}for (int i = 0; i < window_size; i++) {{
{indent}    sum += window[i];
{indent}}}
{indent}float {self._get_feature_var_name(feature_name)} = sum / window_size;
"""

        elif "variance" in feature_name or "std" in feature_name:
            return f"""{indent}float mean = 0.0f, variance = 0.0f;
{indent}for (int i = 0; i < window_size; i++) mean += window[i];
{indent}mean /= window_size;
{indent}for (int i = 0; i < window_size; i++) {{
{indent}    float diff = window[i] - mean;
{indent}    variance += diff * diff;
{indent}}}
{indent}float {self._get_feature_var_name(feature_name)} = variance / window_size;
"""

        elif "maximum" in feature_name or "max" in feature_name:
            return f"""{indent}float max_val = window[0];
{indent}for (int i = 1; i < window_size; i++) {{
{indent}    if (window[i] > max_val) max_val = window[i];
{indent}}}
{indent}float {self._get_feature_var_name(feature_name)} = max_val;
"""

        elif "minimum" in feature_name or "min" in feature_name:
            return f"""{indent}float min_val = window[0];
{indent}for (int i = 1; i < window_size; i++) {{
{indent}    if (window[i] < min_val) min_val = window[i];
{indent}}}
{indent}float {self._get_feature_var_name(feature_name)} = min_val;
"""

        else:
            # Generic feature (placeholder)
            return f"{indent}float {self._get_feature_var_name(feature_name)} = 0.0f; // TODO: Implement\n"

    def _get_feature_var_name(self, feature_name: str) -> str:
        """Convert feature name to valid C variable name."""
        # Replace special characters
        var_name = feature_name.replace("__", "_").replace("-", "_").replace("\"", "").replace("'", "")
        var_name = "feat_" + var_name[:32]  # Limit length
        return var_name

    def _generate_config(self) -> str:
        """Generate config.h with platform-specific settings."""
        code = f"""/**
 * CiRA FutureEdge Studio - Configuration
 * Target: {self.config.target_platform}
 */

#ifndef CONFIG_H
#define CONFIG_H

// Platform settings
#define TARGET_PLATFORM "{self.config.target_platform}"
#define WINDOW_SIZE {self.config.window_size}
#define SAMPLE_RATE {self.config.sample_rate}

// Memory settings
#define MEMORY_LIMIT_KB {self.config.memory_limit_kb}
#define USE_FIXED_POINT {'1' if self.config.use_fixed_point else '0'}
#define FIXED_POINT_BITS {self.config.fixed_point_bits}

// Optimization
#define OPTIMIZE_SIZE {'1' if self.config.optimize_size else '0'}

#endif // CONFIG_H
"""
        return code

    def _estimate_ram_usage(self, features: List[str]) -> int:
        """Estimate RAM usage in bytes."""
        # Feature vector: 4 bytes per feature
        feature_ram = len(features) * 4

        # Window buffer: 4 bytes per sample
        window_ram = self.config.window_size * 4

        # Model data (depends on algorithm)
        if hasattr(self.model, '_fit_X'):
            model_ram = self.model._fit_X.nbytes
        else:
            model_ram = 1024  # Estimate

        total = feature_ram + window_ram + min(model_ram, 10240)  # Cap model at 10KB
        return total


def generate_dsp_code(
    model_path: Path,
    scaler_path: Path,
    selected_features: List[str],
    config: DSPConfig,
    output_dir: Path
) -> GeneratedCode:
    """
    Convenience function to generate DSP code.

    Args:
        model_path: Path to trained model
        scaler_path: Path to scaler
        selected_features: Selected feature names
        config: DSP configuration
        output_dir: Output directory

    Returns:
        GeneratedCode object
    """
    generator = DSPGenerator()
    return generator.generate(model_path, scaler_path, selected_features, config, output_dir)
