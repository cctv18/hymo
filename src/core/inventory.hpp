// core/inventory.hpp - Module inventory
#pragma once

#include <string>
#include <vector>
#include <filesystem>
#include "../conf/config.hpp"

namespace fs = std::filesystem;

namespace hymo {

struct Module {
    std::string id;
    fs::path source_path;
    std::string mode; // "auto", "magic", etc.
};

std::vector<Module> scan_modules(const fs::path& source_dir, const Config& config);

} // namespace hymo
