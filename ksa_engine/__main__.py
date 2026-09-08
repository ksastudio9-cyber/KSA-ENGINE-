from __future__ import annotations

import argparse
import json

from .demo import build_engine
from .scene_io import save_scene


def main() -> None:
    parser = argparse.ArgumentParser(description="KSA Engine developer runtime")
    parser.add_argument("--seconds", type=float, default=1.0, help="Headless simulation duration")
    parser.add_argument("--json", action="store_true", help="Print the runtime snapshot as JSON")
    parser.add_argument("--editor", action="store_true", help="Open the English scene editor")
    parser.add_argument("--play", action="store_true", help="Open the realtime renderer")
    parser.add_argument("--save", metavar="PATH", help="Save the demo scene to a JSON file")
    args = parser.parse_args()
    if args.seconds < 0:
        parser.error("--seconds must be non-negative")
    engine = build_engine()
    if args.save:
        save_scene(engine.scene, args.save)
    if args.editor:
        from .editor import run_editor
        run_editor(engine)
        return
    if args.play:
        from .renderer3d import run_game_3d
        run_game_3d(engine)
        return
    engine.run_for(args.seconds)
    scene = engine.scene
    assert scene is not None
    state = {"scene": scene.name, "entities": len(scene.entities), "elapsed_time": engine.elapsed_time, "fixed_timestep": engine.config.fixed_timestep}
    print(json.dumps(state, indent=2) if args.json else f"KSA Engine | {scene.name} | {len(scene.entities)} entities | {engine.elapsed_time:.3f}s")


if __name__ == "__main__":
    main()
