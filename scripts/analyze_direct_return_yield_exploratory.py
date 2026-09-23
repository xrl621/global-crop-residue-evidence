"""Exploratory, study-balanced direct-return yield audit (not a meta-analysis).

One field trial contributes one mean log response ratio, regardless of how many
years, crops, or nitrogen strata were extracted from it. Within-trial effects
are averaged equally; this is a descriptive choice, not a variance model.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

from describe_evidence import STRICT_EXCLUSION_FLAGS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "literature/evidence_database.csv"
LAND_CLEARING_TRIAL = "mbah_nneji_agbani_2007_2008"
UNLABELLED_ARMS_TRIAL = "rice_primary_140"


def percent(log_ratio: float) -> float:
    return 100.0 * math.expm1(log_ratio)


def load_study_effects(path: Path) -> dict[str, dict[str, object]]:
    studies: dict[str, dict[str, object]] = defaultdict(
        lambda: {"values": [], "countries": set(), "crops": set()}
    )
    seen: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["effect_id"] in seen:
                raise ValueError(f"Duplicate effect_id: {row['effect_id']}")
            seen.add(row["effect_id"])
            if row["pathway"] != "direct_return" or row["outcome"] != "yield":
                continue
            flags = set(filter(None, row["quality_flags"].split(";")))
            if row["variance_origin_status"] != "documented_or_reconstructed":
                continue
            if flags & STRICT_EXCLUSION_FLAGS:
                continue
            value = float(row["lnrr"])
            if not math.isfinite(value):
                raise ValueError(f"Non-finite lnRR: {row['effect_id']}")
            study = studies[row["study_id"]]
            study["values"].append(value)
            study["countries"].add(row["country"])
            crop = row["crop_core"] or row["crop_as_reported"] or "unspecified"
            study["crops"].add(crop)
    return dict(studies)


def study_mean(study: dict[str, object]) -> float:
    values = study["values"]
    return sum(values) / len(values)


def summarize(studies: dict[str, dict[str, object]], excluded: set[str]) -> dict[str, object]:
    selected = {key: value for key, value in studies.items() if key not in excluded}
    if not selected:
        raise ValueError("No studies remain")
    means = {key: study_mean(value) for key, value in selected.items()}
    balance = sum(means.values()) / len(means)
    leave_one_out = {
        key: percent(sum(value for other, value in means.items() if other != key)
                     / (len(means) - 1))
        for key in means
    } if len(means) > 1 else {}
    return {
        "studies": len(selected),
        "effects": sum(len(study["values"]) for study in selected.values()),
        "positive_studies": sum(value > 0 for value in means.values()),
        "balanced_percent": percent(balance),
        "study_percent_range": (min(map(percent, means.values())),
                                max(map(percent, means.values()))),
        "leave_one_out_range": (min(leave_one_out.values()),
                               max(leave_one_out.values())) if leave_one_out else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    studies = load_study_effects(args.input)
    print("Strict uncertainty-screened rows; study is the descriptive unit.")
    print("Within-study mean lnRR is unweighted across extracted arms/years.")
    print("study_id,effects,country,crop_as_available,study_mean_percent")
    for key, study in sorted(studies.items()):
        print(f"{key},{len(study['values'])},"
              f"{'|'.join(sorted(study['countries']))},"
              f"{'|'.join(sorted(study['crops']))},{percent(study_mean(study)):.3f}")
    for label, excluded in (
        ("all_uncertainty_screened", set()),
        ("exclude_land_clearing_residue", {LAND_CLEARING_TRIAL}),
        ("also_exclude_unlabelled_arms", {LAND_CLEARING_TRIAL, UNLABELLED_ARMS_TRIAL}),
    ):
        result = summarize(studies, excluded)
        print(f"{label}: {result}")
    print("Descriptive only: no pooled SE, CI, P value, or global inference.")


if __name__ == "__main__":
    main()
