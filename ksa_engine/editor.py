from __future__ import annotations

import json
from pathlib import Path

import pygame

from .demo import build_engine
from .renderer3d import run_game_3d


class KSAEditor:
    """A lightweight visual game-making workspace for the KSA vertical slice."""

    width = 1440
    height = 860

    def __init__(self, description: str = "مدينة صحراوية ليلية فيها واحة ومعركة") -> None:
        pygame.init()
        pygame.display.set_caption("KSA ENGINE | محرر صناعة الألعاب")
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.heading = pygame.font.Font(None, 42)
        self.small = pygame.font.Font(None, 20)
        self.description = description
        self.cursor = len(description)
        self.engine = build_engine(description)
        self.status = "العالم جاهز. عدّل الوصف ثم اضغط توليد العالم."
        self.running = True
        self.editing = True

    def run(self) -> None:
        while self.running:
            self._events()
            self._draw()
            self.clock.tick(60)
        pygame.quit()

    def _events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._key_down(event)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._click(event.pos)

    def _key_down(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_BACKSPACE and self.editing:
            self.description = self.description[: max(0, self.cursor - 1)] + self.description[self.cursor :]
            self.cursor = max(0, self.cursor - 1)
        elif event.key == pygame.K_DELETE and self.editing:
            self.description = self.description[: self.cursor] + self.description[self.cursor + 1 :]
        elif event.key == pygame.K_LEFT and self.editing:
            self.cursor = max(0, self.cursor - 1)
        elif event.key == pygame.K_RIGHT and self.editing:
            self.cursor = min(len(self.description), self.cursor + 1)
        elif event.key == pygame.K_RETURN:
            self._generate()
        elif self.editing and event.unicode and event.unicode.isprintable():
            self.description = self.description[: self.cursor] + event.unicode + self.description[self.cursor :]
            self.cursor += len(event.unicode)

    def _click(self, position: tuple[int, int]) -> None:
        x, y = position
        if 32 <= x <= 1020 and 112 <= y <= 174:
            self.editing = True
        elif 32 <= x <= 220 and 196 <= y <= 246:
            self._generate()
        elif 238 <= x <= 426 and 196 <= y <= 246:
            self._save_project()
        elif 444 <= x <= 632 and 196 <= y <= 246:
            pygame.display.quit()
            run_game_3d(self.engine)
            pygame.display.set_mode((self.width, self.height))
        elif 32 <= x <= 220 and 790 <= y <= 838:
            self.running = False

    def _generate(self) -> None:
        if self.description.strip():
            self.engine = build_engine(self.description)
            self.status = f"تم توليد {len(self.engine.world.entities)} عناصر من وصفك."
            self.cursor = len(self.description)

    def _save_project(self) -> None:
        world = self.engine.world
        if world is None:
            return
        project = {
            "name": world.name,
            "seed": world.seed,
            "description": self.description,
            "metadata": world.metadata,
            "entities": [
                {
                    "id": entity.id,
                    "name": entity.name,
                    "kind": entity.kind,
                    "position": vars(entity.transform.position),
                    "components": entity.components,
                }
                for entity in world.entities.values()
            ],
        }
        Path("ksa_project.json").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
        self.status = "تم حفظ المشروع في ksa_project.json"

    def _draw(self) -> None:
        self.screen.fill((18, 25, 39))
        pygame.draw.rect(self.screen, (12, 18, 30), (0, 0, self.width, 80))
        pygame.draw.rect(self.screen, (24, 33, 50), (24, 96, 1010, 82), border_radius=6)
        pygame.draw.rect(self.screen, (27, 38, 56), (24, 188, 1010, 570), border_radius=6)
        pygame.draw.rect(self.screen, (27, 38, 56), (1054, 96, 356, 662), border_radius=6)
        self._text("KSA ENGINE", (28, 20), self.heading, (244, 201, 101))
        self._text("محرر صناعة الألعاب", (260, 31), self.small, (164, 181, 198))
        self._text("اكتب وصف عالم لعبتك", (40, 108), self.small, (166, 186, 205))
        self._text(self.description or "اكتب وصف العالم...", (40, 135), self.font, (240, 240, 230))
        if self.editing and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = 40 + self.font.size(self.description[: self.cursor])[0]
            pygame.draw.line(self.screen, (244, 201, 101), (cursor_x, 132), (cursor_x, 158), 2)
        self._button("توليد العالم", (32, 196), (188, 50), (74, 126, 108))
        self._button("حفظ المشروع", (238, 196), (188, 50), (65, 96, 130))
        self._button("تشغيل ثلاثي الأبعاد", (444, 196), (188, 50), (142, 95, 61))
        self._draw_preview()
        self._draw_inspector()
        self._text(self.status, (32, 775), self.small, (176, 192, 202))
        self._button("خروج", (32, 790), (188, 48), (104, 59, 67))
        pygame.display.flip()

    def _draw_preview(self) -> None:
        preview = pygame.Rect(42, 270, 974, 450)
        pygame.draw.rect(self.screen, (34, 52, 62), preview)
        for x in range(preview.left, preview.right, 42):
            pygame.draw.line(self.screen, (42, 68, 72), (x, preview.top), (x, preview.bottom), 1)
        for y in range(preview.top, preview.bottom, 42):
            pygame.draw.line(self.screen, (42, 68, 72), (preview.left, y), (preview.right, y), 1)
        world = self.engine.world
        if world is None:
            return
        entities = list(world.entities.values())
        for index, entity in enumerate(entities):
            x = preview.left + 80 + (index * 113) % (preview.width - 120)
            y = preview.top + 80 + ((index * 71) % (preview.height - 130))
            color = {"building": (173, 112, 68), "character": (223, 181, 75), "npc": (72, 166, 179), "vegetation": (65, 135, 78), "light": (239, 200, 105), "camera": (186, 193, 205)}.get(entity.kind, (112, 135, 150))
            pygame.draw.circle(self.screen, color, (x, y), 12 if entity.kind != "building" else 18)
        self._text("معاينة العالم", (58, 286), self.small, (224, 229, 218))

    def _draw_inspector(self) -> None:
        world = self.engine.world
        if world is None:
            return
        self._text("معلومات العالم", (1076, 120), self.font, (244, 201, 101))
        lines = [
            f"البذرة: {world.seed}",
            f"العناصر: {len(world.entities)}",
            f"التضاريس: {world.metadata.get('terrain', 'غير معروف')}",
            f"الوقت: {world.metadata.get('time_of_day', 'نهار')}",
            "",
            "مدير القصة",
            f"النية: {world.metadata.get('narrative', {}).get('intent', 'لا يوجد')}",
            f"الهدف: {world.metadata.get('narrative', {}).get('objective', '')}",
            "",
            "العناصر",
        ]
        for index, line in enumerate(lines):
            self._text(line, (1076, 166 + index * 27), self.small, (208, 218, 224))
        for index, entity in enumerate(list(world.entities.values())[:8]):
            self._text(f"{entity.id:02d}  {entity.kind:<12} {entity.name[:18]}", (1076, 485 + index * 25), self.small, (157, 180, 192))

    def _button(self, label: str, position: tuple[int, int], size: tuple[int, int], color: tuple[int, int, int]) -> None:
        rect = pygame.Rect(position, size)
        pygame.draw.rect(self.screen, color, rect, border_radius=5)
        text = self.small.render(label, True, (248, 248, 238))
        self.screen.blit(text, text.get_rect(center=rect.center))

    def _text(self, value: str, position: tuple[int, int], font: pygame.font.Font, color: tuple[int, int, int]) -> None:
        self.screen.blit(font.render(value, True, color), position)


def run_editor(description: str | None = None) -> None:
    KSAEditor(description or "مدينة صحراوية ليلية فيها واحة ومعركة").run()