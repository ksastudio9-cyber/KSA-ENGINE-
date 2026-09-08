"""English developer editor with an integrated 3D viewport and scene tools."""

from __future__ import annotations

import pygame

from .demo import build_engine
from .renderer3d import SoftwareRenderer
from .scene_io import save_scene
from .rendering import Material, Mesh
from .core import Transform, Vector3


class KSAEditor:
    width, height = 1440, 900
    toolbar_height = 56
    outliner_width = 300
    details_width = 340

    def __init__(self, engine=None) -> None:
        pygame.init()
        pygame.display.set_caption("KSA Engine Beta | Editor")
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)
        self.small = pygame.font.Font(None, 17)
        self.heading = pygame.font.Font(None, 28)
        self.engine = engine or build_engine()
        self.renderer = SoftwareRenderer(self.width - self.outliner_width - self.details_width, self.height - self.toolbar_height - 150)
        self.selected_id: int | None = None
        self.running = True
        self.status = "Ready"
        self.tool = "select"
        self.rename_mode = False
        self.rename_buffer = ""
        self.content_tab = "Content Browser"

    @property
    def scene(self):
        return self.engine.scene

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
            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.renderer.width = max(320, self.width - self.outliner_width - self.details_width)
                self.renderer.height = max(260, self.height - self.toolbar_height - 150)
            elif event.type == pygame.KEYDOWN:
                self._key_down(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._click(event)
            self.renderer.handle_mouse(event)

    def _key_down(self, event: pygame.event.Event) -> None:
        if self.rename_mode:
            if event.key == pygame.K_RETURN:
                entity = self.scene.entity(self.selected_id) if self.selected_id else None
                if entity and self.rename_buffer.strip():
                    entity.name = self.rename_buffer.strip()[:80]
                self.rename_mode = False
                self.status = "Renamed entity"
            elif event.key == pygame.K_BACKSPACE:
                self.rename_buffer = self.rename_buffer[:-1]
            elif event.unicode and event.unicode.isprintable():
                self.rename_buffer += event.unicode
            return
        if event.key == pygame.K_F2 and self.selected_id:
            entity = self.scene.entity(self.selected_id)
            self.rename_buffer = entity.name if entity else ""
            self.rename_mode = True
        elif event.key == pygame.K_DELETE:
            self._delete_selected()
        elif event.key == pygame.K_d and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self._duplicate_selected()
        elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
            save_scene(self.scene, "scene.json")
            self.status = "Saved scene.json"
        elif event.key in (pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r):
            self.tool = {pygame.K_q: "select", pygame.K_w: "move", pygame.K_e: "rotate", pygame.K_r: "scale"}[event.key]
        elif self.selected_id and event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
            self._transform_selected(event)

    def _click(self, event: pygame.event.Event) -> None:
        x, y = event.pos
        if y < self.toolbar_height:
            tools = ((20, "select"), (92, "move"), (164, "rotate"), (236, "scale"))
            for left, name in tools:
                if left <= x < left + 64:
                    self.tool = name
                    return
        if self.outliner_width <= x < self.width - self.details_width and self.toolbar_height <= y < self.height - 150:
            self.renderer.handle_mouse(event)
        elif x < self.outliner_width and y >= self.toolbar_height:
            self._select_outliner(y)
        elif x >= self.width - self.details_width and y > self.toolbar_height + 50:
            self.status = "Use arrow keys or Q/W/E/R to edit the selected entity"

    def _select_outliner(self, y: int) -> None:
        index = (y - self.toolbar_height - 42) // 27
        entities = list(self.scene.entities.values())
        if 0 <= index < len(entities):
            self.selected_id = entities[index].id
            self.renderer.camera.target = self.scene.world_position(self.selected_id)
            self.status = f"Selected {entities[index].name}"

    def _transform_selected(self, event: pygame.event.Event) -> None:
        entity = self.scene.entity(self.selected_id)
        if entity is None:
            return
        amount = 0.25 if self.renderer.settings.grid_snap else 0.05
        if self.tool == "move":
            x = -amount if event.key == pygame.K_LEFT else amount if event.key == pygame.K_RIGHT else 0.0
            z = -amount if event.key == pygame.K_UP else amount if event.key == pygame.K_DOWN else 0.0
            y = amount if event.key == pygame.K_PAGEUP else -amount if event.key == pygame.K_PAGEDOWN else 0.0
            entity.transform.position = entity.transform.position + Vector3(x, y, z)
        elif self.tool == "rotate":
            amount = 15.0
            y = -amount if event.key in (pygame.K_LEFT, pygame.K_DOWN) else amount
            entity.transform.rotation = entity.transform.rotation + Vector3(0.0, y, 0.0)
        elif self.tool == "scale":
            amount = 0.1 if event.key in (pygame.K_RIGHT, pygame.K_UP, pygame.K_PAGEUP) else -0.1
            entity.transform.scale = entity.transform.scale + Vector3(amount, amount, amount)
        self.status = f"Edited {entity.name}"

    def _delete_selected(self) -> None:
        if self.selected_id is not None:
            entity = self.scene.entity(self.selected_id)
            self.scene.destroy_entity(self.selected_id)
            self.selected_id = None
            self.status = f"Deleted {entity.name if entity else 'entity'}"

    def _duplicate_selected(self) -> None:
        entity = self.scene.entity(self.selected_id) if self.selected_id else None
        if entity is None:
            return
        position = entity.transform.position + Vector3(1.0, 0.0, 1.0)
        copy = self.scene.create_entity(f"{entity.name} Copy", entity.kind, Transform(position, entity.transform.rotation, entity.transform.scale), **dict(entity.components))
        self.selected_id = copy.id
        self.status = f"Duplicated {entity.name}"

    def _draw(self) -> None:
        self.screen.fill((18, 21, 27))
        self._draw_toolbar()
        self._draw_viewport()
        self._draw_outliner()
        self._draw_details()
        pygame.display.flip()

    def _draw_toolbar(self) -> None:
        pygame.draw.rect(self.screen, (29, 33, 41), (0, 0, self.width, self.toolbar_height))
        self._text("KSA ENGINE", (18, 18), self.heading, (226, 182, 75))
        self._text("BETA", (174, 22), self.small, (128, 145, 157))
        for left, name, icon in ((270, "select", "V"), (340, "move", "M"), (410, "rotate", "R"), (480, "scale", "S")):
            selected = self.tool == name
            pygame.draw.rect(self.screen, (75, 101, 113) if selected else (42, 48, 57), (left, 10, 60, 36), border_radius=3)
            self._text(f"{icon} {name.title()}", (left + 8, 21), self.small, (239, 239, 232))
        self._text("Ctrl+S Save   Ctrl+D Duplicate   F2 Rename   Delete Remove", (590, 22), self.small, (148, 160, 170))

    def _draw_viewport(self) -> None:
        rect = pygame.Rect(self.outliner_width, self.toolbar_height, self.width - self.outliner_width - self.details_width, self.height - self.toolbar_height - 150)
        surface = self.screen.subsurface(rect)
        self.renderer.width, self.renderer.height = rect.width, rect.height
        if self.scene:
            self.renderer.draw_scene(surface, self.scene, self.selected_id)
        self._text("Perspective  |  Real-time preview", (rect.left + 16, rect.top + 14), self.small, (226, 231, 224))
        self._text("RMB orbit  MMB pan  Wheel zoom", (rect.left + 16, rect.bottom - 28), self.small, (170, 182, 190))

    def _draw_outliner(self) -> None:
        rect = pygame.Rect(0, self.toolbar_height, self.outliner_width, self.height - self.toolbar_height)
        pygame.draw.rect(self.screen, (24, 28, 35), rect)
        self._text("OUTLINER", (18, rect.top + 18), self.font, (226, 182, 75))
        self._text(self.scene.name if self.scene else "No Scene", (18, rect.top + 45), self.small, (152, 166, 176))
        for index, entity in enumerate(self.scene.entities.values() if self.scene else []):
            y = rect.top + 72 + index * 27
            selected = entity.id == self.selected_id
            pygame.draw.rect(self.screen, (55, 68, 77) if selected else (24, 28, 35), (8, y - 3, rect.width - 16, 24))
            depth = self._hierarchy_depth(entity.id)
            self._text(f"{'  ' * depth}{'▾ ' if any(child.transform.parent_id == entity.id for child in self.scene.entities.values()) else '• '}{entity.name}", (18, y + 2), self.small, (235, 190, 82) if selected else (204, 213, 219))
        self._text("CONTENT BROWSER", (18, self.height - 132), self.font, (226, 182, 75))
        self._text("Assets/", (18, self.height - 102), self.small, (176, 190, 198))
        self._text("Meshes   Materials   Textures", (18, self.height - 76), self.small, (132, 148, 158))

    def _draw_details(self) -> None:
        left = self.width - self.details_width
        pygame.draw.rect(self.screen, (24, 28, 35), (left, self.toolbar_height, self.details_width, self.height - self.toolbar_height))
        self._text("DETAILS", (left + 18, self.toolbar_height + 18), self.font, (226, 182, 75))
        entity = self.scene.entity(self.selected_id) if self.selected_id and self.scene else None
        if entity is None:
            self._text("Select an entity", (left + 18, self.toolbar_height + 62), self.small, (154, 168, 178))
            return
        self._text(entity.name, (left + 18, self.toolbar_height + 53), self.font, (235, 239, 233))
        self._text(f"Type  {entity.kind}", (left + 18, self.toolbar_height + 80), self.small, (154, 168, 178))
        self._text("TRANSFORM", (left + 18, self.toolbar_height + 122), self.font, (226, 182, 75))
        position = entity.transform.position
        rotation = entity.transform.rotation
        scale = entity.transform.scale
        rows = [f"Position  {position.x:.2f}  {position.y:.2f}  {position.z:.2f}", f"Rotation  {rotation.x:.1f}  {rotation.y:.1f}  {rotation.z:.1f}", f"Scale     {scale.x:.2f}  {scale.y:.2f}  {scale.z:.2f}", f"Parent    {entity.transform.parent_id or 'None'}"]
        for index, row in enumerate(rows):
            self._text(row, (left + 18, self.toolbar_height + 153 + index * 26), self.small, (205, 215, 220))
        self._text("RENDER", (left + 18, self.toolbar_height + 285), self.font, (226, 182, 75))
        self._text(f"Mesh       {'Yes' if entity.get_component('mesh') else 'None'}", (left + 18, self.toolbar_height + 316), self.small, (205, 215, 220))
        self._text(f"Material   {'Yes' if entity.get_component('material') else 'None'}", (left + 18, self.toolbar_height + 342), self.small, (205, 215, 220))
        self._text(f"Components {len(entity.components)}", (left + 18, self.toolbar_height + 368), self.small, (205, 215, 220))
        if self.rename_mode:
            self._text(f"Rename: {self.rename_buffer}_", (left + 18, self.toolbar_height + 430), self.small, (226, 182, 75))

    def _hierarchy_depth(self, entity_id: int) -> int:
        depth = 0
        entity = self.scene.entity(entity_id)
        parent_id = entity.transform.parent_id if entity else None
        while parent_id is not None and depth < 8:
            depth += 1
            parent = self.scene.entity(parent_id)
            parent_id = parent.transform.parent_id if parent else None
        return depth

    def _text(self, value: str, position: tuple[int, int], font: pygame.font.Font, color: tuple[int, int, int]) -> None:
        self.screen.blit(font.render(value, True, color), position)


def run_editor(engine=None) -> None:
    KSAEditor(engine).run()
