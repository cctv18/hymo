// core/state.cpp - Runtime state implementation
#include "state.hpp"
#include "../defs.hpp"
#include "../utils.hpp"
#include <fstream>
#include <sstream>

namespace hymo {

bool RuntimeState::save() const {
    ensure_dir_exists(fs::path(STATE_FILE).parent_path());
    
    std::ofstream file(STATE_FILE);
    if (!file.is_open()) {
        LOG_ERROR("Failed to save runtime state");
        return false;
    }
    
    // Simple JSON format
    file << "{\n";
    file << "  \"storage_mode\": \"" << storage_mode << "\",\n";
    file << "  \"mount_point\": \"" << mount_point << "\",\n";
    file << "  \"nuke_active\": " << (nuke_active ? "true" : "false") << ",\n";
    
    file << "  \"overlay_module_ids\": [";
    for (size_t i = 0; i < overlay_module_ids.size(); ++i) {
        file << "\"" << overlay_module_ids[i] << "\"";
        if (i < overlay_module_ids.size() - 1) file << ", ";
    }
    file << "],\n";
    
    file << "  \"magic_module_ids\": [";
    for (size_t i = 0; i < magic_module_ids.size(); ++i) {
        file << "\"" << magic_module_ids[i] << "\"";
        if (i < magic_module_ids.size() - 1) file << ", ";
    }
    file << "],\n";

    file << "  \"hymofs_module_ids\": [";
    for (size_t i = 0; i < hymofs_module_ids.size(); ++i) {
        file << "\"" << hymofs_module_ids[i] << "\"";
        if (i < hymofs_module_ids.size() - 1) file << ", ";
    }
    file << "]\n";
    
    file << "}\n";
    
    return true;
}

RuntimeState load_runtime_state() {
    RuntimeState state;
    
    if (!fs::exists(STATE_FILE)) {
        return state;
    }
    
    std::ifstream file(STATE_FILE);
    if (!file.is_open()) {
        return state;
    }
    
    // Simple JSON parser (very basic)
    std::string line;
    while (std::getline(file, line)) {
        // Remove whitespace
        line.erase(0, line.find_first_not_of(" \t"));
        
        if (line.find("\"storage_mode\"") != std::string::npos) {
            auto start = line.find(": \"") + 3;
            auto end = line.find("\"", start);
            if (end != std::string::npos) {
                state.storage_mode = line.substr(start, end - start);
            }
        } else if (line.find("\"mount_point\"") != std::string::npos) {
            auto start = line.find(": \"") + 3;
            auto end = line.find("\"", start);
            if (end != std::string::npos) {
                state.mount_point = line.substr(start, end - start);
            }
        } else if (line.find("\"nuke_active\"") != std::string::npos) {
            state.nuke_active = line.find("true") != std::string::npos;
        } else if (line.find("\"overlay_module_ids\"") != std::string::npos) {
            auto start = line.find("[");
            auto end = line.find("]");
            if (start != std::string::npos && end != std::string::npos) {
                std::string content = line.substr(start + 1, end - start - 1);
                std::stringstream ss(content);
                std::string item;
                while (std::getline(ss, item, ',')) {
                    // Clean quotes and spaces
                    size_t first = item.find("\"");
                    size_t last = item.rfind("\"");
                    if (first != std::string::npos && last != std::string::npos && last > first) {
                        state.overlay_module_ids.push_back(item.substr(first + 1, last - first - 1));
                    }
                }
            }
        } else if (line.find("\"magic_module_ids\"") != std::string::npos) {
            auto start = line.find("[");
            auto end = line.find("]");
            if (start != std::string::npos && end != std::string::npos) {
                std::string content = line.substr(start + 1, end - start - 1);
                std::stringstream ss(content);
                std::string item;
                while (std::getline(ss, item, ',')) {
                    size_t first = item.find("\"");
                    size_t last = item.rfind("\"");
                    if (first != std::string::npos && last != std::string::npos && last > first) {
                        state.magic_module_ids.push_back(item.substr(first + 1, last - first - 1));
                    }
                }
            }
        } else if (line.find("\"hymofs_module_ids\"") != std::string::npos) {
            auto start = line.find("[");
            auto end = line.find("]");
            if (start != std::string::npos && end != std::string::npos) {
                std::string content = line.substr(start + 1, end - start - 1);
                std::stringstream ss(content);
                std::string item;
                while (std::getline(ss, item, ',')) {
                    size_t first = item.find("\"");
                    size_t last = item.rfind("\"");
                    if (first != std::string::npos && last != std::string::npos && last > first) {
                        state.hymofs_module_ids.push_back(item.substr(first + 1, last - first - 1));
                    }
                }
            }
        }
    }
    
    return state;
}

} // namespace hymo
