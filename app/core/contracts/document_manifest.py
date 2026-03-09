"""Document metadata contract consumed by the renderer."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.core.contracts.base import FrozenContract


class ArtifactPaths(FrozenContract):
    document_manifest: str
    pieces_index: str
    branch_a_render: str
    branch_c_render: str | None = None
    clusters_render: str | None = None
    audio_manifest: str


class ManifestVersions(FrozenContract):
    canonical_bundle: str
    branch_a: str | None = None
    branch_b: str | None = None
    branch_c: str | None = None
    renderer_pack: str


class ManifestSource(FrozenContract):
    kind: Literal["local_sample", "uploaded"]
    raw_artifacts_root: str
    imported_variant_root: str
    rendered_document_root: str


class DocumentManifest(FrozenContract):
    contract_version: str = "v1"
    tenant_id: str
    document_id: str
    document_family_id: str
    variant_id: str
    source_bundle_id: str
    title: str
    owner_user_id: str
    status: Literal["ready", "missing_optional_artifacts"] = "ready"
    available_views: list[Literal["branch_a", "branch_c", "clusters", "audio"]]
    artifacts: ArtifactPaths
    versions: ManifestVersions
    source: ManifestSource
    notes: list[str] = Field(default_factory=list)