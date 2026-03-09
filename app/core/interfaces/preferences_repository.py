"""Reader preference persistence boundary."""

from __future__ import annotations

from typing import Protocol


class PreferencesRepository(Protocol):
    def get_preferences(self, tenant_id: str, document_id: str) -> dict[str, object] | None: ...

    def save_preferences(self, tenant_id: str, document_id: str, payload: dict[str, object]) -> None: ...