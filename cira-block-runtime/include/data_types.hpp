#pragma once

#include <string>
#include <vector>
#include <cstdint>

namespace CiraBlockRuntime {

// Common data structures used across blocks

struct Vector3 {
    float x;
    float y;
    float z;

    Vector3() : x(0), y(0), z(0) {}
    Vector3(float _x, float _y, float _z) : x(_x), y(_y), z(_z) {}
};

struct SensorReading {
    float value;
    uint64_t timestamp;  // Unix timestamp in milliseconds

    SensorReading() : value(0), timestamp(0) {}
    SensorReading(float v, uint64_t ts) : value(v), timestamp(ts) {}
};

struct ModelPrediction {
    int class_id;
    float confidence;
    std::string class_name;

    ModelPrediction() : class_id(-1), confidence(0.0f) {}
    ModelPrediction(int id, float conf, const std::string& name)
        : class_id(id), confidence(conf), class_name(name) {}
};

} // namespace CiraBlockRuntime
