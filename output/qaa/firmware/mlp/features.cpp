/**
 * CiRA FutureEdge Studio - Feature Extraction
 * Implements selected tsfresh features
 */

#include "anomaly_detector.h"
#include <math.h>

void extract_features(const float* window, uint16_t window_size, float* features) {
    int feat_idx = 0;

    // Feature: z__abs_energy
    float feat_z_abs_energy = 0.0f; // TODO: Implement
    features[feat_idx++] = feat_z_abs_energy;

    // Feature: z__fft_coefficient__attr_"real"__coeff_0
    float feat_z_fft_coefficient_attr_real_coef = 0.0f; // TODO: Implement
    features[feat_idx++] = feat_z_fft_coefficient_attr_real_coef;

    // Feature: z__sum_values
    float feat_z_sum_values = 0.0f; // TODO: Implement
    features[feat_idx++] = feat_z_sum_values;

    // Feature: z__fft_coefficient__attr_"abs"__coeff_0
    float feat_z_fft_coefficient_attr_abs_coeff = 0.0f; // TODO: Implement
    features[feat_idx++] = feat_z_fft_coefficient_attr_abs_coeff;

    // Feature: x__fft_coefficient__attr_"abs"__coeff_1
    float feat_x_fft_coefficient_attr_abs_coeff = 0.0f; // TODO: Implement
    features[feat_idx++] = feat_x_fft_coefficient_attr_abs_coeff;

}
