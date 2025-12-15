/**
 * CiRA FutureEdge Studio - Classifier Implementation
 * Algorithm: RANDOM_FOREST
 */

#include "classifier.h"
#include <math.h>
#include <string.h>

// Scaler parameters (mean and std for each feature)
static const float feature_means[NUM_FEATURES] = {
    18181.063175f,
    15614.452510f,
    980.318239f,
    531.086318f,
    519.002347f
};

static const float feature_stds[NUM_FEATURES] = {
    14600.716442f,
    18635.855592f,
    1239.817752f,
    690.118280f,
    670.417417f
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
