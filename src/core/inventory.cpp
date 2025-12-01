// core/inventory.cpp - Module inventory implementation
#include "inventory.hpp"
#include "../defs.hpp"
#include "../utils.hpp"
#include <algorithm>

namespace hymo {

std::vector<Module> scan_modules(const fs::path& source_dir, const Config& config) {
    std::vector<Module> modules;
    
    if (!fs::exists(source_dir)) {
        return modules;
    }
    
    try {
        for (const auto& entry : fs::directory_iterator(source_dir)) {
            if (!entry.is_directory()) {
                continue;
            }
            
            std::string id = entry.path().filename().string();
            
            // Skip internal/system directories
            if (id == "hymo" || id == "lost+found" || id == ".git") {
                continue;
            }
            
            // Check for disable flags
            if (fs::exists(entry.path() / DISABLE_FILE_NAME) ||
                fs::exists(entry.path() / REMOVE_FILE_NAME) ||
                fs::exists(entry.path() / SKIP_MOUNT_FILE_NAME)) {
                continue;
            }
            
            // Determine mode
            std::string mode = "auto";
            auto it = config.module_modes.find(id);
            if (it != config.module_modes.end()) {
                mode = it->second;
            }
            
            modules.push_back(Module{id, entry.path(), mode});
        }
        
        // Sort by ID descending (Z->A) for overlay priority
        std::sort(modules.begin(), modules.end(), 
            [](const Module& a, const Module& b) {
                return a.id > b.id;
            });
            
    } catch (const std::exception& e) {
        LOG_ERROR("Failed to scan modules: " + std::string(e.what()));
    }
    
    return modules;
}

} // namespace hymo
