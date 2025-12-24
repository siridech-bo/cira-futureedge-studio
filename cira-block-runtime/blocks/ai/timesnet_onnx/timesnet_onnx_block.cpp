#include "timesnet_onnx_block.hpp"
#include <iostream>
#include <algorithm>
#include <numeric>
#include <cmath>

using namespace CiraBlockRuntime;

TimesNetOnnxBlock::TimesNetOnnxBlock()
    : model_path_("")
    , num_classes_(2)
    , seq_len_(100)
    , num_channels_(3)
    , prediction_out_(0)
    , confidence_out_(0.0f)
    , is_initialized_(false) {
}

TimesNetOnnxBlock::~TimesNetOnnxBlock() {
    Shutdown();
}

bool TimesNetOnnxBlock::Initialize(const BlockConfig& config) {
    std::cout << "[TimesNet ONNX] Initializing..." << std::endl;

    // Load configuration
    if (config.find("model_path") != config.end()) {
        model_path_ = config.at("model_path");
    }
    if (config.find("num_classes") != config.end()) {
        num_classes_ = std::stoi(config.at("num_classes"));
    }
    if (config.find("seq_len") != config.end()) {
        seq_len_ = std::stoi(config.at("seq_len"));
    }
    if (config.find("num_channels") != config.end()) {
        num_channels_ = std::stoi(config.at("num_channels"));
    }

    std::cout << "  Model Path: " << model_path_ << std::endl;
    std::cout << "  Classes: " << num_classes_ << std::endl;
    std::cout << "  Seq Len: " << seq_len_ << std::endl;
    std::cout << "  Channels: " << num_channels_ << std::endl;

#ifdef USE_ONNXRUNTIME
    if (!LoadModel()) {
        return false;
    }
#else
    std::cout << "  [Simulation Mode] ONNX Runtime not available" << std::endl;
    std::cout << "  Using random inference simulation" << std::endl;
#endif

    is_initialized_ = true;
    std::cout << "[TimesNet ONNX] Initialization complete" << std::endl;
    return true;
}

bool TimesNetOnnxBlock::Execute() {
    if (!is_initialized_) {
        std::cerr << "[TimesNet ONNX] Not initialized" << std::endl;
        return false;
    }

    // Check input size
    int expected_size = seq_len_ * num_channels_;
    if (features_in_.size() != expected_size) {
        std::cerr << "[TimesNet ONNX] Invalid input size: " << features_in_.size()
                  << " (expected " << expected_size << ")" << std::endl;
        return false;
    }

#ifdef USE_ONNXRUNTIME
    RunInference();
#else
    // Simulation mode - generate random prediction
    prediction_out_ = rand() % num_classes_;
    confidence_out_ = 0.5f + (rand() % 50) / 100.0f; // 0.5 to 1.0

    std::cout << "[TimesNet ONNX] Prediction: Class " << prediction_out_
              << " (confidence: " << confidence_out_ << ")" << std::endl;
#endif

    return true;
}

void TimesNetOnnxBlock::Shutdown() {
    if (is_initialized_) {
#ifdef USE_ONNXRUNTIME
        ort_session_.reset();
        ort_env_.reset();
#endif
        is_initialized_ = false;
        std::cout << "[TimesNet ONNX] Shutdown complete" << std::endl;
    }
}

std::vector<Pin> TimesNetOnnxBlock::GetInputPins() const {
    return {
        Pin("features_in", "array", true)
    };
}

std::vector<Pin> TimesNetOnnxBlock::GetOutputPins() const {
    return {
        Pin("prediction_out", "int", false),
        Pin("confidence_out", "float", false)
    };
}

void TimesNetOnnxBlock::SetInput(const std::string& pin_name, const BlockValue& value) {
    if (pin_name == "features_in") {
        features_in_ = std::get<std::vector<float>>(value);
    }
}

BlockValue TimesNetOnnxBlock::GetOutput(const std::string& pin_name) const {
    if (pin_name == "prediction_out") {
        return prediction_out_;
    } else if (pin_name == "confidence_out") {
        return confidence_out_;
    }
    return 0.0f;
}

bool TimesNetOnnxBlock::LoadModel() {
#ifdef USE_ONNXRUNTIME
    try {
        ort_env_ = std::make_unique<Ort::Env>(ORT_LOGGING_LEVEL_WARNING, "TimesNet");

        session_options_.SetIntraOpNumThreads(1);
        session_options_.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_EXTENDED);

#ifdef _WIN32
        std::wstring model_path_wide(model_path_.begin(), model_path_.end());
        ort_session_ = std::make_unique<Ort::Session>(*ort_env_, model_path_wide.c_str(), session_options_);
#else
        ort_session_ = std::make_unique<Ort::Session>(*ort_env_, model_path_.c_str(), session_options_);
#endif

        // Get input/output names
        Ort::AllocatorWithDefaultOptions allocator;
        input_names_.push_back(ort_session_->GetInputName(0, allocator));
        output_names_.push_back(ort_session_->GetOutputName(0, allocator));

        std::cout << "  ✓ ONNX model loaded successfully" << std::endl;
        return true;

    } catch (const Ort::Exception& e) {
        std::cerr << "  ✗ ONNX Runtime error: " << e.what() << std::endl;
        return false;
    }
#else
    return true; // Simulation mode
#endif
}

void TimesNetOnnxBlock::RunInference() {
#ifdef USE_ONNXRUNTIME
    try {
        // Prepare input tensor
        std::vector<int64_t> input_shape = {1, seq_len_, num_channels_};
        Ort::MemoryInfo memory_info = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);

        Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
            memory_info,
            features_in_.data(),
            features_in_.size(),
            input_shape.data(),
            input_shape.size()
        );

        // Run inference
        auto output_tensors = ort_session_->Run(
            Ort::RunOptions{nullptr},
            input_names_.data(),
            &input_tensor,
            1,
            output_names_.data(),
            1
        );

        // Get output
        float* output_data = output_tensors[0].GetTensorMutableData<float>();
        int output_size = num_classes_;

        // Find max probability
        int max_idx = 0;
        float max_prob = output_data[0];
        for (int i = 1; i < output_size; i++) {
            if (output_data[i] > max_prob) {
                max_prob = output_data[i];
                max_idx = i;
            }
        }

        prediction_out_ = max_idx;
        confidence_out_ = max_prob;

        std::cout << "[TimesNet ONNX] Prediction: Class " << prediction_out_
                  << " (confidence: " << confidence_out_ << ")" << std::endl;

    } catch (const Ort::Exception& e) {
        std::cerr << "[TimesNet ONNX] Inference error: " << e.what() << std::endl;
        prediction_out_ = 0;
        confidence_out_ = 0.0f;
    }
#endif
}

// Block factory functions
extern "C" {
    IBlock* CreateBlock() {
        return new TimesNetOnnxBlock();
    }

    void DestroyBlock(IBlock* block) {
        delete block;
    }
}
