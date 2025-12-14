/**
 * CiRA FutureEdge Studio - Feature Extraction
 * Implements selected tsfresh features
 */

#include "anomaly_detector.h"
#include <math.h>

void extract_features(const float* window, uint16_t window_size, float* features) {
    int feat_idx = 0;

    // Feature: accZ__abs_energy
    float feat_accZ_abs_energy = 0.0f; // TODO: Implement
    features[feat_idx++] = feat_accZ_abs_energy;

    // Feature: accX__abs_energy
    float feat_accX_abs_energy = 0.0f; // TODO: Implement
    features[feat_idx++] = feat_accX_abs_energy;

    // Feature: accX__spkt_welch_density__coeff_2
    float feat_accX_spkt_welch_density_coeff_2 = 0.0f; // TODO: Implement
    features[feat_idx++] = feat_accX_spkt_welch_density_coeff_2;

    // Feature: accZ__c3__lag_1
    float feat_accZ_c3_lag_1 = 0.0f; // TODO: Implement
    features[feat_idx++] = feat_accZ_c3_lag_1;

    // Feature: accZ__c3__lag_2
    float feat_accZ_c3_lag_2 = 0.0f; // TODO: Implement
    features[feat_idx++] = feat_accZ_c3_lag_2;

}
