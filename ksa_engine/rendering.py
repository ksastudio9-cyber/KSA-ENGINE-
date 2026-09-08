"""Renderer-facing components and mesh primitives for authored scenes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from .core import Vector3

Color = tuple[int, int, int]


@dataclass
class Material:
    color: Color = (160, 175, 190)
    roughness: float = 0.7
    metallic: float = 0.0
    texture_path: str | None = None


@dataclass
class Mesh:
    name: str = "Cube"
    vertices: list[Vector3] = field(default_factory=list)
    faces: list[tuple[int, ...]] = field(default_factory=list)

    @classmethod
    def cube(cls, name: str = "Cube") -> "Mesh":
        vertices = [
            Vector3(-1, -1, -1), Vector3(1, -1, -1), Vector3(1, -1, 1), Vector3(-1, -1, 1),
            Vector3(-1, 1, -1), Vector3(1, 1, -1), Vector3(1, 1, 1), Vector3(-1, 1, 1),
        ]
        faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)]
        return cls(name, vertices, faces)


@dataclass
class Light:
    kind: str = "directional"
    color: Color = (255, 244, 220)
    intensity: float = 1.0
    direction: Vector3 = Vector3(-0.45, -1.0, -0.35)
    cast_shadows: bool = True


@dataclass
class CameraComponent:
    fov: float = 60.0
    near: float = 0.1
    far: float = 1000.0
    exposure: float = 1.0
    orbit_distance: float = 8.0


@dataclass
class SkySettings:
    top_color: Color = (72, 132, 192)
    horizon_color: Color = (188, 216, 226)
    cloud_color: Color = (235, 241, 238)
    cloud_density: float = 0.35
    ambient_strength: float = 0.35


@dataclass
class RenderSettings:
    clear_color: Color = (22, 31, 46)
    grid_size: float = 1.0
    grid_extent: int = 24
    grid_snap: float = 0.25
    angle_snap: float = 15.0
    show_grid: bool = True
    shadows: bool = True


@dataclass
class TransformGizmo:
    mode: str = "select"
    axis: str | None = None
    snap_enabled: bool = True


@dataclass
class BuiltinMeshes:
    cube: ClassVar[Mesh] = Mesh.cube()
