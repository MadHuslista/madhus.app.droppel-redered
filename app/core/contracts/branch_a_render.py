"""Deterministic transcript rendering contract for Branch A."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from app.core.contracts.base import FrozenContract


class BranchAHeadingBlock(FrozenContract):
    type: Literal["heading"]
    level: int = Field(..., ge=1, le=6)
    text: str
    dom_anchor: str
    start_piece_id: str
    end_piece_id: str


class BranchAParagraphBlock(FrozenContract):
    type: Literal["paragraph"]
    dom_anchor: str
    piece_ids: list[str] = Field(..., min_items=1)


BranchABlock = Annotated[
    BranchAHeadingBlock | BranchAParagraphBlock,
    Field(discriminator="type"),
]


class BranchARender(FrozenContract):
    contract_version: str = "v1"
    document_id: str
    source_bundle_id: str
    blocks: list[BranchABlock]