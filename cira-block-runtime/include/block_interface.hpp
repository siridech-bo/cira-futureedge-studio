#pragma once

#include <string>
#include <vector>
#include <map>
#include <variant>
#include <memory>

namespace CiraBlockRuntime {

// Data types that can be passed between blocks
using BlockValue = std::variant<
    float,
    int,
    bool,
    std::string,
    std::vector<float>  // For arrays/vectors
>;

// Pin definition
struct Pin {
    std::string name;
    std::string type;  // "float", "int", "bool", "string", "array", "vector3"
    bool is_input;

    Pin(const std::string& n, const std::string& t, bool input)
        : name(n), type(t), is_input(input) {}
};

// Block configuration (from manifest)
using BlockConfig = std::map<std::string, std::string>;

// Abstract base class for all blocks
class IBlock {
public:
    virtual ~IBlock() = default;

    // Initialize block with configuration
    virtual bool Initialize(const BlockConfig& config) = 0;

    // Get block metadata
    virtual std::string GetBlockId() const = 0;
    virtual std::string GetBlockVersion() const = 0;
    virtual std::string GetBlockType() const = 0;  // "sensor", "processing", "model", "output"

    // Get input/output pins
    virtual std::vector<Pin> GetInputPins() const = 0;
    virtual std::vector<Pin> GetOutputPins() const = 0;

    // Set input value (called by executor before Execute())
    virtual void SetInput(const std::string& pin_name, const BlockValue& value) = 0;

    // Execute block (process inputs -> outputs)
    // Returns true on success, false on error
    virtual bool Execute() = 0;

    // Get output value (called by executor after Execute())
    virtual BlockValue GetOutput(const std::string& pin_name) const = 0;

    // Cleanup resources
    virtual void Shutdown() = 0;
};

// Factory function types (each block .so exports these)
using BlockCreateFunc = IBlock* (*)();
using BlockDestroyFunc = void (*)(IBlock*);

} // namespace CiraBlockRuntime
