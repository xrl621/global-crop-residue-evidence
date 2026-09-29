"""Regression checks for the frozen Fig. 2 descriptive-statistics package."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_fig2_three_pathway_statistics import build  # noqa: E402


def test_fig2_stats_counts_and_cross_endpoint_levels(tmp_path: Path):
    manifest = build(tmp_path)
    assert manifest["treatment_comparisons"] == 339
    assert manifest["distinct_trial_keys"] == 25
    assert manifest["trial_pathway_endpoint_summaries"] == 60
    cells = pd.read_csv(tmp_path / "pathway_endpoint_summary.csv")
    assert len(cells) == 12
    assert cells.treatment_comparisons.sum() == 339
    assert cells.independent_trial_keys.max() == 11
    crop = pd.read_csv(tmp_path / "pathway_endpoint_crop_support.csv")
    assert len(crop) == 36
    assert crop.treatment_comparisons.sum() == 339
    assert crop.loc[(crop.pathway == "biochar_return") &
                    (crop.endpoint == "CH4") &
                    (crop.crop == "rice"), "independent_trial_keys"].iloc[0] == 4
    directions = pd.read_csv(tmp_path / "trial_direction_summary.csv")
    assert len(directions) == 12
    assert (directions.independent_trial_keys ==
            directions.positive_trials + directions.negative_trials +
            directions.zero_trials).all()
    co = pd.read_csv(tmp_path / "trial_endpoint_co_reporting.csv")
    exact = pd.read_csv(tmp_path / "exact_metadata_pair_candidates.csv")
    assert co.linkage_level.str.contains("only").all()
    assert exact.linkage_level.str.contains("candidate").all()
    assert exact.study_id.nunique() <= co.study_id.nunique()
