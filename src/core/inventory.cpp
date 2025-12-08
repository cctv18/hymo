// core/inventory.cpp - Module inventory implementation
#include "inventory.hpp"
#include "../defs.hpp"
#include "../utils.hpp"
#include <algorithm>
#include <fstream>
#include <sstream>

namespace hymo {

static void parse_module_prop(const fs::path& module_path, Module& module) {
    fs::path prop_file = module_path / "module.prop";
    if (!fs::exists(prop_file)) return;

    std::ifstream file(prop_file);
    std::string line;
    while (std::getline(file, line)) {
        size_t eq = line.find('=');
        if (eq == std::string::npos) continue;

        std::string key = line.substr(0, eq);
        std::string value = line.substr(eq + 1);

        // Trim whitespace if needed (though usually module.prop is strict)
        // Simple key matching
        if (key == "name") module.name = value;
        else if (key == "version") module.version = value;
        else if (key == "author") module.author = value;
        else if (key == "description") module.description = value;
    }
}

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
            
            Module mod{id, entry.path(), mode};
            parse_module_prop(entry.path(), mod);
            modules.push_back(mod);
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
