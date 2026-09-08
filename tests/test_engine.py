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
    assert player.transform.position.y == 0.0

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
