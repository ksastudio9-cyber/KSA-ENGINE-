#include "ksa_engine/runtime.hpp"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <unordered_set>

namespace ksa_engine {

Vec3 Vec3::operator+(const Vec3& other) const { return {x + other.x, y + other.y, z + other.z}; }
Vec3 Vec3::operator-(const Vec3& other) const { return {x - other.x, y - other.y, z - other.z}; }
Vec3 Vec3::operator*(double scalar) const { return {x * scalar, y * scalar, z * scalar}; }
Vec3& Vec3::operator+=(const Vec3& other) { x += other.x; y += other.y; z += other.z; return *this; }
double Vec3::length() const { return std::sqrt(x * x + y * y + z * z); }
Vec3 Vec3::normalized() const { const double value = length(); return value == 0.0 ? Vec3{} : *this * (1.0 / value); }

Entity::Entity(const Entity& other)
    : id(other.id), name(other.name), kind(other.kind), transform(other.transform), active(other.active) {
    if (other.material) material = std::make_unique<Material>(*other.material);
    if (other.mesh) mesh = std::make_unique<MeshComponent>(*other.mesh);
    if (other.camera) camera = std::make_unique<CameraComponent>(*other.camera);
    if (other.light) light = std::make_unique<LightComponent>(*other.light);
    if (other.physics) physics = std::make_unique<PhysicsBody>(*other.physics);
}

Entity& Entity::operator=(const Entity& other) {
    if (this == &other) return *this;
    Entity copy(other);
    *this = std::move(copy);
    return *this;
}

Scene::Scene(std::string name) : name_(std::move(name)) {}

Entity& Scene::create_entity(std::string name, std::string kind, Transform transform) {
    Entity entity;
    entity.id = next_id_++;
    entity.name = std::move(name);
    entity.kind = std::move(kind);
    entity.transform = transform;
    return entities_.emplace(entity.id, std::move(entity)).first->second;
}

void Scene::destroy_entity(std::uint64_t id) {
    entities_.erase(id);
    for (auto& [entity_id, entity] : entities_) {
        if (entity.transform.parent == id) entity.transform.parent = 0;
    }
}

Entity* Scene::find(std::uint64_t id) {
    const auto iterator = entities_.find(id);
    return iterator == entities_.end() ? nullptr : &iterator->second;
}

const Entity* Scene::find(std::uint64_t id) const {
    const auto iterator = entities_.find(id);
    return iterator == entities_.end() ? nullptr : &iterator->second;
}

std::vector<Entity*> Scene::active_entities() {
    std::vector<Entity*> result;
    result.reserve(entities_.size());
    for (auto& [id, entity] : entities_) if (entity.active) result.push_back(&entity);
    return result;
}

Vec3 Scene::world_position(std::uint64_t id) const {
    const Entity* entity = find(id);
    if (!entity) throw std::out_of_range("unknown entity id");
    Vec3 position = entity->transform.position;
    std::unordered_set<std::uint64_t> visited;
    std::uint64_t parent = entity->transform.parent;
    while (parent != 0) {
        if (!visited.insert(parent).second) throw std::logic_error("transform hierarchy cycle");
        const Entity* parent_entity = find(parent);
        if (!parent_entity) break;
        position += parent_entity->transform.position;
        parent = parent_entity->transform.parent;
    }
    return position;
}

void Scene::set_parent(std::uint64_t id, std::uint64_t parent) {
    Entity* entity = find(id);
    if (!entity) throw std::out_of_range("unknown entity id");
    if (id == parent) throw std::invalid_argument("entity cannot parent itself");
    std::uint64_t ancestor = parent;
    while (ancestor != 0) {
        if (ancestor == id) throw std::invalid_argument("transform hierarchy cycle");
        const Entity* parent_entity = find(ancestor);
        ancestor = parent_entity ? parent_entity->transform.parent : 0;
    }
    entity->transform.parent = parent;
}

const std::string& Scene::name() const { return name_; }
const std::unordered_map<std::uint64_t, Entity>& Scene::entities() const { return entities_; }

void EventBus::subscribe(const std::string& name, Listener listener) { listeners_[name].push_back(std::move(listener)); }
void EventBus::publish(Event event) { queue_.push_back(std::move(event)); }
void EventBus::flush() {
    for (const Event& event : queue_) {
        const auto iterator = listeners_.find(event.name);
        if (iterator != listeners_.end()) for (const Listener& listener : iterator->second) listener(event);
    }
    queue_.clear();
}

PhysicsSystem::PhysicsSystem(EventBus& events, Vec3 gravity) : events_(events), gravity_(gravity) {}

void PhysicsSystem::fixed_update(Scene& scene, double delta) {
    std::vector<Entity*> bodies;
    for (Entity* entity : scene.active_entities()) {
        if (!entity->physics) continue;
        bodies.push_back(entity);
        if (entity->physics->is_static) continue;
        PhysicsBody& body = *entity->physics;
        if (body.use_gravity) body.velocity += gravity_ * delta;
        entity->transform.position += body.velocity * delta;
        if (entity->transform.position.y < body.half_extents.y) {
            entity->transform.position.y = body.half_extents.y;
            body.velocity.y = 0.0;
        }
    }

    candidate_pairs_ = 0;
    for (std::size_t left_index = 0; left_index < bodies.size(); ++left_index) {
        Entity& left = *bodies[left_index];
        for (std::size_t right_index = left_index + 1; right_index < bodies.size(); ++right_index) {
            Entity& right = *bodies[right_index];
            const Vec3 delta_position = left.transform.position - right.transform.position;
            const Vec3 extent = left.physics->half_extents + right.physics->half_extents;
            if (std::abs(delta_position.x) > extent.x || std::abs(delta_position.y) > extent.y || std::abs(delta_position.z) > extent.z) continue;
            ++candidate_pairs_;
            const bool trigger = left.physics->is_trigger || right.physics->is_trigger;
            events_.publish({trigger ? "trigger_enter" : "collision_enter", left.id, right.id});
            if (trigger || (left.physics->is_static && right.physics->is_static)) continue;
            const Vec3 penetration{extent.x - std::abs(delta_position.x), extent.y - std::abs(delta_position.y), extent.z - std::abs(delta_position.z)};
            if (penetration.y <= penetration.x && penetration.y <= penetration.z) {
                const double direction = delta_position.y >= 0.0 ? 1.0 : -1.0;
                if (left.physics->is_static) right.transform.position.y -= penetration.y * direction;
                else if (right.physics->is_static) left.transform.position.y += penetration.y * direction;
            }
        }
    }
}

std::size_t PhysicsSystem::candidate_pairs() const { return candidate_pairs_; }

void ResourceManager::register_asset(std::string name, std::string path) { assets_[std::move(name)] = std::move(path); }
const std::string* ResourceManager::path_for(const std::string& name) const {
    const auto iterator = assets_.find(name);
    return iterator == assets_.end() ? nullptr : &iterator->second;
}
std::size_t ResourceManager::size() const { return assets_.size(); }

Engine::Engine(EngineConfig config) : config_(config) {}
void Engine::load_scene(std::shared_ptr<Scene> scene) {
    if (!scene) throw std::invalid_argument("scene cannot be null");
    scene_ = std::move(scene);
    accumulator_ = 0.0;
    stats_ = {};
    physics_ = std::make_unique<PhysicsSystem>(events_);
}

void Engine::update(double frame_delta) {
    if (!scene_) throw std::logic_error("no scene loaded");
    frame_delta = std::max(0.0, std::min(frame_delta, config_.max_frame_delta));
    ++stats_.frame_count;
    if (paused_) return;
    accumulator_ += frame_delta;
    std::uint32_t steps = 0;
    constexpr double epsilon = 1e-12;
    while (accumulator_ + epsilon >= config_.fixed_timestep && steps < config_.max_fixed_steps) {
        physics_->fixed_update(*scene_, config_.fixed_timestep);
        accumulator_ -= config_.fixed_timestep;
        if (std::abs(accumulator_) < epsilon) accumulator_ = 0.0;
        ++stats_.fixed_step_count;
        ++steps;
    }
    if (accumulator_ >= config_.fixed_timestep) {
        stats_.dropped_time += accumulator_ - std::fmod(accumulator_, config_.fixed_timestep);
        accumulator_ = std::fmod(accumulator_, config_.fixed_timestep);
    }
    stats_.interpolation_alpha = accumulator_ / config_.fixed_timestep;
    events_.flush();
}

void Engine::run_for(double seconds) {
    if (seconds < 0.0) throw std::invalid_argument("seconds cannot be negative");
    double elapsed = 0.0;
    while (elapsed < seconds) {
        const double delta = std::min(config_.fixed_timestep, seconds - elapsed);
        update(delta);
        elapsed += delta;
    }
}

void Engine::set_paused(bool paused) { paused_ = paused; }
Scene* Engine::scene() { return scene_.get(); }
const Scene* Engine::scene() const { return scene_.get(); }
const EngineStats& Engine::stats() const { return stats_; }
EventBus& Engine::events() { return events_; }
ResourceManager& Engine::resources() { return resources_; }

std::string to_json(const Engine& engine) {
    const Scene* scene = engine.scene();
    std::ostringstream output;
    output << std::setprecision(17) << "{\n"
           << "  \"scene\": \"" << (scene ? scene->name() : "No Scene") << "\",\n"
           << "  \"entities\": " << (scene ? scene->entities().size() : 0) << ",\n"
           << "  \"elapsed_time\": " << (engine.stats().fixed_step_count * (1.0 / 60.0)) << ",\n"
           << "  \"fixed_steps\": " << engine.stats().fixed_step_count << ",\n"
           << "  \"dropped_time\": " << engine.stats().dropped_time << "\n"
           << "}";
    return output.str();
}

}  // namespace ksa_engine
