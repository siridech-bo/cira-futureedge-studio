#include "block_interface.hpp"
#include <iostream>
#include <vector>
#include <memory>
#include <dlfcn.h>
#include <filesystem>
#include <chrono>
#include <thread>

using namespace CiraBlockRuntime;

// Block loader helper
class BlockLoader {
public:
    BlockLoader(const std::string& library_path) {
        handle_ = dlopen(library_path.c_str(), RTLD_LAZY);
        if (!handle_) {
            std::cerr << "Failed to load library: " << library_path << std::endl;
            std::cerr << "Error: " << dlerror() << std::endl;
            return;
        }

        create_func_ = (BlockCreateFunc)dlsym(handle_, "CreateBlock");
        destroy_func_ = (BlockDestroyFunc)dlsym(handle_, "DestroyBlock");

        if (!create_func_ || !destroy_func_) {
            std::cerr << "Failed to load functions from library" << std::endl;
            dlclose(handle_);
            handle_ = nullptr;
        }
    }

    ~BlockLoader() {
        if (handle_) {
            dlclose(handle_);
        }
    }

    IBlock* CreateBlock() {
        if (create_func_) {
            return create_func_();
        }
        return nullptr;
    }

    void DestroyBlock(IBlock* block) {
        if (destroy_func_) {
            destroy_func_(block);
        }
    }

    bool IsValid() const { return handle_ != nullptr; }

private:
    void* handle_ = nullptr;
    BlockCreateFunc create_func_ = nullptr;
    BlockDestroyFunc destroy_func_ = nullptr;
};

// Test result struct
struct TestResult {
    std::string block_name;
    bool passed;
    std::string message;
};

// Test a single block
TestResult TestBlock(const std::string& block_path, const std::string& block_name,
                     const BlockConfig& config = {}) {
    TestResult result;
    result.block_name = block_name;
    result.passed = false;

    std::cout << "\n========================================" << std::endl;
    std::cout << "Testing: " << block_name << std::endl;
    std::cout << "========================================" << std::endl;

    // Load block library
    BlockLoader loader(block_path);
    if (!loader.IsValid()) {
        result.message = "Failed to load library";
        return result;
    }

    // Create block instance
    IBlock* block = loader.CreateBlock();
    if (!block) {
        result.message = "Failed to create block instance";
        return result;
    }

    // Initialize block
    if (!block->Initialize(config)) {
        result.message = "Failed to initialize block";
        loader.DestroyBlock(block);
        return result;
    }

    // Print block info
    std::cout << "  ID: " << block->GetBlockId() << std::endl;
    std::cout << "  Version: " << block->GetBlockVersion() << std::endl;
    std::cout << "  Type: " << block->GetBlockType() << std::endl;

    // Print pins
    auto input_pins = block->GetInputPins();
    std::cout << "  Input Pins (" << input_pins.size() << "):" << std::endl;
    for (const auto& pin : input_pins) {
        std::cout << "    - " << pin.name << " (" << pin.type << ")" << std::endl;
    }

    auto output_pins = block->GetOutputPins();
    std::cout << "  Output Pins (" << output_pins.size() << "):" << std::endl;
    for (const auto& pin : output_pins) {
        std::cout << "    - " << pin.name << " (" << pin.type << ")" << std::endl;
    }

    // Set default inputs based on pin types
    for (const auto& pin : input_pins) {
        if (pin.type == "float") {
            block->SetInput(pin.name, 0.5f);
        } else if (pin.type == "int") {
            block->SetInput(pin.name, 42);
        } else if (pin.type == "bool") {
            block->SetInput(pin.name, true);
        } else if (pin.type == "string") {
            block->SetInput(pin.name, std::string("Test Message"));
        } else if (pin.type == "array") {
            block->SetInput(pin.name, std::vector<float>{0.1f, 0.2f, 0.3f});
        }
    }

    // Execute block 3 times
    std::cout << "\n  Executing block (3 cycles)..." << std::endl;
    for (int i = 0; i < 3; i++) {
        std::cout << "  --- Cycle " << (i+1) << " ---" << std::endl;
        if (!block->Execute()) {
            result.message = "Execute failed on cycle " + std::to_string(i+1);
            loader.DestroyBlock(block);
            return result;
        }

        // Read outputs
        for (const auto& pin : output_pins) {
            BlockValue output = block->GetOutput(pin.name);
            std::cout << "    Output '" << pin.name << "': ";

            if (pin.type == "float") {
                std::cout << std::get<float>(output);
            } else if (pin.type == "int") {
                std::cout << std::get<int>(output);
            } else if (pin.type == "bool") {
                std::cout << (std::get<bool>(output) ? "true" : "false");
            } else if (pin.type == "string") {
                std::cout << std::get<std::string>(output);
            } else if (pin.type == "array") {
                auto arr = std::get<std::vector<float>>(output);
                std::cout << "[";
                for (size_t j = 0; j < arr.size() && j < 5; j++) {
                    std::cout << arr[j];
                    if (j < arr.size() - 1 && j < 4) std::cout << ", ";
                }
                if (arr.size() > 5) std::cout << "...";
                std::cout << "]";
            }
            std::cout << std::endl;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    // Shutdown
    block->Shutdown();
    loader.DestroyBlock(block);

    result.passed = true;
    result.message = "All tests passed";
    std::cout << "  ✓ Test PASSED" << std::endl;

    return result;
}

int main(int argc, char** argv) {
    std::cout << "========================================" << std::endl;
    std::cout << "  CiRA Block Runtime - Block Test Suite" << std::endl;
    std::cout << "========================================" << std::endl;

    std::string build_dir = "../build/blocks";
    if (argc > 1) {
        build_dir = argv[1];
    }

    std::vector<TestResult> results;

    // Test all blocks
    std::cout << "\nScanning for blocks in: " << build_dir << std::endl;

    // Sensor Blocks
    results.push_back(TestBlock(build_dir + "/sensors/adxl345/adxl345-sensor-v1.0.0.dll",
                                "ADXL345 Sensor"));

    results.push_back(TestBlock(build_dir + "/sensors/bme280/bme280-sensor-v1.0.0.dll",
                                "BME280 Sensor"));

    results.push_back(TestBlock(build_dir + "/sensors/analog_input/analog-input-v1.0.0.dll",
                                "Analog Input"));

    results.push_back(TestBlock(build_dir + "/sensors/gpio_input/gpio-input-v1.0.0.dll",
                                "GPIO Input"));

    // Processing Blocks
    results.push_back(TestBlock(build_dir + "/processing/low_pass_filter/low-pass-filter-v1.0.0.dll",
                                "Low Pass Filter", {{"alpha", "0.3"}}));

    results.push_back(TestBlock(build_dir + "/processing/sliding_window/sliding-window-v1.0.0.dll",
                                "Sliding Window", {{"window_size", "10"}}));

    results.push_back(TestBlock(build_dir + "/processing/normalize/normalize-v1.0.0.dll",
                                "Normalize", {{"input_min", "0"}, {"input_max", "100"},
                                             {"output_min", "0"}, {"output_max", "1"}}));

    results.push_back(TestBlock(build_dir + "/processing/channel_merge/channel-merge-v1.0.0.dll",
                                "Channel Merge", {{"num_channels", "3"}}));

    // AI/Model Blocks
    results.push_back(TestBlock(build_dir + "/ai/timesnet_onnx/timesnet-v1.2.0.dll",
                                "TimesNet ONNX", {{"num_classes", "2"}, {"seq_len", "100"},
                                                  {"num_channels", "3"}}));

    results.push_back(TestBlock(build_dir + "/ai/decision_tree/decision-tree-v1.0.0.dll",
                                "Decision Tree", {{"num_classes", "2"}, {"num_features", "3"}}));

    // Output Blocks
    results.push_back(TestBlock(build_dir + "/outputs/oled_display/oled-display-v1.1.0.dll",
                                "OLED Display"));

    results.push_back(TestBlock(build_dir + "/outputs/gpio_output/gpio-output-v1.0.0.dll",
                                "GPIO Output", {{"gpio_pin", "18"}}));

    results.push_back(TestBlock(build_dir + "/outputs/pwm_output/pwm-output-v1.0.0.dll",
                                "PWM Output", {{"pwm_channel", "0"}, {"frequency", "1000"}}));

    results.push_back(TestBlock(build_dir + "/outputs/mqtt_publisher/mqtt-publisher-v1.0.0.dll",
                                "MQTT Publisher", {{"broker_address", "localhost"},
                                                   {"topic", "test/topic"}}));

    results.push_back(TestBlock(build_dir + "/outputs/http_post/http-post-v1.0.0.dll",
                                "HTTP POST", {{"url", "http://localhost:8080/api/data"}}));

    results.push_back(TestBlock(build_dir + "/outputs/websocket/websocket-v1.0.0.dll",
                                "WebSocket", {{"ws_url", "ws://localhost:8080/ws"}}));

    // Print summary
    std::cout << "\n========================================" << std::endl;
    std::cout << "  TEST SUMMARY" << std::endl;
    std::cout << "========================================" << std::endl;

    int passed = 0;
    int failed = 0;

    for (const auto& result : results) {
        std::cout << (result.passed ? "✓" : "✗") << " "
                  << result.block_name << ": " << result.message << std::endl;
        if (result.passed) passed++;
        else failed++;
    }

    std::cout << "\nTotal: " << results.size() << " blocks" << std::endl;
    std::cout << "Passed: " << passed << std::endl;
    std::cout << "Failed: " << failed << std::endl;
    std::cout << "Success Rate: " << (100.0 * passed / results.size()) << "%" << std::endl;

    return (failed == 0) ? 0 : 1;
}
