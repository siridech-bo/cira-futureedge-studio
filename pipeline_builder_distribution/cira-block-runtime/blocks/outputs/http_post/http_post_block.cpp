#include "http_post_block.hpp"
#include <iostream>

using namespace CiraBlockRuntime;

HTTPPostBlock::HTTPPostBlock()
    : url_("http://localhost:8080/api/data")
    , content_type_("application/json")
    , auth_token_("")
    , payload_("")
    , is_initialized_(false) {
}

HTTPPostBlock::~HTTPPostBlock() {
    Shutdown();
}

bool HTTPPostBlock::Initialize(const BlockConfig& config) {
    std::cout << "[HTTP POST] Initializing..." << std::endl;

    // Load configuration
    if (config.find("url") != config.end()) {
        url_ = config.at("url");
    }
    if (config.find("content_type") != config.end()) {
        content_type_ = config.at("content_type");
    }
    if (config.find("auth_token") != config.end()) {
        auth_token_ = config.at("auth_token");
    }

    std::cout << "  URL: " << url_ << std::endl;
    std::cout << "  Content-Type: " << content_type_ << std::endl;
    std::cout << "  Auth: " << (auth_token_.empty() ? "None" : "Token provided") << std::endl;

#ifdef _WIN32
    std::cout << "  [Simulation Mode] HTTP POST initialized" << std::endl;
#endif

    is_initialized_ = true;
    std::cout << "[HTTP POST] Initialization complete" << std::endl;
    return true;
}

bool HTTPPostBlock::Execute() {
    if (!is_initialized_) {
        std::cerr << "[HTTP POST] Not initialized" << std::endl;
        return false;
    }

    if (payload_.empty()) {
        return true;  // Nothing to send
    }

#ifdef _WIN32
    // Simulation mode - print request
    std::cout << "[HTTP POST] POST " << url_ << std::endl;
    std::cout << "  Payload: " << payload_ << std::endl;
#else
    if (!SendPOSTRequest(payload_)) {
        std::cerr << "[HTTP POST] Failed to send request" << std::endl;
        return false;
    }
#endif

    return true;
}

void HTTPPostBlock::Shutdown() {
    if (is_initialized_) {
        is_initialized_ = false;
        std::cout << "[HTTP POST] Shutdown complete" << std::endl;
    }
}

std::vector<Pin> HTTPPostBlock::GetInputPins() const {
    return {
        Pin("payload", "string", true)
    };
}

std::vector<Pin> HTTPPostBlock::GetOutputPins() const {
    return {}; // No outputs
}

void HTTPPostBlock::SetInput(const std::string& pin_name, const BlockValue& value) {
    if (pin_name == "payload") {
        payload_ = std::get<std::string>(value);
    }
}

BlockValue HTTPPostBlock::GetOutput(const std::string& pin_name) const {
    return 0.0f; // No outputs
}

bool HTTPPostBlock::SendPOSTRequest(const std::string& payload) {
#ifndef _WIN32
    // In a real implementation, this would use libcurl or similar HTTP library
    // For now, simulate the request
    std::cout << "[HTTP POST] POST " << url_ << std::endl;
    std::cout << "  Content-Type: " << content_type_ << std::endl;
    std::cout << "  Payload: " << payload << std::endl;
    std::cout << "  ✓ Request sent successfully (simulated)" << std::endl;
    return true;
#else
    return true;
#endif
}

// Block factory functions
extern "C" {
    IBlock* CreateBlock() {
        return new HTTPPostBlock();
    }

    void DestroyBlock(IBlock* block) {
        delete block;
    }
}
