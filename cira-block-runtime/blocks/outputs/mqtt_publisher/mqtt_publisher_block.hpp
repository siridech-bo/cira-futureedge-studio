#pragma once

#include "block_interface.hpp"
using namespace CiraBlockRuntime;
#include <string>

/**
 * @brief MQTT Publisher Block
 *
 * Publishes data to MQTT broker.
 *
 * Block ID: mqtt-publisher
 * Version: 1.0.0
 *
 * Inputs:
 *   - message (string): Message to publish
 *
 * Outputs:
 *   - None (network output only)
 */
class MQTTPublisherBlock : public IBlock {
public:
    MQTTPublisherBlock();
    ~MQTTPublisherBlock() override;

    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    std::string GetBlockId() const override { return "mqtt-publisher"; }
    std::string GetBlockVersion() const override { return "1.0.0"; }
    std::string GetBlockType() const override { return "output"; }

    std::vector<Pin> GetInputPins() const override;
    std::vector<Pin> GetOutputPins() const override;

    void SetInput(const std::string& pin_name, const BlockValue& value) override;
    BlockValue GetOutput(const std::string& pin_name) const override;

private:
    // Configuration
    std::string broker_address_;
    int broker_port_;
    std::string topic_;
    std::string client_id_;

    // Input values
    std::string message_;

    bool is_initialized_;
    bool is_connected_;

    // MQTT interface (simplified - would use library like Paho MQTT in real implementation)
    bool Connect();
    void Disconnect();
    bool Publish(const std::string& message);
};

// Block factory functions
extern "C" {
    IBlock* CreateBlock();
    void DestroyBlock(IBlock* block);
}
