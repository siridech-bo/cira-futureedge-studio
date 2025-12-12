/**
 * CiRA FutureEdge Studio - Feature Extraction
 * Implements selected tsfresh features
 */

#include "anomaly_detector.h"
#include <math.h>

void extract_features(const float* window, uint16_t window_size, float* features) {
    int feat_idx = 0;

    // Feature: x__length
    float feat_x_length = (float)window_size;
    features[feat_idx++] = feat_x_length;

    // Feature: z__fft_coefficient__attr_"angle"__coeff_3
    float feat_z_fft_coefficient_attr_angle_coe = 0.0f; // TODO: Implement
    features[feat_idx++] = feat_z_fft_coefficient_attr_angle_coe;

    // Feature: audio__range_count__max_1__min_-1
    float max_val = window[0];
    for (int i = 1; i < window_size; i++) {
        if (window[i] > max_val) max_val = window[i];
    }
    float feat_audio_range_count_max_1_min__1 = max_val;
    features[feat_idx++] = feat_audio_range_count_max_1_min__1;

    // Feature: x__friedrich_coefficients__coeff_0__m_3__r_30
    float feat_x_friedrich_coefficients_coeff_0 = 0.0f; // TODO: Implement
    features[feat_idx++] = feat_x_friedrich_coefficients_coeff_0;

    // Feature: audio__friedrich_coefficients__coeff_0__m_3__r_30
    float feat_audio_friedrich_coefficients_coe = 0.0f; // TODO: Implement
    features[feat_idx++] = feat_audio_friedrich_coefficients_coe;

}
