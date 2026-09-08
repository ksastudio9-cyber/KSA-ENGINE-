#include "ksa_engine/runtime.hpp"

#include <cassert>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <memory>
#include <string>
#include <vector>

int main() {
    assert(std::string(ksa_engine::edition_name) == "KSA Engine Full Edition");
    assert(std::string(ksa_engine::version) == "1.0.0");
    auto scene = std::make_shared<ksa_engine::Scene>("Test Scene");
    auto& parent = scene->create_entity("Parent", "entity", {{10.0, 0.0, 2.0}, {}, {1.0, 1.0, 1.0}, 0});
    auto& child = scene->create_entity("Child", "entity", {{1.0, 3.0, 4.0}, {}, {1.0, 1.0, 1.0}, 0});
    scene->set_parent(child.id, parent.id);
    const auto world = scene->world_position(child.id);
    assert(world.x == 11.0 && world.y == 3.0 && world.z == 6.0);

    bool received = false;
    ksa_engine::EventBus events;
    events.subscribe("hit", [&](const ksa_engine::Event&) { received = true; });
    events.publish({"hit", child.id, parent.id});
    events.flush();
    assert(received);

    ksa_engine::Engine engine;
    engine.load_scene(scene);
    engine.run_for(1.0);
    assert(engine.stats().fixed_step_count == 60);
    assert(engine.stats().dropped_time == 0.0);
    assert(engine.profiler().stat("engine.frame") != nullptr);
    assert(engine.profiler().stat("engine.frame")->calls == engine.stats().frame_count);

    auto& falling = scene->create_entity("Falling", "player", {{0.0, 3.0, 0.0}, {}, {1.0, 1.0, 1.0}, 0});
    falling.physics = std::make_unique<ksa_engine::PhysicsBody>();
    falling.transform.rotation = {10.0, 20.0, 30.0};
    falling.transform.scale = {2.0, 3.0, 4.0};
    falling.active = false;
    scene->set_parent(falling.id, parent.id);
    engine.load_scene(scene);
    engine.run_for(1.0);
    assert(falling.transform.position.y >= falling.physics->half_extents.y);

    engine.resources().register_asset("crate", "assets/crate.mesh");
    assert(engine.resources().size() == 1);
    assert(engine.resources().path_for("crate") != nullptr);

    ksa_engine::InputState input;
    auto movement_scene = std::make_shared<ksa_engine::Scene>("Movement");
    auto& movement_player = movement_scene->create_entity("Player", "player");
    ksa_engine::Engine movement_engine;
    movement_engine.load_scene(movement_scene);
    movement_engine.add_system(std::make_shared<ksa_engine::InputMovementSystem>(input, 5.0));
    input.set_down("forward", true);
    movement_engine.update(1.0);
    const double walking_distance = movement_player.transform.position.length();
    input.set_down("run", true);
    movement_engine.update(1.0);
    assert(movement_player.transform.position.length() > walking_distance + 5.0);

    ksa_engine::ResourceManager asset_manager;
    int loader_calls = 0;
    asset_manager.register_loader("virtual", [&](const std::string& asset_path) {
        ++loader_calls;
        auto asset = std::make_shared<ksa_engine::Asset>();
        asset->path = asset_path;
        asset->bytes = {1, 2, 3, 4};
        return asset;
    });
    const auto first_asset = asset_manager.load("demo.virtual");
    const auto second_asset = asset_manager.load("demo.virtual");
    assert(first_asset == second_asset);
    assert(first_asset->bytes.size() == 4);
    assert(loader_calls == 1);
    assert(asset_manager.loaded_count() == 1);
    asset_manager.unload("demo.virtual");
    assert(asset_manager.loaded_count() == 0);

    ksa_engine::HeadlessRenderer renderer;
    renderer.render(*scene, scene->render_settings);
    assert(renderer.frame_count() == 1);
    assert(renderer.last_entity_count() == scene->entities().size());

    ksa_engine::SoftwareRenderer software_renderer(64, 36);
    software_renderer.render(*scene, scene->render_settings);
    assert(software_renderer.frame_count() == 1);
    assert(software_renderer.pixels().size() == 64U * 36U * 3U);
    bool has_non_black_pixel = false;
    for (const auto pixel : software_renderer.pixels()) if (pixel != 0) { has_non_black_pixel = true; break; }
    assert(has_non_black_pixel);

    const std::string path = "runtime_test_scene.json";
    ksa_engine::save_scene(*scene, path);
    const auto restored = ksa_engine::load_scene(path);
    assert(restored->name() == "Test Scene");
    assert(restored->find(parent.id) != nullptr);
    assert(restored->find(parent.id)->name == "Parent");
    const auto* restored_falling = restored->find(falling.id);
    assert(restored_falling != nullptr);
    assert(!restored_falling->active);
    assert(restored_falling->transform.parent == parent.id);
    assert(restored_falling->transform.rotation.y == 20.0);
    assert(restored_falling->transform.scale.z == 4.0);
    std::remove(path.c_str());

    const std::string project_dir = "runtime_project_state";
    std::filesystem::remove_all(project_dir);
    ksa_engine::Engine project_engine;
    project_engine.load_scene(scene);
    project_engine.set_project_directory(project_dir);
    project_engine.set_autosave_enabled(true);
    project_engine.set_autosave_interval(0.0);
    assert(project_engine.save_project_state());
    assert(std::filesystem::exists(project_dir + "/project_state.json"));
    assert(std::filesystem::exists(project_dir + "/scenes/default_scene.json"));

    ksa_engine::Engine loaded_project_engine;
    loaded_project_engine.set_project_directory(project_dir);
    assert(loaded_project_engine.load_project_state());
    assert(loaded_project_engine.scene() != nullptr);
    assert(loaded_project_engine.scene()->name() == "Test Scene");
    std::filesystem::remove_all(project_dir);

    auto region_scene = std::make_shared<ksa_engine::Scene>("Regions");
    auto& danger_zone = region_scene->create_region("Danger Zone", {0.0, 0.0, 0.0}, {10.0, 10.0, 10.0}, "danger");
    auto& zone_child = region_scene->create_entity("Zone Child", "mesh", {{2.0, 3.0, 4.0}, {}, {1.0, 1.0, 1.0}, 0});
    region_scene->set_parent(zone_child.id, danger_zone.id);
    assert(danger_zone.region != nullptr);
    assert(danger_zone.region->type == "danger");
    assert(region_scene->children(danger_zone.id).size() == 1);

    region_scene->register_prefab("crate_box", {
        {"Crate", "mesh", {{0.0, 0.0, 0.0}, {}, {1.0, 1.0, 1.0}, 0}}
    });
    auto& prefab_instance = region_scene->instantiate_prefab("crate_box", "Crate Instance", {{1.0, 1.0, 1.0}, {}, {1.5, 1.5, 1.5}, 0});
    assert(prefab_instance.name == "Crate Instance");
    assert(prefab_instance.transform.scale.x == 1.5);

    auto trigger_scene = std::make_shared<ksa_engine::Scene>("Triggers");
    auto& trigger_a = trigger_scene->create_entity("Trigger A", "trigger", {{0, 1, 0}, {}, {1, 1, 1}, 0});
    trigger_a.physics = std::make_unique<ksa_engine::PhysicsBody>();
    trigger_a.physics->is_static = true;
    trigger_a.physics->is_trigger = true;
    auto& trigger_b = trigger_scene->create_entity("Trigger B", "trigger", {{0.5, 1, 0}, {}, {1, 1, 1}, 0});
    trigger_b.physics = std::make_unique<ksa_engine::PhysicsBody>();
    trigger_b.physics->is_static = true;
    trigger_b.physics->is_trigger = true;
    int enters = 0;
    int exits = 0;
    ksa_engine::Engine trigger_engine;
    trigger_engine.events().subscribe("trigger_enter", [&](const ksa_engine::Event&) { ++enters; });
    trigger_engine.events().subscribe("trigger_exit", [&](const ksa_engine::Event&) { ++exits; });
    trigger_engine.load_scene(trigger_scene);
    trigger_engine.update(1.0 / 60.0);
    assert(enters == 1);
    trigger_b.transform.position.x = 10.0;
    trigger_engine.update(1.0 / 60.0);
    assert(exits == 1);
    return 0;
}