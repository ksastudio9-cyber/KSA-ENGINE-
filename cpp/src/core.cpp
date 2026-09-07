#include "ksa_engine/core.hpp"

#include <algorithm>
#include <functional>
#include <optional>
#include <random>
#include <stdexcept>

namespace ksa {

Entity& World::create_entity(std::string name, std::string kind, Transform transform) {
    entities.push_back(Entity{entities.size() + 1, std::move(name), std::move(kind), transform});
    return entities.back();
}

Engine::Engine(float fixed_timestep) : fixed_timestep_(fixed_timestep) {
    if (fixed_timestep <= 0.0F) {
        throw std::invalid_argument("fixed timestep must be positive");
    }
}

void Engine::load_world(World world) {
    world_ = std::move(world);
    for (System* system : systems_) {
        system->start(*world_);
    }
}

void Engine::add_system(System& system) {
    systems_.push_back(&system);
    if (world_) {
        system.start(*world_);
    }
}

void Engine::update(float delta_time) {
    if (!world_) {
        throw std::runtime_error("no world loaded");
    }
    const float clamped = std::clamp(delta_time, 0.0F, 0.25F);
    world_->elapsed_time += clamped;
    for (System* system : systems_) {
        system->update(*world_, clamped);
    }
}

void Engine::run_for(float duration) {
    if (duration < 0.0F) {
        throw std::invalid_argument("duration must be non-negative");
    }
    while (duration > 0.0F) {
        const float step = std::min(fixed_timestep_, duration);
        update(step);
        duration -= step;
    }
}

World generate_world_from_text(const std::string& description, std::uint64_t seed) {
    if (description.empty()) {
        throw std::invalid_argument("description cannot be empty");
    }
    if (seed == 0) {
        seed = std::hash<std::string>{}(description);
    }
    std::mt19937 generator(static_cast<std::mt19937::result_type>(seed));
    std::uniform_real_distribution<float> spread(-4.0F, 4.0F);
    World world{"KSA Generated World", seed, {}, 0.0F};
    world.create_entity("Main Camera", "camera", Transform{{-12.0F, 8.0F, 12.0F}});
    world.create_entity("Terrain", description.find("صحراء") != std::string::npos ? "desert" : "terrain");
    world.create_entity("Character_1", "character", Transform{{spread(generator), 0.0F, spread(generator)}});
    world.create_entity("Sun Light", "light");
    return world;
}

}  // namespace ksa
