"""Report effect counts and independent study coverage from the public CSV.

This checks only the predeclared minimum study count. It does not declare a
pathway/outcome analysis valid without dependence, uncertainty and boundary
audits.
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
    "rows_with_quality_flags", "meets_count_threshold",
]


def summarize(path: Path, minimum_studies: int) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], dict[str, object]] = defaultdict(
        lambda: {"effects": 0, "studies": set(), "flagged": 0}
    )
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            pathway, outcome, study = row["pathway"], row["outcome"], row["study_id"]
            if not pathway or not outcome or not study:
                raise ValueError("Each row requires pathway, outcome and study_id")
            group = groups[(pathway, outcome)]
            group["effects"] += 1
            group["studies"].add(study)
            group["flagged"] += bool(row["quality_flags"])
    result = []
    for (pathway, outcome), group in sorted(groups.items()):
        n_studies = len(group["studies"])
        result.append({
            "pathway": pathway,
            "outcome": outcome,
            "effect_rows": group["effects"],
            "independent_studies": n_studies,
            "rows_with_quality_flags": group["flagged"],
            "meets_count_threshold": str(n_studies >= minimum_studies).lower(),
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
