/**
 * CiRA FutureEdge Studio - Anomaly Detector
 * Generated for cortex-m4
 * Algorithm: KNN
 */

#ifndef ANOMALY_DETECTOR_H
#define ANOMALY_DETECTOR_H

#include <stdint.h>
#include "config.h"

#ifdef __cplusplus
extern "C" {
#endif

// Feature vector size
#define NUM_FEATURES 5

// Model parameters
#define KNN_K 5

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
