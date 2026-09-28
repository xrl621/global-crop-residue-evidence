"""Mass and coordinate checks for the manuscript resource map."""
import unittest

import numpy as np
import pandas as pd

from scripts.plot_manuscript_fig1 import grid_image


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


if __name__ == "__main__":
    unittest.main()
