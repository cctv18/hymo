#pragma once
#include <string>
#include <vector>

namespace hymo {

bool is_hymofs_available();
bool hymofs_add_module(const std::string& name);
bool hymofs_del_module(const std::string& name);
bool hymofs_clear();

} // namespace hymo
