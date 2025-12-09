#include "hymofs.hpp"
#include "../utils.hpp"
#include <fstream>
#include <iostream>
#include <sys/stat.h>
#include <unistd.h>

namespace hymo {

const char* HYMO_CTL = "/proc/hymo_ctl";

int HymoFS::get_protocol_version() {
    std::ifstream ctl(HYMO_CTL);
    if (!ctl) return -1;
    
    std::string line;
    if (std::getline(ctl, line)) {
        // Expected format: "HymoFS Protocol: <version>"
        if (line.find("HymoFS Protocol: ") == 0) {
            try {
                return std::stoi(line.substr(17));
            } catch (...) {
                return -1;
            }
        }
    }
    return -1;
}

HymoFSStatus HymoFS::check_status() {
    if (!fs::exists(HYMO_CTL)) return HymoFSStatus::NotPresent;
    
    int kernel_version = get_protocol_version();
    int module_version = EXPECTED_PROTOCOL_VERSION;
    
    if (kernel_version != module_version) {
        LOG_WARN("HymoFS protocol mismatch! Kernel: " + std::to_string(kernel_version) + 
                 ", Module: " + std::to_string(module_version));
        
        if (kernel_version < module_version) {
            return HymoFSStatus::KernelTooOld;
        } else {
            return HymoFSStatus::ModuleTooOld;
        }
    }
    return HymoFSStatus::Available;
}

bool HymoFS::is_available() {
    return check_status() == HymoFSStatus::Available;
}

bool HymoFS::clear_rules() {
    std::ofstream ctl(HYMO_CTL);
    if (!ctl) return false;
    ctl << "clear" << std::endl;
    return ctl.good();
}

bool HymoFS::add_rule(const std::string& src, const std::string& target, int type) {
    std::ofstream ctl(HYMO_CTL);
    if (!ctl) return false;
    ctl << "add " << src << " " << target << " " << type << std::endl;
    return ctl.good();
}

bool HymoFS::delete_rule(const std::string& src) {
    std::ofstream ctl(HYMO_CTL);
    if (!ctl) return false;
    ctl << "delete " << src << std::endl;
    return ctl.good();
}

bool HymoFS::hide_path(const std::string& path) {
    std::ofstream ctl(HYMO_CTL);
    if (!ctl) return false;
    ctl << "hide " << path << std::endl;
    return ctl.good();
}

bool HymoFS::inject_dir(const std::string& dir) {
    std::ofstream ctl(HYMO_CTL);
    if (!ctl) return false;
    ctl << "inject " << dir << std::endl;
    return ctl.good();
}

bool HymoFS::inject_directory(const fs::path& target_base, const fs::path& module_dir) {
    if (!fs::exists(module_dir) || !fs::is_directory(module_dir)) return false;

    try {
        for (const auto& entry : fs::recursive_directory_iterator(module_dir)) {
            const fs::path& current_path = entry.path();
            
            // Calculate relative path from module root
            fs::path rel_path = fs::relative(current_path, module_dir);
            fs::path target_path = target_base / rel_path;
            
            if (entry.is_regular_file() || entry.is_symlink()) {
                // For symlinks, we also just redirect the path to the symlink file in the module
                add_rule(target_path.string(), current_path.string());
            } else if (entry.is_character_file()) {
                // Check for whiteout (0:0)
                struct stat st;
                if (stat(current_path.c_str(), &st) == 0 && st.st_rdev == 0) {
                    hide_path(target_path.string());
                }
            }
        }
    } catch (const std::exception& e) {
        LOG_WARN("HymoFS injection error for " + module_dir.string() + ": " + e.what());
        return false;
    }
    return true;
}

bool HymoFS::delete_directory_rules(const fs::path& target_base, const fs::path& module_dir) {
    if (!fs::exists(module_dir) || !fs::is_directory(module_dir)) return false;

    try {
        for (const auto& entry : fs::recursive_directory_iterator(module_dir)) {
            const fs::path& current_path = entry.path();
            
            // Calculate relative path from module root
            fs::path rel_path = fs::relative(current_path, module_dir);
            fs::path target_path = target_base / rel_path;
            
            if (entry.is_regular_file() || entry.is_symlink()) {
                // Delete rule for this file
                // Key for delete is the target path (virtual path), not the source path
                delete_rule(target_path.string());
            } else if (entry.is_character_file()) {
                // Check for whiteout (0:0)
                struct stat st;
                if (stat(current_path.c_str(), &st) == 0 && st.st_rdev == 0) {
                    // For whiteouts, we used hide_path, so we should delete the hide rule
                    // But wait, delete_rule in kernel handles both paths and hide paths?
                    // Let's check the patch.
                    // Yes, delete_rule checks hymo_paths, hymo_hide_paths, and hymo_inject_dirs.
                    // So we just need to pass the path that was hidden.
                    // When hiding, we passed target_path.string().
                    delete_rule(target_path.string());
                }
            }
        }
    } catch (const std::exception& e) {
        LOG_WARN("HymoFS deletion error for " + module_dir.string() + ": " + e.what());
        return false;
    }
    return true;
}

} // namespace hymo
