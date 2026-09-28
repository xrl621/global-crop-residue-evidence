"""Regression checks for the paper-balanced global-patterns release."""
import unittest

import numpy as np
import pandas as pd

from scripts.analyze_encarnation_residue import paper_medians, summarize


class PaperBalancedPatternsTest(unittest.TestCase):
    def test_one_long_paper_does_not_dominate(self):
        frame = pd.DataFrame({
            "Study_ID": ["long", "long", "long", "short"],
            "Comparison_ID": [1, 2, 3, 4],
            "Scope": ["return"] * 4,
            "yield_log_ratio": [np.log(2)] * 3 + [np.log(0.5)],
            "soc_log_ratio": [np.log(2)] * 3 + [np.log(0.5)],
        })
        papers = paper_medians(frame)
        self.assertEqual(len(papers), 2)
        self.assertEqual(int(papers.observations.sum()), 4)
        result = summarize(frame, "Scope")
        self.assertTrue((result.papers == 2).all())
        self.assertTrue((result.comparisons == 4).all())
        self.assertAlmostEqual(float(result.iloc[0].median_pct), 0.0, places=9)

    def test_bootstrap_is_deterministic(self):
        frame = pd.DataFrame({
            "Study_ID": list(range(6)), "Comparison_ID": list(range(6)),
            "Scope": ["return"] * 6,
            "yield_log_ratio": np.arange(6) / 100,
            "soc_log_ratio": np.arange(6) / 200,
        })
        pd.testing.assert_frame_equal(summarize(frame, "Scope"), summarize(frame, "Scope"))


if __name__ == "__main__":
    unittest.main()
