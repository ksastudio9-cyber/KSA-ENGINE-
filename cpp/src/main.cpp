#include "ksa_engine/core.hpp"

#include <cstdlib>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    const std::string description = argc > 1 ? argv[1] : "desert city combat";
    const float duration = argc > 2 ? std::strtof(argv[2], nullptr) : 1.0F;

    try {
        ksa::World world = ksa::generate_world_from_text(description);
        ksa::Engine engine;
        engine.load_world(std::move(world));
        engine.run_for(duration);
        const ksa::World* result = engine.world();
        std::cout << "KSA ENGINE | " << result->name << '\n'
                  << "entities=" << result->entities.size()
                  << " time=" << result->elapsed_time << "s"
                  << " seed=" << result->seed << '\n';
    } catch (const std::exception& error) {
        std::cerr << "KSA ENGINE error: " << error.what() << '\n';
        return 1;
    }
    return 0;
}