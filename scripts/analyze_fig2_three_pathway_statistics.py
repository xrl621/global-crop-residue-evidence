"""Reproducible descriptive statistics for the proposed three-pathway Fig. 2.

No pathway ranking, inverse-variance pooling or independence inference is made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EFFECTS = ROOT / "data/processed/stage_20260928/screened_effects.csv"
TRIALS = ROOT / "data/processed/pathway_endpoint_v2_20260928/trial_level.csv"
OUT = ROOT / "data/processed/fig2_three_pathway_stats_20260929"
PATHWAYS = ("direct_return", "biochar_return", "open_burning")
ENDPOINTS = ("yield", "SOC_concentration", "CH4", "N2O")


def key_count(frame: pd.DataFrame) -> int:
    return int(frame.study_id.nunique())


def summarize(trials: pd.DataFrame, effects: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pathway in PATHWAYS:
        for endpoint in ENDPOINTS:
            tr = trials.loc[(trials.pathway == pathway) & (trials.endpoint == endpoint)]
            ef = effects.loc[(effects.pathway == pathway) & (effects.endpoint == endpoint)]
            values = tr.trial_percent.to_numpy(dtype=float)
            rows.append({
                "pathway": pathway, "endpoint": endpoint,
                "independent_trial_keys": key_count(tr),
                "trial_crop_units": len(tr),
                "treatment_comparisons": len(ef),
                "countries": "|".join(sorted(set(ef.country.astype(str)) - {""})),
                "crops": "|".join(sorted(set(tr.crop.astype(str)) - {""})),
                "positive_trial_crop_units": int((tr.trial_mean_lnrr > 0).sum()),
                "negative_trial_crop_units": int((tr.trial_mean_lnrr < 0).sum()),
                "zero_trial_crop_units": int((tr.trial_mean_lnrr == 0).sum()),
                "trial_crop_median_pct": float(np.median(values)),
                "trial_crop_q25_pct": float(np.quantile(values, .25)),
                "trial_crop_q75_pct": float(np.quantile(values, .75)),
                "trial_crop_min_pct": float(np.min(values)),
                "trial_crop_max_pct": float(np.max(values)),
                "summary_level": "trial-by-crop; descriptive median/IQR, not pooled meta effect",
            })
    summary = pd.DataFrame(rows)
    assert len(summary) == 12 and summary.treatment_comparisons.sum() == 339
    return summary


def trial_direction(trials: pd.DataFrame) -> pd.DataFrame:
    tr = (trials.groupby(["study_id", "pathway", "endpoint"], as_index=False)
          .agg(mean_lnrr=("trial_mean_lnrr", "mean"),
               trial_crop_units=("crop", "nunique"),
               treatment_comparisons=("effect_records", "sum")))
    tr["trial_pct"] = 100 * np.expm1(tr.mean_lnrr)
    tr["direction"] = np.select([tr.mean_lnrr.gt(0), tr.mean_lnrr.lt(0)],
                                  ["increase", "decrease"], default="zero")
    return tr


def trial_direction_summary(direction: pd.DataFrame) -> pd.DataFrame:
    return (direction.groupby(["pathway", "endpoint"], as_index=False)
            .agg(independent_trial_keys=("study_id", "nunique"),
                 positive_trials=("mean_lnrr", lambda x: int((x > 0).sum())),
                 negative_trials=("mean_lnrr", lambda x: int((x < 0).sum())),
                 zero_trials=("mean_lnrr", lambda x: int((x == 0).sum())),
                 median_trial_pct=("trial_pct", "median"),
                 q25_trial_pct=("trial_pct", lambda x: float(x.quantile(.25))),
                 q75_trial_pct=("trial_pct", lambda x: float(x.quantile(.75)))))


def crop_support(trials: pd.DataFrame, effects: pd.DataFrame) -> pd.DataFrame:
    crop_map = {"maize": "maize", "rice": "rice", "wheat": "wheat"}
    rows = []
    for pathway in PATHWAYS:
        for endpoint in ENDPOINTS:
            for crop in crop_map:
                tr = trials.loc[(trials.pathway == pathway) &
                                (trials.endpoint == endpoint) &
                                (trials.crop == crop)]
                ef = effects.loc[(effects.pathway == pathway) &
                                 (effects.endpoint == endpoint) &
                                 (effects.crop_display == crop)]
                rows.append({
                    "pathway": pathway, "endpoint": endpoint, "crop": crop,
                    "independent_trial_keys": key_count(tr),
                    "trial_crop_units": len(tr),
                    "treatment_comparisons": len(ef),
                    "positive_trial_crop_units": int(tr.trial_mean_lnrr.gt(0).sum()),
                    "negative_trial_crop_units": int(tr.trial_mean_lnrr.lt(0).sum()),
                    "median_trial_crop_pct": float(tr.trial_percent.median()) if len(tr) else np.nan,
                    "countries": "|".join(sorted(set(ef.country.astype(str)) - {""})),
                })
    grid = pd.DataFrame(rows)
    if len(grid) != 36 or int(grid.treatment_comparisons.sum()) != len(effects):
        raise ValueError("Crop support grid does not partition source effects")
    return grid


def co_report(trials: pd.DataFrame) -> pd.DataFrame:
    rows = []
    all_groups = trials.groupby(["study_id", "pathway"], sort=True)
    for (study_id, pathway), sub in all_groups:
        endpoints = set(sub.endpoint)
        rows.append({
            "study_id": study_id, "pathway": pathway,
            **{f"has_{endpoint}": endpoint in endpoints for endpoint in ENDPOINTS},
            "has_yield_soc": {"yield", "SOC_concentration"} <= endpoints,
            "has_yield_ch4": {"yield", "CH4"} <= endpoints,
            "has_yield_n2o": {"yield", "N2O"} <= endpoints,
            "has_all_four": set(ENDPOINTS) <= endpoints,
            "endpoint_count": len(endpoints),
            "linkage_level": "same study_id and pathway only; arms/seasons/boundaries not matched",
        })
    return pd.DataFrame(rows)


def exact_candidates(effects: pd.DataFrame) -> pd.DataFrame:
    # Exact string equality is a candidate identity check, not proof that
    # all endpoints were measured in the same plot or reporting period.
    keys = ["study_id", "pathway", "crop_display", "experiment_year",
            "season", "treatment_arm", "control_arm"]
    fields = effects[keys + ["endpoint", "effect_id", "system_boundary",
                             "soil_depth", "outcome_unit"]].copy()
    fields = fields.fillna("")
    grouped = fields.groupby(keys, dropna=False, sort=True)
    rows = []
    for values, group in grouped:
        endpoints = set(group.endpoint)
        if len(endpoints) < 2:
            continue
        row = dict(zip(keys, values))
        row.update({
            "endpoint_set": "|".join(e for e in ENDPOINTS if e in endpoints),
            "endpoint_count": len(endpoints),
            "has_yield_soc": {"yield", "SOC_concentration"} <= endpoints,
            "has_yield_ch4": {"yield", "CH4"} <= endpoints,
            "has_yield_n2o": {"yield", "N2O"} <= endpoints,
            "has_all_four": set(ENDPOINTS) <= endpoints,
            "effect_ids": "|".join(sorted(group.effect_id)),
            "system_boundaries": "|".join(sorted(set(group.system_boundary) - {""})),
            "soil_depths": "|".join(sorted(set(group.soil_depth) - {""})),
            "linkage_level": "exact metadata candidate; plot/time/boundary confirmation still required",
        })
        rows.append(row)
    return pd.DataFrame(rows)


def build(out: Path = OUT) -> dict:
    raw_trial = pd.read_csv(TRIALS, keep_default_na=False)
    raw_effect = pd.read_csv(EFFECTS, keep_default_na=False)
    trial = raw_trial.loc[raw_trial.pathway.isin(PATHWAYS) &
                          raw_trial.endpoint.isin(ENDPOINTS)].copy()
    effect = raw_effect.loc[raw_effect.pathway.isin(PATHWAYS) &
                            raw_effect.crop_display.isin(("rice", "maize", "wheat"))].copy()
    effect["endpoint"] = np.where(effect.outcome.eq("SOC"), effect.soc_kind,
                                   effect.outcome)
    effect = effect.loc[effect.endpoint.isin(ENDPOINTS)].copy()
    if (len(trial) != 62 or len(effect) != 339 or
        trial.study_id.nunique() != 25 or effect.study_id.nunique() != 25):
        raise ValueError("Frozen V1 Fig. 2 data counts changed; re-audit before updating")
    if effect.effect_id.duplicated().any():
        raise ValueError("Duplicate effect IDs")
    ids = {eid for value in trial.effect_ids for eid in str(value).split("|")}
    if ids != set(effect.effect_id):
        raise ValueError("Trial aggregates and source effects do not have identical IDs")
    if int(trial.effect_records.sum()) != len(effect):
        raise ValueError("Trial record counts do not sum to effect count")
    summary = summarize(trial, effect)
    crop_grid = crop_support(trial, effect)
    direction = trial_direction(trial)
    direction_summary = trial_direction_summary(direction)
    co = co_report(trial)
    candidates = exact_candidates(effect)
    co_summary = (co.groupby("pathway")[["has_yield_soc", "has_yield_ch4",
                                     "has_yield_n2o", "has_all_four"]]
                  .sum().astype(int).reset_index())
    candidate_summary = (candidates.groupby("pathway")[["has_yield_soc", "has_yield_ch4",
                                                    "has_yield_n2o", "has_all_four"]]
                         .sum().astype(int).reset_index())
    out.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out / "pathway_endpoint_summary.csv", index=False)
    crop_grid.to_csv(out / "pathway_endpoint_crop_support.csv", index=False)
    direction.to_csv(out / "trial_direction.csv", index=False)
    direction_summary.to_csv(out / "trial_direction_summary.csv", index=False)
    co.to_csv(out / "trial_endpoint_co_reporting.csv", index=False)
    candidates.to_csv(out / "exact_metadata_pair_candidates.csv", index=False)
    co_summary.to_csv(out / "co_reporting_summary.csv", index=False)
    candidate_summary.to_csv(out / "exact_candidate_summary.csv", index=False)
    manifest = {
        "trial_source_sha256": hashlib.sha256(TRIALS.read_bytes()).hexdigest(),
        "effect_source_sha256": hashlib.sha256(EFFECTS.read_bytes()).hexdigest(),
        "trial_crop_units": len(trial), "treatment_comparisons": len(effect),
        "distinct_trial_keys": key_count(trial),
        "trial_pathway_endpoint_summaries": len(direction),
        "distinct_trial_pathway_groups": len(co),
        "exact_metadata_candidate_groups": len(candidates),
        "primary_summary_unit": "trial-by-crop for endpoint distributions; study_id for direction and co-report counts",
        "interval_policy": "IQR is descriptive distribution, not confidence interval",
        "no_meta_analysis": True, "no_cross_pathway_ranking": True,
        "no_full_lifecycle_ghg_claim": True,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False,
                                                 indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.out), ensure_ascii=False, indent=2))
