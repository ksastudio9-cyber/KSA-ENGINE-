#include "ksa_engine/runtime.hpp"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <map>
#include <sstream>
#include <stdexcept>
#include <unordered_set>

namespace ksa_engine {

Vec3 Vec3::operator+(const Vec3& other) const { return {x + other.x, y + other.y, z + other.z}; }
Vec3 Vec3::operator-(const Vec3& other) const { return {x - other.x, y - other.y, z - other.z}; }
Vec3 Vec3::operator*(double scalar) const { return {x * scalar, y * scalar, z * scalar}; }
Vec3 Vec3::operator/(double scalar) const {
    if (scalar == 0.0) throw std::domain_error("cannot divide Vec3 by zero");
    return {x / scalar, y / scalar, z / scalar};
}
Vec3& Vec3::operator+=(const Vec3& other) { x += other.x; y += other.y; z += other.z; return *this; }
double Vec3::length() const { return std::sqrt(x * x + y * y + z * z); }
Vec3 Vec3::normalized() const { const double value = length(); return value == 0.0 ? Vec3{} : *this * (1.0 / value); }
double Vec3::dot(const Vec3& other) const { return x * other.x + y * other.y + z * other.z; }
Vec3 Vec3::lerp(const Vec3& other, double amount) const {
    amount = std::max(0.0, std::min(1.0, amount));
    return *this + (other - *this) * amount;
}

Mesh Mesh::cube(std::string name) {
    return {std::move(name),
        {{-1, -1, -1}, {1, -1, -1}, {1, -1, 1}, {-1, -1, 1},
         {-1, 1, -1}, {1, 1, -1}, {1, 1, 1}, {-1, 1, 1}},
        {{0, 1, 2, 3}, {4, 7, 6, 5}, {0, 4, 5, 1}, {1, 5, 6, 2},
         {2, 6, 7, 3}, {4, 0, 3, 7}}};
}

Entity::Entity(const Entity& other)
    : id(other.id), name(other.name), kind(other.kind), transform(other.transform), active(other.active), target_id(other.target_id) {
    if (other.material) material = std::make_unique<Material>(*other.material);
    if (other.mesh) mesh = std::make_unique<MeshComponent>(*other.mesh);
    if (other.camera) camera = std::make_unique<CameraComponent>(*other.camera);
    if (other.light) light = std::make_unique<LightComponent>(*other.light);
    if (other.physics) physics = std::make_unique<PhysicsBody>(*other.physics);
    if (other.region) region = std::make_unique<RegionComponent>(*other.region);
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
    auto& created = entities_.emplace(entity.id, std::move(entity)).first->second;
    children_[created.transform.parent].push_back(created.id);
    return created;
}

Entity& Scene::create_entity_with_id(std::uint64_t id, std::string name, std::string kind, Transform transform) {
    if (id == 0 || entities_.count(id) != 0) throw std::invalid_argument("entity id is already in use");
    Entity entity;
    entity.id = id;
    entity.name = std::move(name);
    entity.kind = std::move(kind);
    entity.transform = transform;
    next_id_ = std::max(next_id_, id + 1);
    auto& created = entities_.emplace(id, std::move(entity)).first->second;
    children_[created.transform.parent].push_back(created.id);
    return created;
}

Entity& Scene::create_region(std::string name, Vec3 center, Vec3 extent, std::string type) {
    auto& region = create_entity(std::move(name), "region", {center, {}, {1.0, 1.0, 1.0}, 0});
    region.region = std::make_unique<RegionComponent>();
    region.region->name = region.name;
    region.region->type = std::move(type);
    region.region->center = center;
    region.region->extent = extent;
    region.region->enabled = true;
    return region;
}

void Scene::destroy_entity(std::uint64_t id) {
    if (children_.count(id) != 0U) {
        for (const auto child_id : children_.at(id)) {
            if (entities_.count(child_id) != 0U) entities_.at(child_id).transform.parent = 0;
        }
    }
    entities_.erase(id);
    for (auto& [entity_id, entity] : entities_) {
        if (entity.transform.parent == id) entity.transform.parent = 0;
    }
    for (auto& [parent_id, nodes] : children_) {
        auto removed = std::remove(nodes.begin(), nodes.end(), id);
        if (removed != nodes.end()) nodes.erase(removed, nodes.end());
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
    std::sort(result.begin(), result.end(), [](const Entity* left, const Entity* right) { return left->id < right->id; });
    return result;
}

std::vector<Entity*> Scene::children(std::uint64_t parent_id) {
    std::vector<Entity*> result;
    auto iterator = children_.find(parent_id);
    if (iterator == children_.end()) return result;
    for (const auto child_id : iterator->second) {
        if (auto* child = find(child_id)) result.push_back(child);
    }
    return result;
}

std::vector<const Entity*> Scene::children(std::uint64_t parent_id) const {
    std::vector<const Entity*> result;
    const auto iterator = children_.find(parent_id);
    if (iterator == children_.end()) return result;
    for (const auto child_id : iterator->second) {
        if (const auto* child = find(child_id)) result.push_back(child);
    }
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
    if (entity->transform.parent != 0) {
        auto parent_list = children_.find(entity->transform.parent);
        if (parent_list != children_.end()) {
            auto removed = std::remove(parent_list->second.begin(), parent_list->second.end(), id);
            if (removed != parent_list->second.end()) parent_list->second.erase(removed, parent_list->second.end());
        }
    }
    entity->transform.parent = parent;
    children_[parent].push_back(id);
}

void Scene::register_prefab(std::string prefab_name, PrefabDefinition nodes) {
    prefabs_[std::move(prefab_name)] = std::move(nodes);
}

Entity& Scene::instantiate_prefab(const std::string& prefab_name, std::string instance_name, Transform transform) {
    const auto prefab_iterator = prefabs_.find(prefab_name);
    if (prefab_iterator == prefabs_.end()) throw std::out_of_range("prefab is not registered: " + prefab_name);
    const auto& definition = prefab_iterator->second;
    if (definition.empty()) throw std::invalid_argument("prefab cannot be empty: " + prefab_name);
    auto& root = create_entity(std::move(instance_name), definition.front().kind, transform);
    root.transform = transform;
    for (std::size_t index = 1; index < definition.size(); ++index) {
        const auto& node = definition[index];
        auto& child = create_entity(node.name, node.kind, node.transform);
        set_parent(child.id, root.id);
    }
    return root;
}

std::vector<std::string> Scene::prefab_names() const {
    std::vector<std::string> names;
    names.reserve(prefabs_.size());
    for (const auto& [name, _] : prefabs_) names.push_back(name);
    std::sort(names.begin(), names.end());
    return names;
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

void InputState::set_down(std::string key, bool down) { keys_[std::move(key)] = down; }
bool InputState::is_down(const std::string& key) const {
    const auto iterator = keys_.find(key);
    return iterator != keys_.end() && iterator->second;
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

    struct Cell {
        int x;
        int y;
        int z;
        bool operator<(const Cell& other) const {
            return std::tie(x, y, z) < std::tie(other.x, other.y, other.z);
        }
    };
    constexpr double cell_size = 4.0;
    std::map<Cell, std::vector<Entity*>> grid;
    for (Entity* entity : bodies) {
        const Vec3 position = entity->transform.position;
        const Vec3 extent = entity->physics->half_extents;
        const int minimum_x = static_cast<int>(std::floor((position.x - extent.x) / cell_size));
        const int maximum_x = static_cast<int>(std::floor((position.x + extent.x) / cell_size));
        const int minimum_y = static_cast<int>(std::floor((position.y - extent.y) / cell_size));
        const int maximum_y = static_cast<int>(std::floor((position.y + extent.y) / cell_size));
        const int minimum_z = static_cast<int>(std::floor((position.z - extent.z) / cell_size));
        const int maximum_z = static_cast<int>(std::floor((position.z + extent.z) / cell_size));
        for (int x = minimum_x; x <= maximum_x; ++x) {
            for (int y = minimum_y; y <= maximum_y; ++y) {
                for (int z = minimum_z; z <= maximum_z; ++z) grid[{x, y, z}].push_back(entity);
            }
        }
    }

    std::set<std::pair<std::uint64_t, std::uint64_t>> candidates;
    for (const auto& [cell, occupants] : grid) {
        (void)cell;
        for (std::size_t left_index = 0; left_index < occupants.size(); ++left_index) {
            for (std::size_t right_index = left_index + 1; right_index < occupants.size(); ++right_index) {
                const auto left_id = occupants[left_index]->id;
                const auto right_id = occupants[right_index]->id;
                candidates.insert(std::minmax(left_id, right_id));
            }
        }
    }
    candidate_pairs_ = candidates.size();
    std::map<std::uint64_t, Entity*> indexed;
    for (Entity* entity : bodies) indexed[entity->id] = entity;
    std::set<std::pair<std::uint64_t, std::uint64_t>> current_overlaps;
    std::set<std::pair<std::uint64_t, std::uint64_t>> current_triggers;
    for (const auto& pair : candidates) {
        Entity& left = *indexed.at(pair.first);
        Entity& right = *indexed.at(pair.second);
        const Vec3 delta_position = left.transform.position - right.transform.position;
        const Vec3 extent = left.physics->half_extents + right.physics->half_extents;
        if (std::abs(delta_position.x) > extent.x || std::abs(delta_position.y) > extent.y || std::abs(delta_position.z) > extent.z) continue;
        current_overlaps.insert(pair);
        const bool trigger = left.physics->is_trigger || right.physics->is_trigger;
        if (trigger) current_triggers.insert(pair);
        if (overlaps_.count(pair) == 0) events_.publish({trigger ? "trigger_enter" : "collision_enter", left.id, right.id, {}});
        if (trigger || (left.physics->is_static && right.physics->is_static)) continue;
        const Vec3 penetration{extent.x - std::abs(delta_position.x), extent.y - std::abs(delta_position.y), extent.z - std::abs(delta_position.z)};
        const bool resolve_x = penetration.x <= penetration.y && penetration.x <= penetration.z;
        const bool resolve_y = penetration.y <= penetration.z && !resolve_x;
        const double direction = (resolve_x ? delta_position.x : resolve_y ? delta_position.y : delta_position.z) >= 0.0 ? 1.0 : -1.0;
        const double correction = resolve_x ? penetration.x : resolve_y ? penetration.y : penetration.z;
        auto offset = [&](Entity& entity, double amount) {
            if (resolve_x) entity.transform.position.x += amount;
            else if (resolve_y) entity.transform.position.y += amount;
            else entity.transform.position.z += amount;
        };
        auto stop_velocity = [&](PhysicsBody& body) {
            if (resolve_x) body.velocity.x = 0.0;
            else if (resolve_y) body.velocity.y = 0.0;
            else body.velocity.z = 0.0;
        };
        if (left.physics->is_static) { offset(right, -correction * direction); stop_velocity(*right.physics); }
        else if (right.physics->is_static) { offset(left, correction * direction); stop_velocity(*left.physics); }
        else { offset(left, correction * direction * 0.5); offset(right, -correction * direction * 0.5); }
    }
    for (const auto& pair : overlaps_) {
        if (current_overlaps.count(pair) != 0) continue;
        events_.publish({trigger_overlaps_.count(pair) != 0 ? "trigger_exit" : "collision_exit", pair.first, pair.second, {}});
    }
    overlaps_ = std::move(current_overlaps);
    trigger_overlaps_ = std::move(current_triggers);
}

std::size_t PhysicsSystem::candidate_pairs() const { return candidate_pairs_; }
std::size_t PhysicsSystem::active_overlaps() const { return overlaps_.size(); }

void ResourceManager::register_asset(std::string name, std::string path) { assets_[std::move(name)] = std::move(path); }
const std::string* ResourceManager::path_for(const std::string& name) const {
    const auto iterator = assets_.find(name);
    return iterator == assets_.end() ? nullptr : &iterator->second;
}
std::string ResourceManager::extension_for(const std::string& path) {
    const std::size_t separator = path.find_last_of("/\\");
    const std::size_t dot = path.find_last_of('.');
    if (dot == std::string::npos || (separator != std::string::npos && dot < separator)) return {};
    std::string extension = path.substr(dot + 1);
    std::transform(extension.begin(), extension.end(), extension.begin(), [](unsigned char character) { return static_cast<char>(std::tolower(character)); });
    return extension;
}
void ResourceManager::register_loader(std::string extension, Loader loader) {
    if (!loader) throw std::invalid_argument("resource loader cannot be empty");
    std::transform(extension.begin(), extension.end(), extension.begin(), [](unsigned char character) { return static_cast<char>(std::tolower(character)); });
    if (!extension.empty() && extension.front() == '.') extension.erase(extension.begin());
    loaders_[std::move(extension)] = std::move(loader);
}
std::shared_ptr<Asset> ResourceManager::load(const std::string& path, std::string type) {
    if (type.empty()) type = extension_for(path);
    std::transform(type.begin(), type.end(), type.begin(), [](unsigned char character) { return static_cast<char>(std::tolower(character)); });
    const std::string key = type + ":" + path;
    const auto cached = cache_.find(key);
    if (cached != cache_.end()) return cached->second;
    std::shared_ptr<Asset> asset;
    const auto loader = loaders_.find(type);
    if (loader != loaders_.end()) {
        asset = loader->second(path);
    } else {
        std::ifstream input(path, std::ios::binary);
        if (!input) throw std::runtime_error("cannot load asset: " + path);
        asset = std::make_shared<Asset>();
        asset->path = path;
        asset->bytes.assign(std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
    }
    if (!asset) throw std::runtime_error("resource loader returned no asset: " + path);
    cache_[key] = asset;
    return asset;
}
void ResourceManager::unload(const std::string& path, std::string type) {
    if (type.empty()) type = extension_for(path);
    cache_.erase(type + ":" + path);
}
void ResourceManager::clear_cache() { cache_.clear(); }
std::size_t ResourceManager::size() const { return assets_.size(); }
std::size_t ResourceManager::loaded_count() const { return cache_.size(); }

void Profiler::begin(const std::string& name) { active_[name] = std::chrono::steady_clock::now(); }
void Profiler::end(const std::string& name) {
    const auto active = active_.find(name);
    if (active == active_.end()) return;
    const double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - active->second).count();
    active_.erase(active);
    sample(name, seconds);
}
void Profiler::sample(const std::string& name, double seconds) {
    if (seconds < 0.0) throw std::invalid_argument("profile duration cannot be negative");
    ProfileStat& result = stats_[name];
    ++result.calls;
    result.total_seconds += seconds;
    result.peak_seconds = std::max(result.peak_seconds, seconds);
}
const ProfileStat* Profiler::stat(const std::string& name) const {
    const auto iterator = stats_.find(name);
    return iterator == stats_.end() ? nullptr : &iterator->second;
}
const std::unordered_map<std::string, ProfileStat>& Profiler::stats() const { return stats_; }
void Profiler::reset() { active_.clear(); stats_.clear(); }

void HeadlessRenderer::render(const Scene& scene, const RenderSettings&) {
    ++frame_count_;
    last_entity_count_ = scene.entities().size();
}
std::uint64_t HeadlessRenderer::frame_count() const { return frame_count_; }
std::size_t HeadlessRenderer::last_entity_count() const { return last_entity_count_; }

SoftwareRenderer::SoftwareRenderer(int width, int height) : width_(width), height_(height), pixels_(static_cast<std::size_t>(width) * static_cast<std::size_t>(height) * 3U, 0) {
    if (width <= 0 || height <= 0) throw std::invalid_argument("software renderer dimensions must be positive");
}

void SoftwareRenderer::render(const Scene& scene, const RenderSettings& settings) {
    ++frame_count_;
    const Vec3 sun_direction = [&scene] {
        for (const auto& [id, entity] : scene.entities()) {
            (void)id;
            if (entity.light) return entity.light->direction.normalized();
        }
        return Vec3{0.45, 1.0, 0.35}.normalized();
    }();
    double sun_intensity = 1.0;
    for (const auto& [id, entity] : scene.entities()) {
        (void)id;
        if (entity.light) sun_intensity = std::max(0.0, entity.light->intensity);
    }
    for (int y = 0; y < height_; ++y) {
        const double gradient = static_cast<double>(y) / static_cast<double>(height_ - 1);
        const std::uint8_t red = static_cast<std::uint8_t>(std::clamp(settings.clear_red + static_cast<int>((scene.sky.top_red - settings.clear_red) * (1.0 - gradient)), 0, 255));
        const std::uint8_t green = static_cast<std::uint8_t>(std::clamp(settings.clear_green + static_cast<int>((scene.sky.top_green - settings.clear_green) * (1.0 - gradient)), 0, 255));
        const std::uint8_t blue = static_cast<std::uint8_t>(std::clamp(settings.clear_blue + static_cast<int>((scene.sky.top_blue - settings.clear_blue) * (1.0 - gradient)), 0, 255));
        for (int x = 0; x < width_; ++x) {
            const std::size_t offset = (static_cast<std::size_t>(y) * static_cast<std::size_t>(width_) + static_cast<std::size_t>(x)) * 3U;
            pixels_[offset] = red; pixels_[offset + 1] = green; pixels_[offset + 2] = blue;
        }
    }
    const Entity* camera = nullptr;
    for (const auto& [id, entity] : scene.entities()) if (entity.camera && entity.active) { camera = &entity; break; }
    const Vec3 camera_position = camera ? scene.world_position(camera->id) : Vec3{0.0, 3.0, 7.0};
    const double focal = static_cast<double>(height_) / (2.0 * std::tan(0.5 * 60.0 * 3.141592653589793 / 180.0));
    auto project = [&](const Vec3& position) -> std::pair<int, int> {
        const Vec3 relative = position - camera_position;
        const double depth = std::max(0.25, relative.z * -1.0);
        return {static_cast<int>(width_ * 0.5 + relative.x * focal / depth), static_cast<int>(height_ * 0.48 - (relative.y - 1.0) * focal / depth)};
    };
    for (const auto& [id, entity] : scene.entities()) {
        (void)id;
        if (!entity.active || !entity.mesh || entity.camera || entity.light) continue;
        const Vec3 position = scene.world_position(entity.id);
        const auto [screen_x, screen_y] = project(position);
        const int radius = std::max(2, static_cast<int>(focal * std::max(0.2, entity.transform.scale.x) / std::max(0.25, (position - camera_position).length())));
        const double diffuse = std::max(0.0, Vec3{0.0, 1.0, 0.0}.dot(sun_direction * -1.0));
        const double shadow = settings.shadows && entity.kind != "ground" ? 0.82 : 1.0;
        const double light = std::clamp(scene.sky.ambient_strength + diffuse * sun_intensity * shadow, 0.0, 2.0);
        const Material material = entity.material ? *entity.material : Material{};
        const auto shade = [&](std::uint8_t channel) { return static_cast<std::uint8_t>(std::clamp(static_cast<int>(static_cast<double>(channel) * light), 0, 255)); };
        for (int y = std::max(0, screen_y - radius); y <= std::min(height_ - 1, screen_y + radius); ++y) {
            for (int x = std::max(0, screen_x - radius); x <= std::min(width_ - 1, screen_x + radius); ++x) {
                if ((x - screen_x) * (x - screen_x) + (y - screen_y) * (y - screen_y) > radius * radius) continue;
                const std::size_t offset = (static_cast<std::size_t>(y) * static_cast<std::size_t>(width_) + static_cast<std::size_t>(x)) * 3U;
                pixels_[offset] = shade(material.red); pixels_[offset + 1] = shade(material.green); pixels_[offset + 2] = shade(material.blue);
            }
        }
    }
}

void SoftwareRenderer::save_ppm(const std::string& path) const {
    std::ofstream output(path, std::ios::binary);
    if (!output) throw std::runtime_error("cannot open renderer output: " + path);
    output << "P6\n" << width_ << ' ' << height_ << "\n255\n";
    output.write(reinterpret_cast<const char*>(pixels_.data()), static_cast<std::streamsize>(pixels_.size()));
}
int SoftwareRenderer::width() const { return width_; }
int SoftwareRenderer::height() const { return height_; }
const std::vector<std::uint8_t>& SoftwareRenderer::pixels() const { return pixels_; }
std::uint64_t SoftwareRenderer::frame_count() const { return frame_count_; }

Engine::Engine(EngineConfig config) : config_(config), scene_manager_(std::make_unique<SceneManager>(*this)) {
    if (config_.fixed_timestep <= 0.0) throw std::invalid_argument("fixed timestep must be positive");
    if (config_.max_frame_delta <= 0.0) throw std::invalid_argument("max frame delta must be positive");
    if (config_.max_fixed_steps == 0) throw std::invalid_argument("max fixed steps must be positive");
}
void Engine::load_scene(std::shared_ptr<Scene> scene) {
    if (!scene) throw std::invalid_argument("scene cannot be null");
    if (scene_) for (const auto& system : systems_) system->on_stop(*this);
    scene_ = std::move(scene);
    accumulator_ = 0.0;
    stats_ = {};
    physics_ = std::make_unique<PhysicsSystem>(events_);
    for (const auto& system : systems_) system->on_start(*this);
}

void Engine::update(double frame_delta) {
    if (!scene_) throw std::logic_error("no scene loaded");
    const auto frame_started = std::chrono::steady_clock::now();
    profiler_.begin("engine.frame");
    frame_delta = std::max(0.0, std::min(frame_delta, config_.max_frame_delta));
    ++stats_.frame_count;
    if (paused_) {
        stats_.interpolation_alpha = accumulator_ / config_.fixed_timestep;
        stats_.last_frame_seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - frame_started).count();
        stats_.peak_frame_seconds = std::max(stats_.peak_frame_seconds, stats_.last_frame_seconds);
        profiler_.end("engine.frame");
        return;
    }
    accumulator_ += frame_delta;
    std::uint32_t steps = 0;
    constexpr double epsilon = 1e-12;
    while (accumulator_ + epsilon >= config_.fixed_timestep && steps < config_.max_fixed_steps) {
        const auto fixed_started = std::chrono::steady_clock::now();
        profiler_.begin("engine.fixed");
        physics_->fixed_update(*scene_, config_.fixed_timestep);
        ++stats_.system_callbacks;
        for (const auto& system : systems_) {
            system->on_fixed_update(*this, config_.fixed_timestep);
            ++stats_.system_callbacks;
        }
        stats_.last_fixed_seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - fixed_started).count();
        profiler_.end("engine.fixed");
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
    for (const auto& system : systems_) {
        system->on_update(*this, frame_delta);
        ++stats_.system_callbacks;
    }
    events_.flush();
    stats_.last_frame_seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - frame_started).count();
    stats_.peak_frame_seconds = std::max(stats_.peak_frame_seconds, stats_.last_frame_seconds);
    profiler_.end("engine.frame");
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
void Engine::add_system(std::shared_ptr<System> system) {
    if (!system) throw std::invalid_argument("system cannot be null");
    systems_.push_back(std::move(system));
    if (scene_) systems_.back()->on_start(*this);
}
void Engine::remove_system(const std::shared_ptr<System>& system) {
    const auto iterator = std::find(systems_.begin(), systems_.end(), system);
    if (iterator != systems_.end()) {
        (*iterator)->on_stop(*this);
        systems_.erase(iterator);
    }
}
void Engine::set_project_directory(std::string path) { project_directory_ = std::move(path); }
const std::string& Engine::project_directory() const { return project_directory_; }
void Engine::set_project_name(std::string name) { project_name_ = std::move(name); }
const std::string& Engine::project_name() const { return project_name_; }
void Engine::set_autosave_enabled(bool enabled) { autosave_enabled_ = enabled; }
bool Engine::autosave_enabled() const { return autosave_enabled_; }
void Engine::set_autosave_interval(double seconds) { autosave_interval_ = std::max(0.0, seconds); }
double Engine::autosave_interval() const { return autosave_interval_; }

std::string Engine::project_state_path() const {
    return std::filesystem::path(project_directory_) / "project_state.json";
}
std::string Engine::default_scene_path() const {
    return std::filesystem::path(project_directory_) / "scenes" / "default_scene.json";
}

bool Engine::save_project_state() {
    if (!scene_) return false;
    const std::filesystem::path directory(project_directory_);
    std::filesystem::create_directories(directory);
    std::filesystem::create_directories(directory / "scenes");
    const std::string scene_path = default_scene_path();
    save_scene(*scene_, scene_path);

    std::ofstream output(project_state_path());
    if (!output) return false;
    output << "{\n"
           << "  \"project_name\": \"" << project_name_ << "\",\n"
           << "  \"scene_path\": \"" << scene_path << "\",\n"
           << "  \"autosave_enabled\": " << (autosave_enabled_ ? "true" : "false") << ",\n"
           << "  \"autosave_interval\": " << autosave_interval_ << "\n"
           << "}\n";
    return output.good();
}

bool Engine::load_project_state() {
    const std::filesystem::path path(project_state_path());
    std::ifstream input(path);
    if (!input) return false;
    std::string content((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    const auto name_pos = content.find("\"project_name\": \"");
    if (name_pos != std::string::npos) {
        const auto begin = name_pos + std::string("\"project_name\": \"").size();
        const auto end = content.find('"', begin);
        if (end != std::string::npos) project_name_ = content.substr(begin, end - begin);
    }
    const auto scene_pos = content.find("\"scene_path\": \"");
    if (scene_pos != std::string::npos) {
        const auto begin = scene_pos + std::string("\"scene_path\": \"").size();
        const auto end = content.find('"', begin);
        if (end != std::string::npos) {
            const std::string scene_path = content.substr(begin, end - begin);
            if (std::filesystem::exists(scene_path)) {
                const auto loaded = ksa_engine::load_scene(scene_path);
                if (loaded) load_scene(loaded);
            }
        }
    }
    const auto autosave_pos = content.find("\"autosave_enabled\": ");
    if (autosave_pos != std::string::npos) {
        const auto begin = autosave_pos + std::string("\"autosave_enabled\": ").size();
        const std::string value = content.substr(begin, std::min<std::size_t>(5, content.size() - begin));
        autosave_enabled_ = value.find("true") != std::string::npos;
    }
    const auto interval_pos = content.find("\"autosave_interval\": ");
    if (interval_pos != std::string::npos) {
        const auto begin = interval_pos + std::string("\"autosave_interval\": ").size();
        const auto end = content.find('\n', begin);
        if (end != std::string::npos) {
            const std::string value = content.substr(begin, end - begin);
            autosave_interval_ = std::stod(value);
        }
    }
    return scene_ != nullptr;
}

Scene* Engine::scene() { return scene_.get(); }
const Scene* Engine::scene() const { return scene_.get(); }
const EngineStats& Engine::stats() const { return stats_; }
EventBus& Engine::events() { return events_; }
ResourceManager& Engine::resources() { return resources_; }
Profiler& Engine::profiler() { return profiler_; }
const Profiler& Engine::profiler() const { return profiler_; }
SceneManager& Engine::scene_manager() { return *scene_manager_; }

SceneManager::SceneManager(Engine& engine) : engine_(engine) {}
void SceneManager::register_scene(std::shared_ptr<Scene> scene) {
    if (!scene) throw std::invalid_argument("scene cannot be null");
    scenes_[scene->name()] = std::move(scene);
}
std::shared_ptr<Scene> SceneManager::get(const std::string& name) const {
    const auto iterator = scenes_.find(name);
    return iterator == scenes_.end() ? nullptr : iterator->second;
}
std::shared_ptr<Scene> SceneManager::switch_to(const std::string& name) {
    auto scene = get(name);
    if (!scene) throw std::out_of_range("scene is not registered: " + name);
    engine_.load_scene(scene);
    return scene;
}
std::vector<std::string> SceneManager::names() const {
    std::vector<std::string> result;
    for (const auto& [name, scene] : scenes_) result.push_back(name);
    std::sort(result.begin(), result.end());
    return result;
}

void CameraSystem::on_start(Engine& engine) {
    if (!engine.scene()) return;
    for (const auto& [id, entity] : engine.scene()->entities()) {
        if (entity.camera) return;
    }
}
void CameraSystem::on_update(Engine& engine, double delta) {
    if (!engine.scene()) return;
    for (Entity* camera : engine.scene()->active_entities()) {
        if (!camera->camera || !camera->target_id) continue;
        const Entity* target = engine.scene()->find(*camera->target_id);
        if (!target) continue;
        camera->transform.position = camera->transform.position.lerp(target->transform.position + Vec3{0, 2, 5}, 1.0 - std::exp(-8.0 * delta));
    }
}

InputMovementSystem::InputMovementSystem(InputState& input, double speed) : input_(input), speed_(speed) {}
void InputMovementSystem::on_update(Engine& engine, double delta) {
    if (!engine.scene()) return;
    const double x = static_cast<double>(input_.is_down("right")) - static_cast<double>(input_.is_down("left"));
    const double z = static_cast<double>(input_.is_down("back")) - static_cast<double>(input_.is_down("forward"));
    const double length = std::sqrt(x * x + z * z);
    if (length == 0.0) return;
    const double movement_speed = speed_ * (input_.is_down("run") || input_.is_down("sprint") ? 1.8 : 1.0);
    for (Entity* player : engine.scene()->active_entities()) {
        if (player->kind != "player") continue;
        player->transform.position += Vec3{x / length, 0, z / length} * (movement_speed * delta);
        player->transform.rotation.y = std::atan2(x, -z);
    }
}

LightingSystem::LightingSystem(double ambient) : ambient_(std::max(0.0, std::min(1.0, ambient))) {}
void LightingSystem::on_update(Engine& engine, double) {
    if (engine.scene()) engine.scene()->metadata["ambient_strength"] = std::to_string(ambient_);
}

std::string to_json(const Engine& engine) {
    const Scene* scene = engine.scene();
    const ProfileStat* frame_profile = engine.profiler().stat("engine.frame");
    std::ostringstream output;
        output << std::setprecision(17) << "{\n"
            << "  \"engine\": \"" << edition_name << "\",\n"
            << "  \"version\": \"" << version << "\",\n"
           << "  \"scene\": \"" << (scene ? scene->name() : "No Scene") << "\",\n"
           << "  \"entities\": " << (scene ? scene->entities().size() : 0) << ",\n"
           << "  \"elapsed_time\": " << (static_cast<double>(engine.stats().fixed_step_count) * (1.0 / 60.0)) << ",\n"
           << "  \"fixed_steps\": " << engine.stats().fixed_step_count << ",\n"
           << "  \"dropped_time\": " << engine.stats().dropped_time << ",\n"
           << "  \"peak_frame_seconds\": " << engine.stats().peak_frame_seconds << ",\n"
           << "  \"profile_frame_calls\": " << (frame_profile ? frame_profile->calls : 0) << ",\n"
           << "  \"profile_frame_total_seconds\": " << (frame_profile ? frame_profile->total_seconds : 0.0) << "\n"
           << "}";
    return output.str();
}

void save_scene(const Scene& scene, const std::string& path) {
    std::ofstream output(path);
    if (!output) throw std::runtime_error("cannot open scene for writing: " + path);
    output << "{\n  \"name\": \"" << scene.name() << "\",\n  \"entities\": [\n";
    bool first = true;
    for (const auto& [id, entity] : scene.entities()) {
        if (!first) output << ",\n";
        first = false;
        output << "    {\"id\": " << id << ", \"name\": \"" << entity.name
             << "\", \"kind\": \"" << entity.kind << "\", \"active\": " << (entity.active ? 1 : 0)
             << ", \"position\": [" << entity.transform.position.x << ", " << entity.transform.position.y << ", " << entity.transform.position.z
             << "], \"rotation\": [" << entity.transform.rotation.x << ", " << entity.transform.rotation.y << ", " << entity.transform.rotation.z
             << "], \"scale\": [" << entity.transform.scale.x << ", " << entity.transform.scale.y << ", " << entity.transform.scale.z
             << "], \"parent\": " << entity.transform.parent << "}";
    }
    output << "\n  ]\n}\n";
}

std::shared_ptr<Scene> load_scene(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open scene for reading: " + path);
    std::stringstream contents;
    contents << input.rdbuf();
    const std::string text = contents.str();
    const auto name_start = text.find("\"name\": \"");
    if (name_start == std::string::npos) throw std::runtime_error("invalid scene file: missing name");
    const auto name_begin = name_start + 9;
    const auto name_end = text.find('"', name_begin);
    auto scene = std::make_shared<Scene>(text.substr(name_begin, name_end - name_begin));
    std::istringstream lines(text);
    std::string line;
    while (std::getline(lines, line)) {
        const auto id_marker = line.find("{\"id\": ");
        if (id_marker == std::string::npos) continue;
        unsigned long long id = 0;
        int active = 1;
        double x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, sx = 1, sy = 1, sz = 1;
        unsigned long long parent = 0;
        char name[256]{};
        char kind[128]{};
        if (std::sscanf(line.c_str() + id_marker, "{\"id\": %llu, \"name\": \"%255[^\"]\", \"kind\": \"%127[^\"]\", \"active\": %d, \"position\": [%lf, %lf, %lf], \"rotation\": [%lf, %lf, %lf], \"scale\": [%lf, %lf, %lf], \"parent\": %llu}", &id, name, kind, &active, &x, &y, &z, &rx, &ry, &rz, &sx, &sy, &sz, &parent) == 14) {
            auto& entity = scene->create_entity_with_id(id, name, kind, {{x, y, z}, {rx, ry, rz}, {sx, sy, sz}, parent});
            entity.active = active != 0;
        }
    }
    return scene;
}

}  // namespace ksa_engine
