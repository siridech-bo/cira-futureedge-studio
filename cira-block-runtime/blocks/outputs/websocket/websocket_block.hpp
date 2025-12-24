#pragma once

#include "block_interface.hpp"
using namespace CiraBlockRuntime;
#include <string>

/**
 * @brief WebSocket Block
 *
 * Sends data via WebSocket connection.
 *
 * Block ID: websocket
 * Version: 1.0.0
 *
 * Inputs:
 *   - message (string): Message to send via WebSocket
 *
 * Outputs:
 *   - None (network output only)
 */
class WebSocketBlock : public IBlock {
public:
    WebSocketBlock();
    ~WebSocketBlock() override;

    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    std::string GetBlockId() const override { return "websocket"; }
    std::string GetBlockVersion() const override { return "1.0.0"; }
    std::string GetBlockType() const override { return "output"; }

    std::vector<Pin> GetInputPins() const override;
    std::vector<Pin> GetOutputPins() const override;

    void SetInput(const std::string& pin_name, const BlockValue& value) override;
    BlockValue GetOutput(const std::string& pin_name) const override;

private:
    // Configuration
    std::string ws_url_;
    int reconnect_interval_;  // seconds

    // Input values
    std::string message_;

    bool is_initialized_;
    bool is_connected_;

    // WebSocket interface
    bool Connect();
    void Disconnect();
    bool SendMessage(const std::string& message);
};

// Block factory functions
extern "C" {
    IBlock* CreateBlock();
    void DestroyBlock(IBlock* block);
}
