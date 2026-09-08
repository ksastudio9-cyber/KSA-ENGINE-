"""Portable JSON scene persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import Entity, Scene, Transform, Vector3


def save_scene(scene: Scene, path: str | Path) -> None:
    Path(path).write_text(json.dumps(scene.to_dict(), indent=2), encoding="utf-8")


def load_scene(path: str | Path) -> Scene:
    data: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    scene = Scene(str(data.get("name", "Untitled")), metadata=data.get("metadata", {}), next_entity_id=int(data.get("next_entity_id", 1)))
    for raw in data.get("entities", []):
        raw_transform = raw.get("transform", {})
        transform = Transform(
            position=Vector3(**raw_transform.get("position", {})),
            rotation=Vector3(**raw_transform.get("rotation", {})),
            scale=Vector3(**raw_transform.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0})),
            parent_id=raw_transform.get("parent_id"),
        )
        scene.entities[int(raw["id"])] = Entity(int(raw["id"]), str(raw["name"]), str(raw.get("kind", "entity")), transform, raw.get("components", {}), bool(raw.get("active", True)))
    scene.next_entity_id = max([scene.next_entity_id, *[entity_id + 1 for entity_id in scene.entities]], default=scene.next_entity_id)
    return scene
