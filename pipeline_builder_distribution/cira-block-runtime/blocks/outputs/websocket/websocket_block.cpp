#include "websocket_block.hpp"
#include <iostream>

using namespace CiraBlockRuntime;

WebSocketBlock::WebSocketBlock()
    : ws_url_("ws://localhost:8080/ws")
    , reconnect_interval_(5)
    , message_("")
    , is_initialized_(false)
    , is_connected_(false) {
}

WebSocketBlock::~WebSocketBlock() {
    Shutdown();
}

bool WebSocketBlock::Initialize(const BlockConfig& config) {
    std::cout << "[WebSocket] Initializing..." << std::endl;

    // Load configuration
    if (config.find("ws_url") != config.end()) {
        ws_url_ = config.at("ws_url");
    }
    if (config.find("reconnect_interval") != config.end()) {
        reconnect_interval_ = std::stoi(config.at("reconnect_interval"));
    }

    std::cout << "  WebSocket URL: " << ws_url_ << std::endl;
    std::cout << "  Reconnect Interval: " << reconnect_interval_ << "s" << std::endl;

#ifndef _WIN32
    if (!Connect()) {
        std::cout << "  [Warning] WebSocket connection failed, will retry" << std::endl;
    }
#else
    std::cout << "  [Simulation Mode] WebSocket initialized" << std::endl;
#endif

    is_initialized_ = true;
    std::cout << "[WebSocket] Initialization complete" << std::endl;
    return true;
}

bool WebSocketBlock::Execute() {
    if (!is_initialized_) {
        std::cerr << "[WebSocket] Not initialized" << std::endl;
        return false;
    }

    if (message_.empty()) {
        return true;  // Nothing to send
    }

#ifdef _WIN32
    // Simulation mode - print message
    std::cout << "[WebSocket] Sending to '" << ws_url_ << "': " << message_ << std::endl;
#else
    // Reconnect if disconnected
    if (!is_connected_) {
        Connect();
    }

    if (!SendMessage(message_)) {
        std::cerr << "[WebSocket] Failed to send message" << std::endl;
        return false;
    }
#endif

    return true;
}

void WebSocketBlock::Shutdown() {
    if (is_initialized_) {
#ifndef _WIN32
        Disconnect();
#endif
        is_initialized_ = false;
        std::cout << "[WebSocket] Shutdown complete" << std::endl;
    }
}

std::vector<Pin> WebSocketBlock::GetInputPins() const {
    return {
        Pin("message", "string", true)
    };
}

std::vector<Pin> WebSocketBlock::GetOutputPins() const {
    return {}; // No outputs
}

void WebSocketBlock::SetInput(const std::string& pin_name, const BlockValue& value) {
    if (pin_name == "message") {
        message_ = std::get<std::string>(value);
    }
}

BlockValue WebSocketBlock::GetOutput(const std::string& pin_name) const {
    return 0.0f; // No outputs
}

bool WebSocketBlock::Connect() {
#ifndef _WIN32
    // In a real implementation, this would use a WebSocket library
    // For now, simulate connection
    std::cout << "  [WebSocket] Connecting to " << ws_url_ << "..." << std::endl;

    // Simulated connection
    is_connected_ = true;
    std::cout << "  ✓ Connected to WebSocket server" << std::endl;
    return true;
#else
    return true;
#endif
}

void WebSocketBlock::Disconnect() {
#ifndef _WIN32
    if (is_connected_) {
        std::cout << "  [WebSocket] Disconnecting..." << std::endl;
        is_connected_ = false;
    }
#endif
}

bool WebSocketBlock::SendMessage(const std::string& message) {
#ifndef _WIN32
    if (!is_connected_) {
        std::cerr << "[WebSocket] Not connected to server" << std::endl;
        return false;
    }

    // In a real implementation, this would call WebSocket send API
    std::cout << "[WebSocket] Sending: " << message << std::endl;
    return true;
#else
    return true;
#endif
}

// Block factory functions
extern "C" {
    IBlock* CreateBlock() {
        return new WebSocketBlock();
    }

    void DestroyBlock(IBlock* block) {
        delete block;
    }
}
