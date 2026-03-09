"""Contract validation tests for the Phase 0 foundation."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.core.contracts.audio_manifest import AudioManifest
from app.core.contracts.branch_a_render import BranchARender
from app.core.contracts.branch_c_render import BranchCRender
from app.core.contracts.clusters_render import ClustersRender
from app.core.contracts.document_manifest import ArtifactPaths, DocumentManifest, ManifestSource, ManifestVersions
from app.core.contracts.pieces_index import PieceRecord, PiecesIndex


class ContractTests(unittest.TestCase):
    def test_document_manifest_accepts_phase0_shape(self) -> None:
        manifest = DocumentManifest(
            tenant_id="local-dev",
            document_id="sample01-a",
            document_family_id="sample01",
            variant_id="a",
            source_bundle_id="sample01_p03_bundle_a",
            title="Sample 01 / Variant A",
            owner_user_id="local-dev",
            available_views=["branch_a", "audio"],
            artifacts=ArtifactPaths(
                document_manifest="sample_data/rendered/sample01-a/document_manifest.json",
                pieces_index="sample_data/rendered/sample01-a/pieces_index.json",
                branch_a_render="sample_data/rendered/sample01-a/branch_a_render.json",
                audio_manifest="sample_data/rendered/sample01-a/audio_manifest.json",
            ),
            versions=ManifestVersions(
                canonical_bundle="sample01_p03_bundle_a",
                branch_a="sample01_a1_output_a",
                renderer_pack="v1",
            ),
            source=ManifestSource(
                kind="local_sample",
                raw_artifacts_root="data",
                imported_variant_root="sample_data/imported/sample01/a",
                rendered_document_root="sample_data/rendered/sample01-a",
            ),
        )
        self.assertEqual(manifest.document_id, "sample01-a")

    def test_document_manifest_rejects_extra_fields(self) -> None:
        with self.assertRaises(ValidationError):
            DocumentManifest(
                tenant_id="local-dev",
                document_id="sample01-a",
                document_family_id="sample01",
                variant_id="a",
                source_bundle_id="sample01_p03_bundle_a",
                title="title",
                owner_user_id="local-dev",
                available_views=["branch_a", "audio"],
                artifacts=ArtifactPaths(
                    document_manifest="a",
                    pieces_index="b",
                    branch_a_render="c",
                    audio_manifest="d",
                ),
                versions=ManifestVersions(canonical_bundle="bundle", renderer_pack="v1"),
                source=ManifestSource(
                    kind="local_sample",
                    raw_artifacts_root="data",
                    imported_variant_root="sample_data/imported/sample01/a",
                    rendered_document_root="sample_data/rendered/sample01-a",
                ),
                surprise="nope",
            )

    def test_pieces_index_rejects_bad_duration(self) -> None:
        with self.assertRaises(ValidationError):
            PiecesIndex(
                document_id="sample01-a",
                source_bundle_id="sample01_p03_bundle_a",
                piece_count=1,
                pieces=[
                    PieceRecord(
                        piece_id="p0",
                        ordinal=0,
                        piece_text="hello",
                        start_s=10.0,
                        end_s=12.0,
                        duration_s=1.0,
                        dom_anchor="piece-p0",
                    )
                ],
            )

    def test_branch_a_render_accepts_heading_and_paragraph_blocks(self) -> None:
        render = BranchARender(
            document_id="sample01-a",
            source_bundle_id="sample01_p03_bundle_a",
            blocks=[
                {
                    "type": "heading",
                    "level": 1,
                    "text": "Title",
                    "dom_anchor": "h-title",
                    "start_piece_id": "p0",
                    "end_piece_id": "p3",
                },
                {
                    "type": "paragraph",
                    "dom_anchor": "para-0",
                    "piece_ids": ["p0", "p1"],
                },
            ],
        )
        self.assertEqual(len(render.blocks), 2)

    def test_branch_c_render_requires_citations(self) -> None:
        with self.assertRaises(ValidationError):
            BranchCRender(
                document_id="sample01-a",
                source_bundle_id="sample01_p03_bundle_a",
                blocks=[
                    {
                        "type": "summary_sentence",
                        "sentence_id": "s0",
                        "text": "Summary text",
                        "dom_anchor": "s0",
                        "cited_piece_ids": [],
                    }
                ],
            )

    def test_clusters_render_accepts_empty_cluster_list(self) -> None:
        render = ClustersRender(
            document_id="sample01-a",
            source_bundle_id="sample01_p03_bundle_a",
            clusters=[],
        )
        self.assertEqual(render.clusters, [])

    def test_audio_manifest_supports_placeholder_audio(self) -> None:
        manifest = AudioManifest(
            document_id="sample01-a",
            source_bundle_id="sample01_p03_bundle_a",
            duration_s=943.317,
            playback_available=False,
        )
        self.assertFalse(manifest.playback_available)

    def test_document_identity_accepts_underscore_source_bundle_id(self) -> None:
        from app.core.sample_normalization import SampleVariant

        identity = SampleVariant("sample01", "a").as_identity()
        self.assertEqual(identity.source_bundle_id, "sample01_p03_bundle_a")


if __name__ == "__main__":
    unittest.main()