"""Paper-balanced descriptive duration analysis for residue return vs removal."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/encarnation2026_residue_reanalysis/selected_comparisons.csv"
OUT = ROOT / "data/processed/return_duration_20260928"
EDGES = [0, 2, 5, 10, 20, np.inf]
LABELS = ["1–2", ">2–5", ">5–10", ">10–20", ">20"]


def paper_units(frame: pd.DataFrame) -> pd.DataFrame:
    d = frame[frame.CRR_Comparison.isin(["Removed-Incorporated", "Removed-Retained"])].copy()
    required = ["Title", "Comparison_ID", "Length_Year", "yield_log_ratio", "soc_log_ratio"]
    if d[required].isna().any().any() or d.Comparison_ID.duplicated().any():
        raise ValueError("Missing paper/comparison/response identity or repeated comparison ID")
    for col in ["Length_Year", "yield_log_ratio", "soc_log_ratio"]:
        d[col] = pd.to_numeric(d[col], errors="raise")
    if not np.isfinite(d[["Length_Year", "yield_log_ratio", "soc_log_ratio"]]).all().all():
        raise ValueError("Non-finite duration or log ratio")
    if (d.Length_Year <= 0).any():
        raise ValueError("Duration must be positive")
    # Exact publication title is the conservative statistical unit; multiple
    # treatments, years or sites in a paper are not independent publications.
    p = d.groupby("Title", sort=True, as_index=False).agg(
        duration_years=("Length_Year", "median"),
        yield_lnrr=("yield_log_ratio", "median"),
        soc_lnrr=("soc_log_ratio", "median"),
        comparisons=("Comparison_ID", "nunique"),
        region=("Region", lambda v: "|".join(sorted(set(v)))),
        crop=("Main_Crop", lambda v: "|".join(sorted(set(v)))),
        durations_within_paper=("Length_Year", "nunique"),
    )
    p["duration_bin"] = pd.cut(p.duration_years, EDGES, labels=LABELS, include_lowest=True)
    if p.duration_bin.isna().any():
        raise ValueError("Unbinned paper")
    return p


def pct(log_value: float) -> float:
    return float(100 * np.expm1(log_value))


def interval(values: np.ndarray, seed: int, draws: int = 4000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    medians = np.median(rng.choice(values, size=(draws, len(values)), replace=True), axis=1)
    return pct(np.quantile(medians, .025)), pct(np.quantile(medians, .975))


def summaries(p: pd.DataFrame, seed: int = 20260928, draws: int = 4000) -> pd.DataFrame:
    rows = []
    for i, label in enumerate(LABELS):
        g = p[p.duration_bin.eq(label)]
        if g.empty:
            rows.append({"duration_bin": label, "papers": 0})
            continue
        row = dict(duration_bin=label, papers=len(g), comparisons=int(g.comparisons.sum()),
                   median_duration_years=float(g.duration_years.median()),
                   asia_papers=int(g.region.eq("Asia").sum()),
                   maize_papers=int(g.crop.str.split("|").apply(lambda v: "Maize" in v).sum()),
                   rice_papers=int(g.crop.str.split("|").apply(lambda v: "Rice" in v).sum()),
                   wheat_papers=int(g.crop.str.split("|").apply(lambda v: "Wheat" in v).sum()),
                   soybean_papers=int(g.crop.str.split("|").apply(lambda v: "Soybean" in v).sum()),
                   both_positive=int(((g.yield_lnrr > 0) & (g.soc_lnrr > 0)).sum()),
                   yield_only_positive=int(((g.yield_lnrr > 0) & (g.soc_lnrr <= 0)).sum()),
                   soc_only_positive=int(((g.yield_lnrr <= 0) & (g.soc_lnrr > 0)).sum()),
                   neither_positive=int(((g.yield_lnrr <= 0) & (g.soc_lnrr <= 0)).sum()))
        assert sum(row[k] for k in ("both_positive", "yield_only_positive",
                                    "soc_only_positive", "neither_positive")) == len(g)
        for j, (name, col) in enumerate((("yield", "yield_lnrr"), ("soc", "soc_lnrr"))):
            vals = g[col].to_numpy(float)
            row[f"{name}_median_percent"] = pct(np.median(vals))
            lo, hi = interval(vals, seed + i * 2 + j, draws) if len(vals) >= 5 else (np.nan, np.nan)
            row[f"{name}_bootstrap_lo_percent"] = lo
            row[f"{name}_bootstrap_hi_percent"] = hi
        rows.append(row)
    return pd.DataFrame(rows)


def build(source: Path = SOURCE, out: Path = OUT, draws: int = 4000) -> dict:
    source, out = Path(source), Path(out)
    d = pd.read_csv(source, low_memory=False)
    p = paper_units(d)
    primary = summaries(p, draws=draws)
    selected = d[d.CRR_Comparison.isin(["Removed-Incorporated", "Removed-Retained"])]
    plausible = selected[selected[["yield_log_ratio", "soc_log_ratio"]].abs().le(np.log(10)).all(axis=1)]
    sensitivity_frames = []
    for label, frame in (
        ("all", p), ("Asia_only", p[p.region.eq("Asia")]),
        ("non_Asia", p[~p.region.eq("Asia")]),
        ("exclude_soybean_papers", p[~p.crop.str.split("|").apply(lambda v: "Soybean" in v)]),
        ("single_duration_papers", p[p.durations_within_paper.eq(1)]),
        ("ratio_within_tenfold", paper_units(plausible)),
    ):
        s = summaries(frame, draws=draws)
        s.insert(0, "subset", label)
        sensitivity_frames.append(s)
    sensitivity = pd.concat(sensitivity_frames, ignore_index=True)
    out.mkdir(parents=True, exist_ok=True)
    primary.to_csv(out / "duration_summary.csv", index=False, float_format="%.6f")
    sensitivity.to_csv(out / "duration_sensitivity.csv", index=False, float_format="%.6f")
    manifest = {
        "source": str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "selected_comparisons": int(len(selected)), "paper_titles": int(len(p)),
        "papers_with_multiple_duration_values": int(p.durations_within_paper.gt(1).sum()),
        "duration_assignment": "median Length_Year within exact Title",
        "paper_response": "median log treatment/control ratio within exact Title",
        "crop_counts": "non-exclusive paper membership; one paper can report multiple crops",
        "bins_years": dict(zip(LABELS, ["(0,2]", "(2,5]", "(5,10]", "(10,20]", "(20,inf)"])),
        "interval": f"percentile interval from {draws} paper-level bootstrap resamples per bin; not a formal meta-analysis CI",
        "independent_unit": "publication Title; not treatment arm, year, or independent field trial",
        "inference": "descriptive cross-paper association; duration is confounded with crop, region and management; no causal duration effect",
        "source_layer": "third-party secondary compilation, not added to curated primary V1",
        "software": {"pandas": pd.__version__, "numpy": np.__version__},
        "outputs_sha256": {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                           for name in ["duration_summary.csv", "duration_sensitivity.csv"]},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.out), ensure_ascii=False, indent=2))
