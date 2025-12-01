// mount/overlay.hpp - OverlayFS mounting
#pragma once

#include <string>
#include <vector>
#include <optional>
#include <filesystem>

namespace fs = std::filesystem;

namespace hymo {

// Mount overlayfs on target with given lowerdirs
bool mount_overlay(
    const std::string& target_root,
    const std::vector<std::string>& module_roots,
    std::optional<fs::path> upperdir,
    std::optional<fs::path> workdir,
    bool disable_umount
);

// Bind mount helper
bool bind_mount(const fs::path& from, const fs::path& to, bool disable_umount);

} // namespace hymo
