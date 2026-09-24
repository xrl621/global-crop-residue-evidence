"""Describe currently source-screened straw-burning yield trials, not a meta-analysis.

One field trial contributes one mean lnRR after averaging repeated years or
water/season strata within that trial. This deliberately reports no pooled
standard error or global treatment effect while the 10-trial gate is closed.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

try:
    from scripts.describe_evidence import STRICT_EXCLUSION_FLAGS, STRAW_ORIGIN_EXCLUSION_FLAGS
except ModuleNotFoundError:  # direct `python scripts/analysis.py` execution
    from describe_evidence import STRICT_EXCLUSION_FLAGS, STRAW_ORIGIN_EXCLUSION_FLAGS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "literature/evidence_database.csv"


def percent(log_ratio: float) -> float:
    return 100 * math.expm1(log_ratio)


def study_level(path: Path) -> dict[str, dict[str, object]]:
    studies: dict[str, dict[str, object]] = defaultdict(
        lambda: {"lnrr": [], "crop": set(), "country": set()}
    )
    seen: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["effect_id"] in seen:
                raise ValueError(f"Duplicate effect_id: {row['effect_id']}")
            seen.add(row["effect_id"])
            if (row["pathway"], row["outcome"]) != ("open_burning", "yield"):
                continue
            flags = set(filter(None, row["quality_flags"].split(";")))
            if (row["variance_origin_status"] != "documented_or_reconstructed"
                    or flags & (STRICT_EXCLUSION_FLAGS | STRAW_ORIGIN_EXCLUSION_FLAGS)):
                continue
            if not row["treatment_arm"] or not row["control_arm"]:
                raise ValueError(f"Screened effect lacks arms: {row['effect_id']}")
            crop = row["crop_core"] or row["crop_as_reported"]
            if not crop:
                raise ValueError(f"Screened effect lacks crop: {row['effect_id']}")
            lnrr = float(row["lnrr"])
            if not math.isfinite(lnrr):
                raise ValueError(f"Non-finite effect: {row['effect_id']}")
            trial = studies[row["study_id"]]
            trial["lnrr"].append(lnrr)
            trial["crop"].add(crop)
            trial["country"].add(row["country"])
    return dict(studies)


def summarize(studies: dict[str, dict[str, object]]) -> dict[str, float | int]:
    values = [sum(item["lnrr"]) / len(item["lnrr"]) for item in studies.values()]
    if not values:
        raise ValueError("No eligible trials")
    sorted_values = sorted(values)
    middle = len(values) // 2
    median = (sorted_values[middle] if len(values) % 2 else
              (sorted_values[middle - 1] + sorted_values[middle]) / 2)
    leave_one_out = [percent((sum(values) - value) / (len(values) - 1))
                     for value in values] if len(values) > 1 else []
    return {
        "independent_trials": len(values),
        "effect_rows": sum(len(item["lnrr"]) for item in studies.values()),
        "positive_trials": sum(value > 0 for value in values),
        "negative_trials": sum(value < 0 for value in values),
        "study_median_percent": percent(median),
        "study_percent_min": percent(min(values)),
        "study_percent_max": percent(max(values)),
        "equal_trial_average_percent": percent(sum(values) / len(values)),
        "leave_one_out_min": min(leave_one_out) if leave_one_out else math.nan,
        "leave_one_out_max": max(leave_one_out) if leave_one_out else math.nan,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    studies = study_level(args.input)
    print("study_id,effect_rows,crop,country,trial_mean_percent")
    for study_id, item in sorted(studies.items()):
        lnrr = sum(item["lnrr"]) / len(item["lnrr"])
        print(f"{study_id},{len(item['lnrr'])},"
              f"{'|'.join(sorted(item['crop']))},{'|'.join(sorted(item['country']))},"
              f"{percent(lnrr):.3f}")
    print(summarize(studies))
    print("DESCRIPTIVE ONLY: no pooled CI, P value, pathway ranking or global inference.")


if __name__ == "__main__":
    main()
