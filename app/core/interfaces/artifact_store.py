"""Artifact storage protocol shared by local and cloud adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ArtifactStore(Protocol):
    def read_json(self, path: Path) -> dict: ...

    def write_json(self, path: Path, payload: dict) -> None: ...

    def read_text(self, path: Path) -> str: ...

    def write_text(self, path: Path, content: str) -> None: ...

    def exists(self, path: Path) -> bool: ...

    def media_url(self, path: Path, ttl_seconds: int = 900) -> str: ...