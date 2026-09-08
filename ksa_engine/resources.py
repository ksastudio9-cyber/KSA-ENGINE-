"""Small cached resource manager with explicit loader registration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


class ResourceManager:
    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], Any] = {}
        self._loaders: dict[str, Callable[[Path], Any]] = {}

    def register_loader(self, extension: str, loader: Callable[[Path], Any]) -> None:
        self._loaders[extension.lower().lstrip(".")] = loader

    def load(self, path: str | Path, resource_type: str | None = None) -> Any:
        file_path = Path(path)
        kind = (resource_type or file_path.suffix.lstrip(".")).lower()
        key = (kind, str(file_path.resolve()))
        if key in self._cache:
            return self._cache[key]
        loader = self._loaders.get(kind)
        if loader is None:
            raise ValueError(f"No resource loader registered for '{kind}'")
        resource = loader(file_path)
        self._cache[key] = resource
        return resource

    def unload(self, path: str | Path, resource_type: str | None = None) -> None:
        file_path = Path(path)
        kind = (resource_type or file_path.suffix.lstrip(".")).lower()
        self._cache.pop((kind, str(file_path.resolve())), None)

    def clear(self) -> None:
        self._cache.clear()

    @property
    def loaded_count(self) -> int:
        return len(self._cache)
