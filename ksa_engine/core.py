from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Transform:
    position: Vector3 = field(default_factory=Vector3)
    rotation: Vector3 = field(default_factory=Vector3)
    scale: Vector3 = field(default_factory=lambda: Vector3(1.0, 1.0, 1.0))


@dataclass
class Entity:
    id: int
    name: str
    kind: str
    transform: Transform = field(default_factory=Transform)
    components: dict[str, Any] = field(default_factory=dict)
    active: bool = True


@dataclass
class GameWorld:
    name: str
    seed: int
    entities: dict[int, Entity] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    elapsed_time: float = 0.0
    next_entity_id: int = 1

    def create_entity(self, name: str, kind: str, transform: Transform | None = None, **components: Any) -> Entity:
        entity = Entity(self.next_entity_id, name, kind, transform or Transform(), components)
        self.entities[entity.id] = entity
        self.next_entity_id += 1
        return entity

    def find_by_kind(self, kind: str) -> list[Entity]:
        return [entity for entity in self.entities.values() if entity.kind == kind and entity.active]


@dataclass(frozen=True)
class EngineConfig:
    fixed_timestep: float = 1.0 / 60.0
    max_frame_delta: float = 0.25


class Engine:
    def __init__(self, config: EngineConfig | None = None) -> None:
        self.config = config or EngineConfig()
        self.world: GameWorld | None = None
        self.systems: list[Any] = []
        self.running = False

    def load_world(self, world: GameWorld) -> None:
        self.world = world
        for system in self.systems:
            system.start(world)

    def add_system(self, system: Any) -> None:
        self.systems.append(system)
        if self.world is not None:
            system.start(self.world)

    def update(self, delta_time: float) -> None:
        if self.world is None:
            raise RuntimeError("لا يوجد عالم محمّل في المحرك")
        delta_time = max(0.0, min(delta_time, self.config.max_frame_delta))
        self.world.elapsed_time += delta_time
        for system in self.systems:
            system.update(self.world, delta_time)

    def run_for(self, duration: float) -> None:
        if duration < 0:
            raise ValueError("duration must be non-negative")
        self.running = True
        remaining = duration
        while remaining > 0:
            step = min(self.config.fixed_timestep, remaining)
            self.update(step)
            remaining -= step
        self.running = False