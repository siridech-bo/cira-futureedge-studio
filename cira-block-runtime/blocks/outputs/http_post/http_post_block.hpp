#pragma once

#include "block_interface.hpp"
using namespace CiraBlockRuntime;
#include <string>

/**
 * @brief HTTP POST Block
 *
 * Sends HTTP POST requests with data.
 *
 * Block ID: http-post
 * Version: 1.0.0
 *
 * Inputs:
 *   - payload (string): JSON or text payload to POST
 *
 * Outputs:
 *   - None (network output only)
 */
class HTTPPostBlock : public IBlock {
public:
    HTTPPostBlock();
    ~HTTPPostBlock() override;

    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    std::string GetBlockId() const override { return "http-post"; }
    std::string GetBlockVersion() const override { return "1.0.0"; }
    std::string GetBlockType() const override { return "output"; }

    std::vector<Pin> GetInputPins() const override;
    std::vector<Pin> GetOutputPins() const override;

    void SetInput(const std::string& pin_name, const BlockValue& value) override;
    BlockValue GetOutput(const std::string& pin_name) const override;

private:
    // Configuration
    std::string url_;
    std::string content_type_;
    std::string auth_token_;

    // Input values
    std::string payload_;

    bool is_initialized_;

    // HTTP interface
    bool SendPOSTRequest(const std::string& payload);
};

// Block factory functions
extern "C" {
    IBlock* CreateBlock();
    void DestroyBlock(IBlock* block);
}
