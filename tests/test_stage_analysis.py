"""Guard against pseudoreplication, loose joins and scope drift."""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from scripts.analyze_stage_evidence import (
    screen_reason, identity_reason, crop_label, soc_kind,
    matched_outcomes, matched_pathways, aggregate_trials,
)


class StageAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = pd.read_csv(Path(__file__).resolve().parents[1] / "literature/evidence_database.csv",
                            keep_default_na=False)
        cls.d["crop_display"] = cls.d.apply(crop_label, axis=1)
        cls.d["soc_kind"] = cls.d.apply(soc_kind, axis=1)
        cls.s = cls.d[(cls.d.apply(screen_reason, axis=1) == "") &
                     (cls.d.apply(identity_reason, axis=1) == "")].copy()

    def test_snapshot_exclusions_are_accounted_for(self):
        self.assertEqual(len(self.d), 510)
        self.assertEqual(len(self.s), 389)
        self.assertNotIn("shittu_ado_ekiti_2001_2002", set(self.s.study_id))
        self.assertNotIn("biochar_li2024SD_176", set(self.s.study_id))

    def test_no_pseudoreplicated_yield_counts(self):
        t = aggregate_trials(self.s[self.s.outcome == "yield"], ["study_id", "pathway"])
        self.assertEqual(t.groupby("pathway").size().to_dict(),
                         {"biochar_return": 6, "direct_return": 9, "open_burning": 9})
        q = t[(t.study_id == "qin_huizhou_2012_2015") & (t.pathway == "biochar_return")]
        self.assertEqual(len(q), 1)
        self.assertEqual(q.iloc[0].n_effects, 24)

    def test_water_strata_not_cartesian_joined(self):
        joint, _ = matched_outcomes(self.s, "GWP")
        self.assertEqual(len(joint), 42)
        self.assertEqual(len(joint[joint.study_id == "rice_primary_164"]), 4)
        self.assertEqual(joint.study_id.nunique(), 3)
        self.assertTrue(joint.yield_effect_id.is_unique)

    def test_soc_and_yield_periods_not_forcibly_matched(self):
        joint, _ = matched_outcomes(self.s, "SOC")
        self.assertEqual(len(joint), 15)
        self.assertNotIn("jijnasa_bhubaneswar_2022_2024", set(joint.study_id))
        self.assertNotIn("amgain_bhairahawa_2019_2021", set(joint.study_id))
        self.assertTrue((joint.soc_measure == "SOC_concentration").all())

    def test_different_pathways_cancel_same_control(self):
        pairs = matched_pathways(self.s)
        self.assertEqual(len(pairs), 38)
        src = self.s.set_index("effect_id")
        for _, p in pairs.iterrows():
            a, b = src.loc[p.a_effect_id], src.loc[p.b_effect_id]
            expected = np.log(float(a.treatment_mean) / float(b.treatment_mean))
            self.assertAlmostEqual(p.difference_lnrr, expected, places=8)

    def test_conflicting_shared_control_rejected(self):
        altered = self.s.copy()
        mask = (altered.study_id == "jijnasa_bhubaneswar_2022_2024") & (altered.outcome == "yield") & (altered.pathway == "direct_return")
        altered.loc[mask, "control_mean"] *= 2
        with self.assertRaises(ValueError):
            matched_pathways(altered)

    def test_repeated_endpoint_is_not_double_counted(self):
        row = self.s[(self.s.study_id == "du_dingxi_2016_2022") & (self.s.outcome == "SOC")].iloc[[0]].copy()
        row.effect_id = "duplicate_test"
        duplicated = pd.concat([self.s, row], ignore_index=True)
        joint, held = matched_outcomes(duplicated, "SOC")
        self.assertEqual(len(joint), 14)
        self.assertIn("duplicate_test", held)


if __name__ == "__main__":
    unittest.main()
