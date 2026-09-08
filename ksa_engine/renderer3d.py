"""Dependency-light 2.5D renderer for previewing authored scenes."""

from __future__ import annotations

import math
import pygame

from .core import Engine, Vector3
from .events import InputState
from .systems import InputMovementSystem


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
        self.running = True
        self.focal_length = self.height / (2.0 * math.tan(math.radians(60.0) / 2.0))

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
                self.input.keys.update({pygame.key.name(event.key)})
            elif event.type == pygame.KEYUP:
                self.input.keys.discard(pygame.key.name(event.key))

    def _draw(self) -> None:
        self.screen.fill((18, 27, 43))
        pygame.draw.rect(self.screen, (33, 66, 70), (0, self.height // 2, self.width, self.height // 2))
        scene = self.engine.scene
        if scene:
            entities = sorted(scene.find(), key=lambda entity: self._depth(entity), reverse=True)
            for entity in entities:
                if entity.kind not in {"camera", "light", "static"}:
                    self._draw_entity(entity)
        self.screen.blit(self.font.render(f"KSA Engine Beta | {scene.name if scene else 'No Scene'} | {self.engine.elapsed_time:05.1f}s", True, (235, 225, 190)), (24, 20))
        self.screen.blit(self.font.render("WASD to move | ESC to exit", True, (190, 205, 215)), (24, 50))
        pygame.display.flip()

    def _draw_entity(self, entity) -> None:
        projected = self._project(entity.transform.position)
        if projected is None:
            return
        x, y, depth = projected
        material = entity.get_component("material", {})
        base_color = (235, 190, 75) if entity.kind == "player" else tuple(material.get("color", (110, 180, 195)))
        shade = self._light_factor(entity)
        color = tuple(max(0, min(255, int(channel * shade))) for channel in base_color)
        size = max(6, int(34 * self.focal_length / max(depth * 100.0, 1.0)))
        pygame.draw.rect(self.screen, color, (x - size, y - size, size * 2, size * 2))

    def _project(self, point: Vector3) -> tuple[int, int, float] | None:
        camera = self._camera_position()
        relative = point - camera
        depth = -relative.z
        if depth <= 0.1:
            return None
        return (
            int(self.width / 2 + relative.x * self.focal_length / depth),
            int(self.height / 2 - relative.y * self.focal_length / depth),
            depth,
        )

    def _camera_position(self) -> Vector3:
        scene = self.engine.scene
        if scene:
            cameras = scene.find("camera")
            if cameras:
                return cameras[0].transform.position
        return Vector3(0.0, 2.0, -10.0)

    def _depth(self, entity) -> float:
        return -(entity.transform.position - self._camera_position()).z

    def _light_factor(self, entity) -> float:
        ambient = 0.35
        scene = self.engine.scene
        if scene:
            lights = scene.find("light")
            if lights:
                ambient = max(ambient, min(1.0, sum(float(light.get_component("intensity", 1.0)) for light in lights) / len(lights)))
        return max(0.2, min(1.0, ambient))


def run_game_3d(engine: Engine) -> None:
    Renderer3D(engine).run()
