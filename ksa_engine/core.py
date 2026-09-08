"""The small, dependency-free runtime kernel for KSA Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
import math
from time import perf_counter
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

    def __truediv__(self, scalar: float) -> "Vector3":
        if scalar == 0.0:
            raise ZeroDivisionError("Cannot divide Vector3 by zero")
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalized(self) -> "Vector3":
        length = self.length()
        return self if length == 0.0 else self / length

    def dot(self, other: "Vector3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def lerp(self, other: "Vector3", amount: float) -> "Vector3":
        amount = max(0.0, min(1.0, amount))
        return self + (other - self) * amount


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

    def set_parent(self, entity_id: int, parent_id: int | None) -> None:
        entity = self.entity(entity_id)
        if entity is None:
            raise KeyError(f"Unknown entity id: {entity_id}")
        if parent_id == entity_id:
            raise ValueError("An entity cannot parent itself")
        ancestor = parent_id
        while ancestor is not None:
            if ancestor == entity_id:
                raise ValueError("Transform hierarchy cannot contain cycles")
            parent = self.entity(ancestor)
            ancestor = parent.transform.parent_id if parent else None
        entity.transform.parent_id = parent_id

    def world_position(self, entity_id: int) -> Vector3:
        entity = self.entity(entity_id)
        if entity is None:
            raise KeyError(f"Unknown entity id: {entity_id}")
        position = entity.transform.position
        parent_id = entity.transform.parent_id
        visited: set[int] = set()
        while parent_id is not None:
            if parent_id in visited:
                raise ValueError("Transform hierarchy contains a cycle")
            visited.add(parent_id)
            parent = self.entity(parent_id)
            if parent is None:
                break
            position = position + parent.transform.position
            parent_id = parent.transform.parent_id
        return position

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


@dataclass
class EngineStats:
    frame_count: int = 0
    fixed_step_count: int = 0
    dropped_time: float = 0.0
    last_frame_time: float = 0.0
    last_fixed_steps: int = 0


class Engine:
    def __init__(self, config: EngineConfig | None = None) -> None:
        self.config = config or EngineConfig()
        self.scene: Scene | None = None
        self.world: Scene | None = None
        self.systems: list[System] = []
        self.running = False
        self.elapsed_time = 0.0
        self._accumulator = 0.0
        self.stats = EngineStats()
        self.paused = False
        self.scene_manager = SceneManager(self)

    @property
    def interpolation_alpha(self) -> float:
        return self._accumulator / self.config.fixed_timestep

    def add_system(self, system: System) -> None:
        self.systems.append(system)
        if self.scene is not None:
            system.on_start(self)

    def remove_system(self, system: System) -> None:
        if system in self.systems:
            stop = getattr(system, "on_stop", None)
            if stop:
                stop(self)
            self.systems.remove(system)

    def load_scene(self, scene: Scene) -> None:
        previous_scene = self.scene
        if previous_scene is not None:
            for system in self.systems:
                stop = getattr(system, "on_stop", None)
                if stop:
                    stop(self)
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
        started_at = perf_counter()
        frame_delta = max(0.0, min(float(delta_time), self.config.max_frame_delta))
        if self.paused:
            self.stats.frame_count += 1
            self.stats.last_frame_time = perf_counter() - started_at
            return
        self._accumulator += frame_delta
        steps = 0
        epsilon = 1e-12
        while self._accumulator + epsilon >= self.config.fixed_timestep and steps < self.config.max_fixed_steps:
            for system in self.systems:
                fixed_update = getattr(system, "on_fixed_update", None)
                if fixed_update:
                    fixed_update(self, self.config.fixed_timestep)
            self._accumulator -= self.config.fixed_timestep
            if abs(self._accumulator) < epsilon:
                self._accumulator = 0.0
            self.elapsed_time += self.config.fixed_timestep
            self.stats.fixed_step_count += 1
            steps += 1
        if self._accumulator >= self.config.fixed_timestep:
            dropped = self._accumulator - (self._accumulator % self.config.fixed_timestep)
            self._accumulator %= self.config.fixed_timestep
            self.stats.dropped_time += dropped
        for system in self.systems:
            update = getattr(system, "on_update", None)
            if update:
                update(self, frame_delta)
        self.stats.frame_count += 1
        self.stats.last_fixed_steps = steps
        self.stats.last_frame_time = perf_counter() - started_at

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


class SceneManager:
    """Named scene registry with deterministic runtime scene switching."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._scenes: dict[str, Scene] = {}

    def register(self, scene: Scene) -> Scene:
        self._scenes[scene.name] = scene
        return scene

    def get(self, name: str) -> Scene | None:
        return self._scenes.get(name)

    def switch(self, name: str) -> Scene:
        scene = self.get(name)
        if scene is None:
            raise KeyError(f"Scene is not registered: {name}")
        self.engine.load_scene(scene)
        return scene

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._scenes)
