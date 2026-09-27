"""Current-source checks, separate from immutable September 26 regression tests."""
import csv
import math
import unittest
from pathlib import Path

import pandas as pd

from scripts.analyze_stage_evidence import crop_label, identity_reason, screen_reason, soc_kind, matched_outcomes
from scripts.expand_evidence_20260927 import mean_only, DONG_HASH
from scripts.export_evidence_database import FIELDS

ROOT = Path(__file__).resolve().parents[1]


class ExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_csv(ROOT / "literature/evidence_database.csv", keep_default_na=False)
        cls.data["crop_display"] = cls.data.apply(crop_label, axis=1)
        cls.data["soc_kind"] = cls.data.apply(soc_kind, axis=1)
        cls.selected = cls.data[(cls.data.apply(screen_reason, axis=1)=="") &
                                (cls.data.apply(identity_reason, axis=1)=="")]

    def test_increment_is_not_pseudoreplication(self):
        d = self.data
        self.assertEqual((len(d), d.study_id.nunique(), d.effect_id.nunique()), (553,33,553))
        self.assertEqual((len(self.selected),self.selected.study_id.nunique()), (437,26))
        old = pd.read_csv(ROOT / "data/processed/stage_20260926/row_audit.csv")
        self.assertEqual(set(d.study_id)-set(old.study_id), {"sun_zhuanghang_2012_2016"})
        self.assertEqual(len(set(d.effect_id)-set(old.effect_id)),43)

    def test_old_numeric_measurements_unchanged(self):
        old = pd.read_csv(ROOT / "data/processed/stage_20260926/row_audit.csv").set_index("effect_id")
        current = self.data.set_index("effect_id")
        for col in ["treatment_mean","control_mean","treatment_sd","control_sd","lnrr","variance_lnrr"]:
            for key in old.index:
                self.assertAlmostEqual(float(old.loc[key,col]), float(current.loc[key,col]), places=10)

    def test_yang_labels_recovered_but_soc_not_promoted(self):
        a = self.selected[self.selected.study_id=="biochar_li2024SD_176"]
        self.assertEqual(len(a),20)
        self.assertEqual(set(a.treatment_arm), {"CB_20t_CI","CC_40t_CI"})
        self.assertEqual(set(a.control_arm), {"CA_0t_CI"})
        self.assertNotIn("SOC",set(a.outcome))
        self.assertTrue((a.latitude=="").all())
        self.assertTrue(a.quality_flags.str.contains("outdoor_lysimeter").all())

    def test_sun_rounded_errors_and_large_relative_errors_held(self):
        all_sun = self.data[self.data.study_id=="sun_zhuanghang_2012_2016"]
        sun = self.selected[self.selected.study_id=="sun_zhuanghang_2012_2016"]
        self.assertEqual((len(all_sun),len(sun)),(17,10))
        self.assertEqual(sun.outcome.value_counts().to_dict(), {"GHGI":4,"yield":3,"CH4":3})
        self.assertEqual(set(all_sun.treatment_arm),{"CF+WS"})
        self.assertEqual(set(all_sun.control_arm),{"CF"})
        self.assertEqual(len(all_sun[all_sun.quality_flags.str.contains("rounded_zero_standard_error")]),2)

    def test_dong_vector_calibration_and_units(self):
        arms = pd.read_csv(ROOT / "literature/primary_extractions/dong2024_figure7_vector_arms.csv")
        self.assertEqual(len(arms),24)
        self.assertEqual(set(arms.source_sha256),{DONG_HASH})
        self.assertEqual(len(arms.drop_duplicates(["year","arm"])),24)
        for _, row in arms.iterrows():
            self.assertAlmostEqual(row["mean"], (row.axis_y0-row.bar_top)*12/(row.axis_y0-row.axis_y12),places=8)
            self.assertAlmostEqual(row.se, (row.error_bottom-row.error_top)*6/(row.axis_y0-row.axis_y12),places=8)
            self.assertTrue(0 < row.se < 1)
        effects = self.data[(self.data.study_id=="dong_harbin_2015_2017") & (self.data.outcome=="yield")]
        self.assertEqual(len(effects),18)
        self.assertTrue(effects.quality_flags.str.contains("figure_digitized").all())

    def test_same_arm_joint_endpoints_expand_without_cartesian_join(self):
        for endpoint, count in [("SOC",33),("GWP",64)]:
            pairs, _ = matched_outcomes(self.selected,endpoint)
            self.assertEqual((len(pairs),pairs.study_id.nunique()),(count,5))
            self.assertTrue(pairs.yield_effect_id.is_unique)
            self.assertEqual(len(pairs[pairs.study_id=="dong_harbin_2015_2017"]),18)

    def test_mean_only_has_no_invented_variance_and_separate_boundary(self):
        rows = mean_only(FIELDS)
        self.assertEqual(len(rows),10)
        self.assertEqual(len({r["study_id"] for r in rows}),1)
        self.assertNotIn("somboon_khonkaen_2021",set(self.data.study_id))
        for row in rows:
            self.assertEqual(row["variance_lnrr"],"")
            self.assertEqual(row["treatment_sd"],"")
            self.assertEqual(row["control_sd"],"")
            self.assertNotIn(row["outcome"],{"GWP","GHGI"})

    def test_all_new_delta_variances_recompute(self):
        for _, r in self.data.iterrows():
            self.assertAlmostEqual(r.lnrr,math.log(r.treatment_mean/r.control_mean),places=8)
            variance=(r.treatment_sd/r.treatment_mean)**2/r.treatment_n+(r.control_sd/r.control_mean)**2/r.control_n
            self.assertAlmostEqual(r.variance_lnrr,variance,places=8)


if __name__ == "__main__":
    unittest.main()
