"""Mass and coordinate checks for the manuscript resource map."""
import unittest

import numpy as np
import pandas as pd

from scripts.plot_manuscript_fig1 import crop_continent_climate, grid_image


class ManuscriptFigureOneTest(unittest.TestCase):
    def test_grid_cells_are_summed_without_loss(self):
        d = pd.DataFrame({
            "grid_id": ["r065c378", "r065c378", "r066c378"],
            "longitude": [9.25, 9.25, 9.25],
            "latitude": [57.25, 57.25, 56.75],
            "residue_allocated_t": [10.0, 20.0, 5.0],
        })
        image, n_cells, n_positive = grid_image(d)
        self.assertEqual((n_cells, n_positive), (2, 2))
        self.assertAlmostEqual(float(np.nansum(image)), 35.0)
        self.assertAlmostEqual(float(image[294, 378]), 30.0)

    def test_out_of_range_coordinate_fails(self):
        d = pd.DataFrame({
            "grid_id": ["bad"], "longitude": [181.0],
            "latitude": [0.0], "residue_allocated_t": [1.0],
        })
        with self.assertRaises(ValueError):
            grid_image(d)

    def test_75_strata_conserve_assigned_mass(self):
        d = pd.DataFrame({
            "crop_code": ["maiz", "maiz", "rice", "whea"],
            "continent_omd": ["Asia", "Asia", "Americas", "Europe"],
            "koppen_major_group": ["A", "C", "C", "D"],
            "residue_allocated_t": [10.0, 20.0, 5.0, 7.0],
        })
        strata = crop_continent_climate(d)
        self.assertEqual(len(strata), 75)
        self.assertAlmostEqual(strata.residue_allocated_t.sum(), 42.0)
        self.assertAlmostEqual(strata.loc[
            strata.crop_code.eq("maiz") & strata.continent_omd.eq("Asia") &
            strata.koppen_major_group.eq("C"), "residue_allocated_t"].iloc[0], 20.0)

    def test_positive_mass_without_climate_fails(self):
        d = pd.DataFrame({
            "crop_code": ["maiz"], "continent_omd": ["Asia"],
            "koppen_major_group": [None], "residue_allocated_t": [1.0],
        })
        with self.assertRaises(ValueError):
            crop_continent_climate(d)


if __name__ == "__main__":
    unittest.main()
