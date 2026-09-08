"""Deterministic, dependency-free 3D AABB physics for prototypes and tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .core import Engine, Entity, Vector3
from .events import EventBus


@dataclass
class PhysicsBody:
    velocity: Vector3 = Vector3()
    half_extents: Vector3 = Vector3(0.5, 0.5, 0.5)
    mass: float = 1.0
    use_gravity: bool = True
    is_static: bool = False
    is_trigger: bool = False


class PhysicsSystem:
    def __init__(self, gravity: Vector3 = Vector3(0.0, -9.81, 0.0), events: EventBus | None = None) -> None:
        self.gravity = gravity
        self.events = events or EventBus()
        self._overlaps: set[tuple[int, int]] = set()

    def on_start(self, engine: Engine) -> None:
        pass

    def on_update(self, engine: Engine, delta_time: float) -> None:
        self.events.flush()

    def on_fixed_update(self, engine: Engine, fixed_delta: float) -> None:
        assert engine.scene is not None
        bodies = [(entity, entity.get_component("physics")) for entity in engine.scene.find()]
        for entity, body in bodies:
            if not isinstance(body, PhysicsBody) or body.is_static:
                continue
            velocity = body.velocity + (self.gravity * fixed_delta if body.use_gravity else Vector3())
            entity.transform.position = entity.transform.position + velocity * fixed_delta
            body.velocity = velocity
            if entity.transform.position.y < 0.0:
                entity.transform.position = Vector3(entity.transform.position.x, 0.0, entity.transform.position.z)
                body.velocity = Vector3(velocity.x, 0.0, velocity.z)
        self._detect_overlaps(bodies)

    def _detect_overlaps(self, bodies: list[tuple[Entity, Any]]) -> None:
        current: set[tuple[int, int]] = set()
        for index, (left, left_body) in enumerate(bodies):
            if not isinstance(left_body, PhysicsBody):
                continue
            for right, right_body in bodies[index + 1:]:
                if not isinstance(right_body, PhysicsBody) or not self._intersects(left, left_body, right, right_body):
                    continue
                pair = tuple(sorted((left.id, right.id)))
                current.add(pair)
                if pair not in self._overlaps:
                    self.events.publish("trigger_enter" if left_body.is_trigger or right_body.is_trigger else "collision_enter", a=left.id, b=right.id)
        self._overlaps = current

    @staticmethod
    def _intersects(left: Entity, left_body: PhysicsBody, right: Entity, right_body: PhysicsBody) -> bool:
        delta = left.transform.position - right.transform.position
        extent = left_body.half_extents + right_body.half_extents
        return abs(delta.x) <= extent.x and abs(delta.y) <= extent.y and abs(delta.z) <= extent.z
