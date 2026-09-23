"""Export the full-text-validated effect layer as a compact public CSV.

This is a projection of the local 196-column audit table, not a replacement for
the primary extraction records. One output row is one paired effect, whereas
``study_id`` identifies the independent field experiment for analysis.
"""

from __future__ import annotations

import argparse
import csv
import io
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data/formal_analysis_v1/outputs/formal_validated_staging_v0.csv"
DEFAULT_OUTPUT = ROOT / "literature/evidence_database.csv"

FIELDS = [
    "effect_id", "study_id", "paper_doi", "paper_title", "citation",
    "publication_year", "experiment_year", "country", "location",
    "latitude", "longitude", "broad_climate", "koppen_climate",
    "crop_as_reported", "crop_core", "season",
    "residue_as_reported", "pathway", "outcome", "outcome_unit",
    "treatment_arm", "control_arm", "treatment_mean", "control_mean",
    "treatment_sd", "control_sd", "treatment_n", "control_n",
    "lnrr", "variance_lnrr", "percent_change", "shared_control_group",
    "source_locator", "variance_provenance", "analysis_tier", "formal_decision",
    "independence_resolution", "sensitivity_note", "quality_flags", "system_boundary",
    "gwp_version", "soc_measure", "soil_depth", "water_regime",
    "nitrogen_rate", "extraction_method",
]

PATHWAYS = {"direct_return", "biochar_return", "open_burning"}


def value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        item = (row.get(key) or "").strip()
        if item and item.lower() not in {"nan", "none", "null"}:
            return item
    return ""


def number(row: dict[str, str], key: str, *, positive: bool = False) -> float:
    text = value(row, key)
    if not text:
        raise ValueError(f"Missing required numeric field {key} for {value(row, 'effect_id')}")
    result = float(text)
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValueError(f"Invalid {key}={text} for {value(row, 'effect_id')}")
    return result


def compact(result: float) -> str:
    return format(result, ".12g")


def publication_year(row: dict[str, str]) -> str:
    year = value(row, "publication_year")
    if year.endswith(".0") and year[:-2].isdigit() and len(year[:-2]) == 4:
        return year[:-2]
    return year


def project(row: dict[str, str]) -> dict[str, str]:
    effect_id = value(row, "effect_id")
    study_id = value(row, "independent_study_key")
    if not effect_id or not study_id:
        raise ValueError("Every formal effect needs an effect_id and study_id")
    if value(row, "analysis_pathway") not in PATHWAYS:
        raise ValueError(f"Unexpected pathway for {effect_id}")
    if value(row, "reviewed_against_fulltext").lower() not in {"true", "1", "yes"}:
        raise ValueError(f"Effect not verified against full text: {effect_id}")
    if not value(row, "formal_decision").startswith("ADMIT"):
        raise ValueError(f"Effect lacks a formal admission decision: {effect_id}")

    treatment_mean = number(row, "treatment_mean", positive=True)
    control_mean = number(row, "control_mean", positive=True)
    treatment_sd = number(row, "treatment_sd")
    control_sd = number(row, "control_sd")
    treatment_n = number(row, "treatment_n", positive=True)
    control_n = number(row, "control_n", positive=True)
    lnrr = number(row, "analysis_lnRR")
    variance = number(row, "analysis_variance", positive=True)
    if treatment_sd < 0 or control_sd < 0 or min(treatment_n, control_n) < 2:
        raise ValueError(f"Invalid arm uncertainty or replicate n for {effect_id}")
    if abs(math.log(treatment_mean / control_mean) - lnrr) > 1e-8:
        raise ValueError(f"lnRR does not match arm means for {effect_id}")

    quality_flags = []
    if "row_level_origin_unresolved" in value(row, "variance_provenance").lower():
        quality_flags.append("variance_row_origin_unresolved")
    if "pending" in value(row, "analysis_tier").lower():
        quality_flags.append("legacy_analysis_tier_pending")
    if not value(row, "primary_paper_doi"):
        quality_flags.append("primary_doi_missing")
    if not value(row, "primary_table_locator"):
        quality_flags.append("source_locator_missing")

    return {
        "effect_id": effect_id,
        "study_id": study_id,
        "paper_doi": value(row, "primary_paper_doi"),
        "paper_title": value(row, "title"),
        "citation": value(row, "citation"),
        "publication_year": publication_year(row),
        "experiment_year": value(row, "experiment_year"),
        "country": value(row, "country", "site_country"),
        "location": value(row, "location"),
        "latitude": value(row, "latitude"),
        "longitude": value(row, "longitude"),
        "broad_climate": value(row, "broad_climate"),
        "koppen_climate": value(row, "koppen_climate"),
        "crop_as_reported": value(row, "crop"),
        "crop_core": value(row, "crop_core"),
        "season": value(row, "season"),
        "residue_as_reported": value(row, "biochar_feedstock_verified", "residue"),
        "pathway": value(row, "analysis_pathway"),
        "outcome": value(row, "analysis_outcome"),
        "outcome_unit": value(row, "unit"),
        "treatment_arm": value(row, "treatment_arm"),
        "control_arm": value(row, "control_arm"),
        "treatment_mean": compact(treatment_mean),
        "control_mean": compact(control_mean),
        "treatment_sd": compact(treatment_sd),
        "control_sd": compact(control_sd),
        "treatment_n": compact(treatment_n),
        "control_n": compact(control_n),
        "lnrr": compact(lnrr),
        "variance_lnrr": compact(variance),
        "percent_change": compact(math.expm1(lnrr) * 100),
        "shared_control_group": value(row, "shared_control_group"),
        "source_locator": value(row, "primary_table_locator"),
        "variance_provenance": value(row, "variance_provenance"),
        "analysis_tier": value(row, "analysis_tier"),
        "formal_decision": value(row, "formal_decision"),
        "independence_resolution": value(row, "independence_resolution"),
        "sensitivity_note": value(row, "sensitivity_note"),
        "quality_flags": ";".join(quality_flags),
        "system_boundary": value(row, "system_boundary"),
        "gwp_version": value(row, "GWP_version"),
        "soc_measure": value(row, "SOC_measure"),
        "soil_depth": value(row, "soil_depth"),
        "water_regime": value(row, "water_regime"),
        "nitrogen_rate": value(row, "nitrogen_rate"),
        "extraction_method": value(row, "data_extraction_method"),
    }


def build_csv(source: Path) -> tuple[str, int, int]:
    with source.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError("Source table has no header")
        records = [project(row) for row in reader]
    ids = [record["effect_id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("effect_id must be unique")
    if not records:
        raise ValueError("Source table contains no formal effects")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return buffer.getvalue(), len(records), len({r["study_id"] for r in records})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Verify existing CSV matches the source")
    args = parser.parse_args()
    content, effects, studies = build_csv(args.source)
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != content:
            raise SystemExit("Evidence CSV is missing or out of date; run without --check")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8", newline="")
    print(f"validated_effects={effects} independent_studies={studies} columns={len(FIELDS)}")


if __name__ == "__main__":
    main()
