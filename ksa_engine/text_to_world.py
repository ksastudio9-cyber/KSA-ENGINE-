from __future__ import annotations

import hashlib
import random
import re

from .core import GameWorld, Transform, Vector3
from .narrative import NarrativeAI


class TextToWorldGenerator:
    """Build a deterministic playable world from one Arabic or English sentence."""

    _keywords = {
        "desert": ("صحراء", "رمال", "desert", "sand"),
        "city": ("مدينة", "قرية", "city", "village"),
        "oasis": ("واحة", "نخيل", "oasis"),
        "night": ("ليل", "ليلاً", "night"),
        "fort": ("قلعة", "حصن", "fort"),
        "combat": ("معركة", "قتال", "combat"),
    }

    def generate(self, description: str, seed: int | None = None) -> GameWorld:
        if not description.strip():
            raise ValueError("وصف العالم لا يمكن أن يكون فارغًا")
        resolved_seed = seed if seed is not None else self._seed_from(description)
        rng = random.Random(resolved_seed)
        story_plan = NarrativeAI().plan(description)
        features = {name: self._contains(description, words) for name, words in self._keywords.items()}
        terrain = "desert" if features["desert"] else "plains"
        if features["city"]:
            terrain = "urban_desert" if features["desert"] else "urban_plains"
        world = GameWorld("KSA Generated World", resolved_seed, metadata={
            "source_description": description,
            "terrain": terrain,
            "terrain_features": ["dunes"] if features["desert"] else ["grassland"],
            "time_of_day": "night" if features["night"] else "day",
            "audio": {
                "ambience": "wind" if features["desert"] else "nature",
                "music": "battle_theme" if features["combat"] else "arabian_theme",
                "effects": ["footsteps", "wind"],
            },
            "cinematic": {
                "enabled": True,
                "opening_shot": "establishing",
                "shots": ["establishing", "character_focus", "environment_pan"],
            },
            "ui": {"enabled": True, "widgets": ["health", "compass", "quest_log"]},
            "narrative": {
                "intent": story_plan.intent,
                "objective": story_plan.objective,
                "beats": list(story_plan.beats),
                "dialogue_history": [],
            },
        })

        camera = world.create_entity(
            "Main Camera", "camera", Transform(Vector3(-12, 8, 12)),
            projection="perspective", fov=60.0, target_id=None,
        )
        if features["city"] or features["fort"]:
            building_count = 8 if features["city"] else 3
            for index in range(building_count):
                world.create_entity(
                    f"Building_{index + 1}",
                    "building",
                    Transform(Vector3(index * 6.0, 0.0, rng.uniform(-8.0, 8.0))),
                    style="arabian", material="stone",
                )
        if features["oasis"]:
            for index in range(5):
                world.create_entity(
                    f"Palm_{index + 1}", "vegetation",
                    Transform(Vector3(rng.uniform(-5.0, 5.0), 0.0, rng.uniform(-5.0, 5.0))),
                    species="date_palm",
                )
        if story_plan.intent == "rescue_hostage":
            world.create_entity(
                "Hostage",
                "npc",
                Transform(Vector3(8.0, 0.0, 2.0)),
                role="hostage",
                dialogue=list(story_plan.opening_dialogue),
                state="waiting_for_rescue",
            )
            world.create_entity(
                "Captor",
                "npc",
                Transform(Vector3(12.0, 0.0, 2.0)),
                role="captor",
                state="guarding_hostage",
            )
        character_count = 3 if features["combat"] else 1
        for index in range(character_count):
            character = world.create_entity(
                f"Character_{index + 1}", "character",
                Transform(Vector3(rng.uniform(-4.0, 4.0), 0.0, rng.uniform(-4.0, 4.0))),
                animation={"clip": "combat" if features["combat"] else "idle", "time": 0.0},
                role="warrior" if features["combat"] else "traveler",
            )
            if index == 0:
                camera.components["target_id"] = character.id
        world.create_entity(
            "Sun Light", "light",
            intensity=0.35 if features["night"] else 1.0,
            color="warm", kind_of_light="directional",
        )
        return world

    @staticmethod
    def _contains(text: str, words: tuple[str, ...]) -> bool:
        normalized = text.casefold()
        return any(re.search(re.escape(word.casefold()), normalized) for word in words)

    @staticmethod
    def _seed_from(description: str) -> int:
        digest = hashlib.sha256(description.strip().encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big")
