#include "block_interface.hpp"
#include <iostream>
#include <string>
#include <mutex>
#include <variant>

namespace CiraBlockRuntime {

/**
 * WebButtonBlock - Virtual GPIO input controlled from web dashboard
 *
 * This block provides a virtual button that can be pressed/released
 * from the web dashboard. It outputs a boolean value representing
 * the button state.
 *
 * Output Pins:
 *   - state (bool): Current button state (true = pressed, false = released)
 *
 * Configuration:
 *   - button_id (string): Unique identifier for this button
 *   - label (string): Display label for the button in dashboard
 *   - initial_state (bool): Initial button state (default: false)
 */
class WebButtonBlock : public IBlock {
private:
    bool state_;
    std::string button_id_;
    std::string label_;
    bool initial_state_;
    mutable std::mutex state_mutex_;

public:
    WebButtonBlock()
        : state_(false)
        , initial_state_(false)
    {
        std::cout << "WebButtonBlock constructor called" << std::endl;
    }

    ~WebButtonBlock() override {
        std::cout << "WebButtonBlock destructor called" << std::endl;
    }

    bool Initialize(const std::map<std::string, std::string>& config) override {
        std::cout << "WebButtonBlock::Initialize()" << std::endl;

        // Get button ID (required)
        auto it = config.find("button_id");
        if (it != config.end()) {
            button_id_ = it->second;
        } else {
            button_id_ = "button_1";  // Default ID
        }

        // Get label
        it = config.find("label");
        if (it != config.end()) {
            label_ = it->second;
        } else {
            label_ = "Button";  // Default label
        }

        // Get initial state
        it = config.find("initial_state");
        if (it != config.end()) {
            initial_state_ = (it->second == "true" || it->second == "1");
        } else {
            initial_state_ = false;
        }

        state_ = initial_state_;

        std::cout << "  Button ID: " << button_id_ << std::endl;
        std::cout << "  Label: " << label_ << std::endl;
        std::cout << "  Initial State: " << (initial_state_ ? "pressed" : "released") << std::endl;

        return true;
    }

    bool Execute() override {
        // Button state is updated via SetButtonState() called from WebSocket handler
        // Nothing to do in Execute
        return true;
    }

    void SetInput(const std::string& pin_name, const BlockValue& value) override {
        // Button state can be set via REST API
        if (pin_name == "state") {
            if (std::holds_alternative<bool>(value)) {
                SetButtonState(std::get<bool>(value));
            }
        }
    }

    BlockValue GetOutput(const std::string& pin_name) const override {
        std::lock_guard<std::mutex> lock(state_mutex_);

        if (pin_name == "state") {
            return state_;
        }

        std::cerr << "WebButtonBlock: Unknown output pin: " << pin_name << std::endl;
        return false;
    }

    void Shutdown() override {
        std::cout << "WebButtonBlock::Shutdown()" << std::endl;
    }

    // Block metadata
    std::string GetBlockId() const override {
        return "web-button";
    }

    std::string GetBlockVersion() const override {
        return "1.0.0";
    }

    std::string GetBlockType() const override {
        return "web-input";
    }

    std::vector<Pin> GetInputPins() const override {
        // No input pins - button generates output
        return {};
    }

    std::vector<Pin> GetOutputPins() const override {
        return {
            Pin("state", "bool", false)
        };
    }

    // Custom method called by WebSocket handler to update button state
    void SetButtonState(bool pressed) {
        std::lock_guard<std::mutex> lock(state_mutex_);
        state_ = pressed;
        std::cout << "[Web Button '" << label_ << "'] State: "
                  << (pressed ? "PRESSED" : "RELEASED") << std::endl;
    }

    // Get button ID for WebSocket routing
    std::string GetButtonId() const {
        return button_id_;
    }

    // Get label for dashboard display
    std::string GetLabel() const {
        return label_;
    }
};

} // namespace CiraBlockRuntime

// Block factory functions
extern "C" {
    CiraBlockRuntime::IBlock* CreateBlock() {
        return new CiraBlockRuntime::WebButtonBlock();
    }

    void DestroyBlock(CiraBlockRuntime::IBlock* block) {
        delete block;
    }
}
