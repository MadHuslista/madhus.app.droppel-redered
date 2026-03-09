"""Dependency accessors kept deliberately small for Phase 0."""

from __future__ import annotations

from functools import lru_cache

from app.settings import Settings, load_settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()