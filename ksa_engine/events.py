"""Event and input primitives shared by runtime and tools."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Event:
    name: str
    payload: dict[str, Any]


class EventBus:
    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[Event], None]]] = defaultdict(list)
        self._queue: deque[Event] = deque()

    def subscribe(self, name: str, listener: Callable[[Event], None]) -> None:
        self._listeners[name].append(listener)

    def publish(self, name: str, **payload: Any) -> None:
        self._queue.append(Event(name, payload))

    def flush(self) -> None:
        while self._queue:
            event = self._queue.popleft()
            for listener in tuple(self._listeners.get(event.name, ())):
                listener(event)


class InputState:
    def __init__(self) -> None:
        self.keys: set[str] = set()
        self.mouse_position = (0, 0)
        self.mouse_buttons: set[int] = set()

    def is_down(self, key: str) -> bool:
        return key in self.keys
