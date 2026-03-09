"""Cluster overlay contract for Branch B."""

from __future__ import annotations

from pydantic import Field

from app.core.contracts.base import FrozenContract


class ClusterRecord(FrozenContract):
    cluster_id: str
    label: str
    default_color: str
    keywords: list[str] = Field(default_factory=list)
    piece_ids: list[str] = Field(..., min_items=1)


class ClustersRender(FrozenContract):
    contract_version: str = "v1"
    document_id: str
    source_bundle_id: str
    clusters: list[ClusterRecord] = Field(default_factory=list)