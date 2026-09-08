"""Minimal English scene editor built around the runtime scene model."""

from __future__ import annotations

import pygame

from .demo import build_engine
from .scene_io import save_scene


class KSAEditor:
    width, height = 1440, 860

    def __init__(self, engine=None) -> None:
        pygame.init()
        pygame.display.set_caption("KSA Engine Beta | Scene Editor")
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 22)
        self.heading = pygame.font.Font(None, 34)
        self.engine = engine or build_engine()
        self.selected_id: int | None = None
        self.running = True
        self.status = "Ready"

    def run(self) -> None:
        while self.running:
            self._events()
            self.engine.update(min(self.clock.tick(60) / 1000.0, 0.1))
            self._draw()
        pygame.quit()

    def _events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._key_down(event)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._select_from_outliner(event.pos)

    def _key_down(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
            save_scene(self.engine.scene, "scene.json")
            self.status = "Saved scene.json"
        elif self.selected_id is not None and event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
            entity = self.engine.scene.entity(self.selected_id)
            if entity:
                amount = 0.25
                x = -amount if event.key == pygame.K_LEFT else amount if event.key == pygame.K_RIGHT else 0.0
                z = -amount if event.key == pygame.K_UP else amount if event.key == pygame.K_DOWN else 0.0
                position = entity.transform.position
                entity.transform.position = type(position)(position.x + x, position.y, position.z + z)
                self.status = f"Moved {entity.name}"

    def _select_from_outliner(self, position: tuple[int, int]) -> None:
        if position[0] < 1040 or position[1] < 145:
            return
        index = (position[1] - 145) // 30
        entities = list(self.engine.scene.entities.values())
        if 0 <= index < len(entities):
            self.selected_id = entities[index].id

    def _draw(self) -> None:
        self.screen.fill((20, 24, 30))
        pygame.draw.rect(self.screen, (29, 34, 42), (0, 0, self.width, 64))
        pygame.draw.rect(self.screen, (25, 30, 37), (0, 64, 1040, self.height - 64))
        pygame.draw.rect(self.screen, (34, 39, 47), (1040, 64, 400, self.height - 64))
        self._text("KSA ENGINE BETA", (24, 18), self.heading, (235, 190, 90))
        self._text("Scene Editor", (300, 24), self.font, (180, 190, 202))
        self._draw_viewport()
        self._draw_outliner()
        self._draw_inspector()
        pygame.display.flip()

    def _draw_viewport(self) -> None:
        viewport = pygame.Rect(28, 96, 984, 650)
        pygame.draw.rect(self.screen, (47, 58, 63), viewport)
        for x in range(viewport.left, viewport.right, 40):
            pygame.draw.line(self.screen, (55, 68, 71), (x, viewport.top), (x, viewport.bottom))
        for y in range(viewport.top, viewport.bottom, 40):
            pygame.draw.line(self.screen, (55, 68, 71), (viewport.left, y), (viewport.right, y))
        for entity in self.engine.scene.find():
            if entity.kind in {"camera", "light"}:
                continue
            position = entity.transform.position
            screen_position = (int(viewport.centerx + position.x * 45), int(viewport.centery - position.z * 45))
            color = (225, 185, 85) if entity.id == self.selected_id else (120, 175, 190)
            pygame.draw.rect(self.screen, color, (*screen_position, 24, 24))
        self._text("Viewport", (44, 110), self.font, (220, 225, 220))
        self._text(self.status, (28, 780), self.font, (155, 170, 182))

    def _draw_outliner(self) -> None:
        self._text("Outliner", (1060, 90), self.heading, (235, 190, 90))
        for index, entity in enumerate(self.engine.scene.entities.values()):
            color = (235, 190, 90) if entity.id == self.selected_id else (210, 218, 224)
            self._text(f"{entity.id:02d}  {entity.name}  [{entity.kind}]", (1060, 145 + index * 30), self.font, color)

    def _draw_inspector(self) -> None:
        top = 470
        self._text("Details", (1060, top), self.heading, (235, 190, 90))
        entity = self.engine.scene.entity(self.selected_id) if self.selected_id else None
        lines = ["Select an entity" if entity is None else f"Name: {entity.name}", "", "Transform"]
        if entity:
            position = entity.transform.position
            lines += [f"Position  {position.x:.2f}, {position.y:.2f}, {position.z:.2f}", f"Parent    {entity.transform.parent_id or 'None'}", f"Components {len(entity.components)}"]
        for index, line in enumerate(lines):
            self._text(line, (1060, top + 52 + index * 26), self.font, (205, 215, 220))
        self._text("Content Browser", (1060, 670), self.heading, (235, 190, 90))
        self._text("assets/", (1060, 720), self.font, (205, 215, 220))
        self._text("scene.json  |  materials  |  meshes", (1060, 748), self.font, (150, 165, 175))

    def _text(self, value: str, position: tuple[int, int], font: pygame.font.Font, color: tuple[int, int, int]) -> None:
        self.screen.blit(font.render(value, True, color), position)


def run_editor(engine=None) -> None:
    KSAEditor(engine).run()
