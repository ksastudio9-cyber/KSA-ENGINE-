# KSA Engine Beta

KSA Engine Beta is now a C++17-first, modular game runtime for developer-authored scenes. The native `KSA.exe` is built directly by CMake and deliberately contains no AI generation, text-to-world, narrative, or procedural content systems.

## Structure

```text
ksa_engine/
  core.py          # Engine loop, Scene, Entity, Transform, Vector3
  events.py        # EventBus and InputState
  resources.py     # Cached texture/model/audio loader registry
  scene_io.py      # JSON scene persistence
  physics.py       # Fixed-step gravity, AABB collision and triggers
  rendering.py     # Mesh, Material, Light, Camera, Sky and render settings
  systems.py       # Camera, movement and lighting systems
  renderer3d.py    # Software 3D viewport with sky, lights, shadows and grid
  editor.py        # English 3D editor, toolbar, outliner, details and content browser
  demo.py          # Hand-authored sample scene
  __main__.py      # Headless, editor and play entry points
cpp/               # Primary C++17 runtime, engine systems, CLI and tests
assets/            # Project assets
```

## Architecture

`Engine` owns one active `Scene`, an ordered list of systems, and a fixed-step accumulator. A frame is clamped to 250ms, simulation advances at 60Hz, and the accumulator is bounded by a maximum number of fixed steps to avoid a spiral of death. Variable-rate systems run once after fixed simulation. `EngineStats` exposes frame count, fixed-step count, dropped time, and the interpolation alpha used by renderers. Systems can be stopped safely when scenes switch.

`Scene` is the scene graph and entity registry. Entities have a stable integer id, a hierarchical `Transform`, a kind, and extensible component data. Parent cycles are rejected and world positions are resolved from the hierarchy. `SceneManager` registers named scenes and switches them through the engine lifecycle. `EventBus` decouples gameplay and tools. `ResourceManager` provides explicit loader registration and cached resources. `PhysicsSystem` uses a spatial-hash broad phase, deterministic AABB resolution, gravity, and collision/trigger enter/exit events.

The viewport is a software 3D pipeline designed to stay portable inside the packaged EXE. It renders a sky gradient with cloud bands, perspective grid, mesh faces, material color/roughness, directional light shading, and projected dynamic shadows. RMB orbits, MMB pans, the wheel zooms, and the editor toolbar switches Select/Move/Rotate/Scale modes. This is an intentionally inspectable foundation; a future GPU backend can implement the same renderer-facing components without changing scene files.

## Native runtime

```bash
cmake -S cpp -B build/native -DCMAKE_BUILD_TYPE=Release
cmake --build build/native --config Release
./build/native/KSA --seconds 2 --json
```

The native runtime owns the production engine path. The previous Python/Pygame editor remains as a development prototype until a C++ UI backend is selected; it is no longer used to build or package `KSA.exe`.

## Scene files

```python
from ksa_engine import load_scene, save_scene
from ksa_engine.demo import build_engine

engine = build_engine()
save_scene(engine.scene, "scene.json")
scene = load_scene("scene.json")
engine.load_scene(scene)
```

## Native tests

```bash
ctest --test-dir build/native --output-on-failure
```

## Independent download website

The website in `website/` does not depend on GitHub. Put `KSA.exe` in `website/downloads/` and serve it from your own VPS, object storage bucket, or hosting provider:

```bash
python website/server.py --host 0.0.0.0 --port 8080
```

The site is available at `/` and the direct installer path is `/downloads/KSA.exe`. See [website/README.md](website/README.md) for the production reverse-proxy setup. The binary is intentionally ignored by Git so it can be deployed independently from the source repository.

## Engineering position

This is a focused foundation, not a claim of being one of the world's top six engines. Reaching that level requires a long-term production roadmap: GPU-backed rendering, asset import pipelines, editor undo/redo, reflection and serialization schemas, profiling, platform packaging, networking, documentation, and a large test and tooling ecosystem. The rebuilt core establishes the boundaries needed to grow toward those goals without coupling the runtime to content generation.
