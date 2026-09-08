cmake_minimum_required(VERSION 3.20)
project(ksa_engine_native VERSION 1.0.0 LANGUAGES CXX)

option(KSA_ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
option(KSA_ENABLE_NATIVE_EDITOR "Build the SDL2/OpenGL native 3D editor" ${WIN32})

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(ksa_engine_runtime STATIC
    src/runtime.cpp
)
target_include_directories(ksa_engine_runtime PUBLIC include)
target_compile_definitions(ksa_engine_runtime PUBLIC KSA_ENGINE_VERSION="${PROJECT_VERSION}")

if (MSVC)
    target_compile_options(ksa_engine_runtime PRIVATE /W4 /permissive-)
else()
    target_compile_options(ksa_engine_runtime PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
endif()

if (KSA_ENABLE_SANITIZERS AND NOT MSVC)
    target_compile_options(ksa_engine_runtime PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
    target_link_options(ksa_engine_runtime PRIVATE -fsanitize=address,undefined)
endif()

add_executable(ksa_engine_cpp src/main.cpp)
target_link_libraries(ksa_engine_cpp PRIVATE ksa_engine_runtime)
if (KSA_ENABLE_NATIVE_EDITOR)
    include(FetchContent)
    FetchContent_Declare(
        SDL2
        GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
        GIT_TAG release-2.30.9
        GIT_SHALLOW TRUE
    )
    set(SDL_SHARED OFF CACHE BOOL "" FORCE)
    set(SDL_STATIC ON CACHE BOOL "" FORCE)
    set(SDL_TESTS OFF CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(SDL2)
    find_package(OpenGL REQUIRED)
    target_sources(ksa_engine_cpp PRIVATE src/native_editor.cpp)
    target_compile_definitions(ksa_engine_cpp PRIVATE KSA_NATIVE_EDITOR=1)
    target_link_libraries(ksa_engine_cpp PRIVATE SDL2::SDL2-static OpenGL::GL)
    if (WIN32)
        target_link_libraries(ksa_engine_cpp PRIVATE SDL2::SDL2main)
    endif()
endif()
if (KSA_ENABLE_SANITIZERS AND NOT MSVC)
    target_compile_options(ksa_engine_cpp PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
    target_link_options(ksa_engine_cpp PRIVATE -fsanitize=address,undefined)
endif()
set_target_properties(ksa_engine_cpp PROPERTIES OUTPUT_NAME "KSA ENGINE")

add_executable(ksa_download_server ../website/server.cpp)
if (WIN32)
    target_link_libraries(ksa_download_server PRIVATE ws2_32)
endif()
if (MSVC)
    target_compile_options(ksa_download_server PRIVATE /W4 /permissive-)
else()
    target_compile_options(ksa_download_server PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
endif()

include(CTest)
if (BUILD_TESTING)
    add_test(NAME native_runtime_smoke COMMAND ksa_engine_cpp --seconds 1 --json)
    add_executable(ksa_engine_runtime_tests tests/runtime_tests.cpp)
    target_link_libraries(ksa_engine_runtime_tests PRIVATE ksa_engine_runtime)
    if (KSA_ENABLE_SANITIZERS AND NOT MSVC)
        target_compile_options(ksa_engine_runtime_tests PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(ksa_engine_runtime_tests PRIVATE -fsanitize=address,undefined)
    endif()
    add_test(NAME native_runtime_unit COMMAND ksa_engine_runtime_tests)
endif()

install(TARGETS ksa_engine_runtime ksa_engine_cpp ksa_download_server
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
)
install(DIRECTORY include/ DESTINATION include)
