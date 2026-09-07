from __future__ import annotations

import argparse
import json

from .demo import build_engine
from .systems import NarrativeSystem


def main() -> None:
    parser = argparse.ArgumentParser(description="KSA ENGINE text-to-world runtime")
    parser.add_argument(
        "description",
        nargs="?",
        default="مدينة صحراوية ليلية فيها واحة ومعركة",
        help="وصف العالم بالعربية أو الإنجليزية",
    )
    parser.add_argument("--seconds", type=float, default=1.0, help="مدة التشغيل")
    parser.add_argument("--seed", type=int, default=None, help="بذرة التوليد")
    parser.add_argument("--json", action="store_true", help="إخراج الحالة بصيغة JSON")
    parser.add_argument("--play", action="store_true", help="فتح نافذة لعب تفاعلية")
    parser.add_argument("--editor", action="store_true", help="فتح محرر صناعة الألعاب")
    parser.add_argument("--say", default=None, help="كلام اللاعب للحصول على رد سردي")
    args = parser.parse_args()

    if args.seconds < 0:
        parser.error("--seconds يجب أن يكون غير سالب")

    if args.play:
        from .renderer3d import run_game_3d

        run_game_3d(build_engine(args.description, args.seed))
        return
    if args.editor:
        from .editor import run_editor

        run_editor(args.description)
        return

    engine = build_engine(args.description, args.seed)
    engine.run_for(args.seconds)
    world = engine.world
    assert world is not None
    state = {
        "name": world.name,
        "seed": world.seed,
        "entities": len(world.entities),
        "elapsed_time": world.elapsed_time,
        "terrain": world.metadata.get("terrain"),
        "time_of_day": world.metadata.get("time_of_day"),
    }
    if args.json:
        if args.say:
            narrative_system = next(system for system in engine.systems if isinstance(system, NarrativeSystem))
            state["response"] = narrative_system.say(world, args.say)
        print(json.dumps(state, ensure_ascii=False, indent=2))
    else:
        print(f"KSA ENGINE | {state['name']}")
        print(f"entities={state['entities']} time={state['elapsed_time']:.3f}s seed={state['seed']}")
        print(f"terrain={state['terrain']} time_of_day={state['time_of_day']}")
        if args.say:
            narrative_system = next(system for system in engine.systems if isinstance(system, NarrativeSystem))
            print(f"العالم: {narrative_system.say(world, args.say)}")


if __name__ == "__main__":
    main()