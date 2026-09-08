"""Deterministic, dependency-free 3D AABB physics for prototypes and tools."""

from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
import math
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
        self._trigger_pairs: set[tuple[int, int]] = set()
        self.candidate_pairs = 0

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
            floor_height = body.half_extents.y
            if entity.transform.position.y < floor_height:
                entity.transform.position = Vector3(entity.transform.position.x, floor_height, entity.transform.position.z)
                body.velocity = Vector3(velocity.x, 0.0, velocity.z)
        self._detect_overlaps(bodies)

    def _detect_overlaps(self, bodies: list[tuple[Entity, Any]]) -> None:
        grid: dict[tuple[int, int, int], list[tuple[Entity, PhysicsBody]]] = defaultdict(list)
        cell_size = 4.0
        for entity, body in bodies:
            if not isinstance(body, PhysicsBody):
                continue
            position = entity.transform.position
            radius = body.half_extents
            minimum = Vector3(position.x - radius.x, position.y - radius.y, position.z - radius.z)
            maximum = Vector3(position.x + radius.x, position.y + radius.y, position.z + radius.z)
            for x in range(math.floor(minimum.x / cell_size), math.floor(maximum.x / cell_size) + 1):
                for y in range(math.floor(minimum.y / cell_size), math.floor(maximum.y / cell_size) + 1):
                    for z in range(math.floor(minimum.z / cell_size), math.floor(maximum.z / cell_size) + 1):
                        grid[(x, y, z)].append((entity, body))

        current: set[tuple[int, int]] = set()
        candidates: set[tuple[int, int]] = set()
        indexed_bodies = {entity.id: (entity, body) for entity, body in bodies if isinstance(body, PhysicsBody)}
        for occupants in grid.values():
            for index, (left, _) in enumerate(occupants):
                for right, _ in occupants[index + 1:]:
                    if left.id != right.id:
                        candidates.add(tuple(sorted((left.id, right.id))))
        self.candidate_pairs = len(candidates)
        for left_id, right_id in candidates:
            left, left_body = indexed_bodies[left_id]
            right, right_body = indexed_bodies[right_id]
            if not self._intersects(left, left_body, right, right_body):
                continue
            pair = (left_id, right_id)
            current.add(pair)
            is_trigger = left_body.is_trigger or right_body.is_trigger
            if not is_trigger:
                self._resolve_overlap(left, left_body, right, right_body)
            if pair not in self._overlaps:
                self.events.publish("trigger_enter" if is_trigger else "collision_enter", a=left.id, b=right.id)
                if is_trigger:
                    self._trigger_pairs.add(pair)
        for pair in self._overlaps - current:
            event_name = "trigger_exit" if pair in self._trigger_pairs else "collision_exit"
            self.events.publish(event_name, a=pair[0], b=pair[1])
            self._trigger_pairs.discard(pair)
        self._overlaps = current

    @staticmethod
    def _intersects(left: Entity, left_body: PhysicsBody, right: Entity, right_body: PhysicsBody) -> bool:
        delta = left.transform.position - right.transform.position
        extent = left_body.half_extents + right_body.half_extents
        return abs(delta.x) <= extent.x and abs(delta.y) <= extent.y and abs(delta.z) <= extent.z

    @staticmethod
    def _resolve_overlap(left: Entity, left_body: PhysicsBody, right: Entity, right_body: PhysicsBody) -> None:
        if left_body.is_static and right_body.is_static:
            return
        delta = left.transform.position - right.transform.position
        extent = left_body.half_extents + right_body.half_extents
        penetration = Vector3(extent.x - abs(delta.x), extent.y - abs(delta.y), extent.z - abs(delta.z))
        axis = min((penetration.x, "x"), (penetration.y, "y"), (penetration.z, "z"))[1]
        direction = 1.0 if getattr(delta, axis) >= 0.0 else -1.0
        correction = getattr(penetration, axis) * direction
        if left_body.is_static:
            right.transform.position = PhysicsSystem._offset(right.transform.position, axis, -correction)
            right_body.velocity = PhysicsSystem._zero_axis(right_body.velocity, axis)
        elif right_body.is_static:
            left.transform.position = PhysicsSystem._offset(left.transform.position, axis, correction)
            left_body.velocity = PhysicsSystem._zero_axis(left_body.velocity, axis)
        else:
            half = correction * 0.5
            left.transform.position = PhysicsSystem._offset(left.transform.position, axis, half)
            right.transform.position = PhysicsSystem._offset(right.transform.position, axis, -half)

    @staticmethod
    def _offset(value: Vector3, axis: str, amount: float) -> Vector3:
        return Vector3(value.x + amount if axis == "x" else value.x, value.y + amount if axis == "y" else value.y, value.z + amount if axis == "z" else value.z)

    @staticmethod
    def _zero_axis(value: Vector3, axis: str) -> Vector3:
        return Vector3(0.0 if axis == "x" else value.x, 0.0 if axis == "y" else value.y, 0.0 if axis == "z" else value.z)
