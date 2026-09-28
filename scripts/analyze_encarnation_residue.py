"""Independent-paper descriptive reanalysis of public paired yield/SOC contrasts.

This is a secondary analysis, not an extension of our curated intervention
database or a variance-weighted meta-analysis. The downloaded source workbook
is deliberately kept outside Git; see the manifest for its SHA-256 and URL.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/external/encarnation2026_yield_soc/Yield_data.csv"
OUT = ROOT / "data/processed/encarnation2026_residue_reanalysis"
COMPARISONS = {
    "Removed-Incorporated": "Incorporated vs removed",
    "Removed-Retained": "Surface-retained vs removed",
    "Burned-Incorporated": "Incorporated vs burned",
    "Burned-Retained": "Surface-retained vs burned",
}


def paper_medians(frame: pd.DataFrame, dimension: str | None = None) -> pd.DataFrame:
    groups = ([dimension] if dimension else []) + ["Study_ID"]
    return frame.groupby(groups, dropna=False, as_index=False).agg(
        yield_log_ratio=("yield_log_ratio", "median"),
        soc_log_ratio=("soc_log_ratio", "median"),
        observations=("Comparison_ID", "nunique"),
    )


def bootstrap_median(values: np.ndarray, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    draws = np.median(rng.choice(values, size=(4000, len(values)), replace=True), axis=1)
    return tuple(float(x) for x in np.quantile(draws, [0.025, 0.975]))


def summarize(frame: pd.DataFrame, dimension: str, seed: int = 20260928) -> pd.DataFrame:
    records = []
    p = paper_medians(frame, dimension)
    for label, group in p.groupby(dimension, dropna=False, sort=True):
        for outcome, source_col in [("Yield", "yield_log_ratio"), ("Topsoil SOC", "soc_log_ratio")]:
            vals = group[source_col].to_numpy(dtype=float)
            lo, hi = bootstrap_median(vals, seed + len(records)) if len(vals) >= 5 else (np.nan, np.nan)
            records.append({
                "dimension": dimension, "group": label, "outcome": outcome,
                "papers": len(group), "comparisons": int(group.observations.sum()),
                "median_pct": 100 * np.expm1(np.median(vals)),
                "bootstrap_95_lo_pct": 100 * np.expm1(lo),
                "bootstrap_95_hi_pct": 100 * np.expm1(hi),
                "paper_positive_fraction": float((vals > 0).mean()),
            })
    return pd.DataFrame.from_records(records)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(SOURCE, low_memory=False)
    assert len(d) == 3051 and d.Study_ID.nunique() == 510
    assert d.Comparison_ID.is_unique
    selection = d.Management.eq("CRR") & d.CRR_Comparison.isin(COMPARISONS)
    s = d.loc[selection].copy()
    initial = len(s)
    measures = ["C_yield_ton", "T_yield_ton", "Control_SOC_Stock", "Treatment_SOC_Stock"]
    for col in measures:
        s[col] = pd.to_numeric(s[col], errors="coerce")
    valid = np.isfinite(s[measures]).all(axis=1) & s[measures].gt(0).all(axis=1)
    s = s.loc[valid].copy()
    s["yield_log_ratio"] = np.log(s.T_yield_ton / s.C_yield_ton)
    s["soc_log_ratio"] = np.log(s.Treatment_SOC_Stock / s.Control_SOC_Stock)
    s["Pathway"] = s.CRR_Comparison.map(COMPARISONS)
    assert np.isfinite(s[["yield_log_ratio", "soc_log_ratio"]]).all().all()
    s.to_csv(OUT / "selected_comparisons.csv", index=False, columns=[
        "Study_ID", "Comparison_ID", "Title", "DOI", "Region", "Country", "Latitude", "Longitude",
        "Main_Crop", "Combined_Climate_Class", "Length_Year", "CRR_Comparison", "Pathway",
        "yield_log_ratio", "soc_log_ratio",
    ])

    retained = s[s.CRR_Comparison.str.startswith("Removed-")].copy()
    retained["Scope"] = "Residue return vs removal"
    subsets = [retained, s.assign(Scope=s.Pathway)]
    summary = pd.concat([summarize(part, "Scope") for part in subsets], ignore_index=True)
    for dim in ["Main_Crop", "Combined_Climate_Class", "Region"]:
        summary = pd.concat([summary, summarize(retained, dim)], ignore_index=True)
    summary.to_csv(OUT / "paper_balanced_summaries.csv", index=False, float_format="%.5f")

    p = paper_medians(retained)
    p.to_csv(OUT / "paper_medians_return_vs_removal.csv", index=False, float_format="%.8f")
    joint = {
        "papers": len(p),
        "positive_yield_and_soc_papers": int(((p.yield_log_ratio > 0) & (p.soc_log_ratio > 0)).sum()),
        "negative_yield_positive_soc_papers": int(((p.yield_log_ratio < 0) & (p.soc_log_ratio > 0)).sum()),
        "positive_yield_negative_soc_papers": int(((p.yield_log_ratio > 0) & (p.soc_log_ratio < 0)).sum()),
        "negative_yield_and_soc_papers": int(((p.yield_log_ratio < 0) & (p.soc_log_ratio < 0)).sum()),
    }
    # Grossly implausible ratios are a *sensitivity*, never silently excluded.
    plausible = retained[retained[["yield_log_ratio", "soc_log_ratio"]].abs().le(np.log(10)).all(axis=1)]
    manifest = {
        "source_url": "https://github.com/davidencarnation/sustainable_ag_SOC_yield_meta_analysis",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "source_rows": len(d), "source_papers": int(d.Study_ID.nunique()),
        "pre_validity_residue_rows": initial, "post_validity_residue_rows": len(s),
        "return_vs_removal_rows": len(retained), "return_vs_removal_papers": int(retained.Study_ID.nunique()),
        "implausible_ratio_rows_omitted_sensitivity": len(retained) - len(plausible),
        "plausible_sensitivity_papers": int(plausible.Study_ID.nunique()),
        "plausible_sensitivity_summary": summarize(plausible.assign(Scope="Residue return vs removal"), "Scope").to_dict(orient="records"),
        "joint_study_median_signs": joint,
        "method": "Median log treatment/control ratio within Study_ID, then median across papers; 4000 paper-resampling bootstrap draws, no inverse-variance weighting.",
        "limitations": [
            "A Study_ID is a source paper, not necessarily an independent field site or trial.",
            "The source is a secondary curated dataset; primary paper values have not all been rechecked.",
            "Region and climate contrasts are descriptive, confounded and unevenly supported.",
            "Only crop-residue retention/incorporation is covered; no biochar or N2O outcome here.",
            "Source authors report cleaned data; some measurement uncertainties may be imputed.",
        ],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    build()
