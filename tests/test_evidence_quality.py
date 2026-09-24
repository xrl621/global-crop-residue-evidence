"""Regression checks for the public evidence-quality projection."""

import csv
import unittest
from collections import Counter
from pathlib import Path

from scripts.describe_evidence import summarize
from scripts.export_evidence_database import analysis_tier
from scripts.analyze_open_burning_yield_exploratory import study_level, summarize as burning_summary


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "literature/evidence_database.csv"


class EvidenceQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with EVIDENCE.open("r", encoding="utf-8-sig", newline="") as stream:
            cls.rows = list(csv.DictReader(stream))

    def test_snapshot_size_and_independent_units(self):
        self.assertEqual(len(self.rows), 488)
        self.assertEqual(len({row["effect_id"] for row in self.rows}), 488)
        self.assertEqual(len({row["study_id"] for row in self.rows}), 30)

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
        self.assertEqual(summary[("direct_return", "yield")]["independent_studies"], 11)
        self.assertEqual(summary[("direct_return", "yield")]["strict_screen_independent_studies"], 8)
        self.assertEqual(summary[("direct_return", "SOC")]["independent_studies"], 9)
        self.assertEqual(summary[("direct_return", "CH4")]["independent_studies"], 4)
        self.assertEqual(summary[("direct_return", "N2O")]["independent_studies"], 5)
        self.assertEqual(summary[("biochar_return", "yield")]["independent_studies"], 6)
        self.assertEqual(summary[("biochar_return", "yield")]["variance_screen_independent_studies"], 6)
        self.assertEqual(summary[("biochar_return", "SOC")]["variance_screen_independent_studies"], 5)
        self.assertEqual(summary[("biochar_return", "CH4")]["variance_screen_independent_studies"], 4)
        self.assertEqual(summary[("biochar_return", "N2O")]["variance_screen_independent_studies"], 4)
        passing = [row for row in summary.values() if row["meets_count_threshold"] == "true"]
        self.assertEqual([(row["pathway"], row["outcome"]) for row in passing], [("direct_return", "yield"), ("open_burning", "yield")])
        strictly_passing = [row for row in summary.values() if row["meets_strict_threshold"] == "true"]
        self.assertEqual(strictly_passing, [])
        self.assertEqual(summary[("direct_return", "yield")]["straw_origin_screen_independent_studies"], 7)
        self.assertEqual(summary[("direct_return", "yield")]["straw_origin_screen_effect_rows"], 35)
        self.assertEqual(summary[("open_burning", "yield")]["strict_screen_independent_studies"], 9)
        self.assertEqual(summary[("open_burning", "yield")]["straw_origin_screen_independent_studies"], 8)
        self.assertEqual(summary[("open_burning", "yield")]["straw_origin_screen_effect_rows"], 16)
        self.assertFalse(any(row["meets_straw_origin_threshold"] == "true" for row in summary.values()))

    def test_rice_140_yield_labels_and_land_clearing_source_screen(self):
        by_id = {row["effect_id"]: row for row in self.rows}
        expected = {
            "0013": ("RoT + S", "RoT - S", "rice in rice-wheat cropping system"),
            "0014": ("PT + S", "PT - S", "single rice"),
            "0015": ("RoT + S", "RoT - S", "double rice"),
        }
        for pair, (treatment, control, crop) in expected.items():
            row = by_id[f"rice_primary_rice_ext_pair_{pair}_yield"]
            self.assertEqual((row["treatment_arm"], row["control_arm"]), (treatment, control))
            self.assertEqual((row["crop_as_reported"], row["crop_core"]), (crop, "rice"))
            self.assertIn("primary_table_metadata_backfilled", row["quality_flags"])
        pending = [row for row in self.rows if row["study_id"] == "rice_primary_140" and row["outcome"] != "yield"]
        self.assertEqual(len(pending), 12)
        self.assertTrue(all("primary_non_yield_arm_and_value_recheck" in row["quality_flags"] for row in pending))
        land_clearing = [row for row in self.rows if row["study_id"] == "mbah_nneji_agbani_2007_2008"]
        self.assertEqual(len(land_clearing), 12)
        self.assertTrue(all("land_clearing_residue_not_harvest_straw" in row["quality_flags"] for row in land_clearing))

    def test_new_primary_extractions_have_study_level_clusters_and_source_flags(self):
        by_study = Counter(row["study_id"] for row in self.rows)
        self.assertEqual(by_study["panneerselvam_cuttack_2021_2022"], 6)
        self.assertEqual(by_study["huang_shangzhuang_2006_2013"], 16)
        self.assertEqual(by_study["sharma_ludhiana_2011_2018"], 4)
        self.assertEqual(by_study["du_dingxi_2016_2022"], 24)
        sharma = [row for row in self.rows if row["study_id"] == "sharma_ludhiana_2011_2018"]
        self.assertTrue(all(row["quality_flags"] == "pooled_se_denominator_ambiguous" for row in sharma))
        self.assertTrue(all(row["paper_doi"] == "10.1016/j.heliyon.2023.e17828" for row in sharma))
        huang = [row for row in self.rows if row["study_id"] == "huang_shangzhuang_2006_2013"]
        self.assertEqual(Counter(row["outcome"] for row in huang), {"yield": 8, "N2O": 8})
        self.assertTrue(all(row["treatment_arm"].replace("S", "", 1) == row["control_arm"] for row in huang))
        du = [row for row in self.rows if row["study_id"] == "du_dingxi_2016_2022"]
        self.assertEqual(Counter(row["outcome"] for row in du), {"yield": 6, "SOC": 6, "GWP": 6, "GHGI": 6})
        self.assertTrue(all("source_coordinates_malformed" in row["quality_flags"] for row in du))
        self.assertTrue(all(row["nitrogen_rate"] in {"55 kg N ha-1", "110 kg N ha-1", "220 kg N ha-1"} for row in du))
        self.assertTrue(all(row["latitude"] == row["longitude"] == "" for row in du))
        self.assertTrue(all(row["treatment_arm"].replace("CTS-", "CT-") == row["control_arm"] for row in du))
        du_by_id = {row["effect_id"]: row for row in du}
        self.assertAlmostEqual(float(du_by_id["du_dingxi_2016_2022_2021_LN_yield"]["treatment_mean"]), 1436.00)
        self.assertAlmostEqual(float(du_by_id["du_dingxi_2016_2022_2021_LN_yield"]["control_mean"]), 1382.67)
        self.assertAlmostEqual(float(du_by_id["du_dingxi_2016_2022_2022_MN_SOC"]["treatment_mean"]), 6.49)
        self.assertEqual(du_by_id["du_dingxi_2016_2022_2022_MN_SOC"]["soil_depth"], "0-10 cm")
        self.assertEqual(du_by_id["du_dingxi_2016_2022_2021_HN_GWP"]["gwp_version"], "AR4 CH4=25 N2O=298")

    def test_legacy_undefined_error_type_is_excluded_from_strict_screen(self):
        flagged = [row for row in self.rows if "reported_error_type_ambiguous" in row["quality_flags"]]
        self.assertEqual(Counter(row["study_id"] for row in flagged),
                         {"rice_primary_466": 45, "rice_primary_494": 24, "rice_primary_392": 2})
        self.assertTrue(any(row["outcome"] == "yield" for row in flagged))

    def test_reviewed_legacy_burning_arms_are_visible_without_inventing_studies(self):
        counts = Counter(row["study_id"] for row in self.rows)
        expected = {"rice_primary_164": 20, "rice_primary_392": 2, "rice_primary_53": 13}
        for study, count in expected.items():
            self.assertEqual(counts[study], count + (10 if study == "rice_primary_53" else 0))
            burning = [row for row in self.rows if row["study_id"] == study
                       and row["pathway"] == "open_burning"]
            self.assertEqual(len(burning), count)
            self.assertTrue(all(row["crop_core"] == "rice" for row in burning))
            self.assertTrue(all(row["treatment_arm"] and row["control_arm"] for row in burning))
            self.assertTrue(all("primary_table_metadata_backfilled" in row["quality_flags"]
                                for row in burning))
        ma = [row for row in self.rows if row["study_id"] == "rice_primary_392"]
        self.assertTrue(all("reported_error_type_ambiguous" in row["quality_flags"] for row in ma))

    def test_burning_descriptive_unit_is_independent_trial(self):
        trials = study_level(EVIDENCE)
        result = burning_summary(trials)
        self.assertEqual((result["independent_trials"], result["effect_rows"]), (8, 16))
        self.assertEqual((result["positive_trials"], result["negative_trials"]), (6, 2))
        self.assertEqual(len(trials["rice_primary_164"]["lnrr"]), 4)
        self.assertNotIn("rice_primary_392", trials)
        self.assertNotIn("mbah_nneji_agbani_2007_2008", trials)

    def test_liu_direct_return_addendum_preserves_shared_control(self):
        added = [row for row in self.rows if row["effect_id"].startswith("rice_primary_53_") and row["pathway"] == "direct_return"]
        self.assertEqual(len(added), 10)
        by_id = {row["effect_id"]: row for row in self.rows}
        for row in added:
            burning = by_id[row["effect_id"].replace("_direct_", "_")]
            for key in ("study_id", "paper_doi", "outcome", "experiment_year", "control_mean", "control_sd", "control_n", "shared_control_group"):
                self.assertEqual(row[key], burning[key])
            self.assertGreater(float(row["variance_lnrr"]), 0)
            self.assertEqual(row["treatment_n"], "3")

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
