"""Regression checks for the public evidence-quality projection."""

import csv
import unittest
from collections import Counter
from pathlib import Path

from scripts.describe_evidence import summarize
from scripts.export_evidence_database import analysis_tier


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "literature/evidence_database.csv"


class EvidenceQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with EVIDENCE.open("r", encoding="utf-8-sig", newline="") as stream:
            cls.rows = list(csv.DictReader(stream))

    def test_snapshot_size_and_independent_units(self):
        self.assertEqual(len(self.rows), 428)
        self.assertEqual(len({row["effect_id"] for row in self.rows}), 428)
        self.assertEqual(len({row["study_id"] for row in self.rows}), 26)

    def test_reconciled_tiers_preserve_original(self):
        reconciled = [
            row for row in self.rows
            if row["tier_reconciliation"] == "primary_fulltext_review_reconciled_2026-09-23"
        ]
        self.assertEqual(len(reconciled), 30)
        self.assertEqual(
            Counter(row["study_id"] for row in reconciled),
            {
                "biochar_li2024SD_31": 6,
                "biochar_li2024SD_71": 12,
                "biochar_li2024SD_73": 12,
            },
        )
        self.assertTrue(all("pending" in row["source_analysis_tier"] for row in reconciled))
        self.assertTrue(all("pending" not in row["analysis_tier"] for row in reconciled))

    def test_unresolved_variance_remains_held(self):
        unresolved = [
            row for row in self.rows
            if row["variance_origin_status"] == "unresolved_row_origin"
        ]
        self.assertEqual(len(unresolved), 2)
        self.assertEqual(
            Counter(row["study_id"] for row in unresolved),
            {"biochar_li2024SD_176": 2},
        )
        self.assertTrue(all("variance_row_origin_unresolved" in row["quality_flags"] for row in unresolved))

    def test_primary_table_recheck_is_traceable(self):
        reviewed = [
            row for row in self.rows
            if row["tier_reconciliation"] == "primary_tables_verified_2026-09-23"
        ]
        self.assertEqual(len(reviewed), 20)
        self.assertEqual(
            Counter(row["study_id"] for row in reviewed),
            {"biochar_li2024SD_176": 12, "biochar_li2024SD_3": 8},
        )
        self.assertTrue(all(row["source_locator"] for row in reviewed))
        self.assertTrue(all(row["variance_origin_status"] == "documented_or_reconstructed" for row in reviewed))
        self.assertTrue(all("pending" in row["source_analysis_tier"] for row in reviewed))
        values = {row["effect_id"]: row for row in reviewed}
        yield_sd = {
            "BiocharDS_v1_row_01259_CropYield": (0.569, 0.137),
            "BiocharDS_v1_row_01260_CropYield": (0.347, 0.137),
            "BiocharDS_v1_row_01262_CropYield": (0.199, 0.584),
            "BiocharDS_v1_row_01263_CropYield": (0.843, 0.584),
        }
        for effect_id, (treatment_sd, control_sd) in yield_sd.items():
            self.assertAlmostEqual(float(values[effect_id]["treatment_sd"]), treatment_sd)
            self.assertAlmostEqual(float(values[effect_id]["control_sd"]), control_sd)

    def test_study_count_gate_uses_variance_screen(self):
        summary = {(row["pathway"], row["outcome"]): row for row in summarize(EVIDENCE, 10)}
        self.assertEqual(summary[("biochar_return", "yield")]["independent_studies"], 6)
        self.assertEqual(summary[("biochar_return", "yield")]["variance_screen_independent_studies"], 6)
        self.assertEqual(summary[("biochar_return", "SOC")]["variance_screen_independent_studies"], 5)
        self.assertEqual(summary[("biochar_return", "CH4")]["variance_screen_independent_studies"], 4)
        self.assertEqual(summary[("biochar_return", "N2O")]["variance_screen_independent_studies"], 4)
        passing = [row for row in summary.values() if row["meets_count_threshold"] == "true"]
        self.assertEqual([(row["pathway"], row["outcome"]) for row in passing], [("open_burning", "yield")])

    def test_tier_reconciliation_fails_closed_on_source_change(self):
        source_row = {
            "effect_id": "signature-test",
            "independent_study_key": "biochar_li2024SD_73",
            "analysis_tier": "B1_biochar_setting_independence_pending",
            "analysis_pathway": "biochar_return",
            "analysis_outcome": "SOC",
            "primary_table_locator": "not Table 2",
            "variance_provenance": "primary Table 2 mean ± SD, n=3",
        }
        with self.assertRaisesRegex(ValueError, "signature changed"):
            analysis_tier(source_row)


if __name__ == "__main__":
    unittest.main()
