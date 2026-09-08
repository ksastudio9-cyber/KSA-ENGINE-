cmake_minimum_required(VERSION 3.20)
project(ksa_engine_native VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(ksa_engine_runtime STATIC
    src/runtime.cpp
)
target_include_directories(ksa_engine_runtime PUBLIC include)

if (MSVC)
    target_compile_options(ksa_engine_runtime PRIVATE /W4 /permissive-)
else()
    target_compile_options(ksa_engine_runtime PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_executable(ksa_engine_cpp src/main.cpp)
target_link_libraries(ksa_engine_cpp PRIVATE ksa_engine_runtime)
set_target_properties(ksa_engine_cpp PROPERTIES OUTPUT_NAME "KSA")

include(CTest)
if (BUILD_TESTING)
    add_test(NAME native_runtime_smoke COMMAND ksa_engine_cpp --seconds 1 --json)
    add_executable(ksa_engine_runtime_tests tests/runtime_tests.cpp)
    target_link_libraries(ksa_engine_runtime_tests PRIVATE ksa_engine_runtime)
    add_test(NAME native_runtime_unit COMMAND ksa_engine_runtime_tests)
endif()

install(TARGETS ksa_engine_cpp RUNTIME DESTINATION bin)
