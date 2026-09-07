from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class StoryPlan:
    intent: str
    objective: str
    beats: tuple[str, ...]
    opening_dialogue: tuple[str, ...]
    entities: tuple[str, ...]


class NarrativeAI:
    """Local deterministic narrative director for prototypes and offline play."""

    _hostage_words = ("مخطوف", "مختطف", "رهينة", "محتجز", "خطف", "kidnap", "kidnapped", "hostage")
    _rescue_words = ("أنقذ", "انقاذ", "ساعد", "إنقاذ", "rescue", "save", "help")
    _combat_words = ("قتال", "معركة", "عدو", "حارس", "battle", "combat", "enemy", "guard")

    def plan(self, description: str) -> StoryPlan:
        text = description.casefold()
        if self._has_any(text, self._hostage_words):
            return StoryPlan(
                intent="rescue_hostage",
                objective="إنقاذ الرجل المخطوف وإخراجه إلى مكان آمن",
                beats=("discover_hostage", "hear_plea", "find_captor", "escape_to_safety"),
                opening_dialogue=("تكفى ساعدني!", "خطفوني وحبسوني هنا... لا تتركني."),
                entities=("hostage", "captor", "rescue_objective"),
            )
        if self._has_any(text, self._combat_words):
            return StoryPlan(
                intent="survive_conflict",
                objective="البقاء على قيد الحياة وحماية أهل المكان",
                beats=("establish_threat", "prepare_for_battle", "resolve_conflict"),
                opening_dialogue=("انتبه، الأعداء يقتربون!",),
                entities=("enemy_group", "rescue_objective"),
            )
        return StoryPlan(
            intent="explore_world",
            objective="استكشاف العالم واكتشاف قصته",
            beats=("establish_environment", "discover_clue", "choose_next_step"),
            opening_dialogue=("هناك شيء غريب يحدث هنا... هل ستكتشفه؟",),
            entities=("guide", "exploration_objective"),
        )

    def respond(self, world_metadata: dict, player_text: str) -> str:
        narrative = world_metadata.get("narrative", {})
        intent = narrative.get("intent", "explore_world")
        text = player_text.casefold().strip()
        if intent == "rescue_hostage":
            if self._has_any(text, self._rescue_words):
                return "سمعتك! المفتاح مع الحارس عند البوابة. أسرع قبل أن يعودوا."
            if "من" in text or "who" in text or "مين" in text:
                return "اسمه لم يُذكر، لكنه يرتدي عباءة سوداء ويحرس الطريق إلى القلعة."
            return "أنا أسمعك من الداخل... اقترب بحذر، الحارس يراقب المكان."
        if self._has_any(text, self._combat_words):
            return "ثبت موقعك واتبع أثر الأقدام؛ الخطر قادم من جهة القلعة."
        return "فهمت. سأضيف ذلك إلى خطتك: استكشف المكان وابحث عن الدليل التالي."

    @staticmethod
    def _has_any(text: str, words: tuple[str, ...]) -> bool:
        return any(re.search(re.escape(word.casefold()), text) for word in words)