from __future__ import annotations

import math
import random

import pygame

from .core import Entity, GameWorld, Vector3
from .demo import build_engine


class GameWindow:
    """Small playable renderer for the generated world, backed by the engine state."""

    width = 1280
    height = 720
    world_scale = 28.0

    def __init__(self, engine) -> None:
        pygame.init()
        pygame.display.set_caption("KSA ENGINE | Arabian Procedural World")
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 34)
        self.engine = engine
        self.world: GameWorld = engine.world
        self.player = self.world.find_by_kind("character")[0]
        self.camera_x = self.player.transform.position.x
        self.camera_z = self.player.transform.position.z
        self.running = True
        self.rng = random.Random(self.world.seed)
        self.stars = [(self.rng.randrange(self.width), self.rng.randrange(80, self.height)) for _ in range(90)]

    def run(self) -> None:
        while self.running:
            delta_time = min(self.clock.tick(60) / 1000.0, 0.05)
            self._events()
            self._move_player(delta_time)
            self.engine.update(delta_time)
            self._draw()
        pygame.quit()

    def _events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def _move_player(self, delta_time: float) -> None:
        keys = pygame.key.get_pressed()
        horizontal = float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(keys[pygame.K_a] or keys[pygame.K_LEFT])
        depth = float(keys[pygame.K_s] or keys[pygame.K_DOWN]) - float(keys[pygame.K_w] or keys[pygame.K_UP])
        length = math.hypot(horizontal, depth)
        velocity = Vector3()
        if length:
            speed = 5.0
            horizontal, depth = horizontal / length, depth / length
            position = self.player.transform.position
            self.player.transform.position = Vector3(
                position.x + horizontal * speed * delta_time,
                position.y,
                position.z + depth * speed * delta_time,
            )
            velocity = Vector3(horizontal * speed, 0.0, depth * speed)
        self.player.components["velocity"] = velocity
        self.player.components.setdefault("animation", {})["clip"] = "run" if length else "idle"

    def _screen_position(self, entity: Entity) -> tuple[int, int]:
        return self._screen_point(entity.transform.position)

    def _screen_point(self, position: Vector3) -> tuple[int, int]:
        return (
            int(self.width * 0.5 + (position.x - self.camera_x) * self.world_scale),
            int(self.height * 0.54 + (position.z - self.camera_z) * self.world_scale),
        )

    def _draw(self) -> None:
        night = self.world.metadata.get("time_of_day") == "night"
        self.screen.fill((18, 27, 49) if night else (194, 157, 94))
        if night:
            for star_x, star_y in self.stars:
                pygame.draw.circle(self.screen, (245, 225, 164), (star_x, star_y), 1)
        self._draw_ground(night)
        for entity in self.world.entities.values():
            if entity.active and entity.kind != "camera":
                self._draw_entity(entity, night)
        self._draw_ui(night)
        pygame.display.flip()

    def _draw_ground(self, night: bool) -> None:
        line_color = (103, 91, 81) if night else (170, 125, 70)
        for grid_x in range(-24, 25):
            start = self._screen_point(Vector3(grid_x, 0, -20))
            end = self._screen_point(Vector3(grid_x, 0, 20))
            pygame.draw.line(self.screen, line_color, start, end, 1)
        for grid_z in range(-20, 21):
            start = self._screen_point(Vector3(-24, 0, grid_z))
            end = self._screen_point(Vector3(24, 0, grid_z))
            pygame.draw.line(self.screen, line_color, start, end, 1)

    def _draw_entity(self, entity: Entity, night: bool) -> None:
        screen_x, screen_y = self._screen_position(entity)
        if entity.kind == "building":
            color = (109, 68, 47) if night else (169, 106, 60)
            pygame.draw.rect(self.screen, color, (screen_x - 26, screen_y - 24, 52, 48))
            pygame.draw.polygon(self.screen, (64, 42, 47), [(screen_x - 31, screen_y - 24), (screen_x, screen_y - 45), (screen_x + 31, screen_y - 24)])
        elif entity.kind == "vegetation":
            pygame.draw.line(self.screen, (90, 55, 32), (screen_x, screen_y + 18), (screen_x, screen_y - 8), 5)
            for angle in range(0, 360, 60):
                leaf_x = screen_x + int(math.cos(math.radians(angle)) * 18)
                leaf_y = screen_y - 8 + int(math.sin(math.radians(angle)) * 13)
                pygame.draw.line(self.screen, (62, 127, 71), (screen_x, screen_y - 8), (leaf_x, leaf_y), 4)
        elif entity.kind == "character":
            body_color = (229, 184, 83) if entity.id == self.player.id else (184, 76, 65)
            pygame.draw.circle(self.screen, (242, 202, 150), (screen_x, screen_y - 12), 8)
            pygame.draw.rect(self.screen, body_color, (screen_x - 8, screen_y - 4, 16, 25), border_radius=4)
        elif entity.kind == "npc":
            body_color = (83, 177, 193) if entity.components.get("role") == "hostage" else (184, 76, 65)
            pygame.draw.circle(self.screen, (242, 202, 150), (screen_x, screen_y - 12), 8)
            pygame.draw.rect(self.screen, body_color, (screen_x - 8, screen_y - 4, 16, 25), border_radius=4)
            if entity.components.get("role") == "hostage":
                pygame.draw.circle(self.screen, (238, 219, 152), (screen_x, screen_y - 39), 4)
        elif entity.kind == "light":
            pygame.draw.circle(self.screen, (255, 215, 105), (screen_x, screen_y), 8)
        elif entity.kind == "water":
            pygame.draw.ellipse(self.screen, (46, 123, 157), (screen_x - 42, screen_y - 22, 84, 44))

    def _draw_ui(self, night: bool) -> None:
        panel = pygame.Surface((self.width, 72), pygame.SRCALPHA)
        panel.fill((8, 14, 28, 220))
        self.screen.blit(panel, (0, 0))
        title = self.title_font.render("KSA ENGINE", True, (243, 201, 105))
        status = self.font.render(
            f"{self.world.name}  |  كيانات: {len(self.world.entities)}  |  الزمن: {self.world.elapsed_time:05.1f}s",
            True,
            (235, 235, 225),
        )
        hint = self.font.render("WASD / الأسهم للحركة   |   ESC للخروج", True, (176, 192, 202))
        self.screen.blit(title, (24, 12))
        self.screen.blit(status, (245, 14))
        self.screen.blit(hint, (245, 42))
        dialogue = self.world.metadata.get("narrative", {}).get("dialogue_history", [])
        hostage = next((entity for entity in self.world.find_by_kind("npc") if entity.components.get("role") == "hostage"), None)
        if hostage and not dialogue:
            lines = hostage.components.get("dialogue", [])
            if lines:
                speech = self.font.render(f"الرهينة: {lines[0]}", True, (255, 238, 180))
                self.screen.blit(speech, (24, self.height - 38))


def run_game(description: str, seed: int | None = None) -> None:
    engine = build_engine(description, seed)
    GameWindow(engine).run()