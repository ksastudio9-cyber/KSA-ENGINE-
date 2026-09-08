"""A hand-authored sample scene used by the editor and runtime demo."""

from . import CameraSystem, Engine, LightingSystem, PhysicsBody, PhysicsSystem, Scene, Transform, Vector3


def create_demo_scene() -> Scene:
    scene = Scene("KSA Sandbox")
    player = scene.create_entity("Player", "player", Transform(Vector3(0.0, 1.0, 0.0)), physics=PhysicsBody(half_extents=Vector3(0.45, 1.0, 0.45)))
    scene.create_entity("Camera", "camera", Transform(Vector3(0.0, 3.0, 7.0)), target_id=player.id)
    scene.create_entity("Directional Light", "light", intensity=1.0, direction=Vector3(-0.4, -1.0, -0.2))
    scene.create_entity("Ground", "static", Transform(Vector3(0.0, -0.5, 0.0)), physics=PhysicsBody(half_extents=Vector3(20.0, 0.5, 20.0), use_gravity=False, is_static=True))
    for index, position in enumerate((Vector3(-3, 0, -2), Vector3(3, 0, -4), Vector3(0, 0, -7))):
        scene.create_entity(f"Crate {index + 1}", "mesh", Transform(position), physics=PhysicsBody(half_extents=Vector3(0.75, 0.75, 0.75), use_gravity=False, is_static=True), material={"color": (170, 110, 65)})
    return scene


def build_engine() -> Engine:
    engine = Engine()
    engine.add_system(PhysicsSystem())
    engine.add_system(CameraSystem())
    engine.add_system(LightingSystem())
    engine.load_scene(create_demo_scene())
    return engine
