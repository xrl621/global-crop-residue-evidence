"""Paper-balanced yield–topsoil SOC reanalysis for manuscript Fig 2.

This uses an openly released secondary compilation. It is descriptive and
paper-resampling based, not an inverse-variance or primary-trial meta-analysis.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/encarnation2026_residue_reanalysis/selected_comparisons.csv"
OUT = ROOT / "data/processed/manuscript_fig2_joint_20260929"
CROPS = ("Maize", "Rice", "Wheat")
CLIMATES = ("Temperate Moist", "Temperate Dry", "Subtropical Moist",
            "Subtropical Dry", "Tropical Moist", "Tropical Dry")
RETURN_PATHS = ("Incorporated vs removed", "Surface-retained vs removed")
BOOTSTRAP_DRAWS = 4000
SEED = 20260929


def paper_medians(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    return (frame.groupby(keys, as_index=False, sort=True)
            .agg(yield_lnrr=("yield_log_ratio", "median"),
                 soc_lnrr=("soc_log_ratio", "median"),
                 comparison_rows=("Comparison_ID", "nunique")))


def interval(values: np.ndarray, seed: int) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    if len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("Empty or non-finite paper-level effect vector")
    estimate = float(np.median(values))
    rng = np.random.default_rng(seed)
    draws = np.median(rng.choice(values, size=(BOOTSTRAP_DRAWS, len(values)),
                                 replace=True), axis=1)
    lo, hi = np.quantile(draws, [.025, .975])
    return tuple(100 * float(np.expm1(x)) for x in (estimate, lo, hi))


def outcome_rows(frame: pd.DataFrame, dimension: str, group: str, seed: int) -> list[dict]:
    rows = []
    for index, (outcome, col) in enumerate((("Yield", "yield_lnrr"),
                                             ("Topsoil SOC stock", "soc_lnrr"))):
        median, lo, hi = interval(frame[col].to_numpy(), seed + index)
        rows.append(dict(dimension=dimension, group=group, outcome=outcome,
                         papers=int(frame.Title.nunique()), median_percent=median,
                         bootstrap_95_lo_percent=lo, bootstrap_95_hi_percent=hi,
                         positive_papers=int(frame[col].gt(0).sum()),
                         bootstrap_unit="unique paper title"))
    return rows


def joint_rows(frame: pd.DataFrame, dimension: str, group: str) -> list[dict]:
    y, s = frame.yield_lnrr.gt(0), frame.soc_lnrr.gt(0)
    categories = (("Both positive", y & s),
                  ("Yield only positive", y & ~s),
                  ("SOC only positive", ~y & s),
                  ("Neither positive", ~y & ~s))
    n = int(frame.Title.nunique())
    rows = [dict(dimension=dimension, group=group, category=label,
                 papers=int(mask.sum()), denominator_papers=n,
                 percent=100 * float(mask.mean())) for label, mask in categories]
    if sum(row["papers"] for row in rows) != n:
        raise ValueError("Joint-direction categories do not partition titles")
    return rows


def build(source: Path = SOURCE, out: Path = OUT) -> dict:
    data = pd.read_csv(source)
    required = {"Comparison_ID", "Title", "Pathway", "Main_Crop", "Region",
                "Combined_Climate_Class",
                "yield_log_ratio", "soc_log_ratio"}
    if missing := required - set(data.columns):
        raise ValueError(f"Missing source columns: {sorted(missing)}")
    core = data.loc[data.Pathway.isin(RETURN_PATHS) &
                    data.Main_Crop.isin(CROPS)].copy()
    if core.Comparison_ID.duplicated().any() or core.Title.isna().any():
        raise ValueError("Comparison IDs or paper titles are not auditable")
    if not np.isfinite(core[["yield_log_ratio", "soc_log_ratio"]]).all().all():
        raise ValueError("Non-finite paired effect ratio")
    if core.groupby("Title").Region.nunique(dropna=False).gt(1).any():
        raise ValueError("A paper title spans multiple regions; region test needs review")

    paper = paper_medians(core, ["Title"])
    regions = core.groupby("Title").Region.first().reset_index()
    paper = paper.merge(regions, on="Title", validate="one_to_one")
    paper["Region_group"] = np.where(paper.Region.eq("Asia"), "Asia", "Outside Asia")
    crop = paper_medians(core, ["Main_Crop", "Title"])
    climate = paper_medians(core.dropna(subset=["Combined_Climate_Class"]),
                            ["Combined_Climate_Class", "Title"])
    if int(crop.comparison_rows.sum()) != len(core):
        raise ValueError("Crop-paper groups fail to account for source comparisons")

    effect_summary = outcome_rows(paper, "All", "Three cereals", SEED)
    joint = joint_rows(paper, "All", "Three cereals")
    for idx, name in enumerate(CROPS):
        subset = crop[crop.Main_Crop.eq(name)]
        effect_summary += outcome_rows(subset, "Crop", name, SEED + 10 * (idx + 1))
        joint += joint_rows(subset, "Crop", name)
    for idx, name in enumerate(("Asia", "Outside Asia")):
        subset = paper[paper.Region_group.eq(name)]
        effect_summary += outcome_rows(subset, "Region", name, SEED + 100 + 10 * idx)
    for idx, name in enumerate(CLIMATES):
        subset = climate[climate.Combined_Climate_Class.eq(name)]
        effect_summary += outcome_rows(subset, "Climate", name, SEED + 200 + 10 * idx)

    # A transparent sensitivity check; implausible raw ratios are not silently
    # removed from the main estimate or figure source.
    threshold = np.log(10)
    plausible = core.loc[core[["yield_log_ratio", "soc_log_ratio"]]
                         .abs().le(threshold).all(axis=1)]
    plausible_paper = paper_medians(plausible, ["Title"])
    sensitivity = outcome_rows(plausible_paper, "Sensitivity", "Raw ratios within 0.1–10",
                               SEED + 1000)
    out.mkdir(parents=True, exist_ok=True)
    paper.to_csv(out / "paper_global.csv", index=False)
    crop.to_csv(out / "paper_crop.csv", index=False)
    climate.to_csv(out / "paper_climate.csv", index=False)
    pd.DataFrame(effect_summary).to_csv(out / "effect_summary.csv", index=False)
    pd.DataFrame(joint).to_csv(out / "joint_direction.csv", index=False)
    pd.DataFrame(sensitivity).to_csv(out / "plausible_ratio_sensitivity.csv", index=False)
    audit = dict(source="selected_comparisons.csv",
                 source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                 source_comparisons=len(data), focal_return_comparisons=len(core),
                 focal_paper_titles=len(paper), paper_crop_units=len(crop),
                 papers_in_multiple_crops=int(crop.groupby("Title").size().gt(1).sum()),
                 climate_title_units=len(climate),
                 titles_in_multiple_climates=int(climate.groupby("Title").size().gt(1).sum()),
                 climate_title_counts=climate.Combined_Climate_Class.value_counts().to_dict(),
                 region_title_counts=paper.Region_group.value_counts().to_dict(),
                 raw_ratio_over_10_or_under_point_1_rows=len(core) - len(plausible),
                 plausible_ratio_papers=len(plausible_paper),
                 main_rule="within-title median paired log ratios, then across-title median",
                 uncertainty=f"{BOOTSTRAP_DRAWS} title-resampling bootstrap draws; 95% percentile interval",
                 inference="secondary-data descriptive association; not primary-trial causal meta-analysis")
    (out / "manifest.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return audit


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
