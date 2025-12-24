#include "block_loader.hpp"
#include <iostream>

#ifdef _WIN32
#include <windows.h>
#else
#include <dlfcn.h>
#endif

namespace CiraBlockRuntime {

BlockLoader::BlockLoader()
    : block_library_path_("/usr/local/lib/cira/blocks/")
{
}

BlockLoader::~BlockLoader() {
    UnloadAll();
}

void BlockLoader::SetBlockLibraryPath(const std::string& path) {
    block_library_path_ = path;
    if (!block_library_path_.empty() && block_library_path_.back() != '/') {
        block_library_path_ += '/';
    }
}

std::string BlockLoader::GetBlockKey(const std::string& block_id, const std::string& version) const {
    return block_id + "-" + version;
}

std::string BlockLoader::GetBlockPath(const std::string& block_id, const std::string& version) const {
    // Format: /usr/local/lib/cira/blocks/block_id-version.so (Linux)
    //         block_id-version.dll (Windows)
#ifdef _WIN32
    return block_library_path_ + block_id + "-v" + version + ".dll";
#else
    return block_library_path_ + block_id + "-v" + version + ".so";
#endif
}

bool BlockLoader::IsBlockAvailable(const std::string& block_id, const std::string& version) const {
    std::string path = GetBlockPath(block_id, version);

#ifdef _WIN32
    DWORD attrs = GetFileAttributesA(path.c_str());
    return (attrs != INVALID_FILE_ATTRIBUTES && !(attrs & FILE_ATTRIBUTE_DIRECTORY));
#else
    return (access(path.c_str(), F_OK) == 0);
#endif
}

IBlock* BlockLoader::LoadBlock(const std::string& block_id, const std::string& version) {
    std::string key = GetBlockKey(block_id, version);

    // Check if already loaded
    auto it = loaded_blocks_.find(key);
    if (it != loaded_blocks_.end()) {
        std::cout << "Block " << key << " already loaded, reusing instance" << std::endl;
        return it->second.instance;
    }

    // Get block library path
    std::string lib_path = GetBlockPath(block_id, version);
    std::cout << "Loading block: " << lib_path << std::endl;

    void* handle = nullptr;

#ifdef _WIN32
    handle = LoadLibraryA(lib_path.c_str());
    if (!handle) {
        error_ = "Failed to load library: " + lib_path;
        return nullptr;
    }

    BlockCreateFunc create_func = (BlockCreateFunc)GetProcAddress((HMODULE)handle, "CreateBlock");
    BlockDestroyFunc destroy_func = (BlockDestroyFunc)GetProcAddress((HMODULE)handle, "DestroyBlock");
#else
    handle = dlopen(lib_path.c_str(), RTLD_LAZY);
    if (!handle) {
        error_ = std::string("Failed to load library: ") + dlerror();
        std::cerr << error_ << std::endl;
        return nullptr;
    }

    // Clear any existing errors
    dlerror();

    BlockCreateFunc create_func = (BlockCreateFunc)dlsym(handle, "CreateBlock");
    const char* dlsym_error = dlerror();
    if (dlsym_error) {
        error_ = std::string("Failed to find CreateBlock: ") + dlsym_error;
        dlclose(handle);
        return nullptr;
    }

    BlockDestroyFunc destroy_func = (BlockDestroyFunc)dlsym(handle, "DestroyBlock");
    dlsym_error = dlerror();
    if (dlsym_error) {
        error_ = std::string("Failed to find DestroyBlock: ") + dlsym_error;
        dlclose(handle);
        return nullptr;
    }
#endif

    // Create block instance
    IBlock* block = create_func();
    if (!block) {
        error_ = "Failed to create block instance";
#ifdef _WIN32
        FreeLibrary((HMODULE)handle);
#else
        dlclose(handle);
#endif
        return nullptr;
    }

    // Store loaded block
    LoadedBlock loaded;
    loaded.block_id = block_id;
    loaded.version = version;
    loaded.library_handle = handle;
    loaded.instance = block;
    loaded.create_func = create_func;
    loaded.destroy_func = destroy_func;

    loaded_blocks_[key] = loaded;

    std::cout << "✓ Loaded block: " << block_id << " v" << version << std::endl;
    std::cout << "  Type: " << block->GetBlockType() << std::endl;

    return block;
}

void BlockLoader::UnloadBlock(const std::string& block_id, const std::string& version) {
    std::string key = GetBlockKey(block_id, version);
    auto it = loaded_blocks_.find(key);
    if (it == loaded_blocks_.end()) {
        return;
    }

    LoadedBlock& loaded = it->second;

    // Destroy block instance
    if (loaded.instance) {
        loaded.destroy_func(loaded.instance);
        loaded.instance = nullptr;
    }

    // Unload library
    if (loaded.library_handle) {
#ifdef _WIN32
        FreeLibrary((HMODULE)loaded.library_handle);
#else
        dlclose(loaded.library_handle);
#endif
        loaded.library_handle = nullptr;
    }

    loaded_blocks_.erase(it);
    std::cout << "Unloaded block: " << key << std::endl;
}

void BlockLoader::UnloadAll() {
    for (auto& [key, loaded] : loaded_blocks_) {
        if (loaded.instance) {
            loaded.destroy_func(loaded.instance);
        }
        if (loaded.library_handle) {
#ifdef _WIN32
            FreeLibrary((HMODULE)loaded.library_handle);
#else
            dlclose(loaded.library_handle);
#endif
        }
    }
    loaded_blocks_.clear();
    std::cout << "All blocks unloaded" << std::endl;
}

} // namespace CiraBlockRuntime
