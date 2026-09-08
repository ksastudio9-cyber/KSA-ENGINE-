"""Portable JSON scene persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import Entity, Scene, Transform, Vector3
from .physics import PhysicsBody
from .rendering import CameraComponent, Light, Material, Mesh, RenderSettings, SkySettings


def save_scene(scene: Scene, path: str | Path) -> None:
    Path(path).write_text(json.dumps(scene.to_dict(), indent=2), encoding="utf-8")


def load_scene(path: str | Path) -> Scene:
    data: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    metadata = dict(data.get("metadata", {}))
    if isinstance(metadata.get("render_settings"), dict):
        metadata["render_settings"] = RenderSettings(**metadata["render_settings"])
    if isinstance(metadata.get("sky"), dict):
        metadata["sky"] = SkySettings(**metadata["sky"])
    scene = Scene(str(data.get("name", "Untitled")), metadata=metadata, next_entity_id=int(data.get("next_entity_id", 1)))
    for raw in data.get("entities", []):
        raw_transform = raw.get("transform", {})
        transform = Transform(
            position=Vector3(**raw_transform.get("position", {})),
            rotation=Vector3(**raw_transform.get("rotation", {})),
            scale=Vector3(**raw_transform.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0})),
            parent_id=raw_transform.get("parent_id"),
        )
        components = {name: _decode_component(name, value) for name, value in raw.get("components", {}).items()}
        scene.entities[int(raw["id"])] = Entity(int(raw["id"]), str(raw["name"]), str(raw.get("kind", "entity")), transform, components, bool(raw.get("active", True)))
    scene.next_entity_id = max([scene.next_entity_id, *[entity_id + 1 for entity_id in scene.entities]], default=scene.next_entity_id)
    return scene


def _decode_component(name: str, value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    if name == "physics":
        value = dict(value)
        value["velocity"] = Vector3(**value.get("velocity", {}))
        value["half_extents"] = Vector3(**value.get("half_extents", {}))
        return PhysicsBody(**value)
    if name == "material":
        return Material(**value)
    if name == "light":
        value = dict(value)
        value["direction"] = Vector3(**value.get("direction", {}))
        return Light(**value)
    if name == "camera":
        return CameraComponent(**value)
    if name == "render_settings":
        return RenderSettings(**value)
    if name == "sky":
        return SkySettings(**value)
    if name == "mesh":
        vertices = [Vector3(**vertex) for vertex in value.get("vertices", [])]
        faces = [tuple(face) for face in value.get("faces", [])]
        return Mesh(str(value.get("name", "Mesh")), vertices, faces)
    return value
