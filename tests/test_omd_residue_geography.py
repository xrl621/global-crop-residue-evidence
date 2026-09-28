import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from integrate_omd_residue_geography import allocate_national_mass


class OmdNationalAllocationTest(unittest.TestCase):
    def test_national_mass_is_conserved_without_cross_crop_mixing(self):
        frame = pd.DataFrame({
            "country_m49": [1, 1, 1, 2],
            "crop_code": ["maiz", "maiz", "rice", "maiz"],
            "mapspam_production_t": [1.0, 3.0, 5.0, 2.0],
            "omd_residue_production_t": [40.0, 40.0, 20.0, 7.0],
        })
        result = allocate_national_mass(frame)
        self.assertEqual(result.residue_allocated_t.tolist(), [10.0, 30.0, 20.0, 7.0])

    def test_zero_production_is_not_invented_as_residue(self):
        frame = pd.DataFrame({
            "country_m49": [1], "crop_code": ["maiz"],
            "mapspam_production_t": [0.0], "omd_residue_production_t": [40.0],
        })
        result = allocate_national_mass(frame)
        self.assertEqual(float(result.residue_allocated_t.iloc[0]), 0.0)


if __name__ == "__main__":
    unittest.main()
