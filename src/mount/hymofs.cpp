#include "hymofs.hpp"
#include "../utils.hpp"
#include <fstream>
#include <filesystem>
#include <iostream>

namespace fs = std::filesystem;

namespace hymo {

static const char* HYMO_CTL_PATH = "/proc/hymo_ctl";

bool is_hymofs_available() {
    return fs::exists(HYMO_CTL_PATH);
}

static bool write_ctl(const std::string& cmd) {
    std::ofstream ctl(HYMO_CTL_PATH);
    if (!ctl.is_open()) {
        LOG_ERROR("Failed to open " + std::string(HYMO_CTL_PATH));
        return false;
    }
    ctl << cmd;
    if (ctl.fail()) {
        LOG_ERROR("Failed to write to " + std::string(HYMO_CTL_PATH));
        return false;
    }
    return true;
}

bool hymofs_add_module(const std::string& name) {
    LOG_DEBUG("HymoFS: Adding module " + name);
    return write_ctl("add " + name);
}

bool hymofs_del_module(const std::string& name) {
    LOG_DEBUG("HymoFS: Removing module " + name);
    return write_ctl("del " + name);
}

bool hymofs_clear() {
    LOG_DEBUG("HymoFS: Clearing all modules");
    // Note: The kernel implementation requires 2 arguments for sscanf, 
    // so we send "clear all" even though "all" is ignored.
    return write_ctl("clear all");
}

} // namespace hymo
