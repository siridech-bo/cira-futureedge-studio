#pragma once

#include "block_interface.hpp"
#include <string>
#include <memory>
#include <map>

namespace CiraBlockRuntime {

// Wrapper for a loaded block
struct LoadedBlock {
    std::string block_id;
    std::string version;
    void* library_handle;  // dlopen handle
    IBlock* instance;
    BlockCreateFunc create_func;
    BlockDestroyFunc destroy_func;
};

// Block loader - dynamically loads .so files
class BlockLoader {
public:
    BlockLoader();
    ~BlockLoader();

    // Set directory where blocks are installed
    void SetBlockLibraryPath(const std::string& path);

    // Load a block by ID and version
    // Returns pointer to block instance, or nullptr on failure
    IBlock* LoadBlock(const std::string& block_id, const std::string& version);

    // Unload a specific block
    void UnloadBlock(const std::string& block_id, const std::string& version);

    // Unload all blocks
    void UnloadAll();

    // Check if a block is available (file exists)
    bool IsBlockAvailable(const std::string& block_id, const std::string& version) const;

    // Get error message
    const std::string& GetError() const { return error_; }

private:
    std::string block_library_path_;
    std::map<std::string, LoadedBlock> loaded_blocks_;  // Key: "block_id-version"
    std::string error_;

    std::string GetBlockKey(const std::string& block_id, const std::string& version) const;
    std::string GetBlockPath(const std::string& block_id, const std::string& version) const;
};

} // namespace CiraBlockRuntime
