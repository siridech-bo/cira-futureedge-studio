#pragma once

#include "block_interface.hpp"
using namespace CiraBlockRuntime;
#include <string>
#include <vector>
#include <memory>

#ifdef USE_ONNXRUNTIME
#include <onnxruntime_cxx_api.h>
#endif

/**
 * @brief TimesNet ONNX Inference Block
 *
 * Runs TimesNet model inference using ONNX Runtime.
 *
 * Block ID: timesnet
 * Version: 1.2.0
 *
 * Inputs:
 *   - features_in (array): Input feature array [batch, seq_len, channels]
 *
 * Outputs:
 *   - prediction_out (int): Predicted class ID
 *   - confidence_out (float): Confidence score (0.0 - 1.0)
 */
class TimesNetOnnxBlock : public IBlock {
public:
    TimesNetOnnxBlock();
    ~TimesNetOnnxBlock() override;

    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    std::string GetBlockId() const override { return "timesnet"; }
    std::string GetBlockVersion() const override { return "1.2.0"; }
    std::string GetBlockType() const override { return "model"; }

    std::vector<Pin> GetInputPins() const override;
    std::vector<Pin> GetOutputPins() const override;

    void SetInput(const std::string& pin_name, const BlockValue& value) override;
    BlockValue GetOutput(const std::string& pin_name) const override;

private:
    // Configuration
    std::string model_path_;
    int num_classes_;
    int seq_len_;
    int num_channels_;
    std::vector<std::string> class_names_;

    // Input/Output
    std::vector<float> features_in_;
    int prediction_out_;
    float confidence_out_;

#ifdef USE_ONNXRUNTIME
    // ONNX Runtime
    std::unique_ptr<Ort::Env> ort_env_;
    std::unique_ptr<Ort::Session> ort_session_;
    Ort::SessionOptions session_options_;
    std::vector<const char*> input_names_;
    std::vector<const char*> output_names_;
#endif

    bool is_initialized_;
    bool LoadModel();
    void RunInference();
};

// Block factory functions
extern "C" {
    IBlock* CreateBlock();
    void DestroyBlock(IBlock* block);
}
