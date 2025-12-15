/**
 * CiRA FutureEdge Studio - Classifier Implementation
 * Algorithm: RANDOM_FOREST
 */

#include "classifier.h"
#include <math.h>
#include <string.h>

// Scaler parameters (mean and std for each feature)
static const float feature_means[NUM_FEATURES] = {
    12097.580839f,
    10416.147409f,
    614.154059f,
    530.229175f,
    518.357905f
};

static const float feature_stds[NUM_FEATURES] = {
    9874.665694f,
    12625.036098f,
    821.546545f,
    726.538823f,
    706.696981f
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
