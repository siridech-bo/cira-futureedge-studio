/**
 * CiRA FutureEdge Studio - Classifier Implementation
 * Algorithm: RANDOM_FOREST
 */

#include "anomaly_detector.h"
#include <math.h>
#include <string.h>

// Scaler parameters (mean and std for each feature)
static const float feature_means[NUM_FEATURES] = {
    6037.022628f,
    5216.024496f,
    1968.764098f,
    528.640081f,
    516.185921f
};

static const float feature_stds[NUM_FEATURES] = {
    5026.242754f,
    6395.179406f,
    3406.122881f,
    751.341201f,
    729.297685f
};

#define ANOMALY_THRESHOLD 2.0f

float compute_anomaly_score(const float* features) {
    // Generic: Euclidean distance from origin (after normalization)
    float dist = 0.0f;
    for (int i = 0; i < NUM_FEATURES; i++) {
        dist += features[i] * features[i];
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
