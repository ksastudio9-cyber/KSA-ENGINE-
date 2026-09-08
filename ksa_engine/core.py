"""The small, dependency-free runtime kernel for KSA Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vector3":
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)


@dataclass
class Transform:
    position: Vector3 = field(default_factory=Vector3)
    rotation: Vector3 = field(default_factory=Vector3)
    scale: Vector3 = field(default_factory=lambda: Vector3(1.0, 1.0, 1.0))
    parent_id: int | None = None


@dataclass
class Entity:
    id: int
    name: str
    kind: str = "entity"
    transform: Transform = field(default_factory=Transform)
    components: dict[str, Any] = field(default_factory=dict)
    active: bool = True

    def add_component(self, name: str, value: Any) -> Any:
        self.components[name] = value
        return value

    def get_component(self, name: str, default: Any = None) -> Any:
        return self.components.get(name, default)


@dataclass
class Scene:
    name: str = "Untitled"
    entities: dict[int, Entity] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    next_entity_id: int = 1

    def create_entity(self, name: str, kind: str = "entity", transform: Transform | None = None, **components: Any) -> Entity:
        entity = Entity(self.next_entity_id, name, kind, transform or Transform(), components)
        self.entities[entity.id] = entity
        self.next_entity_id += 1
        return entity

    def destroy_entity(self, entity_id: int) -> None:
        self.entities.pop(entity_id, None)
        for entity in self.entities.values():
            if entity.transform.parent_id == entity_id:
                entity.transform.parent_id = None

    def find(self, kind: str | None = None) -> list[Entity]:
        return [entity for entity in self.entities.values() if entity.active and (kind is None or entity.kind == kind)]

    def entity(self, entity_id: int) -> Entity | None:
        return self.entities.get(entity_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "metadata": self.metadata,
            "next_entity_id": self.next_entity_id,
            "entities": [
                {"id": entity.id, "name": entity.name, "kind": entity.kind, "active": entity.active,
                 "transform": asdict(entity.transform), "components": _json_value(entity.components)}
                for entity in self.entities.values()
            ],
        }


def _json_value(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _json_value(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


GameWorld = Scene


class System(Protocol):
    def on_start(self, engine: "Engine") -> None: ...
    def on_update(self, engine: "Engine", delta_time: float) -> None: ...
    def on_fixed_update(self, engine: "Engine", fixed_delta: float) -> None: ...


@dataclass(frozen=True)
class EngineConfig:
    fixed_timestep: float = 1.0 / 60.0
    max_frame_delta: float = 0.25
    max_fixed_steps: int = 8


class Engine:
    def __init__(self, config: EngineConfig | None = None) -> None:
        self.config = config or EngineConfig()
        self.scene: Scene | None = None
        self.world: Scene | None = None
        self.systems: list[System] = []
        self.running = False
        self.elapsed_time = 0.0
        self._accumulator = 0.0

    def add_system(self, system: System) -> None:
        self.systems.append(system)
        if self.scene is not None:
            system.on_start(self)

    def load_scene(self, scene: Scene) -> None:
        self.scene = scene
        self.world = scene
        self.elapsed_time = 0.0
        self._accumulator = 0.0
        for system in self.systems:
            system.on_start(self)

    def load_world(self, world: Scene) -> None:
        self.load_scene(world)

    def update(self, delta_time: float) -> None:
        if self.scene is None:
            raise RuntimeError("No scene is loaded")
        frame_delta = max(0.0, min(float(delta_time), self.config.max_frame_delta))
        self._accumulator += frame_delta
        steps = 0
        while self._accumulator >= self.config.fixed_timestep and steps < self.config.max_fixed_steps:
            for system in self.systems:
                fixed_update = getattr(system, "on_fixed_update", None)
                if fixed_update:
                    fixed_update(self, self.config.fixed_timestep)
            self._accumulator -= self.config.fixed_timestep
            self.elapsed_time += self.config.fixed_timestep
            steps += 1
        for system in self.systems:
            update = getattr(system, "on_update", None)
            if update:
                update(self, frame_delta)

    def run_for(self, duration: float) -> None:
        if duration < 0:
            raise ValueError("duration must be non-negative")
        self.running = True
        elapsed = 0.0
        while elapsed < duration:
            delta = min(self.config.fixed_timestep, duration - elapsed)
            self.update(delta)
            elapsed += delta
        self.running = False
