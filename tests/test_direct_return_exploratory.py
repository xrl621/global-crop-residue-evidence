"""Checks for the descriptive trial-balanced calculation."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_direct_return_yield_exploratory import summarize  # noqa: E402


class TrialBalancedSummaryTests(unittest.TestCase):
    def test_many_arms_do_not_outvote_one_trial(self) -> None:
        studies = {
            "trial_a": {"values": [math.log(2.0)] * 10},
            "trial_b": {"values": [math.log(0.5)]},
        }
        result = summarize(studies, set())
        self.assertEqual(result["studies"], 2)
        self.assertEqual(result["effects"], 11)
        self.assertAlmostEqual(result["balanced_percent"], 0.0)

    def test_exclusion_changes_trial_and_effect_counts(self) -> None:
        studies = {
            "trial_a": {"values": [math.log(1.1)] * 2},
            "trial_b": {"values": [math.log(0.9)]},
        }
        result = summarize(studies, {"trial_a"})
        self.assertEqual((result["studies"], result["effects"]), (1, 1))
        self.assertAlmostEqual(result["balanced_percent"], -10.0)


if __name__ == "__main__":
    unittest.main()
