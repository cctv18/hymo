// conf/config.hpp - Configuration management
#pragma once

#include <string>
#include <vector>
#include <map>
#include <filesystem>

namespace fs = std::filesystem;

namespace hymo {

struct Config {
    fs::path moduledir = "/data/adb/modules";
    fs::path tempdir;
    std::string mountsource = "KSU";
    bool verbose = false;
    bool force_ext4 = false;
    bool disable_umount = false;
    bool enable_nuke = true;
    std::vector<std::string> partitions;
    std::map<std::string, std::string> module_modes;
    
    static Config load_default();
    static Config from_file(const fs::path& path);
    bool save_to_file(const fs::path& path) const;
    
    void merge_with_cli(
        const fs::path& moduledir_override,
        const fs::path& tempdir_override,
        const std::string& mountsource_override,
        bool verbose_override,
        const std::vector<std::string>& partitions_override
    );
};

std::map<std::string, std::string> load_module_modes();

} // namespace hymo
