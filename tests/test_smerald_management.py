"""Small deterministic checks for the global management accounting layer."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from integrate_smerald_management import summarize_mass  # noqa: E402


class SmeraldAccountingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.values = {
            "residue_production": np.array([[10.0, np.nan], [20.0, 0.0]]),
            "burnt_residues": np.array([[1.0, np.nan], [2.0, 0.0]]),
            "animal_usage": np.array([[2.0, np.nan], [3.0, 0.0]]),
            "other_usage": np.array([[1.0, np.nan], [5.0, 0.0]]),
            "left_on_field": np.array([[6.0, np.nan], [10.0, 0.0]]),
        }

    def test_mass_closure(self) -> None:
        summary = summarize_mass(self.values)
        self.assertEqual(summary["residue_production_Mg"], 30.0)
        self.assertEqual(sum(summary[k + "_Mg"] for k in self.values if k != "residue_production"), 30.0)

    def test_rejects_cell_level_imbalance(self) -> None:
        values = {key: array.copy() for key, array in self.values.items()}
        values["burnt_residues"][0, 0] += 0.1
        values["burnt_residues"][1, 0] -= 0.1
        with self.assertRaises(ValueError):
            summarize_mass(values)

    def test_rejects_different_valid_masks(self) -> None:
        values = {key: array.copy() for key, array in self.values.items()}
        values["animal_usage"][0, 1] = 0
        with self.assertRaises(ValueError):
            summarize_mass(values)


if __name__ == "__main__":
    unittest.main()
