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

// OLED requires display library


// ==================== Global Variables ====================
// TimesNet Model Node 1
std::unique_ptr<Ort::Session> onnx_session_1;
std::unique_ptr<Ort::Env> onnx_env_1;
int prediction_1 = 0;
float confidence_1 = 0.0f;
// ADXL345 Node 2
int adxl345_fd_2 = -1;
float adxl345_x_2, adxl345_y_2, adxl345_z_2;
// Channel Merge Node 3
float channel_0_3 = 0.0f;
float channel_1_3 = 0.0f;
float channel_2_3 = 0.0f;
std::array<float, 3> merged_output_3;
// Sliding Window Node 4
std::deque<float> window_buffer_4;
bool window_ready_4 = false;
// OLED Display Node 5
// GPIO Output Node 6
// OLED Display Node 7
// GPIO Output Node 8
// OLED Display Node 9
// GPIO Output Node 10
// OLED Display Node 11

int main() {
    std::cout << "CiRA Pipeline Initialized" << std::endl;
    std::cout << "Nodes: 11" << std::endl;

    // ==================== Node Initialization ====================
    // Initialize TimesNet Model Node 1
    try {
        onnx_env_1 = std::make_unique<Ort::Env>(ORT_LOGGING_LEVEL_WARNING, "TimesNet");
        Ort::SessionOptions session_options;
        session_options.SetIntraOpNumThreads(4);
        session_options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
        
        onnx_session_1 = std::make_unique<Ort::Session>(*onnx_env_1, "models/timesnet_model.onnx", session_options);
        std::cout << "TimesNet model loaded: models/timesnet_model.onnx" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Failed to load ONNX model: " << e.what() << std::endl;
    }
    // Initialize ADXL345 Node 2
    adxl345_fd_2 = open("/dev/i2c-1", O_RDWR);
    if (adxl345_fd_2 >= 0) {
        ioctl(adxl345_fd_2, I2C_SLAVE, 0x53);
        char power_ctl[2] = {0x2D, 0x08};
        write(adxl345_fd_2, power_ctl, 2);
    }
    // Channel Merge Node 3 - no initialization needed
    // Initialize Sliding Window Node 4
    window_buffer_4.clear();
    // Initialize OLED Display Node 5
    // Initialize GPIO Output Node 6
    // Initialize OLED Display Node 7
    // Initialize GPIO Output Node 8
    // Initialize OLED Display Node 9
    // Initialize GPIO Output Node 10
    // Initialize OLED Display Node 11

    // Pipeline connections: 9 link(s)
    // Node 2 (accel_x) -> Node 3 (channel_0)
    // Node 2 (accel_y) -> Node 3 (channel_1)
    // Node 2 (accel_z) -> Node 3 (channel_2)
    // Node 3 (merged_out) -> Node 4 (input)
    // Node 4 (window_out) -> Node 1 (features_in)
    // Node 1 (confidence_out) -> Node 5 (value)
    // Node 1 (confidence_out) -> Node 7 (value)
    // Node 1 (confidence_out) -> Node 9 (value)
    // Node 1 (confidence_out) -> Node 11 (value)

    // ==================== Main Execution Loop ====================
    bool running = true;
    while (running) {
        // TimesNet Model Node 1 - Inference
        if (onnx_session_1) {
            // TODO: Prepare input tensor from connected nodes
            // std::vector<float> input_data = {/* features */};
            // Run inference
            // auto output_tensors = onnx_session_1->Run(...);
            // prediction_1 = output_tensors[0];
            // confidence_1 = output_tensors[1];
        }
        // Read ADXL345 Node 2
        if (adxl345_fd_2 >= 0) {
            char buf[6];
            char reg = 0x32;
            write(adxl345_fd_2, &reg, 1);
            read(adxl345_fd_2, buf, 6);
            int16_t x = (buf[1] << 8) | buf[0];
            int16_t y = (buf[3] << 8) | buf[2];
            int16_t z = (buf[5] << 8) | buf[4];
            adxl345_x_2 = x * 0.004f;
            adxl345_y_2 = y * 0.004f;
            adxl345_z_2 = z * 0.004f;
        }
        // Channel Merge Node 3 - Combine channels
        merged_output_3[0] = channel_0_3;
        merged_output_3[1] = channel_1_3;
        merged_output_3[2] = channel_2_3;
        // Sliding Window Node 4
        // TODO: Get input from connected node
        float input_4 = 0.0f;
        window_buffer_4.push_back(input_4);
        if (window_buffer_4.size() > 100) {
            window_buffer_4.pop_front();
        }
        window_ready_4 = (window_buffer_4.size() == 100);
        // OLED Display Node 5
        // TODO: Update display
        // GPIO Output Node 6
        // TODO: Write to GPIO
        // OLED Display Node 7
        // TODO: Update display
        // GPIO Output Node 8
        // TODO: Write to GPIO
        // OLED Display Node 9
        // TODO: Update display
        // GPIO Output Node 10
        // TODO: Write to GPIO
        // OLED Display Node 11
        // TODO: Update display
        
        // For demonstration, run once
        running = false;
    }

    // ==================== Cleanup ====================
    // Cleanup TimesNet Model Node 1
    onnx_session_1.reset();
    onnx_env_1.reset();
    if (adxl345_fd_2 >= 0) close(adxl345_fd_2);
    // Channel Merge Node 3 - no cleanup needed

    std::cout << "Pipeline execution completed" << std::endl;
    return 0;
}
