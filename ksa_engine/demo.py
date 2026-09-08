"""A hand-authored sample scene used by the editor and runtime demo."""

from . import CameraComponent, CameraSystem, Engine, Light, LightingSystem, Material, Mesh, PhysicsBody, PhysicsSystem, RenderSettings, Scene, SkySettings, Transform, Vector3


def create_demo_scene() -> Scene:
    scene = Scene("KSA Sandbox", metadata={"render_settings": RenderSettings(), "sky": SkySettings()})
    player = scene.create_entity("Player", "player", Transform(Vector3(0.0, 1.0, 0.0), scale=Vector3(0.45, 1.0, 0.45)), physics=PhysicsBody(half_extents=Vector3(0.45, 1.0, 0.45)), mesh=Mesh.cube(), material=Material((225, 180, 72), roughness=0.55))
    scene.create_entity("Camera", "camera", Transform(Vector3(0.0, 3.0, 7.0)), target_id=player.id, camera=CameraComponent())
    scene.create_entity("Directional Sun", "light", light=Light(intensity=1.0, direction=Vector3(-0.4, -1.0, -0.2)))
    scene.create_entity("Ground", "static", Transform(Vector3(0.0, -0.5, 0.0)), physics=PhysicsBody(half_extents=Vector3(20.0, 0.5, 20.0), use_gravity=False, is_static=True))
    for index, position in enumerate((Vector3(-3, 0, -2), Vector3(3, 0, -4), Vector3(0, 0, -7))):
        scene.create_entity(f"Crate {index + 1}", "mesh", Transform(position, scale=Vector3(0.75, 0.75, 0.75)), physics=PhysicsBody(half_extents=Vector3(0.75, 0.75, 0.75), use_gravity=False, is_static=True), mesh=Mesh.cube(), material=Material((170, 110, 65), roughness=0.8))
    return scene


def build_engine() -> Engine:
    engine = Engine()
    engine.add_system(PhysicsSystem())
    engine.add_system(CameraSystem())
    engine.add_system(LightingSystem())
    engine.load_scene(create_demo_scene())
    return engine
