#pragma once

#include <cstdint>
#include <chrono>
#include <functional>
#include <fstream>
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <tuple>
#include <unordered_map>
#include <vector>

namespace ksa_engine {

inline constexpr const char* edition_name = "KSA Engine Full Edition";
#ifdef KSA_ENGINE_VERSION
inline constexpr const char* version = KSA_ENGINE_VERSION;
#else
inline constexpr const char* version = "1.0.0";
#endif

struct Vec3 {
    double x{0.0};
    double y{0.0};
    double z{0.0};

    Vec3 operator+(const Vec3& other) const;
    Vec3 operator-(const Vec3& other) const;
    Vec3 operator*(double scalar) const;
    Vec3 operator/(double scalar) const;
    Vec3& operator+=(const Vec3& other);
    double length() const;
    Vec3 normalized() const;
    double dot(const Vec3& other) const;
    Vec3 lerp(const Vec3& other, double amount) const;
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

struct Mesh {
    std::string name{"Cube"};
    std::vector<Vec3> vertices;
    std::vector<std::vector<std::size_t>> faces;
    static Mesh cube(std::string name = "Cube");
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

struct SkySettings {
    std::uint8_t top_red{72};
    std::uint8_t top_green{132};
    std::uint8_t top_blue{192};
    double ambient_strength{0.35};
};

struct RenderSettings {
    std::uint8_t clear_red{22};
    std::uint8_t clear_green{31};
    std::uint8_t clear_blue{46};
    double grid_size{1.0};
    int grid_extent{24};
    bool show_grid{true};
    bool shadows{true};
    int shadow_map_size{2048};
    double shadow_bias{0.003};
    int filtering_radius{1};
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
    std::optional<std::uint64_t> target_id;

    Entity() = default;
    Entity(const Entity& other);
    Entity& operator=(const Entity& other);
};

class Scene {
public:
    explicit Scene(std::string name = "Untitled");

    Entity& create_entity(std::string name, std::string kind = "entity", Transform transform = {});
    Entity& create_entity_with_id(std::uint64_t id, std::string name, std::string kind = "entity", Transform transform = {});
    void destroy_entity(std::uint64_t id);
    Entity* find(std::uint64_t id);
    const Entity* find(std::uint64_t id) const;
    std::vector<Entity*> active_entities();
    Vec3 world_position(std::uint64_t id) const;
    void set_parent(std::uint64_t id, std::uint64_t parent);

    const std::string& name() const;
    const std::unordered_map<std::uint64_t, Entity>& entities() const;
    std::unordered_map<std::string, std::string> metadata;
    SkySettings sky;
    RenderSettings render_settings;

private:
    std::string name_;
    std::uint64_t next_id_{1};
    std::unordered_map<std::uint64_t, Entity> entities_;
};

struct Event {
    std::string name;
    std::uint64_t a{0};
    std::uint64_t b{0};
    std::unordered_map<std::string, std::string> payload;
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

class Engine;
class System {
public:
    virtual ~System() = default;
    virtual void on_start(Engine&) {}
    virtual void on_stop(Engine&) {}
    virtual void on_fixed_update(Engine&, double) {}
    virtual void on_update(Engine&, double) {}
};

class PhysicsSystem {
public:
    explicit PhysicsSystem(EventBus& events, Vec3 gravity = {0.0, -9.81, 0.0});
    void fixed_update(Scene& scene, double delta);
    std::size_t candidate_pairs() const;
    std::size_t active_overlaps() const;

private:
    EventBus& events_;
    Vec3 gravity_;
    std::size_t candidate_pairs_{0};
    std::set<std::pair<std::uint64_t, std::uint64_t>> overlaps_;
    std::set<std::pair<std::uint64_t, std::uint64_t>> trigger_overlaps_;
};

class InputState {
public:
    void set_down(std::string key, bool down);
    bool is_down(const std::string& key) const;

private:
    std::unordered_map<std::string, bool> keys_;
};

class CameraSystem : public System {
public:
    void on_start(Engine& engine) override;
    void on_update(Engine& engine, double delta) override;
};

class InputMovementSystem : public System {
public:
    explicit InputMovementSystem(InputState& input, double speed = 5.0);
    void on_update(Engine& engine, double delta) override;

private:
    InputState& input_;
    double speed_;
};

class LightingSystem : public System {
public:
    explicit LightingSystem(double ambient = 0.35);
    void on_update(Engine& engine, double delta) override;

private:
    double ambient_;
};

class SceneManager {
public:
    explicit SceneManager(Engine& engine);
    void register_scene(std::shared_ptr<Scene> scene);
    std::shared_ptr<Scene> get(const std::string& name) const;
    std::shared_ptr<Scene> switch_to(const std::string& name);
    std::vector<std::string> names() const;

private:
    Engine& engine_;
    std::unordered_map<std::string, std::shared_ptr<Scene>> scenes_;
};

struct Asset {
    std::string path;
    std::vector<std::uint8_t> bytes;
};

class ResourceManager {
public:
    using Loader = std::function<std::shared_ptr<Asset>(const std::string& path)>;
    void register_asset(std::string name, std::string path);
    const std::string* path_for(const std::string& name) const;
    void register_loader(std::string extension, Loader loader);
    std::shared_ptr<Asset> load(const std::string& path, std::string type = {});
    void unload(const std::string& path, std::string type = {});
    void clear_cache();
    std::size_t size() const;
    std::size_t loaded_count() const;

private:
    static std::string extension_for(const std::string& path);
    std::unordered_map<std::string, std::string> assets_;
    std::unordered_map<std::string, Loader> loaders_;
    std::unordered_map<std::string, std::shared_ptr<Asset>> cache_;
};

struct ProfileStat {
    std::uint64_t calls{0};
    double total_seconds{0.0};
    double peak_seconds{0.0};
};

class Profiler {
public:
    void begin(const std::string& name);
    void end(const std::string& name);
    void sample(const std::string& name, double seconds);
    const ProfileStat* stat(const std::string& name) const;
    const std::unordered_map<std::string, ProfileStat>& stats() const;
    void reset();

private:
    std::unordered_map<std::string, std::chrono::steady_clock::time_point> active_;
    std::unordered_map<std::string, ProfileStat> stats_;
};

class RendererBackend {
public:
    virtual ~RendererBackend() = default;
    virtual void render(const Scene& scene, const RenderSettings& settings) = 0;
};

class HeadlessRenderer final : public RendererBackend {
public:
    void render(const Scene& scene, const RenderSettings& settings) override;
    std::uint64_t frame_count() const;
    std::size_t last_entity_count() const;

private:
    std::uint64_t frame_count_{0};
    std::size_t last_entity_count_{0};
};

class SoftwareRenderer final : public RendererBackend {
public:
    SoftwareRenderer(int width = 640, int height = 360);
    void render(const Scene& scene, const RenderSettings& settings) override;
    void save_ppm(const std::string& path) const;
    int width() const;
    int height() const;
    const std::vector<std::uint8_t>& pixels() const;
    std::uint64_t frame_count() const;

private:
    int width_;
    int height_;
    std::vector<std::uint8_t> pixels_;
    std::uint64_t frame_count_{0};
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
    double last_frame_seconds{0.0};
    double last_fixed_seconds{0.0};
    double peak_frame_seconds{0.0};
    std::uint64_t system_callbacks{0};
};

class Engine {
public:
    explicit Engine(EngineConfig config = {});
    void load_scene(std::shared_ptr<Scene> scene);
    void update(double frame_delta);
    void run_for(double seconds);
    void set_paused(bool paused);
    void add_system(std::shared_ptr<System> system);
    void remove_system(const std::shared_ptr<System>& system);

    Scene* scene();
    const Scene* scene() const;
    const EngineStats& stats() const;
    EventBus& events();
    ResourceManager& resources();
    Profiler& profiler();
    const Profiler& profiler() const;
    SceneManager& scene_manager();

private:
    EngineConfig config_;
    EngineStats stats_;
    std::shared_ptr<Scene> scene_;
    EventBus events_;
    ResourceManager resources_;
    Profiler profiler_;
    std::unique_ptr<PhysicsSystem> physics_;
    std::vector<std::shared_ptr<System>> systems_;
    std::unique_ptr<SceneManager> scene_manager_;
    double accumulator_{0.0};
    bool paused_{false};
};

std::string to_json(const Engine& engine);
void save_scene(const Scene& scene, const std::string& path);
std::shared_ptr<Scene> load_scene(const std::string& path);

}  // namespace ksa_engine
