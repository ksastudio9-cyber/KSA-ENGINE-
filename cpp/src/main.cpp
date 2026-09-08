#include "ksa_engine/runtime.hpp"
#include "ksa_engine/native_editor.hpp"

#include <cstdlib>
#include <exception>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

namespace {

std::shared_ptr<ksa_engine::Scene> create_demo_scene() {
    auto scene = std::make_shared<ksa_engine::Scene>("KSA Sandbox");
    auto& player = scene->create_entity("Player", "player", {{0.0, 1.0, 0.0}, {}, {0.45, 1.0, 0.45}, 0});
    player.mesh = std::make_unique<ksa_engine::MeshComponent>();
    player.material = std::make_unique<ksa_engine::Material>();
    player.material->red = 225; player.material->green = 180; player.material->blue = 72;
    player.physics = std::make_unique<ksa_engine::PhysicsBody>();
    player.physics->half_extents = {0.45, 1.0, 0.45};
    auto& camera = scene->create_entity("Camera", "camera", {{0.0, 3.0, 7.0}, {}, {1.0, 1.0, 1.0}, 0});
    camera.camera = std::make_unique<ksa_engine::CameraComponent>();
    auto& light = scene->create_entity("Directional Sun", "light");
    light.light = std::make_unique<ksa_engine::LightComponent>();
    auto& ground = scene->create_entity("Ground", "static", {{0.0, -0.5, 0.0}, {}, {20.0, 0.5, 20.0}, 0});
    ground.mesh = std::make_unique<ksa_engine::MeshComponent>();
    ground.physics = std::make_unique<ksa_engine::PhysicsBody>();
    ground.physics->half_extents = {20.0, 0.5, 20.0};
    ground.physics->is_static = true;
    for (int index = 0; index < 3; ++index) {
        auto& crate = scene->create_entity("Crate " + std::to_string(index + 1), "mesh", {{static_cast<double>(index * 3 - 3), 0.0, static_cast<double>(-index * 2 - 2)}, {}, {0.75, 0.75, 0.75}, 0});
        crate.mesh = std::make_unique<ksa_engine::MeshComponent>();
        crate.material = std::make_unique<ksa_engine::Material>();
        crate.material->red = 170; crate.material->green = 110; crate.material->blue = 65;
        crate.physics = std::make_unique<ksa_engine::PhysicsBody>();
        crate.physics->half_extents = {0.75, 0.75, 0.75};
        crate.physics->is_static = true;
        crate.physics->use_gravity = false;
    }
    return scene;
}

void print_usage() {
    std::cout << ksa_engine::edition_name << " v" << ksa_engine::version << "\n"
              << "Usage: KSA [--editor|--play] [--seconds N] [--json] [--save PATH]\n"
              << "       KSA [--render PATH]\n"
              << "       KSA [--profile]\n"
              << "       KSA --version\n";
}

}  // namespace

int main(int argc, char* argv[]) {
    try {
        double seconds = 1.0;
        bool json = false;
        bool editor = false;
        bool play = false;
        bool profile = false;
        std::string save_path;
        std::string render_path;
        #ifdef KSA_NATIVE_EDITOR
        if (argc == 1) editor = true;
        #endif
        for (int index = 1; index < argc; ++index) {
            const std::string argument = argv[index];
            if (argument == "--help" || argument == "-h") { print_usage(); return 0; }
            if (argument == "--version") { std::cout << ksa_engine::edition_name << " v" << ksa_engine::version << '\n'; return 0; }
            if (argument == "--json") { json = true; continue; }
            if (argument == "--editor") { editor = true; continue; }
            if (argument == "--play") { play = true; continue; }
            if (argument == "--profile") { profile = true; continue; }
            if (argument == "--seconds" && index + 1 < argc) { seconds = std::stod(argv[++index]); continue; }
            if (argument == "--save" && index + 1 < argc) { save_path = argv[++index]; continue; }
            if (argument == "--render" && index + 1 < argc) { render_path = argv[++index]; continue; }
            throw std::invalid_argument("unknown option: " + argument);
        }
        if (seconds < 0.0) throw std::invalid_argument("seconds cannot be negative");
        if (editor) std::cout << ksa_engine::edition_name << " editor shell\n";
        if (play) std::cout << ksa_engine::edition_name << " play runtime\n";
        ksa_engine::Engine engine;
        engine.load_scene(create_demo_scene());
        if (editor) {
    #ifdef KSA_NATIVE_EDITOR
            return ksa_engine::run_native_editor(*engine.scene());
    #else
            std::cout << "Native editor is disabled in this build. Configure with -DKSA_ENABLE_NATIVE_EDITOR=ON.\n";
            return 0;
    #endif
        }
        engine.add_system(std::make_shared<ksa_engine::CameraSystem>());
        engine.add_system(std::make_shared<ksa_engine::LightingSystem>());
        if (!save_path.empty()) ksa_engine::save_scene(*engine.scene(), save_path);
        engine.run_for(seconds);
        if (!render_path.empty()) {
            ksa_engine::SoftwareRenderer renderer;
            renderer.render(*engine.scene(), engine.scene()->render_settings);
            renderer.save_ppm(render_path);
        }
        if (json) {
            std::cout << ksa_engine::to_json(engine) << '\n';
        } else {
            std::cout << "KSA Engine | " << engine.scene()->name()
                      << " | entities=" << engine.scene()->entities().size()
                      << " | fixed_steps=" << engine.stats().fixed_step_count
                      << " | dropped_time=" << engine.stats().dropped_time << '\n';
            if (profile) {
                const auto* frame = engine.profiler().stat("engine.frame");
                std::cout << "Profile | frames=" << (frame ? frame->calls : 0)
                          << " | total_seconds=" << (frame ? frame->total_seconds : 0.0)
                          << " | peak_seconds=" << (frame ? frame->peak_seconds : 0.0) << '\n';
            }
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "KSA Engine error: " << error.what() << '\n';
        return EXIT_FAILURE;
    }
}
