"""Authentication boundary for local and cloud modes."""

from __future__ import annotations

from typing import Protocol


class AuthVerifier(Protocol):
    def verify_request(self, request) -> dict[str, object]: ...