"""Built-in runtime systems that do not depend on content generation."""

from __future__ import annotations

from dataclasses import dataclass
import math

from .core import Engine, Vector3
from .events import InputState


@dataclass
class Camera:
    fov: float = 60.0
    near: float = 0.1
    far: float = 1000.0
    position: Vector3 = Vector3(0.0, 3.0, 8.0)
    target: Vector3 = Vector3()
    smoothing: float = 8.0


class CameraSystem:
    def __init__(self, entity_id: int | None = None, camera: Camera | None = None) -> None:
        self.entity_id = entity_id
        self.camera = camera or Camera()

    def on_start(self, engine: Engine) -> None:
        if self.entity_id is None and engine.scene:
            cameras = engine.scene.find("camera")
            self.entity_id = cameras[0].id if cameras else None

    def on_update(self, engine: Engine, delta_time: float) -> None:
        if self.entity_id is None or engine.scene is None:
            return
        entity = engine.scene.entity(self.entity_id)
        if entity is None:
            return
        target_id = entity.get_component("target_id")
        target = engine.scene.entity(target_id) if target_id else None
        if target is None:
            return
        blend = 1.0 - math.exp(-self.camera.smoothing * delta_time)
        target_position = target.transform.position + Vector3(0.0, 2.0, 5.0)
        position = entity.transform.position
        entity.transform.position = position + (target_position - position) * blend
        self.camera.position = entity.transform.position
        self.camera.target = target.transform.position


class InputMovementSystem:
    def __init__(self, input_state: InputState, speed: float = 5.0) -> None:
        self.input = input_state
        self.speed = speed

    def on_start(self, engine: Engine) -> None:
        pass

    def on_update(self, engine: Engine, delta_time: float) -> None:
        if engine.scene is None:
            return
        players = engine.scene.find("player")
        if not players:
            return
        x = float(self.input.is_down("right")) - float(self.input.is_down("left"))
        z = float(self.input.is_down("back")) - float(self.input.is_down("forward"))
        length = math.hypot(x, z)
        if length:
            player = players[0]
            player.transform.position = player.transform.position + Vector3(x / length, 0.0, z / length) * (self.speed * delta_time)


class LightingSystem:
    def __init__(self, ambient: float = 0.35, directional: Vector3 = Vector3(-0.4, -1.0, -0.3)) -> None:
        self.ambient = max(0.0, min(1.0, ambient))
        self.directional = directional

    def on_start(self, engine: Engine) -> None:
        pass

    def on_update(self, engine: Engine, delta_time: float) -> None:
        pass
