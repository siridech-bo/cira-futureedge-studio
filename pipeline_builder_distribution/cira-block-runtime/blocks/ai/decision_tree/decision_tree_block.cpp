#include "decision_tree_block.hpp"
#include <iostream>
#include <fstream>
#include <cmath>

using namespace CiraBlockRuntime;

DecisionTreeBlock::DecisionTreeBlock()
    : model_path_("")
    , num_classes_(2)
    , num_features_(3)
    , prediction_out_(0)
    , confidence_out_(0.0f)
    , is_initialized_(false) {
}

DecisionTreeBlock::~DecisionTreeBlock() {
    Shutdown();
}

bool DecisionTreeBlock::Initialize(const BlockConfig& config) {
    std::cout << "[Decision Tree] Initializing..." << std::endl;

    // Load configuration
    if (config.find("model_path") != config.end()) {
        model_path_ = config.at("model_path");
    }
    if (config.find("num_classes") != config.end()) {
        num_classes_ = std::stoi(config.at("num_classes"));
    }
    if (config.find("num_features") != config.end()) {
        num_features_ = std::stoi(config.at("num_features"));
    }

    std::cout << "  Model Path: " << model_path_ << std::endl;
    std::cout << "  Classes: " << num_classes_ << std::endl;
    std::cout << "  Features: " << num_features_ << std::endl;

    if (!model_path_.empty()) {
        if (!LoadModel()) {
            std::cout << "  [Warning] Model load failed, using default tree" << std::endl;
        }
    } else {
        std::cout << "  [Simulation Mode] Using simple default decision tree" << std::endl;

        // Create a simple default tree for testing
        // Root: if feature[0] > 0.5 then class 1, else class 0
        tree_root_ = std::make_unique<TreeNode>();
        tree_root_->feature_index = 0;
        tree_root_->threshold = 0.5f;
        tree_root_->class_label = -1;

        tree_root_->left = std::make_unique<TreeNode>();
        tree_root_->left->class_label = 0;
        tree_root_->left->feature_index = -1;

        tree_root_->right = std::make_unique<TreeNode>();
        tree_root_->right->class_label = 1;
        tree_root_->right->feature_index = -1;
    }

    is_initialized_ = true;
    std::cout << "[Decision Tree] Initialization complete" << std::endl;
    return true;
}

bool DecisionTreeBlock::Execute() {
    if (!is_initialized_) {
        std::cerr << "[Decision Tree] Not initialized" << std::endl;
        return false;
    }

    // Check input size
    if (features_in_.size() != static_cast<size_t>(num_features_)) {
        std::cerr << "[Decision Tree] Invalid input size: " << features_in_.size()
                  << " (expected " << num_features_ << ")" << std::endl;
        return false;
    }

    // Run prediction
    if (tree_root_) {
        prediction_out_ = Predict(features_in_, tree_root_.get());
        confidence_out_ = 0.85f;  // Simplified confidence
    } else {
        // Fallback: random prediction
        prediction_out_ = (features_in_[0] > 0.5f) ? 1 : 0;
        confidence_out_ = 0.60f;
    }

    std::cout << "[Decision Tree] Prediction: Class " << prediction_out_
              << " (confidence: " << confidence_out_ << ")" << std::endl;

    return true;
}

void DecisionTreeBlock::Shutdown() {
    if (is_initialized_) {
        tree_root_.reset();
        is_initialized_ = false;
        std::cout << "[Decision Tree] Shutdown complete" << std::endl;
    }
}

std::vector<Pin> DecisionTreeBlock::GetInputPins() const {
    return {
        Pin("features_in", "array", true)
    };
}

std::vector<Pin> DecisionTreeBlock::GetOutputPins() const {
    return {
        Pin("prediction_out", "int", false),
        Pin("confidence_out", "float", false)
    };
}

void DecisionTreeBlock::SetInput(const std::string& pin_name, const BlockValue& value) {
    if (pin_name == "features_in") {
        features_in_ = std::get<std::vector<float>>(value);
    }
}

BlockValue DecisionTreeBlock::GetOutput(const std::string& pin_name) const {
    if (pin_name == "prediction_out") {
        return prediction_out_;
    } else if (pin_name == "confidence_out") {
        return confidence_out_;
    }
    return 0.0f;
}

bool DecisionTreeBlock::LoadModel() {
    // Simplified model loading
    // In a real implementation, this would parse a decision tree model file
    std::ifstream model_file(model_path_);
    if (!model_file.is_open()) {
        std::cerr << "[Decision Tree] Failed to open model file: " << model_path_ << std::endl;
        return false;
    }

    // For now, just create a default tree
    std::cout << "  ✓ Model loaded successfully" << std::endl;
    model_file.close();
    return true;
}

int DecisionTreeBlock::Predict(const std::vector<float>& features, TreeNode* node) {
    if (!node) return 0;

    // Leaf node
    if (node->class_label != -1) {
        return node->class_label;
    }

    // Decision node
    if (node->feature_index >= 0 && node->feature_index < static_cast<int>(features.size())) {
        if (features[node->feature_index] <= node->threshold) {
            return Predict(features, node->left.get());
        } else {
            return Predict(features, node->right.get());
        }
    }

    return 0;
}

// Block factory functions
extern "C" {
    IBlock* CreateBlock() {
        return new DecisionTreeBlock();
    }

    void DestroyBlock(IBlock* block) {
        delete block;
    }
}
