"""Grounded summary rendering contract for Branch C."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from app.core.contracts.base import FrozenContract


class BranchCHeadingBlock(FrozenContract):
    type: Literal["heading"]
    level: int = Field(..., ge=1, le=6)
    text: str
    dom_anchor: str


class BranchCSummarySentenceBlock(FrozenContract):
    type: Literal["summary_sentence"]
    sentence_id: str
    text: str
    dom_anchor: str
    cited_piece_ids: list[str] = Field(..., min_items=1)


BranchCBlock = Annotated[
    BranchCHeadingBlock | BranchCSummarySentenceBlock,
    Field(discriminator="type"),
]


class BranchCRender(FrozenContract):
    contract_version: str = "v1"
    document_id: str
    source_bundle_id: str
    summary_source: Literal["fixture", "pipeline"] = "fixture"
    blocks: list[BranchCBlock]