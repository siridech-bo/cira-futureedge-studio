// Jetson Nano C++ Code
// Generated from CiRA Pipeline Builder

#include <array>

#include <cmath>
#include <iostream>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <unistd.h>

#include <onnxruntime_cxx_api.h>
#include <vector>
#include <memory>

#include <vector>
#include <vector>
#include <deque>

// Low Pass Filter - no special includes needed

// OLED requires display library


// ==================== Global Variables ====================
// BME280 Node 1
int bme280_fd_1 = -1;
float temp_1, humidity_1, pressure_1;
// Low Pass Filter Node 2
float filter_output_2 = 0.0f;
float filter_prev_2 = 0.0f;
// Sliding Window Node 3
std::deque<float> window_buffer_3;
bool window_ready_3 = false;
// TimesNet Model Node 5
std::unique_ptr<Ort::Session> onnx_session_5;
std::unique_ptr<Ort::Env> onnx_env_5;
int prediction_5 = 0;
float confidence_5 = 0.0f;
// TimesNet Model Node 6
std::unique_ptr<Ort::Session> onnx_session_6;
std::unique_ptr<Ort::Env> onnx_env_6;
int prediction_6 = 0;
float confidence_6 = 0.0f;
// ADXL345 Node 7
int adxl345_fd_7 = -1;
float adxl345_x_7, adxl345_y_7, adxl345_z_7;
// Channel Merge Node 8
float channel_0_8 = 0.0f;
float channel_1_8 = 0.0f;
float channel_2_8 = 0.0f;
std::array<float, 3> merged_output_8;
// Sliding Window Node 9
std::deque<float> window_buffer_9;
bool window_ready_9 = false;
// OLED Display Node 10
// GPIO Output Node 11
// OLED Display Node 12
// GPIO Output Node 13
// OLED Display Node 14
// GPIO Output Node 15
// OLED Display Node 16
// GPIO Output Node 17
// OLED Display Node 18
// ADXL345 Node 19
int adxl345_fd_19 = -1;
float adxl345_x_19, adxl345_y_19, adxl345_z_19;
// Channel Merge Node 20
float channel_0_20 = 0.0f;
float channel_1_20 = 0.0f;
float channel_2_20 = 0.0f;
std::array<float, 3> merged_output_20;
// Sliding Window Node 21
std::deque<float> window_buffer_21;
bool window_ready_21 = false;
// OLED Display Node 22
// GPIO Output Node 23
// OLED Display Node 24
// GPIO Output Node 25
// OLED Display Node 26
// GPIO Output Node 27
// OLED Display Node 28
// GPIO Output Node 29
// OLED Display Node 30

int main() {
    std::cout << "CiRA Pipeline Initialized" << std::endl;
    std::cout << "Nodes: 29" << std::endl;

    // ==================== Node Initialization ====================
    // Initialize BME280 Node 1
    bme280_fd_1 = open("/dev/i2c-1", O_RDWR);
    if (bme280_fd_1 >= 0) {
        ioctl(bme280_fd_1, I2C_SLAVE, 0x76);
        // Configure BME280 (normal mode, oversampling)
        char config[2] = {0xF4, 0x27};
        write(bme280_fd_1, config, 2);
    }
    // Initialize Low Pass Filter Node 2
    filter_prev_2 = 0.0f;
    // Initialize Sliding Window Node 3
    window_buffer_3.clear();
    // Initialize TimesNet Model Node 5
    try {
        onnx_env_5 = std::make_unique<Ort::Env>(ORT_LOGGING_LEVEL_WARNING, "TimesNet");
        Ort::SessionOptions session_options;
        session_options.SetIntraOpNumThreads(4);
        session_options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
        
        onnx_session_5 = std::make_unique<Ort::Session>(*onnx_env_5, "models/model.onnx", session_options);
        std::cout << "TimesNet model loaded: models/model.onnx" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Failed to load ONNX model: " << e.what() << std::endl;
    }
    // Initialize TimesNet Model Node 6
    try {
        onnx_env_6 = std::make_unique<Ort::Env>(ORT_LOGGING_LEVEL_WARNING, "TimesNet");
        Ort::SessionOptions session_options;
        session_options.SetIntraOpNumThreads(4);
        session_options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
        
        onnx_session_6 = std::make_unique<Ort::Session>(*onnx_env_6, "models/timesnet_model.onnx", session_options);
        std::cout << "TimesNet model loaded: models/timesnet_model.onnx" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Failed to load ONNX model: " << e.what() << std::endl;
    }
    // Initialize ADXL345 Node 7
    adxl345_fd_7 = open("/dev/i2c-1", O_RDWR);
    if (adxl345_fd_7 >= 0) {
        ioctl(adxl345_fd_7, I2C_SLAVE, 0x53);
        char power_ctl[2] = {0x2D, 0x08};
        write(adxl345_fd_7, power_ctl, 2);
    }
    // Channel Merge Node 8 - no initialization needed
    // Initialize Sliding Window Node 9
    window_buffer_9.clear();
    // Initialize OLED Display Node 10
    // Initialize GPIO Output Node 11
    // Initialize OLED Display Node 12
    // Initialize GPIO Output Node 13
    // Initialize OLED Display Node 14
    // Initialize GPIO Output Node 15
    // Initialize OLED Display Node 16
    // Initialize GPIO Output Node 17
    // Initialize OLED Display Node 18
    // Initialize ADXL345 Node 19
    adxl345_fd_19 = open("/dev/i2c-1", O_RDWR);
    if (adxl345_fd_19 >= 0) {
        ioctl(adxl345_fd_19, I2C_SLAVE, 0x53);
        char power_ctl[2] = {0x2D, 0x08};
        write(adxl345_fd_19, power_ctl, 2);
    }
    // Channel Merge Node 20 - no initialization needed
    // Initialize Sliding Window Node 21
    window_buffer_21.clear();
    // Initialize OLED Display Node 22
    // Initialize GPIO Output Node 23
    // Initialize OLED Display Node 24
    // Initialize GPIO Output Node 25
    // Initialize OLED Display Node 26
    // Initialize GPIO Output Node 27
    // Initialize OLED Display Node 28
    // Initialize GPIO Output Node 29
    // Initialize OLED Display Node 30

    // Pipeline connections: 23 link(s)
    // Node 1 (temperature) -> Node 2 (input)
    // Node 3 (window_out) -> Node 5 (features_in)
    // Node 2 (output) -> Node 3 (input)
    // Node 7 (accel_x) -> Node 8 (channel_0)
    // Node 7 (accel_y) -> Node 8 (channel_1)
    // Node 7 (accel_z) -> Node 8 (channel_2)
    // Node 8 (merged_out) -> Node 9 (input)
    // Node 9 (window_out) -> Node 5 (features_in)
    // Node 5 (confidence_out) -> Node 10 (value)
    // Node 5 (confidence_out) -> Node 12 (value)
    // Node 5 (confidence_out) -> Node 14 (value)
    // Node 5 (confidence_out) -> Node 16 (value)
    // Node 5 (confidence_out) -> Node 18 (value)
    // Node 19 (accel_x) -> Node 20 (channel_0)
    // Node 19 (accel_y) -> Node 20 (channel_1)
    // Node 19 (accel_z) -> Node 20 (channel_2)
    // Node 20 (merged_out) -> Node 21 (input)
    // Node 21 (window_out) -> Node 5 (features_in)
    // Node 5 (confidence_out) -> Node 22 (value)
    // Node 5 (confidence_out) -> Node 24 (value)
    // Node 5 (confidence_out) -> Node 26 (value)
    // Node 5 (confidence_out) -> Node 28 (value)
    // Node 5 (confidence_out) -> Node 30 (value)

    // ==================== Main Execution Loop ====================
    bool running = true;
    while (running) {
        // Read BME280 Node 1
        if (bme280_fd_1 >= 0) {
            // TODO: Implement BME280 reading with calibration
            temp_1 = 25.0f;
            humidity_1 = 50.0f;
            pressure_1 = 1013.25f;
        }
        // Low Pass Filter Node 2
        // output = alpha * input + (1 - alpha) * prev_output
        // TODO: Get input from connected node
        float input_2 = 0.0f; // Connect to upstream node
        filter_output_2 = 0.1f * input_2 + (1.0f - 0.1f) * filter_prev_2;
        filter_prev_2 = filter_output_2;
        // Sliding Window Node 3
        // TODO: Get input from connected node
        float input_3 = 0.0f;
        window_buffer_3.push_back(input_3);
        if (window_buffer_3.size() > 128) {
            window_buffer_3.pop_front();
        }
        window_ready_3 = (window_buffer_3.size() == 128);
        // TimesNet Model Node 5 - Inference
        if (onnx_session_5) {
            // TODO: Prepare input tensor from connected nodes
            // std::vector<float> input_data = {/* features */};
            // Run inference
            // auto output_tensors = onnx_session_5->Run(...);
            // prediction_5 = output_tensors[0];
            // confidence_5 = output_tensors[1];
        }
        // TimesNet Model Node 6 - Inference
        if (onnx_session_6) {
            // TODO: Prepare input tensor from connected nodes
            // std::vector<float> input_data = {/* features */};
            // Run inference
            // auto output_tensors = onnx_session_6->Run(...);
            // prediction_6 = output_tensors[0];
            // confidence_6 = output_tensors[1];
        }
        // Read ADXL345 Node 7
        if (adxl345_fd_7 >= 0) {
            char buf[6];
            char reg = 0x32;
            write(adxl345_fd_7, &reg, 1);
            read(adxl345_fd_7, buf, 6);
            int16_t x = (buf[1] << 8) | buf[0];
            int16_t y = (buf[3] << 8) | buf[2];
            int16_t z = (buf[5] << 8) | buf[4];
            adxl345_x_7 = x * 0.004f;
            adxl345_y_7 = y * 0.004f;
            adxl345_z_7 = z * 0.004f;
        }
        // Channel Merge Node 8 - Combine channels
        merged_output_8[0] = channel_0_8;
        merged_output_8[1] = channel_1_8;
        merged_output_8[2] = channel_2_8;
        // Sliding Window Node 9
        // TODO: Get input from connected node
        float input_9 = 0.0f;
        window_buffer_9.push_back(input_9);
        if (window_buffer_9.size() > 100) {
            window_buffer_9.pop_front();
        }
        window_ready_9 = (window_buffer_9.size() == 100);
        // OLED Display Node 10
        // TODO: Update display
        // GPIO Output Node 11
        // TODO: Write to GPIO
        // OLED Display Node 12
        // TODO: Update display
        // GPIO Output Node 13
        // TODO: Write to GPIO
        // OLED Display Node 14
        // TODO: Update display
        // GPIO Output Node 15
        // TODO: Write to GPIO
        // OLED Display Node 16
        // TODO: Update display
        // GPIO Output Node 17
        // TODO: Write to GPIO
        // OLED Display Node 18
        // TODO: Update display
        // Read ADXL345 Node 19
        if (adxl345_fd_19 >= 0) {
            char buf[6];
            char reg = 0x32;
            write(adxl345_fd_19, &reg, 1);
            read(adxl345_fd_19, buf, 6);
            int16_t x = (buf[1] << 8) | buf[0];
            int16_t y = (buf[3] << 8) | buf[2];
            int16_t z = (buf[5] << 8) | buf[4];
            adxl345_x_19 = x * 0.004f;
            adxl345_y_19 = y * 0.004f;
            adxl345_z_19 = z * 0.004f;
        }
        // Channel Merge Node 20 - Combine channels
        merged_output_20[0] = channel_0_20;
        merged_output_20[1] = channel_1_20;
        merged_output_20[2] = channel_2_20;
        // Sliding Window Node 21
        // TODO: Get input from connected node
        float input_21 = 0.0f;
        window_buffer_21.push_back(input_21);
        if (window_buffer_21.size() > 100) {
            window_buffer_21.pop_front();
        }
        window_ready_21 = (window_buffer_21.size() == 100);
        // OLED Display Node 22
        // TODO: Update display
        // GPIO Output Node 23
        // TODO: Write to GPIO
        // OLED Display Node 24
        // TODO: Update display
        // GPIO Output Node 25
        // TODO: Write to GPIO
        // OLED Display Node 26
        // TODO: Update display
        // GPIO Output Node 27
        // TODO: Write to GPIO
        // OLED Display Node 28
        // TODO: Update display
        // GPIO Output Node 29
        // TODO: Write to GPIO
        // OLED Display Node 30
        // TODO: Update display
        
        // For demonstration, run once
        running = false;
    }

    // ==================== Cleanup ====================
    // Cleanup TimesNet Model Node 5
    onnx_session_5.reset();
    onnx_env_5.reset();
    // Cleanup TimesNet Model Node 6
    onnx_session_6.reset();
    onnx_env_6.reset();
    if (adxl345_fd_7 >= 0) close(adxl345_fd_7);
    // Channel Merge Node 8 - no cleanup needed
    if (adxl345_fd_19 >= 0) close(adxl345_fd_19);
    // Channel Merge Node 20 - no cleanup needed

    std::cout << "Pipeline execution completed" << std::endl;
    return 0;
}
