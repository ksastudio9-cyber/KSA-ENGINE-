"""A dependency-light software 3D viewport used by the runtime and editor."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import pygame

from .core import Engine, Vector3
from .events import InputState
from .rendering import BuiltinMeshes, Light, Material, Mesh, RenderSettings, SkySettings
from .systems import InputMovementSystem


@dataclass
class OrbitCamera:
    target: Vector3 = Vector3(0.0, 0.5, -3.0)
    distance: float = 10.0
    yaw: float = 0.0
    pitch: float = -0.18
    fov: float = 60.0
    near: float = 0.1
    far: float = 1000.0

    def position(self) -> Vector3:
        horizontal = math.cos(self.pitch) * self.distance
        return Vector3(
            self.target.x + math.sin(self.yaw) * horizontal,
            self.target.y - math.sin(self.pitch) * self.distance,
            self.target.z + math.cos(self.yaw) * horizontal,
        )

    def orbit(self, delta_x: float, delta_y: float) -> None:
        self.yaw += delta_x * 0.008
        self.pitch = max(-1.35, min(1.35, self.pitch + delta_y * 0.008))

    def zoom(self, amount: float) -> None:
        self.distance = max(1.5, min(200.0, self.distance * (1.0 + amount)))

    def pan(self, delta_x: float, delta_y: float) -> None:
        right = Vector3(math.cos(self.yaw), 0.0, -math.sin(self.yaw))
        self.target = self.target + right * (delta_x * self.distance * 0.002) + Vector3(0.0, delta_y * self.distance * 0.002, 0.0)


class SoftwareRenderer:
    def __init__(self, width: int, height: int, settings: RenderSettings | None = None, sky: SkySettings | None = None) -> None:
        self.width = width
        self.height = height
        self.settings = settings or RenderSettings()
        self.sky = sky or SkySettings()
        self.camera = OrbitCamera()
        self._drag_button: int | None = None
        self._last_mouse = (0, 0)

    def draw_scene(self, surface: pygame.Surface, scene: Any, selected_id: int | None = None) -> None:
        scene_settings = scene.metadata.get("render_settings")
        scene_sky = scene.metadata.get("sky")
        if isinstance(scene_settings, RenderSettings):
            self.settings = scene_settings
        if isinstance(scene_sky, SkySettings):
            self.sky = scene_sky
        self._draw_sky(surface)
        if self.settings.show_grid:
            self._draw_grid(surface)
        entities = [entity for entity in scene.find() if entity.kind not in {"camera", "light"}]
        for entity in sorted(entities, key=lambda item: self._depth(scene.world_position(item.id)), reverse=True):
            self._draw_entity(surface, scene, entity, entity.id == selected_id)

    def handle_mouse(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._drag_button = event.button
            self._last_mouse = event.pos
            if event.button == 4:
                self.camera.zoom(-0.1)
            elif event.button == 5:
                self.camera.zoom(0.1)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._drag_button = None
        elif event.type == pygame.MOUSEMOTION and self._drag_button:
            delta_x = event.pos[0] - self._last_mouse[0]
            delta_y = event.pos[1] - self._last_mouse[1]
            if self._drag_button == 3:
                self.camera.orbit(delta_x, delta_y)
            elif self._drag_button == 2:
                self.camera.pan(delta_x, delta_y)
            self._last_mouse = event.pos
        elif event.type == pygame.MOUSEWHEEL:
            self.camera.zoom(-event.y * 0.08)

    def _draw_sky(self, surface: pygame.Surface) -> None:
        horizon = max(1, self.height // 2)
        for y in range(self.height):
            amount = min(1.0, y / horizon)
            color = self._mix(self.sky.top_color, self.sky.horizon_color, amount)
            pygame.draw.line(surface, color, (0, y), (self.width, y))
        cloud_color = self.sky.cloud_color
        for index in range(5):
            x = int((index * 263 + 90) % (self.width + 180) - 90)
            y = 72 + (index % 3) * 42
            pygame.draw.ellipse(surface, (*cloud_color, 42), (x, y, 170, 26))

    def _draw_grid(self, surface: pygame.Surface) -> None:
        extent = self.settings.grid_extent
        for value in range(-extent, extent + 1):
            self._line_3d(surface, Vector3(value, 0.0, -extent), Vector3(value, 0.0, extent), (72, 88, 96) if value else (120, 110, 80))
            self._line_3d(surface, Vector3(-extent, 0.0, value), Vector3(extent, 0.0, value), (72, 88, 96) if value else (120, 110, 80))

    def _draw_entity(self, surface: pygame.Surface, scene: Any, entity: Any, selected: bool) -> None:
        mesh = entity.get_component("mesh", BuiltinMeshes.cube)
        if not isinstance(mesh, Mesh):
            mesh = BuiltinMeshes.cube
        material = entity.get_component("material", Material())
        if not isinstance(material, Material):
            material = Material()
        origin = scene.world_position(entity.id)
        projected: list[tuple[int, int, float] | None] = []
        for vertex in mesh.vertices:
            world = Vector3(origin.x + vertex.x * entity.transform.scale.x, origin.y + vertex.y * entity.transform.scale.y, origin.z + vertex.z * entity.transform.scale.z)
            projected.append(self._project(world))
        self._draw_shadow(surface, origin, entity.transform.scale, scene)
        faces: list[tuple[float, tuple[int, ...]]] = []
        for face in mesh.faces:
            points = [projected[index] for index in face]
            if any(point is None for point in points):
                continue
            depth = sum(point[2] for point in points if point) / len(points)
            faces.append((depth, face))
        for _, face in sorted(faces, reverse=True):
            points = [projected[index] for index in face]
            color = self._shade(material.color, scene, origin)
            pygame.draw.polygon(surface, color, [(point[0], point[1]) for point in points if point])
            pygame.draw.line(surface, (20, 28, 34), [(point[0], point[1]) for point in points if point], True, 1)
        if selected:
            center = self._project(origin)
            if center:
                pygame.draw.circle(surface, (244, 191, 78), center[:2], 7, 2)

    def _draw_shadow(self, surface: pygame.Surface, origin: Vector3, scale: Vector3, scene: Any) -> None:
        if not self.settings.shadows or origin.y <= 0.0:
            return
        light = next((entity.get_component("light") for entity in scene.find("light") if isinstance(entity.get_component("light"), Light)), None)
        if light is None or not light.cast_shadows or light.direction.y >= -0.01:
            return
        length = origin.y / -light.direction.y
        shadow_center = origin + light.direction.normalized() * length
        corners = [Vector3(shadow_center.x + x * scale.x, 0.02, shadow_center.z + z * scale.z) for x, z in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        projected = [self._project(corner) for corner in corners]
        if all(projected):
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.polygon(overlay, (15, 22, 25, 90), [(point[0], point[1]) for point in projected if point])
            surface.blit(overlay, (0, 0))

    def _shade(self, color: tuple[int, int, int], scene: Any, origin: Vector3) -> tuple[int, int, int]:
        light = next((entity.get_component("light") for entity in scene.find("light") if isinstance(entity.get_component("light"), Light)), None)
        brightness = self.sky.ambient_strength
        if light:
            brightness += max(0.0, min(1.0, light.intensity * (0.55 + 0.45 * max(0.0, -light.direction.normalized().y))))
        return tuple(max(0, min(255, int(channel * brightness))) for channel in color)

    def _project(self, point: Vector3) -> tuple[int, int, float] | None:
        camera = self.camera.position()
        forward = (self.camera.target - camera).normalized()
        right = Vector3(forward.z, 0.0, -forward.x).normalized()
        up = Vector3(-right.y * forward.z, right.z * forward.x, right.x * forward.y).normalized()
        relative = point - camera
        depth = relative.dot(forward)
        if depth <= self.camera.near or depth >= self.camera.far:
            return None
        focal = self.height / (2.0 * math.tan(math.radians(self.camera.fov) / 2.0))
        return (int(self.width / 2 + relative.dot(right) * focal / depth), int(self.height / 2 - relative.dot(up) * focal / depth), depth)

    def _line_3d(self, surface: pygame.Surface, start: Vector3, end: Vector3, color: tuple[int, int, int]) -> None:
        first = self._project(start)
        second = self._project(end)
        if first and second:
            pygame.draw.line(surface, color, first[:2], second[:2], 1)

    def _depth(self, point: Vector3) -> float:
        projected = self._project(point)
        return projected[2] if projected else -1.0

    @staticmethod
    def _mix(first: tuple[int, int, int], second: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
        return tuple(int(left + (right - left) * amount) for left, right in zip(first, second))


class Renderer3D:
    width, height = 1280, 720

    def __init__(self, engine: Engine) -> None:
        pygame.init()
        pygame.display.set_caption("KSA Engine Beta | Runtime")
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.engine = engine
        self.input = InputState()
        self.engine.add_system(InputMovementSystem(self.input))
        self.renderer = SoftwareRenderer(self.width, self.height)
        self.running = True

    def run(self) -> None:
        while self.running:
            delta = min(self.clock.tick(60) / 1000.0, 0.1)
            self._events()
            self.engine.update(delta)
            self._draw()
        pygame.quit()

    def _events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.input.keys.add(pygame.key.name(event.key))
            elif event.type == pygame.KEYUP:
                self.input.keys.discard(pygame.key.name(event.key))
            self.renderer.handle_mouse(event)

    def _draw(self) -> None:
        scene = self.engine.scene
        if scene:
            self.renderer.draw_scene(self.screen, scene)
        self.screen.blit(self.font.render(f"KSA Engine Beta | {scene.name if scene else 'No Scene'} | {self.engine.elapsed_time:05.1f}s", True, (235, 225, 190)), (24, 20))
        self.screen.blit(self.font.render("WASD move | RMB orbit | MMB pan | Wheel zoom | ESC exit", True, (190, 205, 215)), (24, 50))
        pygame.display.flip()


def run_game_3d(engine: Engine) -> None:
    Renderer3D(engine).run()
