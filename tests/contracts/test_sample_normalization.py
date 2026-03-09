"""Normalization rules are frozen before importer and packager work begins."""

from __future__ import annotations

import unittest
from pathlib import Path

from app.core.render_artifacts import RenderArtifactName
from app.core.sample_normalization import (
    SampleVariant,
    imported_variant_root,
    parse_sample_variant,
    parse_whisper_family,
    raw_sample_paths,
    rendered_contract_path,
)


class SampleNormalizationTests(unittest.TestCase):
    def test_parse_variant_from_canonical_bundle(self) -> None:
        variant = parse_sample_variant("sample01_p03_bundle_a.json")
        self.assertEqual(variant, SampleVariant(family_id="sample01", variant_id="a"))

    def test_parse_variant_from_branch_b_directory(self) -> None:
        variant = parse_sample_variant("sample02_p03_bundle_b")
        self.assertEqual(variant.document_id, "sample02-b")

    def test_parse_whisper_family(self) -> None:
        family_id = parse_whisper_family("sample01_n06_sample_output_word.json")
        self.assertEqual(family_id, "sample01")

    def test_import_root_is_family_then_variant(self) -> None:
        variant = SampleVariant("sample01", "a")
        self.assertEqual(
            imported_variant_root(Path("sample_data"), variant),
            Path("sample_data/imported/sample01/a"),
        )

    def test_render_path_is_document_scoped(self) -> None:
        variant = SampleVariant("sample01", "a")
        self.assertEqual(
            rendered_contract_path(
                Path("sample_data/rendered"),
                variant,
                RenderArtifactName.PIECES_INDEX,
            ),
            Path("sample_data/rendered/sample01-a/pieces_index.json"),
        )

    def test_raw_paths_match_current_repo_layout(self) -> None:
        variant = SampleVariant("sample01", "b")
        paths = raw_sample_paths(Path("data"), variant)
        self.assertEqual(
            paths.branch_b_clusters_final_json,
            Path(
                "data/b1_clusters/sample01_p03_bundle_b/stage5_out/branch_b_clusters_final.json"
            ),
        )


if __name__ == "__main__":
    unittest.main()