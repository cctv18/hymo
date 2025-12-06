// core/planner.cpp - Mount planning implementation
#include "planner.hpp"
#include "../defs.hpp"
#include "../utils.hpp"
#include "../mount/hymofs.hpp"
#include <map>
#include <set>
#include <algorithm>
#include <fstream>
#include <iostream>
#include <sys/stat.h>
#include <sys/sysmacros.h>

namespace hymo {

bool MountPlan::is_covered_by_overlay(const std::string& path) const {
    for (const auto& op : overlay_ops) {
        std::string p_str = path;
        std::string t_str = op.target;
        
        if (p_str == t_str) return true;
        
        if (p_str.size() > t_str.size() && 
            p_str.compare(0, t_str.size(), t_str) == 0 && 
            p_str[t_str.size()] == '/') {
            return true;
        }
    }
    return false;
}

static bool has_files(const fs::path& path) {
    if (!fs::exists(path) || !fs::is_directory(path)) {
        return false;
    }
    
    try {
        bool has_regular_content = false;
        for (const auto& entry : fs::directory_iterator(path)) {
            // Skip symlinks to avoid triggering mounts for redundant links (e.g. system/vendor -> /vendor)
            if (entry.is_symlink()) {
                continue;
            }
            has_regular_content = true;
            break;
        }
        return has_regular_content;
    } catch (...) {
        return false;
    }
}

static bool has_meaningful_content(const fs::path& base, const std::vector<std::string>& partitions) {
    for (const auto& part : partitions) {
        fs::path p = base / part;
        if (fs::exists(p) && has_files(p)) {
            return true;
        }
    }
    return false;
}

// Helper to identify directories that MUST use OverlayFS
static std::set<fs::path> scan_for_overlay_requirements(
    const std::vector<Module>& modules,
    const fs::path& storage_root,
    const std::vector<std::string>& partitions
) {
    std::set<fs::path> required_overlays;
    
    for (const auto& module : modules) {
        if (module.mode == "magic") continue; // Magic mount handled separately
        
        fs::path mod_path = storage_root / module.id;
        
        for (const auto& part : partitions) {
            fs::path part_root = mod_path / part;
            if (!fs::exists(part_root)) continue;
            
            try {
                for (const auto& entry : fs::recursive_directory_iterator(part_root)) {
                    fs::path rel = fs::relative(entry.path(), mod_path);
                    fs::path system_path = fs::path("/") / rel;
                    
                    // Check 1: .replace (Directory Replacement)
                    if (entry.path().filename() == ".replace") {
                        required_overlays.insert(system_path.parent_path());
                        continue;
                    }
                    
                    // Check 2: Whiteout (Char dev 0:0)
                    if (fs::is_character_file(entry.status())) {
                        struct stat st;
                        if (stat(entry.path().c_str(), &st) == 0) {
                            if (major(st.st_rdev) == 0 && minor(st.st_rdev) == 0) {
                                required_overlays.insert(system_path.parent_path());
                                continue;
                            }
                        }
                    }
                    
                    // Check 3: New File (Addition)
                    if (!fs::exists(system_path)) {
                        // Find nearest existing parent
                        fs::path parent = system_path.parent_path();
                        while (!fs::exists(parent) && parent != "/") {
                            parent = parent.parent_path();
                        }
                        if (parent != "/") {
                            required_overlays.insert(parent);
                        }
                    }
                }
            } catch (...) {
                // Ignore errors during scan
            }
        }
    }
    return required_overlays;
}

MountPlan generate_plan(
    const Config& config,
    const std::vector<Module>& modules,
    const fs::path& storage_root
) {
    MountPlan plan;
    
    std::map<std::string, std::vector<fs::path>> overlay_layers;
    std::set<fs::path> magic_paths;
    std::set<std::string> overlay_ids;
    std::set<std::string> magic_ids;
    
    std::vector<std::string> target_partitions = BUILTIN_PARTITIONS;
    for (const auto& part : config.partitions) {
        target_partitions.push_back(part);
    }
    
    bool use_hymofs = is_hymofs_available();
    bool use_overlay = is_overlayfs_supported();
    
    // **Phase 1: Identify Hybrid Requirements**
    // Find directories that MUST be OverlayFS due to additions/deletions
    std::set<fs::path> required_overlays = scan_for_overlay_requirements(modules, storage_root, target_partitions);
    
    for (const auto& req : required_overlays) {
        LOG_DEBUG("Hybrid Mode: Forced OverlayFS for " + req.string());
        overlay_layers[req.string()] = {}; // Initialize
    }

    // **Phase 2: Assign Strategies**
    for (const auto& module : modules) {
        fs::path content_path = storage_root / module.id;
        
        if (!fs::exists(content_path)) continue;
        if (!has_meaningful_content(content_path, target_partitions)) continue;
        
        if (module.mode == "magic") {
            magic_paths.insert(content_path);
            magic_ids.insert(module.id);
            continue;
        }
        
        bool try_hymofs = (module.mode == "auto");
        bool try_overlay = (module.mode == "auto" || module.mode == "overlay");
        
        bool participates_in_overlay = false;
        bool participates_in_hymofs = false;
        
        // 1. Handle Forced Overlays (Hybrid Mode)
        if (try_overlay && use_overlay) {
            for (auto& [target, layers] : overlay_layers) {
                fs::path rel_target = fs::relative(target, "/");
                fs::path mod_target_content = content_path / rel_target;
                
                if (fs::exists(mod_target_content)) {
                    layers.push_back(mod_target_content);
                    participates_in_overlay = true;
                }
            }
        }
        
        // 2. Handle Partition-Level Logic (Legacy/Fallback)
        for (const auto& part : target_partitions) {
            fs::path part_path = content_path / part;
            if (!fs::exists(part_path)) continue;
            
            if (module.mode == "overlay" && use_overlay) {
                 std::string part_root = "/" + part;
                 if (overlay_layers.find(part_root) == overlay_layers.end()) {
                     overlay_layers[part_root] = {};
                 }
                 overlay_layers[part_root].push_back(part_path);
                 participates_in_overlay = true;
            }
            
            if (try_hymofs && use_hymofs) {
                participates_in_hymofs = true;
            }
        }
        
        if (participates_in_hymofs) plan.hymofs_module_ids.push_back(module.id);
        if (participates_in_overlay) overlay_ids.insert(module.id);
    }
    
    // Construct Overlay Operations
    for (auto& [target, layers] : overlay_layers) {
        if (layers.empty()) continue;
        
        if (!fs::exists(target) || !fs::is_directory(target)) {
             LOG_WARN("Overlay target " + target + " invalid, skipping");
             continue;
        }
        
        plan.overlay_ops.push_back(OverlayOperation{target, layers});
    }
    
    plan.magic_module_paths.assign(magic_paths.begin(), magic_paths.end());
    plan.overlay_module_ids.assign(overlay_ids.begin(), overlay_ids.end());
    plan.magic_module_ids.assign(magic_ids.begin(), magic_ids.end());
    
    return plan;
}

void update_hymofs_mappings(
    const Config& config,
    const std::vector<Module>& modules,
    const fs::path& storage_root,
    const MountPlan& plan
) {
    std::ofstream ctl("/proc/hymo_ctl");
    if (!ctl) {
        LOG_ERROR("Failed to open /proc/hymo_ctl");
        return;
    }

    // Clear existing mappings
    ctl << "clear" << std::endl;

    std::vector<std::string> target_partitions = BUILTIN_PARTITIONS;
    for (const auto& part : config.partitions) {
        target_partitions.push_back(part);
    }

    for (auto it = modules.rbegin(); it != modules.rend(); ++it) {
        const auto& module = *it;
        fs::path mod_path = storage_root / module.id;
        
        for (const auto& part : target_partitions) {
            fs::path part_root = mod_path / part;
            if (!fs::exists(part_root)) continue;

            try {
                for (const auto& entry : fs::recursive_directory_iterator(part_root)) {
                    if (entry.is_regular_file() || entry.is_symlink()) {
                        fs::path rel = fs::relative(entry.path(), mod_path);
                        fs::path virtual_path = fs::path("/") / rel;
                        
                        if (plan.is_covered_by_overlay(virtual_path.string())) {
                            continue;
                        }
                        
                        ctl << "add " << virtual_path.string() << " " << entry.path().string() << std::endl;
                    }
                }
            } catch (const std::exception& e) {
                LOG_WARN("Error scanning module " + module.id + ": " + std::string(e.what()));
            }
        }
    }
    
    LOG_INFO("HymoFS mappings updated via /proc/hymo_ctl");
}

} // namespace hymo
