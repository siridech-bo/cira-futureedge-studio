#include "mqtt_publisher_block.hpp"
#include <iostream>

using namespace CiraBlockRuntime;

MQTTPublisherBlock::MQTTPublisherBlock()
    : broker_address_("localhost")
    , broker_port_(1883)
    , topic_("sensor/data")
    , client_id_("cira_block_runtime")
    , message_("")
    , is_initialized_(false)
    , is_connected_(false) {
}

MQTTPublisherBlock::~MQTTPublisherBlock() {
    Shutdown();
}

bool MQTTPublisherBlock::Initialize(const BlockConfig& config) {
    std::cout << "[MQTT Publisher] Initializing..." << std::endl;

    // Load configuration
    if (config.find("broker_address") != config.end()) {
        broker_address_ = config.at("broker_address");
    }
    if (config.find("broker_port") != config.end()) {
        broker_port_ = std::stoi(config.at("broker_port"));
    }
    if (config.find("topic") != config.end()) {
        topic_ = config.at("topic");
    }
    if (config.find("client_id") != config.end()) {
        client_id_ = config.at("client_id");
    }

    std::cout << "  Broker: " << broker_address_ << ":" << broker_port_ << std::endl;
    std::cout << "  Topic: " << topic_ << std::endl;
    std::cout << "  Client ID: " << client_id_ << std::endl;

#ifndef _WIN32
    if (!Connect()) {
        std::cout << "  [Warning] MQTT connection failed, running in simulation mode" << std::endl;
    }
#else
    std::cout << "  [Simulation Mode] MQTT publisher initialized" << std::endl;
#endif

    is_initialized_ = true;
    std::cout << "[MQTT Publisher] Initialization complete" << std::endl;
    return true;
}

bool MQTTPublisherBlock::Execute() {
    if (!is_initialized_) {
        std::cerr << "[MQTT Publisher] Not initialized" << std::endl;
        return false;
    }

    if (message_.empty()) {
        return true;  // Nothing to publish
    }

#ifdef _WIN32
    // Simulation mode - print message
    std::cout << "[MQTT Publisher] Publishing to '" << topic_ << "': " << message_ << std::endl;
#else
    if (!Publish(message_)) {
        std::cerr << "[MQTT Publisher] Failed to publish message" << std::endl;
        return false;
    }
#endif

    return true;
}

void MQTTPublisherBlock::Shutdown() {
    if (is_initialized_) {
#ifndef _WIN32
        Disconnect();
#endif
        is_initialized_ = false;
        std::cout << "[MQTT Publisher] Shutdown complete" << std::endl;
    }
}

std::vector<Pin> MQTTPublisherBlock::GetInputPins() const {
    return {
        Pin("message", "string", true)
    };
}

std::vector<Pin> MQTTPublisherBlock::GetOutputPins() const {
    return {}; // No outputs
}

void MQTTPublisherBlock::SetInput(const std::string& pin_name, const BlockValue& value) {
    if (pin_name == "message") {
        message_ = std::get<std::string>(value);
    }
}

BlockValue MQTTPublisherBlock::GetOutput(const std::string& pin_name) const {
    return 0.0f; // No outputs
}

bool MQTTPublisherBlock::Connect() {
#ifndef _WIN32
    // In a real implementation, this would use Paho MQTT or similar library
    // For now, just simulate connection
    std::cout << "  [MQTT] Connecting to " << broker_address_ << ":" << broker_port_ << "..." << std::endl;

    // Simulated connection
    is_connected_ = true;
    std::cout << "  ✓ Connected to MQTT broker" << std::endl;
    return true;
#else
    return true;
#endif
}

void MQTTPublisherBlock::Disconnect() {
#ifndef _WIN32
    if (is_connected_) {
        std::cout << "  [MQTT] Disconnecting..." << std::endl;
        is_connected_ = false;
    }
#endif
}

bool MQTTPublisherBlock::Publish(const std::string& message) {
#ifndef _WIN32
    if (!is_connected_) {
        std::cerr << "[MQTT Publisher] Not connected to broker" << std::endl;
        return false;
    }

    // In a real implementation, this would call MQTT publish API
    std::cout << "[MQTT Publisher] Publishing to '" << topic_ << "': " << message << std::endl;
    return true;
#else
    return true;
#endif
}

// Block factory functions
extern "C" {
    IBlock* CreateBlock() {
        return new MQTTPublisherBlock();
    }

    void DestroyBlock(IBlock* block) {
        delete block;
    }
}
