"""Canonical render artifact names and deterministic output helpers."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path


class RenderArtifactName(StrEnum):
    DOCUMENT_MANIFEST = "document_manifest"
    PIECES_INDEX = "pieces_index"
    BRANCH_A_RENDER = "branch_a_render"
    BRANCH_C_RENDER = "branch_c_render"
    CLUSTERS_RENDER = "clusters_render"
    AUDIO_MANIFEST = "audio_manifest"

    @property
    def filename(self) -> str:
        return f"{self.value}.json"


def rendered_artifact_path(
    render_output_root: Path,
    document_id: str,
    artifact_name: RenderArtifactName,
) -> Path:
    return render_output_root / document_id / artifact_name.filename