#pragma once

#include <cstdint>
#include <string>

namespace ksa_engine {

struct WorldSummary {
    std::string description;
    std::string terrain;
    std::string time_of_day;
    std::string music;
    std::uint64_t seed;
    std::uint32_t entities;
    double elapsed_time;
    bool has_oasis;
    bool has_combat;
    bool has_hostage;
};

WorldSummary generate_world(const std::string& description, std::uint64_t seed = 0, bool has_seed = false);
void run_for(WorldSummary& world, double seconds);
std::string to_json(const WorldSummary& world);

}  // namespace ksa_engine
