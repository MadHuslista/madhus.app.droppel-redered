"""Canonical piece index shared by all views."""

from __future__ import annotations

from pydantic import Field, root_validator

from app.core.contracts.base import FrozenContract


class PieceRecord(FrozenContract):
    piece_id: str
    ordinal: int = Field(..., ge=0)
    piece_text: str
    whisper_text: str | None = None
    start_s: float = Field(..., ge=0)
    end_s: float = Field(..., ge=0)
    duration_s: float = Field(..., ge=0)
    dom_anchor: str
    cluster_ids: list[str] = Field(default_factory=list)
    text_hash: str | None = None

    @root_validator
    def validate_time_range(cls, values: dict) -> dict:
        start_s = values.get("start_s")
        end_s = values.get("end_s")
        duration_s = values.get("duration_s")
        if end_s is not None and start_s is not None and end_s < start_s:
            raise ValueError("end_s must be greater than or equal to start_s")
        if (
            start_s is not None
            and end_s is not None
            and duration_s is not None
            and abs((end_s - start_s) - duration_s) > 1e-3
        ):
            raise ValueError("duration_s must match start/end range")
        return values


class PiecesIndex(FrozenContract):
    contract_version: str = "v1"
    document_id: str
    source_bundle_id: str
    piece_count: int = Field(..., ge=0)
    pieces: list[PieceRecord]

    @root_validator
    def validate_piece_count(cls, values: dict) -> dict:
        piece_count = values.get("piece_count")
        pieces = values.get("pieces") or []
        if piece_count is not None and piece_count != len(pieces):
            raise ValueError("piece_count must match number of pieces")
        return values