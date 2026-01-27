#pragma once

#include "block_interface.hpp"
using namespace CiraBlockRuntime;
#include <string>
#include <vector>
#include <memory>

/**
 * @brief Decision Tree Block
 *
 * Simple decision tree classifier.
 *
 * Block ID: decision-tree
 * Version: 1.0.0
 *
 * Inputs:
 *   - features_in (array): Input feature array
 *
 * Outputs:
 *   - prediction_out (int): Predicted class ID
 *   - confidence_out (float): Confidence score
 */
class DecisionTreeBlock : public IBlock {
public:
    DecisionTreeBlock();
    ~DecisionTreeBlock() override;

    bool Initialize(const BlockConfig& config) override;
    bool Execute() override;
    void Shutdown() override;

    std::string GetBlockId() const override { return "decision-tree"; }
    std::string GetBlockVersion() const override { return "1.0.0"; }
    std::string GetBlockType() const override { return "model"; }

    std::vector<Pin> GetInputPins() const override;
    std::vector<Pin> GetOutputPins() const override;

    void SetInput(const std::string& pin_name, const BlockValue& value) override;
    BlockValue GetOutput(const std::string& pin_name) const override;

private:
    // Configuration
    std::string model_path_;
    int num_classes_;
    int num_features_;

    // Input/Output
    std::vector<float> features_in_;
    int prediction_out_;
    float confidence_out_;

    bool is_initialized_;

    // Simple decision tree structure
    struct TreeNode {
        int feature_index;
        float threshold;
        int class_label;  // -1 if not a leaf
        std::unique_ptr<TreeNode> left;
        std::unique_ptr<TreeNode> right;
    };

    std::unique_ptr<TreeNode> tree_root_;

    bool LoadModel();
    int Predict(const std::vector<float>& features, TreeNode* node);
};

// Block factory functions
extern "C" {
    IBlock* CreateBlock();
    void DestroyBlock(IBlock* block);
}
