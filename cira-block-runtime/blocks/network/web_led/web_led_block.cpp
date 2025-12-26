#include "block_interface.hpp"
#include <iostream>
#include <string>
#include <mutex>
#include <variant>

namespace CiraBlockRuntime {

/**
 * WebLEDBlock - Virtual LED output displayed on web dashboard
 *
 * This block takes a boolean input and displays it as an LED
 * on the web dashboard. The LED state is sent via WebSocket.
 *
 * Input Pins:
 *   - state (bool): LED state (true = ON, false = OFF)
 *
 * Configuration:
 *   - led_id (string): Unique identifier for this LED
 *   - label (string): Display label for the LED in dashboard
 *   - color (string): LED color (red, green, blue, yellow, white)
 */
class WebLEDBlock : public IBlock {
private:
    bool state_;
    bool prev_state_;
    std::string led_id_;
    std::string label_;
    std::string color_;
    mutable std::mutex state_mutex_;
    bool state_changed_;

public:
    WebLEDBlock()
        : state_(false)
        , prev_state_(false)
        , color_("green")
        , state_changed_(false)
    {
        std::cout << "WebLEDBlock constructor called" << std::endl;
    }

    ~WebLEDBlock() override {
        std::cout << "WebLEDBlock destructor called" << std::endl;
    }

    bool Initialize(const std::map<std::string, std::string>& config) override {
        std::cout << "WebLEDBlock::Initialize()" << std::endl;

        // Get LED ID (required)
        auto it = config.find("led_id");
        if (it != config.end()) {
            led_id_ = it->second;
        } else {
            led_id_ = "led_1";  // Default ID
        }

        // Get label
        it = config.find("label");
        if (it != config.end()) {
            label_ = it->second;
        } else {
            label_ = "LED";  // Default label
        }

        // Get color
        it = config.find("color");
        if (it != config.end()) {
            color_ = it->second;
        } else {
            color_ = "green";  // Default color
        }

        std::cout << "  LED ID: " << led_id_ << std::endl;
        std::cout << "  Label: " << label_ << std::endl;
        std::cout << "  Color: " << color_ << std::endl;

        return true;
    }

    bool Execute() override {
        // State is set via SetInput()
        // Check if state changed
        std::lock_guard<std::mutex> lock(state_mutex_);
        if (state_ != prev_state_) {
            state_changed_ = true;
            prev_state_ = state_;
            std::cout << "[Web LED '" << label_ << "'] State: "
                      << (state_ ? "ON" : "OFF") << std::endl;
        }
        return true;
    }

    void SetInput(const std::string& pin_name, const BlockValue& value) override {
        if (pin_name == "state") {
            std::lock_guard<std::mutex> lock(state_mutex_);
            if (std::holds_alternative<bool>(value)) {
                state_ = std::get<bool>(value);
            } else if (std::holds_alternative<int>(value)) {
                state_ = (std::get<int>(value) != 0);
            } else if (std::holds_alternative<float>(value)) {
                state_ = (std::get<float>(value) != 0.0f);
            }
        }
    }

    BlockValue GetOutput(const std::string& pin_name) const override {
        std::lock_guard<std::mutex> lock(state_mutex_);

        if (pin_name == "state") {
            return state_;
        }

        std::cerr << "WebLEDBlock: Unknown output pin: " << pin_name << std::endl;
        return false;
    }

    void Shutdown() override {
        std::cout << "WebLEDBlock::Shutdown()" << std::endl;
    }

    // Block metadata
    std::string GetBlockId() const override {
        return "web-led";
    }

    std::string GetBlockVersion() const override {
        return "1.0.0";
    }

    std::string GetBlockType() const override {
        return "web-output";
    }

    std::vector<Pin> GetInputPins() const override {
        return {
            Pin("state", "bool", true)
        };
    }

    std::vector<Pin> GetOutputPins() const override {
        return {
            Pin("state", "bool", false)
        };
    }

    // Get LED state for WebSocket transmission
    bool GetLEDState() const {
        return state_;
    }

    // Get LED ID for WebSocket routing
    std::string GetLEDId() const {
        return led_id_;
    }

    // Get label for dashboard display
    std::string GetLabel() const {
        return label_;
    }

    // Get color for dashboard display
    std::string GetColor() const {
        return color_;
    }

    // Check if state changed (to send update to dashboard)
    bool HasStateChanged() {
        std::lock_guard<std::mutex> lock(state_mutex_);
        bool changed = state_changed_;
        state_changed_ = false;  // Reset flag
        return changed;
    }
};

} // namespace CiraBlockRuntime

// Block factory functions
extern "C" {
    CiraBlockRuntime::IBlock* CreateBlock() {
        return new CiraBlockRuntime::WebLEDBlock();
    }

    void DestroyBlock(CiraBlockRuntime::IBlock* block) {
        delete block;
    }
}
