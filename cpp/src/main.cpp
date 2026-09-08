#include "ksa_engine/runtime.hpp"
#include "ksa_engine/native_editor.hpp"

#include <chrono>
#include <cstdlib>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>

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

#ifdef KSA_NATIVE_EDITOR
void prepare_native_editor_scene(ksa_engine::Scene& scene) {
    bool has_renderable = false;
    for (auto& [id, entity] : scene.entities()) {
        (void)id;
        if (entity.kind == "camera" || entity.kind == "light") continue;
        if (!entity.mesh) entity.mesh = std::make_unique<ksa_engine::MeshComponent>();
        if (!entity.material) {
            entity.material = std::make_unique<ksa_engine::Material>();
            if (entity.kind == "static") {
                entity.material->red = 110; entity.material->green = 82; entity.material->blue = 52;
            } else if (entity.kind == "player") {
                entity.material->red = 225; entity.material->green = 180; entity.material->blue = 72;
            } else {
                entity.material->red = 170; entity.material->green = 110; entity.material->blue = 65;
            }
        }
        has_renderable = true;
    }
    if (!has_renderable) {
        auto& block = scene.create_entity("Starter Block", "mesh", {{0.0, 1.0, 0.0}, {}, {1.0, 1.0, 1.0}, 0});
        block.mesh = std::make_unique<ksa_engine::MeshComponent>();
        block.material = std::make_unique<ksa_engine::Material>();
        block.material->red = 205; block.material->green = 150; block.material->blue = 55;
    }
}
#endif

void print_usage() {
    std::cout << ksa_engine::edition_name << " v" << ksa_engine::version << "\n"
              << "Usage: KSA [--editor|--play] [--seconds N] [--json] [--save PATH]\n"
              << "       KSA [--render PATH]\n"
              << "       KSA [--profile]\n"
              << "       KSA --version\n"
              << "       KSA --new-project NAME\n"
              << "       KSA --launcher\n";
}

void show_splash_screen() {
    std::cout << "\n";
    std::cout << "       .:: KSA ENGINE ::.\n";
    std::cout << "   ___  __  __  ____  _  _    ___\n";
    std::cout << "  / __|/ / / / |  _ \\| || |  / _ \\\n";
    std::cout << " | (_ | (_| | | | |_) | || |_| | | |\n";
    std::cout << "  \\___|\\__,_| |_|____/|____|\\___/\n";
    std::cout << "\n";
    std::cout << "  KSA Engine // World Builder\n";
    std::cout << "  Build your world, save your progress, and launch your project.\n";
    for (int pulse = 0; pulse < 3; ++pulse) {
        std::cout << "  Loading" << std::string(pulse + 1, '.') << "\r";
        std::cout.flush();
        std::this_thread::sleep_for(std::chrono::milliseconds(350));
    }
    std::cout << "\n\n";
}

std::string prompt_line(const std::string& label) {
    std::cout << label;
    std::string value;
    std::getline(std::cin, value);
    return value;
}

std::string resolve_default_project_dir(const std::string& name) {
    const std::filesystem::path root = std::filesystem::current_path() / "projects" / name;
    return root.string();
}

void run_launcher_flow(ksa_engine::Engine& engine) {
    show_splash_screen();
    std::cout << "=== PROJECT LAUNCHER ===\n";
    std::cout << "1) Create Project\n";
    std::cout << "2) Continue Last Project\n";
    std::cout << "3) Open Existing Project\n";
    std::cout << "4) Exit\n";
    std::cout << "Select an option: ";
    std::string option;
    std::getline(std::cin, option);

    std::string project_name = "KSA Project";
    std::string project_dir = resolve_default_project_dir(project_name);

    if (option == "1" || option == "create" || option == "Create Project") {
        project_name = prompt_line("Project name: ");
        if (project_name.empty()) project_name = "KSA Project";
        project_dir = resolve_default_project_dir(project_name);
        std::filesystem::create_directories(std::filesystem::path(project_dir) / "scenes");
        engine.set_project_name(project_name);
        engine.set_project_directory(project_dir);
        engine.save_project_state();
        std::cout << "Project created: " << project_name << " at " << project_dir << "\n";
        return;
    }

    if (option == "2" || option == "continue" || option == "Continue Last Project") {
        const std::filesystem::path fallback = std::filesystem::current_path() / "projects" / "KSA Project";
        project_dir = fallback.string();
        if (!std::filesystem::exists(fallback / "project_state.json")) {
            std::cout << "No previous project was found. Creating a new project.\n";
            project_dir = resolve_default_project_dir("KSA Project");
            std::filesystem::create_directories(std::filesystem::path(project_dir) / "scenes");
        }
        engine.set_project_directory(project_dir);
        engine.set_project_name(project_name);
        engine.load_project_state();
        std::cout << "Continuing project: " << project_dir << "\n";
        return;
    }

    if (option == "3" || option == "open" || option == "Open Existing Project") {
        const std::string input_dir = prompt_line("Project folder: ");
        if (!input_dir.empty()) {
            project_dir = input_dir;
            engine.set_project_directory(project_dir);
            engine.load_project_state();
            std::cout << "Opening project: " << project_dir << "\n";
            return;
        }
    }

    std::cout << "Launching default project.\n";
    engine.set_project_directory(project_dir);
    engine.set_project_name(project_name);
    if (std::filesystem::exists(std::filesystem::path(project_dir) / "project_state.json")) {
        engine.load_project_state();
    } else {
        engine.save_project_state();
    }
}

}  // namespace

int main(int argc, char* argv[]) {
    try {
        double seconds = 1.0;
        bool json = false;
        bool editor = false;
        bool play = false;
        bool profile = false;
        bool launcher = false;
        bool new_project = false;
        std::string save_path;
        std::string render_path;
        std::string project_name;
        std::string project_dir;
        #ifdef KSA_NATIVE_EDITOR
        if (argc == 1) launcher = true;
        #endif
        for (int index = 1; index < argc; ++index) {
            const std::string argument = argv[index];
            if (argument == "--help" || argument == "-h") { print_usage(); return 0; }
            if (argument == "--version") { std::cout << ksa_engine::edition_name << " v" << ksa_engine::version << '\n'; return 0; }
            if (argument == "--json") { json = true; continue; }
            if (argument == "--editor") { editor = true; continue; }
            if (argument == "--play") { play = true; continue; }
            if (argument == "--launcher") { launcher = true; continue; }
            if (argument == "--new-project" && index + 1 < argc) { new_project = true; project_name = argv[++index]; continue; }
            if (argument == "--profile") { profile = true; continue; }
            if (argument == "--seconds" && index + 1 < argc) { seconds = std::stod(argv[++index]); continue; }
            if (argument == "--save" && index + 1 < argc) { save_path = argv[++index]; continue; }
            if (argument == "--render" && index + 1 < argc) { render_path = argv[++index]; continue; }
            if (argument == "--project-dir" && index + 1 < argc) { project_dir = argv[++index]; continue; }
            throw std::invalid_argument("unknown option: " + argument);
        }
        if (seconds < 0.0) throw std::invalid_argument("seconds cannot be negative");
        if (editor) std::cout << ksa_engine::edition_name << " editor shell\n";
        if (play) std::cout << ksa_engine::edition_name << " play runtime\n";
        ksa_engine::Engine engine;
        if (!project_dir.empty()) {
            engine.set_project_directory(project_dir);
        } else {
            const std::string default_project = project_name.empty() ? "KSA Project" : project_name;
            engine.set_project_directory(resolve_default_project_dir(default_project));
            engine.set_project_name(default_project);
        }
        if (new_project) {
            std::filesystem::create_directories(std::filesystem::path(engine.project_directory()) / "scenes");
            engine.save_project_state();
        }
        if (launcher) {
            run_launcher_flow(engine);
        }
        engine.load_scene(create_demo_scene());
        if (std::filesystem::exists(std::filesystem::path(engine.project_directory()) / "project_state.json")) {
            engine.load_project_state();
        }
        if (editor) {
    #ifdef KSA_NATIVE_EDITOR
            prepare_native_editor_scene(*engine.scene());
            const bool saved = engine.save_project_state();
            if (!saved) std::cerr << "Could not save initial project state before editor launch.\n";
            const int result = ksa_engine::run_native_editor(*engine.scene());
            engine.save_project_state();
            return result;
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
        const bool project_saved = engine.save_project_state();
        if (!project_saved) std::cerr << "Autosave failed for project: " << engine.project_directory() << '\n';
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
