#include "ksa_engine/runtime.hpp"

#include <cassert>
#include <memory>

int main() {
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

    auto& falling = scene->create_entity("Falling", "player", {{0.0, 3.0, 0.0}, {}, {1.0, 1.0, 1.0}, 0});
    falling.physics = std::make_unique<ksa_engine::PhysicsBody>();
    engine.load_scene(scene);
    engine.run_for(1.0);
    assert(falling.transform.position.y >= falling.physics->half_extents.y);

    engine.resources().register_asset("crate", "assets/crate.mesh");
    assert(engine.resources().size() == 1);
    assert(engine.resources().path_for("crate") != nullptr);
    return 0;
}