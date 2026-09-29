#!/usr/bin/env python3
"""Build the Fig. 2 pathway × endpoint independent-trial promotion matrix.

This is a count-gate audit, not a meta-analysis. Reaching the target count
does not establish model readiness or global representativeness.
"""
from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path

DEFAULT_INPUT = Path("data/processed/fig2_three_pathway_stats_20260929/pathway_endpoint_summary.csv")
DEFAULT_OUTPUT = Path("data/processed/fig2_promotion_20260929/pathway_endpoint_promotion.csv")
TARGET = 10
PATHWAYS = ("direct_return", "biochar_return", "open_burning")
ENDPOINTS = ("yield", "SOC_concentration", "CH4", "N2O")
FIELDS = (
    "pathway", "endpoint", "independent_trial_keys", "treatment_comparisons",
    "countries", "crops", "target_independent_trials", "gap_to_10",
    "count_gate_status", "inference_guardrail",
)

def classify(k: int) -> str:
    if k >= TARGET:
        return "COUNT_GATE_MET_BOUNDARY_REVIEW_REQUIRED"
    if k >= 5:
        return "NEAR_COUNT_GATE"
    return "CRITICAL_INDEPENDENT_TRIAL_GAP"

def build_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        src = list(csv.DictReader(fh))
    lookup = {(r["pathway"], r["endpoint"]): r for r in src}
    rows = []
    missing = []
    for pathway in PATHWAYS:
        for endpoint in ENDPOINTS:
            r = lookup.get((pathway, endpoint))
            if r is None:
                missing.append((pathway, endpoint))
                continue
            k = int(r["independent_trial_keys"])
            rows.append({
                "pathway": pathway,
                "endpoint": endpoint,
                "independent_trial_keys": str(k),
                "treatment_comparisons": r.get("treatment_comparisons", r.get("effect_records", "")),
                "countries": r["countries"],
                "crops": r["crops"],
                "target_independent_trials": str(TARGET),
                "gap_to_10": str(max(0, TARGET-k)),
                "count_gate_status": classify(k),
                "inference_guardrail": "screening_target_only_not_model_readiness",
            })
    if missing:
        raise SystemExit(f"Missing required cells: {missing}")
    return rows

def render(rows: list[dict[str, str]]) -> str:
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    expected = render(build_rows(args.input))
    if args.check:
        if not args.output.exists():
            raise SystemExit(f"Missing output: {args.output}")
        if args.output.read_text(encoding="utf-8-sig") != expected:
            raise SystemExit("Promotion matrix is stale; rerun without --check.")
        print(f"OK: {args.output}")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(expected, encoding="utf-8")
    print(f"Wrote {args.output}")

if __name__ == "__main__":
    main()
