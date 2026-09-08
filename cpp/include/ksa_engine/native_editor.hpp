#pragma once

#include "ksa_engine/runtime.hpp"

namespace ksa_engine {

#ifdef KSA_NATIVE_EDITOR
int run_native_editor(Scene& scene);
#endif

}  // namespace ksa_engine
