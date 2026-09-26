"""Reproducible descriptive stage analysis; no global pooled inference.

Reads the public snapshot only. Every figure value retains source effect IDs.
Repeated years/doses are averaged in log space within trial for display only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from scripts.describe_evidence import STRICT_EXCLUSION_FLAGS, STRAW_ORIGIN_EXCLUSION_FLAGS
except ModuleNotFoundError:
    from describe_evidence import STRICT_EXCLUSION_FLAGS, STRAW_ORIGIN_EXCLUSION_FLAGS

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data/processed/stage_20260926"
PATHWAYS = ["direct_return", "biochar_return", "open_burning"]
CROP_MAP = {
    "paddy in paddy-wheat rotation": "rice",
    "spring wheat after maize": "wheat",
    "wheat following rice": "wheat",
    "late-sown wheat after rice": "wheat",
    "wheat in rice-wheat rotation": "wheat",
    "winter wheat": "wheat", "rice": "rice",
    "double-cropped rice": "rice", "rice-wheat rotation": "rotation",
}


def pct(value):
    return 100 * np.expm1(value)


def crop_label(row):
    return row["crop_core"] or CROP_MAP.get(row["crop_as_reported"], "unresolved")


def screen_reason(row):
    flags = set(filter(None, row["quality_flags"].split(";")))
    reasons = sorted(flags & (STRICT_EXCLUSION_FLAGS | STRAW_ORIGIN_EXCLUSION_FLAGS))
    if row["variance_origin_status"] != "documented_or_reconstructed":
        reasons.append("variance_origin_unresolved")
    return ";".join(reasons)


def identity_reason(row):
    reasons = []
    if not row["treatment_arm"] or not row["control_arm"]:
        reasons.append("arm_label_missing")
    if row["crop_display"] == "unresolved":
        reasons.append("crop_label_missing")
    return ";".join(reasons)


def soc_kind(row):
    if row["outcome"] != "SOC":
        return "not_SOC"
    desc = (row["soc_measure"] + " " + row["outcome_unit"]).lower()
    if "organic matter" in desc:
        return "SOM_proxy"
    if "labels tc" in desc:
        return "total_C_not_resolved_as_SOC"
    if "kg-1" in desc or "g kg" in desc or "percent" in desc:
        return "SOC_concentration"
    return "SOC_measure_unresolved"


def join_values(values):
    return "|".join(sorted(set(str(x) for x in values if str(x))))


def aggregate_trials(frame, keys):
    rows = []
    for key, g in frame.groupby(keys, sort=True):
        if not isinstance(key, tuple):
            key = (key,)
        row = dict(zip(keys, key))
        row.update(n_effects=len(g), mean_lnrr=float(g.lnrr.mean()),
                   percent=float(pct(g.lnrr.mean())),
                   effect_ids=join_values(g.effect_id), countries=join_values(g.country),
                   crops=join_values(g.crop_display), doi=join_values(g.paper_doi),
                   citations=join_values(g.citation))
        rows.append(row)
    return pd.DataFrame(rows)


def matched_outcomes(frame, outcome):
    """Fail closed on non-unique keys; never create a many-to-many endpoint join."""
    keys = ["study_id", "pathway", "crop_display", "experiment_year", "season",
            "treatment_arm", "control_arm", "water_regime", "nitrogen_rate"]
    left = frame[frame.outcome == "yield"].copy()
    right = frame[frame.outcome == outcome].copy()
    if outcome == "SOC":
        right = right[right.soc_kind == "SOC_concentration"]
    if outcome == "GWP":
        right = right[right.system_boundary.str.contains("soil", case=False)]
    # A period must be documented. Empty season is allowed only within the same
    # recorded year; this is period-label concordance, not proof of same sample.
    left = left[left.experiment_year != ""]
    right = right[right.experiment_year != ""]
    duplicate_ids = set(left.loc[left.duplicated(keys, keep=False), "effect_id"])
    duplicate_ids.update(right.loc[right.duplicated(keys, keep=False), "effect_id"])
    left = left[~left.effect_id.isin(duplicate_ids)]
    right = right[~right.effect_id.isin(duplicate_ids)]
    joined = left.merge(right, on=keys, suffixes=("_yield", "_endpoint"), validate="one_to_one")
    rows = []
    for _, r in joined.iterrows():
        rows.append({**{k: r[k] for k in keys}, "endpoint": outcome,
                     "yield_effect_id": r.effect_id_yield,
                     "endpoint_effect_id": r.effect_id_endpoint,
                     "yield_percent": float(pct(r.lnrr_yield)),
                     "endpoint_percent": float(pct(r.lnrr_endpoint)),
                     "yield_lnrr": r.lnrr_yield, "endpoint_lnrr": r.lnrr_endpoint,
                     "system_boundary": r.system_boundary_endpoint,
                     "soc_measure": r.soc_kind_endpoint,
                     "doi": join_values([r.paper_doi_yield, r.paper_doi_endpoint]),
                     "pairing_level": "same_recorded_period_and_arms; not_raw_plot_covariance"})
    return pd.DataFrame(rows), sorted(duplicate_ids)


def matched_pathways(frame):
    """Only shared-control identifiers AND matching denominators permit contrast."""
    y = frame[(frame.outcome == "yield") & (frame.shared_control_group != "")].copy()
    keys = ["study_id", "crop_display", "experiment_year", "season", "shared_control_group"]
    rows = []
    for a, b in [("direct_return", "open_burning"), ("biochar_return", "direct_return")]:
        pair = y[y.pathway == a].merge(y[y.pathway == b], on=keys, suffixes=("_a", "_b"))
        for _, r in pair.iterrows():
            if any(r[f"{k}_a"] and r[f"{k}_b"] and r[f"{k}_a"] != r[f"{k}_b"]
                   for k in ["water_regime", "nitrogen_rate"]):
                continue
            if not math.isclose(float(r.control_mean_a), float(r.control_mean_b), rel_tol=1e-6):
                raise ValueError("Shared control label disagrees with its numeric mean")
            rows.append({**{k: r[k] for k in keys}, "contrast": f"{a}_vs_{b}",
                         "a_effect_id": r.effect_id_a, "b_effect_id": r.effect_id_b,
                         "a_arm": r.treatment_arm_a, "b_arm": r.treatment_arm_b,
                         "difference_lnrr": r.lnrr_a - r.lnrr_b,
                         "percent": float(pct(r.lnrr_a - r.lnrr_b)),
                         "matching_note": "same_explicit_shared_control_and_mean; missing_water_or_N_labels_not_imputed",
                         "doi": join_values([r.paper_doi_a, r.paper_doi_b])})
    return pd.DataFrame(rows)


def build(source, out):
    d = pd.read_csv(source, keep_default_na=False)
    if not d.effect_id.is_unique:
        raise ValueError("Duplicate effect IDs")
    for column in ["lnrr", "treatment_mean", "control_mean"]:
        d[column] = pd.to_numeric(d[column], errors="raise")
        if not np.isfinite(d[column]).all():
            raise ValueError(f"Nonfinite {column}")
    if not ((d.treatment_mean > 0) & (d.control_mean > 0)).all():
        raise ValueError("Nonpositive raw means cannot enter lnRR")
    if not np.allclose(d.lnrr, np.log(d.treatment_mean / d.control_mean), atol=1e-8):
        raise ValueError("Stored lnRR differs from raw means")
    d["crop_display"] = d.apply(crop_label, axis=1)
    d["screen_exclusion"] = d.apply(screen_reason, axis=1)
    d["identity_exclusion"] = d.apply(identity_reason, axis=1)
    d["soc_kind"] = d.apply(soc_kind, axis=1)
    d["descriptive_eligible"] = (d.screen_exclusion == "") & (d.identity_exclusion == "")
    d["response_percent"] = pct(d.lnrr)
    out.mkdir(parents=True, exist_ok=True)
    d.to_csv(out / "row_audit.csv", index=False, encoding="utf-8-sig")
    held = d[(d.screen_exclusion != "") | (d.identity_exclusion != "")]
    held.groupby(["study_id", "screen_exclusion", "identity_exclusion"], as_index=False).agg(
        rows=("effect_id", "size"), outcomes=("outcome", join_values),
        doi=("paper_doi", join_values), effect_ids=("effect_id", join_values)
    ).to_csv(out / "held_recovery_queue.csv", index=False, encoding="utf-8-sig")
    selected = d[d.descriptive_eligible].copy()
    selected.to_csv(out / "screened_effects.csv", index=False, encoding="utf-8-sig")
    trials = aggregate_trials(selected, ["study_id", "pathway", "outcome", "soc_kind"])
    trials.to_csv(out / "trial_responses.csv", index=False, encoding="utf-8-sig")
    crop_trials = aggregate_trials(selected[selected.outcome == "yield"],
                                   ["study_id", "pathway", "crop_display"])
    crop_trials.to_csv(out / "yield_by_crop.csv", index=False, encoding="utf-8-sig")
    joined, duplicates = [], {}
    for outcome in ["SOC", "GWP"]:
        pairs, duplicate = matched_outcomes(selected, outcome)
        joined.append(pairs)
        duplicates[outcome] = duplicate
    joint = pd.concat(joined, ignore_index=True)
    joint.to_csv(out / "joint_outcome_pairs.csv", index=False, encoding="utf-8-sig")
    joint_audit = []
    for endpoint in ["SOC", "GWP"]:
        pairs = joint[joint.endpoint == endpoint]
        matched_ids = set(pairs.yield_effect_id) | set(pairs.endpoint_effect_id)
        for _, r in selected[selected.outcome.isin(["yield", endpoint])].iterrows():
            if r.effect_id in matched_ids:
                reason = "matched"
            elif r.outcome == "SOC" and r.soc_kind != "SOC_concentration":
                reason = "not_SOC_concentration"
            elif r.outcome == "GWP" and "soil" not in r.system_boundary.lower():
                reason = "soil_GWP_boundary_not_documented"
            elif not r.experiment_year:
                reason = "period_missing"
            elif r.effect_id in duplicates[endpoint]:
                reason = "nonunique_period_arm_key_including_depths"
            else:
                reason = "no_unique_counterpart_with_same_period_arms_water_N"
            joint_audit.append(dict(endpoint=endpoint, effect_id=r.effect_id, outcome=r.outcome, reason=reason))
    pd.DataFrame(joint_audit).to_csv(out / "joint_matching_audit.csv", index=False)
    contrasts = matched_pathways(selected)
    contrasts.to_csv(out / "matched_pathway_pairs.csv", index=False, encoding="utf-8-sig")
    contrast_trials = contrasts.groupby(["contrast", "study_id"], as_index=False).agg(
        n_pairs=("percent", "size"), mean_lnrr=("difference_lnrr", "mean"),
        source_a=("a_effect_id", join_values), source_b=("b_effect_id", join_values))
    contrast_trials["percent"] = pct(contrast_trials.mean_lnrr)
    contrast_trials.to_csv(out / "matched_pathway_trials.csv", index=False, encoding="utf-8-sig")
    coverage = d.groupby(["pathway", "outcome"], as_index=False).agg(
        all_rows=("effect_id", "size"), all_trials=("study_id", "nunique"))
    for label, subset in [("core_screen", d[d.screen_exclusion == ""]), ("descriptive", selected)]:
        c = subset.groupby(["pathway", "outcome"], as_index=False).agg(
            **{f"{label}_rows": ("effect_id", "size"), f"{label}_trials": ("study_id", "nunique")})
        coverage = coverage.merge(c, on=["pathway", "outcome"], how="left")
    coverage.fillna(0).to_csv(out / "coverage.csv", index=False)
    # Metadata coverage is explicitly separate from response analysis.
    selected.groupby(["country", "crop_display"], as_index=False).agg(
        rows=("effect_id", "size"), trials=("study_id", "nunique")
    ).to_csv(out / "country_crop_coverage.csv", index=False)
    summary = []
    for (pathway, outcome, kind), g in trials.groupby(["pathway", "outcome", "soc_kind"]):
        summary.append(dict(pathway=pathway, outcome=outcome, soc_kind=kind,
                            trials=len(g), effects=int(g.n_effects.sum()),
                            positive=int((g.mean_lnrr > 0).sum()), negative=int((g.mean_lnrr < 0).sum()),
                            median_trial_percent=float(pct(g.mean_lnrr.median())),
                            min_trial_percent=float(g.percent.min()), max_trial_percent=float(g.percent.max())))
    pd.DataFrame(summary).to_csv(out / "descriptive_summary.csv", index=False)
    manifest = dict(source="literature/evidence_database.csv",
                    sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    all_rows=len(d), all_trials=d.study_id.nunique(),
                    core_rows=int((d.screen_exclusion == "").sum()),
                    descriptive_rows=len(selected), descriptive_trials=selected.study_id.nunique(),
                    source_screen_excluded=int((d.screen_exclusion != "").sum()),
                    identity_excluded_after_screen=int(((d.screen_exclusion == "") & (d.identity_exclusion != "")).sum()),
                    duplicate_endpoint_pairing_exclusions=duplicates,
                    software=dict(python=platform.python_version(), pandas=pd.__version__, numpy=np.__version__),
                    inference="descriptive only; no CI, significance test, pathway ranking or global extrapolation")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(pd.DataFrame(summary).to_string(index=False))
    print("JOINT PAIRS\n", joint.groupby(["endpoint", "pathway", "study_id"]).size().to_string())
    print("PATHWAY CONTRASTS\n", contrast_trials[["contrast", "study_id", "n_pairs", "percent"]].to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "literature/evidence_database.csv")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    build(args.input, args.output)
