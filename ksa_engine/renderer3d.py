from __future__ import annotations

import math

import pygame

from .core import Entity, GameWorld, Vector3


class Renderer3D:
    """Dependency-light perspective renderer for the playable KSA vertical slice."""

    width = 1280
    height = 720
    focal_length = 620.0

    def __init__(self, engine) -> None:
        pygame.init()
        pygame.display.set_caption("KSA ENGINE 3D | Arabian Procedural World")
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        self.engine = engine
        self.world: GameWorld = engine.world
        self.running = True
        self.player = self.world.find_by_kind("character")[0]

    def run(self) -> None:
        while self.running:
            delta = min(self.clock.tick(60) / 1000.0, 0.05)
            self._events()
            self._move_player(delta)
            self.engine.update(delta)
            self._draw()
        pygame.quit()

    def _events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False

    def _move_player(self, delta: float) -> None:
        keys = pygame.key.get_pressed()
        x = float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(keys[pygame.K_a] or keys[pygame.K_LEFT])
        z = float(keys[pygame.K_w] or keys[pygame.K_UP]) - float(keys[pygame.K_s] or keys[pygame.K_DOWN])
        length = math.hypot(x, z)
        speed = 5.0
        if length:
            x, z = x / length, z / length
            position = self.player.transform.position
            self.player.transform.position = Vector3(position.x + x * speed * delta, position.y, position.z + z * speed * delta)
        self.player.components["velocity"] = Vector3(x * speed, 0.0, z * speed)
        self.player.components.setdefault("animation", {})["clip"] = "run" if length else "idle"

    def _camera_basis(self) -> tuple[Vector3, Vector3, Vector3, Vector3]:
        camera = self.world.find_by_kind("camera")[0]
        target = self.world.entities.get(camera.components.get("target_id"), self.player)
        eye = camera.transform.position
        target_position = target.transform.position
        forward = self._normalize(Vector3(target_position.x - eye.x, target_position.y - eye.y, target_position.z - eye.z))
        right = self._normalize(Vector3(forward.z, 0.0, -forward.x))
        up = self._cross(right, forward)
        return eye, forward, right, up

    def _project(self, point: Vector3) -> tuple[int, int, float] | None:
        eye, forward, right, up = self._camera_basis()
        relative = Vector3(point.x - eye.x, point.y - eye.y, point.z - eye.z)
        depth = self._dot(relative, forward)
        if depth <= 0.15:
            return None
        horizontal = self._dot(relative, right)
        vertical = self._dot(relative, up)
        return (int(self.width / 2 + horizontal * self.focal_length / depth), int(self.height / 2 - vertical * self.focal_length / depth), depth)

    def _draw(self) -> None:
        night = self.world.metadata.get("time_of_day") == "night"
        self.screen.fill((10, 18, 38) if night else (112, 179, 220))
        self._draw_sun(night)
        self._draw_ground(night)
        drawable = [entity for entity in self.world.entities.values() if entity.active and entity.kind not in {"camera", "light"}]
        drawable.sort(key=lambda entity: self._distance_to_camera(entity), reverse=True)
        for entity in drawable:
            self._draw_entity(entity, night)
        self._draw_ui()
        pygame.display.flip()

    def _draw_sun(self, night: bool) -> None:
        color = (245, 231, 160) if night else (255, 226, 135)
        pygame.draw.circle(self.screen, color, (self.width - 110, 110), 34 if night else 46)

    def _draw_ground(self, night: bool) -> None:
        color = (42, 55, 61) if night else (180, 130, 76)
        for x in range(-30, 31, 3):
            self._quad(Vector3(x, -0.15, -8), Vector3(x + 0.08, -0.15, -8), Vector3(x + 0.08, -0.15, 70), Vector3(x, -0.15, 70), color=color)
        for z in range(-8, 71, 3):
            self._quad(Vector3(-30, -0.14, z), Vector3(30, -0.14, z), Vector3(30, -0.14, z + 0.08), Vector3(-30, -0.14, z + 0.08), color=color)

    def _draw_entity(self, entity: Entity, night: bool) -> None:
        position = entity.transform.position
        if entity.kind == "building":
            self._cube(position, 2.5, 3.5, (90, 54, 43) if night else (157, 91, 55))
        elif entity.kind == "vegetation":
            self._palm(position)
        elif entity.kind in {"character", "npc"}:
            color = (222, 176, 73) if entity.id == self.player.id else ((71, 170, 184) if entity.components.get("role") == "hostage" else (180, 64, 57))
            self._cube(Vector3(position.x, position.y + 0.8, position.z), 0.45, 1.6, color)
            self._sphere(Vector3(position.x, position.y + 1.8, position.z), 0.34, (235, 192, 143))
        elif entity.kind == "water":
            self._cube(Vector3(position.x, -0.02, position.z), 2.8, 0.08, (37, 119, 158))

    def _cube(self, center: Vector3, width: float, height: float, color: tuple[int, int, int]) -> None:
        points = [Vector3(center.x + dx * width, center.y + dy * height, center.z + dz * width) for dx, dy, dz in ((-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1), (-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1))]
        faces = ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7))
        for face in faces:
            projected = [self._project(points[index]) for index in face]
            if all(projected):
                pygame.draw.polygon(self.screen, color, [(point[0], point[1]) for point in projected if point])

    def _sphere(self, center: Vector3, radius: float, color: tuple[int, int, int]) -> None:
        projected = self._project(center)
        edge = self._project(Vector3(center.x + radius, center.y, center.z))
        if projected and edge:
            pygame.draw.circle(self.screen, color, projected[:2], max(2, abs(edge[0] - projected[0])))

    def _palm(self, position: Vector3) -> None:
        base = self._project(position)
        top = self._project(Vector3(position.x, position.y + 2.5, position.z))
        if base and top:
            pygame.draw.line(self.screen, (91, 55, 30), base[:2], top[:2], 6)
            for offset in (-0.7, -0.35, 0.0, 0.35, 0.7):
                leaf = self._project(Vector3(position.x + offset, position.y + 2.8, position.z + abs(offset) * 0.4))
                if leaf:
                    pygame.draw.line(self.screen, (45, 123, 65), top[:2], leaf[:2], 4)

    def _quad(self, *corners: Vector3, color: tuple[int, int, int]) -> None:
        projected = [self._project(corner) for corner in corners]
        if all(projected):
            pygame.draw.polygon(self.screen, color, [(point[0], point[1]) for point in projected if point])

    def _draw_ui(self) -> None:
        panel = pygame.Surface((self.width, 72), pygame.SRCALPHA)
        panel.fill((7, 12, 25, 220))
        self.screen.blit(panel, (0, 0))
        title = self.title_font.render("KSA ENGINE 3D", True, (244, 201, 101))
        info = self.font.render(f"{self.world.name} | Entities: {len(self.world.entities)} | {self.world.elapsed_time:05.1f}s", True, (235, 235, 225))
        hint = self.font.render("WASD / الأسهم للحركة | ESC للخروج", True, (176, 192, 202))
        self.screen.blit(title, (24, 10))
        self.screen.blit(info, (265, 14))
        self.screen.blit(hint, (265, 43))

    def _distance_to_camera(self, entity: Entity) -> float:
        camera = self.world.find_by_kind("camera")[0].transform.position
        position = entity.transform.position
        return (position.x - camera.x) ** 2 + (position.z - camera.z) ** 2

    @staticmethod
    def _dot(left: Vector3, right: Vector3) -> float:
        return left.x * right.x + left.y * right.y + left.z * right.z

    @staticmethod
    def _cross(left: Vector3, right: Vector3) -> Vector3:
        return Vector3(left.y * right.z - left.z * right.y, left.z * right.x - left.x * right.z, left.x * right.y - left.y * right.x)

    @staticmethod
    def _normalize(value: Vector3) -> Vector3:
        length = math.sqrt(value.x * value.x + value.y * value.y + value.z * value.z) or 1.0
        return Vector3(value.x / length, value.y / length, value.z / length)


def run_game_3d(engine) -> None:
    Renderer3D(engine).run()