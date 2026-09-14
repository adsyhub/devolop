"""Tests for studio_analysis and studio_repair."""

from __future__ import annotations

import unittest
from studio_analysis import analyze_manifest, compute_content_sha256
from studio_repair import (
    Patch,
    PatchOp,
    apply_patch,
    apply_deterministic_repairs,
    RevisionMismatchError,
    CasConflictError,
    PatchValidationError,
    sha256_text,
)


class StudioAnalysisAndRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_manifest = {
            "schemaVersion": 1,
            "title": "Repair Test Course",
            "audio": "audio.mp3",
            "sourceLanguage": "ja",
            "sentences": [
                {
                    "id": "s-001",
                    "startTime": 0.0,
                    "endTime": 2.5,
                    "sourceText": "これはテストです。  \r\n",
                    "zhTranslation": "这是测试。 ",
                    "explanationText": "テスト：测试。 ",
                },
                {
                    "id": "s-002",
                    "startTime": 2.5,
                    "endTime": 5.0,
                    "sourceText": "二番目の文です。",
                    "zhTranslation": "",
                    "explanationText": "",
                },
            ],
        }

    def test_structured_analysis_identifies_missing_enrichment_and_quality_verdict(self) -> None:
        report = analyze_manifest(self.sample_manifest)
        self.assertIn(report.quality_decision, {"passed", "limited"})
        self.assertGreater(len(report.check_results), 0)
        self.assertIn("# 质量分析报告", report.markdown_report)

        # Sentence 2 missing translation should be recorded as a check result
        missing_zh = [c for c in report.check_results if c.check_id == "enrichment.translation_present"]
        self.assertEqual(len(missing_zh), 1)
        self.assertEqual(missing_zh[0].result, "unknown")

    def test_apply_deterministic_repairs_normalizes_whitespace(self) -> None:
        repaired, ops = apply_deterministic_repairs(self.sample_manifest)
        self.assertEqual(len(ops), 3)  # sourceText, zhTranslation, explanationText for s-001 had trailing spaces
        self.assertEqual(repaired["sentences"][0]["sourceText"], "これはテストです。")
        self.assertEqual(repaired["sentences"][0]["zhTranslation"], "这是测试。")
        self.assertEqual(repaired["sentences"][0]["explanationText"], "テスト:测试。".replace(":", "："))

    def test_apply_patch_success_and_cas_protection(self) -> None:
        current_rev = compute_content_sha256(self.sample_manifest)
        old_val = self.sample_manifest["sentences"][1]["zhTranslation"]

        patch = Patch(
            patch_id="p-001",
            subject_id="course",
            base_revision=current_rev,
            operations=[
                PatchOp(
                    op="replace_field",
                    item_id="s-002",
                    field="zhTranslation",
                    value="这是第二句话。",
                    expected_value_hash=sha256_text(old_val),
                )
            ],
        )

        patched, ok, msg = apply_patch(self.sample_manifest, patch)
        self.assertTrue(ok)
        self.assertEqual(patched["sentences"][1]["zhTranslation"], "这是第二句话。")

        # Wrong expected value hash triggers CAS conflict
        bad_cas_patch = Patch(
            patch_id="p-002",
            subject_id="course",
            base_revision=current_rev,
            operations=[
                PatchOp(
                    op="replace_field",
                    item_id="s-002",
                    field="zhTranslation",
                    value="另一个翻译",
                    expected_value_hash="sha256:nonexistent",
                )
            ],
        )
        with self.assertRaises(CasConflictError):
            apply_patch(self.sample_manifest, bad_cas_patch)

        # Wrong base revision triggers revision mismatch
        bad_rev_patch = Patch(
            patch_id="p-003",
            subject_id="course",
            base_revision="sha256:outdated",
            operations=[
                PatchOp(
                    op="replace_field",
                    item_id="s-002",
                    field="zhTranslation",
                    value="更新",
                )
            ],
        )
        with self.assertRaises(RevisionMismatchError):
            apply_patch(self.sample_manifest, bad_rev_patch)

        # Forbidden field triggers validation error
        forbidden_patch = Patch(
            patch_id="p-004",
            subject_id="course",
            base_revision=current_rev,
            operations=[
                PatchOp(
                    op="replace_field",
                    item_id="s-002",
                    field="__system_code__",
                    value="malicious",
                )
            ],
        )
        with self.assertRaises(PatchValidationError):
            apply_patch(self.sample_manifest, forbidden_patch)

