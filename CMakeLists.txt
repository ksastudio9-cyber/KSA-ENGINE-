cmake_minimum_required(VERSION 3.20)
project(ksa_engine LANGUAGES CXX)

add_library(ksa_engine STATIC cpp/src/core.cpp)
target_include_directories(ksa_engine PUBLIC cpp/include)
target_compile_features(ksa_engine PUBLIC cxx_std_20)

add_executable(ksa_engine_cli cpp/src/main.cpp)
target_link_libraries(ksa_engine_cli PRIVATE ksa_engine)

if (MSVC)
    target_compile_options(ksa_engine PRIVATE /W4)
else()
    target_compile_options(ksa_engine PRIVATE -Wall -Wextra -Wpedantic)
endif()
