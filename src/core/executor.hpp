// core/executor.hpp - Mount execution
#pragma once

#include "planner.hpp"
#include "../conf/config.hpp"
#include <vector>
#include <string>

namespace hymo {

struct ExecutionResult {
    std::vector<std::string> overlay_module_ids;
    std::vector<std::string> magic_module_ids;
};

ExecutionResult execute_plan(const MountPlan& plan, const Config& config);

} // namespace hymo
