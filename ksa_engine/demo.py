from .core import Engine
from .systems import AnimationSystem, AudioSystem, CameraController, LightingSystem, NarrativeSystem, SceneComposer
from .text_to_world import TextToWorldGenerator


def build_engine(description: str, seed: int | None = None) -> Engine:
    world = TextToWorldGenerator().generate(description, seed)
    engine = Engine()
    camera = world.find_by_kind("camera")[0]
    character = world.find_by_kind("character")[0]
    engine.add_system(CameraController(camera.id, character.id))
    engine.add_system(SceneComposer())
    engine.add_system(LightingSystem())
    engine.add_system(AudioSystem())
    engine.add_system(NarrativeSystem())
    engine.add_system(AnimationSystem())
    engine.load_world(world)
    return engine


if __name__ == "__main__":
    engine = build_engine("مدينة صحراوية ليلية فيها واحة ومعركة")
    engine.run_for(1.0)
    print(f"Generated {len(engine.world.entities)} entities in {engine.world.elapsed_time:.2f}s")