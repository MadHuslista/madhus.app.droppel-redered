"""Rules for normalizing local sample artifacts before packaging."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.core.ids import DocumentIdentity
from app.core.render_artifacts import RenderArtifactName, rendered_artifact_path
from app.errors import NormalizationError

_SAMPLE_ID = r"(?P<family>sample[0-9]{2})"
_VARIANT = r"(?P<variant>[a-z])"

CANONICAL_BUNDLE_RE = re.compile(rf"^{_SAMPLE_ID}_p03_bundle_{_VARIANT}\.json$")
SAT_SPLIT_RE = re.compile(rf"^{_SAMPLE_ID}_p02_sat_split_{_VARIANT}\.json$")
TITLE_TREE_RE = re.compile(rf"^{_SAMPLE_ID}_a1_output_{_VARIANT}\.json$")
BRANCH_A_MD_RE = re.compile(rf"^{_SAMPLE_ID}_a2_output_{_VARIANT}\.md$")
BRANCH_B_DIR_RE = re.compile(rf"^{_SAMPLE_ID}_p03_bundle_{_VARIANT}$")
WHISPER_RE = re.compile(rf"^{_SAMPLE_ID}_n06_sample_output_word\.json$")


@dataclass(frozen=True)
class SampleVariant:
    family_id: str
    variant_id: str

    @property
    def document_id(self) -> str:
        return f"{self.family_id}-{self.variant_id}"

    @property
    def source_bundle_id(self) -> str:
        return f"{self.family_id}_p03_bundle_{self.variant_id}"

    def as_identity(self, tenant_id: str = "local-dev") -> DocumentIdentity:
        return DocumentIdentity(
            tenant_id=tenant_id,
            document_id=self.document_id,
            document_family_id=self.family_id,
            variant_id=self.variant_id,
            source_bundle_id=self.source_bundle_id,
        )


@dataclass(frozen=True)
class RawSamplePaths:
    whisper_json: Path
    sat_split_json: Path
    canonical_bundle_json: Path
    branch_a_title_tree_json: Path
    branch_a_markdown: Path
    branch_b_root: Path
    branch_b_clusters_final_json: Path
    branch_b_piece_to_cluster_json: Path


def parse_sample_variant(filename: str) -> SampleVariant:
    for pattern in (CANONICAL_BUNDLE_RE, SAT_SPLIT_RE, TITLE_TREE_RE, BRANCH_A_MD_RE, BRANCH_B_DIR_RE):
        match = pattern.fullmatch(filename)
        if match:
            return SampleVariant(match.group("family"), match.group("variant"))
    msg = f"unsupported sample variant filename: {filename}"
    raise NormalizationError(msg)


def parse_whisper_family(filename: str) -> str:
    match = WHISPER_RE.fullmatch(filename)
    if not match:
        msg = f"unsupported whisper filename: {filename}"
        raise NormalizationError(msg)
    return match.group("family")


def imported_family_root(sample_data_root: Path, family_id: str) -> Path:
    return sample_data_root / "imported" / family_id


def imported_variant_root(sample_data_root: Path, variant: SampleVariant) -> Path:
    return imported_family_root(sample_data_root, variant.family_id) / variant.variant_id


def imported_metadata_path(sample_data_root: Path, variant: SampleVariant) -> Path:
    return imported_variant_root(sample_data_root, variant) / "metadata.json"


def rendered_document_root(render_output_root: Path, variant: SampleVariant) -> Path:
    return render_output_root / variant.document_id


def rendered_contract_path(
    render_output_root: Path,
    variant: SampleVariant,
    artifact_name: RenderArtifactName,
) -> Path:
    return rendered_artifact_path(render_output_root, variant.document_id, artifact_name)


def raw_sample_paths(raw_artifacts_root: Path, variant: SampleVariant) -> RawSamplePaths:
    return RawSamplePaths(
        whisper_json=raw_artifacts_root
        / "n06_whisper"
        / f"{variant.family_id}_n06_sample_output_word.json",
        sat_split_json=raw_artifacts_root
        / "p02_split_SaT"
        / f"{variant.family_id}_p02_sat_split_{variant.variant_id}.json",
        canonical_bundle_json=raw_artifacts_root
        / "p03_build_cannon_bundle"
        / f"{variant.source_bundle_id}.json",
        branch_a_title_tree_json=raw_artifacts_root
        / "a1_tittle_tree"
        / f"{variant.family_id}_a1_output_{variant.variant_id}.json",
        branch_a_markdown=raw_artifacts_root
        / "a2_recompose_md"
        / f"{variant.family_id}_a2_output_{variant.variant_id}.md",
        branch_b_root=raw_artifacts_root / "b1_clusters" / variant.source_bundle_id,
        branch_b_clusters_final_json=raw_artifacts_root
        / "b1_clusters"
        / variant.source_bundle_id
        / "stage5_out"
        / "branch_b_clusters_final.json",
        branch_b_piece_to_cluster_json=raw_artifacts_root
        / "b1_clusters"
        / variant.source_bundle_id
        / "stage5_out"
        / "piece_to_cluster.json",
    )