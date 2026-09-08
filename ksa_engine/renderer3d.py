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
            entities = sorted(scene.find(), key=lambda entity: entity.transform.position.z, reverse=True)
            for entity in entities:
                if entity.kind not in {"camera", "light", "static"}:
                    self._draw_entity(entity)
        self.screen.blit(self.font.render(f"KSA Engine Beta | {scene.name if scene else 'No Scene'} | {self.engine.elapsed_time:05.1f}s", True, (235, 225, 190)), (24, 20))
        self.screen.blit(self.font.render("WASD to move | ESC to exit", True, (190, 205, 215)), (24, 50))
        pygame.display.flip()

    def _draw_entity(self, entity) -> None:
        position = entity.transform.position
        depth = max(1.0, position.z + 10.0)
        x = int(self.width / 2 + position.x * 480 / depth)
        y = int(self.height / 2 - position.y * 300 / depth)
        size = max(8, int(42 / depth))
        color = (235, 190, 75) if entity.kind == "player" else tuple(entity.get_component("material", {}).get("color", (110, 180, 195)))
        pygame.draw.rect(self.screen, color, (x - size, y - size, size * 2, size * 2))


def run_game_3d(engine: Engine) -> None:
    Renderer3D(engine).run()
