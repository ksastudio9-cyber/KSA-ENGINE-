import tempfile
from pathlib import Path

from ksa_engine import Engine, PhysicsBody, PhysicsSystem, Scene, Transform, Vector3, load_scene, save_scene
from ksa_engine.events import EventBus


def test_fixed_timestep_and_scene_entities():
    scene = Scene("Test Scene")
    entity = scene.create_entity("Player", "player", Transform(Vector3(1, 2, 3)))
    calls = []

    class System:
        def on_start(self, engine):
            calls.append("start")

        def on_fixed_update(self, engine, delta):
            calls.append("fixed")

        def on_update(self, engine, delta):
            calls.append("frame")

    engine = Engine()
    engine.add_system(System())
    engine.load_scene(scene)
    engine.update(1 / 30)

    assert entity.id == 1
    assert calls == ["start", "fixed", "fixed", "frame"]
    assert engine.elapsed_time == 2 / 60


def test_physics_gravity_and_scene_round_trip():
    scene = Scene("Physics")
    player = scene.create_entity("Player", "player", Transform(Vector3(0, 2, 0)), physics=PhysicsBody())
    engine = Engine()
    engine.add_system(PhysicsSystem())
    engine.load_scene(scene)
    engine.run_for(1.0)
    assert player.transform.position.y == player.get_component("physics").half_extents.y

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "scene.json"
        save_scene(scene, path)
        restored = load_scene(path)
        assert restored.name == "Physics"
        assert restored.entity(player.id).name == "Player"


def test_event_bus_dispatches_queued_events():
    events = EventBus()
    received = []
    events.subscribe("hit", lambda event: received.append(event.payload["damage"]))
    events.publish("hit", damage=12)
    assert received == []
    events.flush()
    assert received == [12]


def test_transform_hierarchy_rejects_cycles():
    scene = Scene("Hierarchy")
    parent = scene.create_entity("Parent", transform=Transform(Vector3(10, 0, 2)))
    child = scene.create_entity("Child", transform=Transform(Vector3(1, 3, 4)))
    scene.set_parent(child.id, parent.id)
    assert scene.world_position(child.id) == Vector3(11, 3, 6)
    try:
        scene.set_parent(parent.id, child.id)
    except ValueError:
        pass
    else:
        raise AssertionError("transform hierarchy accepted a cycle")


def test_scene_manager_switches_registered_scenes():
    first = Scene("First")
    second = Scene("Second")
    engine = Engine()
    engine.scene_manager.register(first)
    engine.scene_manager.register(second)
    engine.scene_manager.switch("First")
    engine.scene_manager.switch("Second")
    assert engine.scene is second
    assert engine.scene_manager.names == ("First", "Second")


def test_physics_broad_phase_resolves_static_body():
    scene = Scene("Collision")
    scene.create_entity("Wall", "static", Transform(Vector3(0, 1, 0)), physics=PhysicsBody(half_extents=Vector3(1, 1, 1), use_gravity=False, is_static=True))
    player = scene.create_entity("Player", "player", Transform(Vector3(0, 3, 0)), physics=PhysicsBody(half_extents=Vector3(0.5, 0.5, 0.5)))
    physics = PhysicsSystem()
    engine = Engine()
    engine.add_system(physics)
    engine.load_scene(scene)
    engine.run_for(1.0)
    assert player.transform.position.y >= 1.5
    assert physics.candidate_pairs >= 1
