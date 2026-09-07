from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


@dataclass
class LLMNarrativeAI:
    """Real model-backed director for Ollama or any OpenAI-compatible endpoint."""

    base_url: str
    model: str
    api_key: str | None = None
    timeout: float = 30.0
    pending_actions: list[dict[str, Any]] = field(default_factory=list)
    last_error: str | None = None

    @classmethod
    def from_environment(cls) -> "LLMNarrativeAI | None":
        base_url = os.getenv("KSA_LLM_BASE_URL", "").strip()
        if not base_url:
            return None
        return cls(
            base_url=base_url.rstrip("/"),
            model=os.getenv("KSA_LLM_MODEL", "llama3.2").strip(),
            api_key=os.getenv("KSA_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
        )

    def respond(self, world_metadata: dict[str, Any], player_text: str) -> str:
        self.pending_actions = []
        prompt = self._prompt(world_metadata, player_text)
        try:
            raw = self._request(prompt)
            response = self._decode(raw)
            self.last_error = None
            self.pending_actions = self._safe_actions(response.get("world_actions", []))
            return str(response.get("reply", "لم أفهم طلبك بالكامل، لكنني سأبحث في العالم عن طريقة للمساعدة."))
        except (OSError, URLError, ValueError, KeyError, json.JSONDecodeError) as error:
            self.last_error = str(error)
            return "تعذر الاتصال بعقل العالم الآن. شغّل نموذج Ollama أو راجع إعدادات KSA_LLM_BASE_URL."

    def consume_actions(self) -> list[dict[str, Any]]:
        actions = self.pending_actions
        self.pending_actions = []
        return actions

    def _request(self, prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "أنت مدير قصة داخل KSA ENGINE. افهم كلام اللاعب بحرية، تذكر السياق، "
                    "وطور القصة من نفسك. أعد JSON صالحا فقط بالمفاتيح: reply نص عربي طبيعي، "
                    "world_actions قائمة. كل world_action يمكن أن يكون {action:'spawn_entity', "
                    "name, kind, role, dialogue} أو {action:'set_objective', objective}. "
                    "لا تنشئ أكثر من كيانين في الرد ولا تستخدم أنواعًا خطرة."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        payload = json.dumps({"model": self.model, "messages": messages, "stream": False}).encode("utf-8")
        is_ollama = ":11434" in self.base_url or self.base_url.endswith("/api")
        endpoint = f"{self.base_url}/chat" if is_ollama else f"{self.base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(endpoint, data=payload, headers=headers, method="POST")
        with urlopen(request, timeout=self.timeout) as response:
            document = json.loads(response.read().decode("utf-8"))
        return document["message"]["content"] if is_ollama else document["choices"][0]["message"]["content"]

    def _prompt(self, metadata: dict[str, Any], player_text: str) -> str:
        narrative = metadata.get("narrative", {})
        history = narrative.get("dialogue_history", [])[-8:]
        context = {
            "world": metadata.get("source_description", ""),
            "objective": narrative.get("objective", ""),
            "beats": narrative.get("beats", []),
            "history": history,
        }
        return f"سياق العالم:\n{json.dumps(context, ensure_ascii=False)}\n\nكلام اللاعب الآن:\n{player_text}"

    @staticmethod
    def _decode(raw: str) -> dict[str, Any]:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        decoded = json.loads(clean)
        if not isinstance(decoded, dict) or not isinstance(decoded.get("reply"), str):
            raise ValueError("model response must contain a reply")
        return decoded

    @staticmethod
    def _safe_actions(actions: Any) -> list[dict[str, Any]]:
        if not isinstance(actions, list):
            return []
        safe: list[dict[str, Any]] = []
        for action in actions[:2]:
            if not isinstance(action, dict) or action.get("action") not in {"spawn_entity", "set_objective"}:
                continue
            safe.append(action)
        return safe