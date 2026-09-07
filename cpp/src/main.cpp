#include "ksa_engine/runtime.hpp"

#include <cstdlib>
#include <exception>
#include <iostream>
#include <string>

namespace {

void print_usage() {
    std::cout << "KSA ENGINE native runtime\n"
              << "Usage: ksa_engine_cpp [description] [--seconds N] [--seed N] [--json]\n";
}

}  // namespace

int main(int argc, char* argv[]) {
    try {
        std::string description = "مدينة صحراوية ليلية فيها واحة ومعركة";
        double seconds = 1.0;
        std::uint64_t seed = 0;
        bool has_seed = false;
        bool json = false;

        for (int index = 1; index < argc; ++index) {
            const std::string argument = argv[index];
            if (argument == "--help" || argument == "-h") {
                print_usage();
                return 0;
            }
            if (argument == "--json") {
                json = true;
                continue;
            }
            if (argument == "--seconds" && index + 1 < argc) {
                seconds = std::stod(argv[++index]);
                continue;
            }
            if (argument == "--seed" && index + 1 < argc) {
                seed = std::stoull(argv[++index]);
                has_seed = true;
                continue;
            }
            if (!argument.empty() && argument.front() == '-') {
                throw std::invalid_argument("unknown option: " + argument);
            }
            description = argument;
        }

        auto world = ksa_engine::generate_world(description, seed, has_seed);
        ksa_engine::run_for(world, seconds);
        if (json) {
            std::cout << ksa_engine::to_json(world) << '\n';
        } else {
            std::cout << "KSA ENGINE | KSA Generated World\n"
                      << "entities=" << world.entities
                      << " elapsed=" << world.elapsed_time
                      << " seed=" << world.seed << '\n'
                      << "terrain=" << world.terrain
                      << " time_of_day=" << world.time_of_day << '\n';
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "KSA ENGINE error: " << error.what() << '\n';
        return EXIT_FAILURE;
    }
}
