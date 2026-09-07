#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace ksa {

struct Vector3 {
    float x{0.0F};
    float y{0.0F};
    float z{0.0F};
};

struct Transform {
    Vector3 position{};
    Vector3 rotation{};
    Vector3 scale{1.0F, 1.0F, 1.0F};
};

struct Entity {
    std::uint64_t id{0};
    std::string name;
    std::string kind;
    Transform transform{};
    bool active{true};
};

struct World {
    std::string name;
    std::uint64_t seed{0};
    std::vector<Entity> entities;
    float elapsed_time{0.0F};

    Entity& create_entity(std::string name, std::string kind, Transform transform = {});
};

class System {
public:
    virtual ~System() = default;
    virtual void start(World&) {}
    virtual void update(World&, float) {}
};

class Engine {
public:
    explicit Engine(float fixed_timestep = 1.0F / 60.0F);
    void load_world(World world);
    void add_system(System& system);
    void update(float delta_time);
    void run_for(float duration);
    World* world() { return world_ ? &*world_ : nullptr; }

private:
    float fixed_timestep_;
    std::vector<System*> systems_;
    std::optional<World> world_;
};

World generate_world_from_text(const std::string& description, std::uint64_t seed = 0);

}  // namespace ksa
