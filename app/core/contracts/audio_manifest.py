"""Audio playback contract shared with the reader UI."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.core.contracts.base import FrozenContract


class AudioManifest(FrozenContract):
    contract_version: str = "v1"
    document_id: str
    source_bundle_id: str
    audio_url: str | None = None
    duration_s: float = Field(..., ge=0)
    playback_available: bool = False
    waveform_url: str | None = None
    timing_source: Literal["canonical_bundle", "whisper_words"] = "canonical_bundle"