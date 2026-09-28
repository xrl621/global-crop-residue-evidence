"""Checks that duration evidence is counted by publication, not row."""
import unittest

import numpy as np
import pandas as pd

from scripts.analyze_return_duration import paper_units, summaries


class ReturnDurationTest(unittest.TestCase):
    def sample(self):
        return pd.DataFrame({
            "Title": ["Paper A", "Paper A", "Paper B", "Paper C"],
            "Comparison_ID": [1, 2, 3, 4],
            "CRR_Comparison": ["Removed-Incorporated"] * 3 + ["Burned-Incorporated"],
            "Length_Year": [1, 3, 25, 4],
            "yield_log_ratio": np.log([1.1, 1.2, .9, 10]),
            "soc_log_ratio": np.log([1.2, 1.3, 1.5, 10]),
            "Region": ["Asia", "Asia", "Africa", "Asia"],
            "Main_Crop": ["Maize", "Wheat", "Rice", "Rice"],
        })

    def test_paper_identity_duration_and_crop_membership(self):
        p = paper_units(self.sample())
        self.assertEqual(len(p), 2)
        a = p[p.Title.eq("Paper A")].iloc[0]
        self.assertEqual(a.duration_years, 2)
        self.assertEqual(a.crop, "Maize|Wheat")
        self.assertEqual(a.comparisons, 2)
        self.assertAlmostEqual(a.yield_lnrr, np.median(np.log([1.1, 1.2])))
        s = summaries(p, draws=100)
        self.assertEqual(int(s.papers.sum()), 2)
        self.assertEqual(int(s.comparisons.sum()), 3)
        self.assertEqual(int(s.maize_papers.sum()), 1)
        self.assertEqual(int(s.wheat_papers.sum()), 1)
        self.assertEqual(int(s.both_positive.sum()), 1)
        self.assertEqual(int(s.soc_only_positive.sum()), 1)
        self.assertTrue(np.isnan(s[s.duration_bin.eq(">20")].iloc[0].soc_bootstrap_lo_percent))

    def test_repeated_comparison_id_is_rejected(self):
        d = self.sample()
        d.loc[1, "Comparison_ID"] = 1
        with self.assertRaises(ValueError):
            paper_units(d)

    def test_nonpositive_duration_is_rejected(self):
        d = self.sample()
        d.loc[0, "Length_Year"] = 0
        with self.assertRaises(ValueError):
            paper_units(d)


if __name__ == "__main__":
    unittest.main()
