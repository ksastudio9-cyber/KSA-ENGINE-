#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace ksa_engine {

struct Vec3 {
    double x{0.0};
    double y{0.0};
    double z{0.0};

    Vec3 operator+(const Vec3& other) const;
    Vec3 operator-(const Vec3& other) const;
    Vec3 operator*(double scalar) const;
    Vec3& operator+=(const Vec3& other);
    double length() const;
    Vec3 normalized() const;
};

struct Transform {
    Vec3 position{};
    Vec3 rotation{};
    Vec3 scale{1.0, 1.0, 1.0};
    std::uint64_t parent{0};
};

struct Material {
    std::uint8_t red{160};
    std::uint8_t green{175};
    std::uint8_t blue{190};
    double roughness{0.7};
    double metallic{0.0};
    std::string texture_path;
};

struct MeshComponent {
    std::string asset{"cube"};
};

struct CameraComponent {
    double fov{60.0};
    double near_clip{0.1};
    double far_clip{1000.0};
    double exposure{1.0};
};

struct LightComponent {
    Vec3 direction{-0.45, -1.0, -0.35};
    double intensity{1.0};
    bool casts_shadows{true};
};

struct PhysicsBody {
    Vec3 velocity{};
    Vec3 half_extents{0.5, 0.5, 0.5};
    bool use_gravity{true};
    bool is_static{false};
    bool is_trigger{false};
};

struct Entity {
    std::uint64_t id{0};
    std::string name;
    std::string kind{"entity"};
    Transform transform{};
    bool active{true};
    std::unique_ptr<Material> material;
    std::unique_ptr<MeshComponent> mesh;
    std::unique_ptr<CameraComponent> camera;
    std::unique_ptr<LightComponent> light;
    std::unique_ptr<PhysicsBody> physics;

    Entity() = default;
    Entity(const Entity& other);
    Entity& operator=(const Entity& other);
};

class Scene {
public:
    explicit Scene(std::string name = "Untitled");

    Entity& create_entity(std::string name, std::string kind = "entity", Transform transform = {});
    void destroy_entity(std::uint64_t id);
    Entity* find(std::uint64_t id);
    const Entity* find(std::uint64_t id) const;
    std::vector<Entity*> active_entities();
    Vec3 world_position(std::uint64_t id) const;
    void set_parent(std::uint64_t id, std::uint64_t parent);

    const std::string& name() const;
    const std::unordered_map<std::uint64_t, Entity>& entities() const;
    std::unordered_map<std::string, std::string> metadata;

private:
    std::string name_;
    std::uint64_t next_id_{1};
    std::unordered_map<std::uint64_t, Entity> entities_;
};

struct Event {
    std::string name;
    std::uint64_t a{0};
    std::uint64_t b{0};
};

class EventBus {
public:
    using Listener = std::function<void(const Event&)>;
    void subscribe(const std::string& name, Listener listener);
    void publish(Event event);
    void flush();

private:
    std::unordered_map<std::string, std::vector<Listener>> listeners_;
    std::vector<Event> queue_;
};

class PhysicsSystem {
public:
    explicit PhysicsSystem(EventBus& events, Vec3 gravity = {0.0, -9.81, 0.0});
    void fixed_update(Scene& scene, double delta);
    std::size_t candidate_pairs() const;

private:
    EventBus& events_;
    Vec3 gravity_;
    std::size_t candidate_pairs_{0};
    std::vector<std::uint64_t> overlaps_;
};

class ResourceManager {
public:
    void register_asset(std::string name, std::string path);
    const std::string* path_for(const std::string& name) const;
    std::size_t size() const;

private:
    std::unordered_map<std::string, std::string> assets_;
};

struct EngineConfig {
    double fixed_timestep{1.0 / 60.0};
    double max_frame_delta{0.25};
    std::uint32_t max_fixed_steps{8};
};

struct EngineStats {
    std::uint64_t frame_count{0};
    std::uint64_t fixed_step_count{0};
    double dropped_time{0.0};
    double interpolation_alpha{0.0};
};

class Engine {
public:
    explicit Engine(EngineConfig config = {});
    void load_scene(std::shared_ptr<Scene> scene);
    void update(double frame_delta);
    void run_for(double seconds);
    void set_paused(bool paused);

    Scene* scene();
    const Scene* scene() const;
    const EngineStats& stats() const;
    EventBus& events();
    ResourceManager& resources();

private:
    EngineConfig config_;
    EngineStats stats_;
    std::shared_ptr<Scene> scene_;
    EventBus events_;
    ResourceManager resources_;
    std::unique_ptr<PhysicsSystem> physics_;
    double accumulator_{0.0};
    bool paused_{false};
};

std::string to_json(const Engine& engine);

}  // namespace ksa_engine
