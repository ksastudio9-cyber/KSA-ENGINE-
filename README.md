# KSA Engine Full Edition

KSA Engine Full Edition is a C++17-first, modular native game runtime for developer-authored scenes. Version `1.0.0` is the first Full Edition foundation release, built directly by CMake.

## Structure

```text
cpp/
  include/ksa_engine/runtime.hpp  # Public engine, scene, physics and system API
  src/runtime.cpp                 # Runtime implementation and JSON scene I/O
  src/main.cpp                    # Native CLI, editor shell and demo scene
  tests/runtime_tests.cpp         # Native runtime tests
assets/            # Project assets
```

## Architecture

`Engine` owns one active `Scene`, an ordered list of systems, and a fixed-step accumulator. A frame is clamped to 250ms, simulation advances at 60Hz, and the accumulator is bounded by a maximum number of fixed steps to avoid a spiral of death. Variable-rate systems run once after fixed simulation. `EngineStats` exposes frame count, fixed-step count, dropped time, and the interpolation alpha used by renderers. Systems can be stopped safely when scenes switch.

`Scene` is the scene graph and entity registry. Entities have a stable integer id, a hierarchical `Transform`, a kind, and extensible component data. Parent cycles are rejected and world positions are resolved from the hierarchy. `SceneManager` registers named scenes and switches them through the engine lifecycle. `EventBus` decouples gameplay and tools. `ResourceManager` provides explicit loader registration and cached resources. `PhysicsSystem` uses a spatial-hash broad phase, deterministic AABB resolution, gravity, and collision/trigger enter/exit events.

The current native build is a deterministic headless runtime and editor/play shell. Rendering-facing components are defined in the runtime API, while a production GPU viewport remains a deliberate next milestone rather than an undocumented claim.

## Native runtime

```bash
cmake -S cpp -B build/native -DCMAKE_BUILD_TYPE=Release
cmake --build build/native --config Release
./build/native/KSA --seconds 2 --json
./build/native/KSA --version
./build/native/KSA --seconds 2 --profile
./build/native/KSA --seconds 1 --render frame.ppm
```

The native C++17 runtime is the only engine path. It includes the headless runtime, deterministic scene systems, spatial-hash physics, enter/exit events, a cached asset pipeline with extension loaders, JSON scene I/O, built-in frame profiling, a replaceable renderer backend, editor/play shell and native tests. No Python runtime or Python dependencies are required.

The browser-based 3D editor is available at `website/editor.html`. It uses WebGL for a live block world with free camera controls, WASD movement, selection, transform gizmos, block creation/duplication/deletion, resize/rotation/position controls, image textures, and JSON map save/load. It is intentionally separate from the native runtime until the native GPU backend is introduced.

On Windows, `KSA --editor` now builds the native SDL2/OpenGL editor into the EXE. The native editor supports a free orbit camera (`WASD`, right mouse drag, wheel zoom), `B` to create a block, `Tab` to select the next block, `Delete` to remove the selected block, arrow keys to transform the selected block, and `1`/`2`/`3` for move/rotate/scale modes. The Windows CI fetches SDL2 and validates the native runtime tests before packaging `KSA.exe`.

`--render frame.ppm` uses the built-in deterministic software renderer. It produces a real 640x360 framebuffer with a sky gradient, directional sun lighting, material shading, camera projection, and a simple shadow darkening pass. `RenderSettings::shadow_map_size` defaults to 2048 for the renderer contract; a GPU shadow-map backend and HDR/cloud texture pipeline remain separate production work.

## Production interfaces

`ResourceManager` supports registered asset loaders, binary fallback loading, cache reuse, unload, and cache reset. `Profiler` records calls, total duration, and peak duration for named runtime sections. `RendererBackend` defines the rendering boundary; `HeadlessRenderer` is the portable validation backend and a GPU renderer can be added without changing scene or simulation contracts.

## Scene files

```bash
./build/native/KSA --seconds 1 --json --save scene.json
```

## Native tests

```bash
ctest --test-dir build/native --output-on-failure
```

Install the native library and public headers with:

```bash
cmake --install build/native --prefix ./dist/native
```

## Independent download website

The website in `website/` does not depend on GitHub. Put `KSA.exe` in `website/downloads/` and serve it from your own VPS, object storage bucket, or hosting provider:

Serve the static files with any web server, for example `cmake`-built deployment tooling, Nginx, or Caddy.

The site is available at `/` and the direct installer path is `/downloads/KSA.exe`. See [website/README.md](website/README.md) for the production reverse-proxy setup. The binary is intentionally ignored by Git so it can be deployed independently from the source repository.

## Engineering position

Full Edition means the product has moved beyond the Beta label and has a versioned, tested native foundation. It does not claim to outrank mature commercial engines. The high-rank roadmap remains GPU rendering, asset import, editor undo/redo, reflection, profiling, networking, platform packaging, documentation, and a growing user ecosystem.
