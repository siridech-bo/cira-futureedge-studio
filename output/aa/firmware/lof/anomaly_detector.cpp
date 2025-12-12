/**
 * CiRA FutureEdge Studio - Anomaly Detector Implementation
 * Algorithm: LOF
 */

#include "anomaly_detector.h"
#include <math.h>
#include <string.h>

// Scaler parameters (mean and std for each feature)
static const float feature_means[NUM_FEATURES] = {
    100.000000f,
    6.741768f,
    100.000000f,
    46456.344945f,
    211875654745012731904.000000f
};

static const float feature_stds[NUM_FEATURES] = {
    1.000000f,
    95.872745f,
    1.000000f,
    2464637.650877f,
    66401207809366514728960.000000f
};

#define ANOMALY_THRESHOLD 1.5f

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
