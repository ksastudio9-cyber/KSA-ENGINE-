# KSA Engine Beta

KSA Engine Beta is a small, modular game runtime for developer-authored scenes. It has an English developer UI and deliberately contains no AI generation, text-to-world, narrative, or procedural content systems.

## Structure

```text
ksa_engine/
  core.py          # Engine loop, Scene, Entity, Transform, Vector3
  events.py        # EventBus and InputState
  resources.py     # Cached texture/model/audio loader registry
  scene_io.py      # JSON scene persistence
  physics.py       # Fixed-step gravity, AABB collision and triggers
  systems.py       # Camera, movement and lighting systems
  renderer3d.py    # Dependency-light 2.5D runtime renderer
  editor.py        # English viewport, outliner, details and content browser
  demo.py          # Hand-authored sample scene
  __main__.py      # Headless, editor and play entry points
cpp/               # Optional native C++ runtime target
assets/            # Project assets
```

## Architecture

`Engine` owns one active `Scene`, an ordered list of systems, and a fixed-step accumulator. A frame is clamped to 250ms, simulation advances at 60Hz, and the accumulator is bounded by a maximum number of fixed steps to avoid a spiral of death. Variable-rate systems run once after fixed simulation.

`Scene` is the scene graph and entity registry. Entities have a stable integer id, a hierarchical `Transform`, a kind, and extensible component data. `EventBus` decouples gameplay and tools. `ResourceManager` provides explicit loader registration and cached resources. `PhysicsSystem` operates on `PhysicsBody` components and publishes collision or trigger events.

## Run

```bash
python -m pip install -r requirements.txt
python -m ksa_engine --seconds 2 --json
python -m ksa_engine --editor
python -m ksa_engine --play
python -m ksa_engine --save scene.json
```

The editor uses English labels: `Viewport`, `Outliner`, `Details`, and `Content Browser`. Select entities in the outliner, move them with arrow keys, and save with `Ctrl+S`. The play view supports `WASD` movement and `Esc` exit.

## Scene files

```python
from ksa_engine import load_scene, save_scene
from ksa_engine.demo import build_engine

engine = build_engine()
save_scene(engine.scene, "scene.json")
scene = load_scene("scene.json")
engine.load_scene(scene)
```

## Native build

```bash
cmake -S cpp -B build/native -DCMAKE_BUILD_TYPE=Release
cmake --build build/native --config Release
ctest --test-dir build/native --output-on-failure
```

## Download website

The static download page lives in `website/index.html` and is deployed to GitHub Pages by `.github/workflows/deploy-website.yml`. Push a version tag such as `v0.1.0` to build Windows and publish `KSA.exe` to the GitHub Release. The website's download button then resolves to the latest release asset.

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Engineering position

This is a focused foundation, not a claim of being one of the world's top six engines. Reaching that level requires a long-term production roadmap: GPU-backed rendering, asset import pipelines, editor undo/redo, reflection and serialization schemas, profiling, platform packaging, networking, documentation, and a large test and tooling ecosystem. The rebuilt core establishes the boundaries needed to grow toward those goals without coupling the runtime to content generation.
