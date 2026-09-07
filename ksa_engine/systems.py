from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .core import Entity, GameWorld, Vector3
from .llm import LLMNarrativeAI
from .narrative import NarrativeAI


class WorldSystem:
    def start(self, world: GameWorld) -> None:
        pass

    def update(self, world: GameWorld, delta_time: float) -> None:
        pass


@dataclass
class CameraController(WorldSystem):
    entity_id: int | None = None
    target_entity_id: int | None = None
    follow_distance: float = 12.0
    height: float = 7.0

    def start(self, world: GameWorld) -> None:
        if self.entity_id is None:
            cameras = world.find_by_kind("camera")
            self.entity_id = cameras[0].id if cameras else None
        if self.target_entity_id is None and self.entity_id is not None:
            camera = world.entities.get(self.entity_id)
            self.target_entity_id = camera.components.get("target_id") if camera else None
        if self.target_entity_id is None:
            characters = world.find_by_kind("character")
            self.target_entity_id = characters[0].id if characters else None

    def update(self, world: GameWorld, delta_time: float) -> None:
        if self.entity_id is None or self.target_entity_id is None:
            return
        camera = world.entities.get(self.entity_id)
        target = world.entities.get(self.target_entity_id)
        if camera is None or target is None:
            return
        target_position = target.transform.position
        camera.transform.position = Vector3(
            target_position.x - self.follow_distance,
            target_position.y + self.height,
            target_position.z,
        )


@dataclass
class LightingSystem(WorldSystem):
    exposure: float = 1.0
    active_lights: list[dict[str, Any]] = field(default_factory=list)

    def start(self, world: GameWorld) -> None:
        self.active_lights = [entity.components for entity in world.find_by_kind("light")]

    def update(self, world: GameWorld, delta_time: float) -> None:
        for light in self.active_lights:
            light["intensity"] = max(0.0, float(light.get("intensity", 1.0)))


@dataclass
class AudioSystem(WorldSystem):
    events: list[dict[str, Any]] = field(default_factory=list)
    ambience: str = "silence"

    def start(self, world: GameWorld) -> None:
        self.ambience = world.metadata.get("audio", {}).get("ambience", "silence")

    def play(self, event: str, entity_id: int | None = None) -> None:
        self.events.append({"event": event, "entity_id": entity_id})

    def update(self, world: GameWorld, delta_time: float) -> None:
        world.metadata.setdefault("audio", {})["last_update"] = world.elapsed_time


@dataclass
class NarrativeSystem(WorldSystem):
    director: Any = field(default_factory=lambda: LLMNarrativeAI.from_environment() or NarrativeAI())

    def start(self, world: GameWorld) -> None:
        world.metadata.setdefault("narrative", {})["ai_provider"] = type(self.director).__name__

    def say(self, world: GameWorld, player_text: str) -> str:
        if not player_text.strip():
            raise ValueError("كلام اللاعب لا يمكن أن يكون فارغًا")
        response = self.director.respond(world.metadata, player_text)
        for action in getattr(self.director, "consume_actions", lambda: [])():
            self._apply_action(world, action)
        history = world.metadata.setdefault("narrative", {}).setdefault("dialogue_history", [])
        history.append({"player": player_text, "speaker": "world", "text": response})
        return response

    @staticmethod
    def _apply_action(world: GameWorld, action: dict[str, Any]) -> None:
        if action.get("action") == "set_objective":
            world.metadata.setdefault("narrative", {})["objective"] = str(action.get("objective", ""))[:240]
        elif action.get("action") == "spawn_entity" and action.get("name"):
            world.create_entity(
                str(action["name"])[:80],
                str(action.get("kind", "npc"))[:40],
                role=str(action.get("role", "generated_npc"))[:80],
                dialogue=[str(action.get("dialogue", ""))[:240]],
            )


@dataclass
class AnimationSystem(WorldSystem):
    clips: dict[str, float] = field(default_factory=lambda: {"idle": 0.0, "walk": 1.0, "run": 1.5, "combat": 1.0})

    def update(self, world: GameWorld, delta_time: float) -> None:
        for entity in world.find_by_kind("character"):
            animation = entity.components.setdefault("animation", {"clip": "idle", "time": 0.0})
            animation["time"] += delta_time * self.clips.get(animation["clip"], 1.0)


@dataclass
class SceneComposer(WorldSystem):
    def start(self, world: GameWorld) -> None:
        composition = world.metadata.setdefault("composition", {})
        composition["entity_count"] = len(world.entities)
        composition["camera_id"] = next((entity.id for entity in world.find_by_kind("camera")), None)
        composition["focus_entity_id"] = next((entity.id for entity in world.find_by_kind("character")), None)

    def update(self, world: GameWorld, delta_time: float) -> None:
        world.metadata.setdefault("composition", {})["entity_count"] = len(world.entities)
