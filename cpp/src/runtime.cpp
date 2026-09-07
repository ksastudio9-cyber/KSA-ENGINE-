#include "ksa_engine/runtime.hpp"

#include <algorithm>
#include <iomanip>
#include <limits>
#include <sstream>
#include <string_view>

namespace ksa_engine {
namespace {

bool contains(std::string_view text, std::string_view needle) {
    return text.find(needle) != std::string_view::npos;
}

std::uint64_t seed_from(std::string_view text) {
    // FNV-1a keeps the native runtime deterministic without third-party crypto.
    std::uint64_t hash = 14695981039346656037ULL;
    for (unsigned char byte : text) {
        hash ^= byte;
        hash *= 1099511628211ULL;
    }
    return hash;
}

std::string escape_json(std::string_view value) {
    std::string escaped;
    escaped.reserve(value.size() + 2);
    for (char character : value) {
        if (character == '\\' || character == '"') {
            escaped.push_back('\\');
        }
        if (character == '\n') {
            escaped += "\\n";
        } else if (character == '\r') {
            escaped += "\\r";
        } else {
            escaped.push_back(character);
        }
    }
    return escaped;
}

}  // namespace

WorldSummary generate_world(const std::string& description, std::uint64_t seed, bool has_seed) {
    if (description.empty()) {
        throw std::invalid_argument("world description cannot be empty");
    }

    const bool desert = contains(description, "desert") || contains(description, "صحراء") || contains(description, "رمال");
    const bool city = contains(description, "city") || contains(description, "مدينة") || contains(description, "قرية");
    const bool oasis = contains(description, "oasis") || contains(description, "واحة") || contains(description, "نخيل");
    const bool night = contains(description, "night") || contains(description, "ليل") || contains(description, "ليلاً");
    const bool fort = contains(description, "fort") || contains(description, "قلعة") || contains(description, "حصن");
    const bool combat = contains(description, "combat") || contains(description, "معركة") || contains(description, "قتال");
    const bool hostage = contains(description, "hostage") || contains(description, "مخطوف") || contains(description, "رهينة");

    WorldSummary world;
    world.description = description;
    world.seed = has_seed ? seed : seed_from(description);
    world.terrain = city ? (desert ? "urban_desert" : "urban_plains") : (desert ? "desert" : "plains");
    world.time_of_day = night ? "night" : "day";
    world.music = combat ? "battle_theme" : "arabian_theme";
    world.has_oasis = oasis;
    world.has_combat = combat;
    world.has_hostage = hostage;
    world.entities = 1;  // camera
    if (city || fort) {
        world.entities += city ? 8 : 3;
    }
    if (oasis) {
        world.entities += 5;
    }
    if (hostage) {
        world.entities += 2;
    }
    world.entities += combat ? 3 : 1;
    world.entities += 1;  // sun light
    world.elapsed_time = 0.0;
    return world;
}

void run_for(WorldSummary& world, double seconds) {
    if (seconds < 0.0) {
        throw std::invalid_argument("seconds cannot be negative");
    }
    world.elapsed_time = seconds;
}

std::string to_json(const WorldSummary& world) {
    std::ostringstream output;
    output << std::setprecision(std::numeric_limits<double>::max_digits10);
    output << "{\n"
           << "  \"name\": \"KSA Generated World\",\n"
           << "  \"seed\": " << world.seed << ",\n"
           << "  \"entities\": " << world.entities << ",\n"
           << "  \"elapsed_time\": " << world.elapsed_time << ",\n"
           << "  \"terrain\": \"" << escape_json(world.terrain) << "\",\n"
           << "  \"time_of_day\": \"" << escape_json(world.time_of_day) << "\",\n"
           << "  \"music\": \"" << escape_json(world.music) << "\"\n"
           << "}";
    return output.str();
}

}  // namespace ksa_engine
