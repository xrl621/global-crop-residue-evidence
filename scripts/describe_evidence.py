"""Report effect counts and independent study coverage from the public CSV.

The count threshold uses studies with no unresolved row-level variance origin.
A stricter sensitivity screen also omits pooled-SE and large-relative-SE flags.
Neither screen declares an analysis valid without dependence, other uncertainty,
and system-boundary audits.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "literature/evidence_database.csv"
FIELDS = [
    "pathway", "outcome", "effect_rows", "independent_studies",
    "variance_screen_effect_rows", "variance_screen_independent_studies",
    "strict_screen_effect_rows", "strict_screen_independent_studies",
    "rows_with_quality_flags", "meets_count_threshold", "meets_strict_threshold",
]

STRICT_EXCLUSION_FLAGS = {
    "pooled_se_denominator_ambiguous",
    "large_relative_se_lnrr_delta_approx",
}


def summarize(path: Path, minimum_studies: int) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], dict[str, object]] = defaultdict(
        lambda: {"effects": 0, "studies": set(), "variance_effects": 0,
                 "variance_studies": set(), "strict_effects": 0,
                 "strict_studies": set(), "flagged": 0}
    )
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "variance_origin_status" not in reader.fieldnames:
            raise ValueError("Input needs the current variance_origin_status column")
        for row in reader:
            pathway, outcome, study = row["pathway"], row["outcome"], row["study_id"]
            if not pathway or not outcome or not study:
                raise ValueError("Each row requires pathway, outcome and study_id")
            variance_status = row["variance_origin_status"]
            if variance_status not in {"unresolved_row_origin", "documented_or_reconstructed"}:
                raise ValueError(f"Unknown variance origin status for {row['effect_id']}")
            group = groups[(pathway, outcome)]
            group["effects"] += 1
            group["studies"].add(study)
            group["flagged"] += bool(row["quality_flags"])
            if variance_status == "documented_or_reconstructed":
                group["variance_effects"] += 1
                group["variance_studies"].add(study)
                flags = set(filter(None, row["quality_flags"].split(";")))
                if not (flags & STRICT_EXCLUSION_FLAGS):
                    group["strict_effects"] += 1
                    group["strict_studies"].add(study)
    result = []
    for (pathway, outcome), group in sorted(groups.items()):
        n_studies = len(group["studies"])
        result.append({
            "pathway": pathway,
            "outcome": outcome,
            "effect_rows": group["effects"],
            "independent_studies": n_studies,
            "variance_screen_effect_rows": group["variance_effects"],
            "variance_screen_independent_studies": len(group["variance_studies"]),
            "strict_screen_effect_rows": group["strict_effects"],
            "strict_screen_independent_studies": len(group["strict_studies"]),
            "rows_with_quality_flags": group["flagged"],
            "meets_count_threshold": str(
                len(group["variance_studies"]) >= minimum_studies
            ).lower(),
            "meets_strict_threshold": str(
                len(group["strict_studies"]) >= minimum_studies
            ).lower(),
        })
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--minimum-studies", type=int, default=10)
    args = parser.parse_args()
    if args.minimum_studies < 1:
        parser.error("--minimum-studies must be positive")
    writer = csv.DictWriter(sys.stdout, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(summarize(args.input, args.minimum_studies))


if __name__ == "__main__":
    main()
