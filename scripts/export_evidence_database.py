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
PRIMARY_ADDENDA = [
    ROOT / "literature/primary_extractions/liu2016_direct_return.csv",
    ROOT / "literature/primary_extractions/panneerselvam2024_yield.csv",
    ROOT / "literature/primary_extractions/huang2013_yield_n2o.csv",
    ROOT / "literature/primary_extractions/sharma2023_yield.csv",
    ROOT / "literature/primary_extractions/du2024_yield_soc_gwp_ghgi.csv",
]

FIELDS = [
    "effect_id", "study_id", "paper_doi", "paper_title", "citation",
    "publication_year", "experiment_year", "country", "location",
    "latitude", "longitude", "broad_climate", "koppen_climate",
    "crop_as_reported", "crop_core", "season",
    "residue_as_reported", "pathway", "outcome", "outcome_unit",
    "treatment_arm", "control_arm", "treatment_mean", "control_mean",
    "treatment_sd", "control_sd", "treatment_n", "control_n",
    "lnrr", "variance_lnrr", "percent_change", "shared_control_group",
    "source_locator", "variance_provenance", "analysis_tier", "source_analysis_tier",
    "tier_reconciliation", "formal_decision", "variance_origin_status",
    "independence_resolution", "sensitivity_note", "quality_flags", "system_boundary",
    "gwp_version", "soc_measure", "soil_depth", "water_regime",
    "nitrogen_rate", "extraction_method",
]

PATHWAYS = {"direct_return", "biochar_return", "open_burning"}

# These three candidate-tier labels were not updated when the named study's
# primary-source review replaced the secondary extraction. Keep the original
# label in the public export and fail closed if the expected reviewed row
# signature changes. This does not resolve uncertainty in studies 3 or 176.
RECONCILED_TIERS = {
    "biochar_li2024SD_31": {
        "tier": "A_primary_matched_pair_figure_digitized_SD",
        "locators": {"yield": "Figure 2"},
        "variance_marker": "primary states mean ± one SD",
    },
    "biochar_li2024SD_71": {
        "tier": "A_primary_matched_pair_SE_converted_table_and_figure",
        "locators": {"yield": "Table 5", "CH4": "Figure 3a", "N2O": "Figure 3b"},
        "variance_marker": "primary SE converted to SD",
    },
    "biochar_li2024SD_73": {
        "tier": "A_primary_exact_table_mean_SD",
        "locators": {"SOC": "Table 2"},
        "variance_marker": "primary Table 2 mean ± SD",
    },
}

# Table 2 of doi:10.3390/agronomy13030880 reports these within-tillage
# rice-yield contrasts as mean ± SE. The legacy staging omitted their arm and
# crop labels. Only the three yield rows are backfilled here: the other 12
# outcome rows require separate source-value/unit reconciliation.
RICE_140_YIELD_BACKFILL = {
    "rice_primary_rice_ext_pair_0013_yield": {
        "means": (7000.0, 7700.0), "arms": ("RoT + S", "RoT - S"),
        "system": "rice in rice-wheat cropping system",
    },
    "rice_primary_rice_ext_pair_0014_yield": {
        "means": (9100.0, 8800.0), "arms": ("PT + S", "PT - S"),
        "system": "single rice",
    },
    "rice_primary_rice_ext_pair_0015_yield": {
        "means": (8200.0, 9100.0), "arms": ("RoT + S", "RoT - S"),
        "system": "double rice",
    },
}

LAND_CLEARING_STUDY = "mbah_nneji_agbani_2007_2008"


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


def analysis_tier(row: dict[str, str]) -> tuple[str, str]:
    original = value(row, "analysis_tier")
    study_id = value(row, "independent_study_key")
    rule = RECONCILED_TIERS.get(study_id)
    if not rule or "pending" not in original.lower():
        return original, ""
    outcome = value(row, "analysis_outcome")
    locator = value(row, "primary_table_locator")
    provenance = value(row, "variance_provenance")
    if (
        value(row, "analysis_pathway") != "biochar_return"
        or rule["locators"].get(outcome) != locator
        or rule["variance_marker"] not in provenance
        or "row_level_origin_unresolved" in provenance.lower()
    ):
        raise ValueError(f"Tier reconciliation signature changed for {value(row, 'effect_id')}")
    return rule["tier"], "primary_fulltext_review_reconciled_2026-09-23"


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

    tier, projected_reconciliation = analysis_tier(row)
    tier_reconciliation = value(row, "tier_reconciliation") or projected_reconciliation
    quality_flags = []
    if "row_level_origin_unresolved" in value(row, "variance_provenance").lower():
        quality_flags.append("variance_row_origin_unresolved")
    if "pending" in tier.lower():
        quality_flags.append("legacy_analysis_tier_pending")
    provenance_lower = value(row, "variance_provenance").lower()
    if "footnote omits the label" in provenance_lower or "without defining se versus sd" in provenance_lower:
        quality_flags.append("reported_error_type_ambiguous")
    if not value(row, "primary_paper_doi"):
        quality_flags.append("primary_doi_missing")
    if not value(row, "primary_table_locator"):
        quality_flags.append("source_locator_missing")

    if study_id == LAND_CLEARING_STUDY:
        if not (
            value(row, "primary_paper_doi") == "10.5897/AJAR09.746"
            and "land-clearing residue" in value(row, "control_arm")
        ):
            raise ValueError(f"Land-clearing source signature changed for {effect_id}")
        quality_flags.append("land_clearing_residue_not_harvest_straw")

    backfill = RICE_140_YIELD_BACKFILL.get(effect_id)
    if backfill:
        if not (
            study_id == "rice_primary_140"
            and value(row, "primary_paper_doi") == "10.3390/agronomy13030880"
            and value(row, "analysis_pathway") == "direct_return"
            and value(row, "analysis_outcome") == "yield"
            and "Table 2" in value(row, "primary_table_locator")
            and (treatment_mean, control_mean) == backfill["means"]
            and not any(value(row, key) for key in
                        ("crop", "crop_core", "treatment_arm", "control_arm"))
        ):
            raise ValueError(f"Rice 140 Table 2 backfill signature changed for {effect_id}")
        quality_flags.append("primary_table_metadata_backfilled")
    elif study_id == "rice_primary_140":
        if not (
            value(row, "primary_paper_doi") == "10.3390/agronomy13030880"
            and value(row, "analysis_pathway") == "direct_return"
            and value(row, "analysis_outcome") in {"CH4", "N2O", "GWP", "GHGI"}
            and effect_id.startswith("rice_primary_rice_ext_pair_00")
        ):
            raise ValueError(f"Rice 140 non-yield signature changed for {effect_id}")
        quality_flags.append("primary_non_yield_arm_and_value_recheck")

    result = {
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
        "analysis_tier": tier,
        "source_analysis_tier": value(row, "secondary_analysis_tier", "analysis_tier"),
        "tier_reconciliation": tier_reconciliation,
        "formal_decision": value(row, "formal_decision"),
        "variance_origin_status": (
            "unresolved_row_origin" if "variance_row_origin_unresolved" in quality_flags
            else "documented_or_reconstructed"
        ),
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
    if backfill:
        result["crop_as_reported"] = backfill["system"]
        result["crop_core"] = "rice"
        result["treatment_arm"], result["control_arm"] = backfill["arms"]
        result["outcome_unit"] = "kg ha-1 grain yield"
        result["sensitivity_note"] = (
            (result["sensitivity_note"] + "; ") if result["sensitivity_note"] else ""
        ) + "crop and arms backfilled from primary Table 2; other outcomes not reconciled"
    return result


def project_primary_addendum(row: dict[str, str]) -> dict[str, str]:
    """Project a verified arm-level table transcription into the public schema."""
    effect_id = value(row, "effect_id")
    if not effect_id or value(row, "pathway") not in PATHWAYS:
        raise ValueError(f"Invalid primary addendum identity/pathway: {effect_id}")
    study_id = value(row, "study_id")
    if study_id not in {"rice_primary_53", "panneerselvam_cuttack_2021_2022", "huang_shangzhuang_2006_2013", "sharma_ludhiana_2011_2018", "du_dingxi_2016_2022"}:
        raise ValueError(f"Primary addendum study needs explicit review: {effect_id}")
    if study_id == "panneerselvam_cuttack_2021_2022" and not (
        value(row, "paper_doi") == "10.1016/j.jenvman.2024.120916"
        and value(row, "pathway") == "direct_return"
        and value(row, "outcome") == "yield"
        and value(row, "source_locator") == "Table 2"
        and value(row, "treatment_arm").replace("RR+", "", 1) == value(row, "control_arm").replace("CC+", "", 1)
        and value(row, "treatment_arm").startswith("RR+")
        and value(row, "control_arm").startswith("CC+")
        and value(row, "season") in {"Kharif_wet", "Rabi_dry"}
    ):
        raise ValueError(f"Panneerselvam matched-stratum signature changed: {effect_id}")
    if study_id == "huang_shangzhuang_2006_2013" and not (
        value(row, "paper_doi") == "10.5194/bg-10-7897-2013"
        and value(row, "pathway") == "direct_return"
        and (value(row, "outcome"), value(row, "source_locator")) in {("yield", "Table 3"), ("N2O", "Table 5")}
        and (value(row, "treatment_arm"), value(row, "control_arm")) in {("SN0", "N0"), ("SNcon", "Ncon")}
        and value(row, "crop_core") in {"wheat", "maize"}
        and value(row, "nitrogen_rate") == (
            "0 kg N ha-1" if value(row, "control_arm") == "N0"
            else "300 kg N ha-1" if value(row, "crop_core") == "wheat"
            else "260 kg N ha-1"
        )
    ):
        raise ValueError(f"Huang fixed-N matched-arm signature changed: {effect_id}")
    if study_id == "sharma_ludhiana_2011_2018" and not (
        value(row, "paper_doi") == "10.1016/j.heliyon.2023.e17828"
        and value(row, "pathway") == "direct_return"
        and value(row, "outcome") == "yield"
        and value(row, "crop_core") in {"rice", "wheat"}
        and value(row, "source_locator") == ("Table 2" if value(row, "crop_core") == "rice" else "Table 3")
        and (value(row, "treatment_arm"), value(row, "control_arm")) in {
            ("CTRW25", "CTRW0"), ("CTRW25+GM", "CTRW0+GM")
        }
        and value(row, "experiment_year") == "2011-2018 pooled"
    ):
        raise ValueError(f"Sharma matched-tillage and matched-GM signature changed: {effect_id}")
    if study_id == "du_dingxi_2016_2022" and not (
        value(row, "paper_doi") == "10.3390/agronomy14092087"
        and value(row, "pathway") == "direct_return"
        and value(row, "crop_core") == "wheat"
        and value(row, "experiment_year") in {"2021", "2022"}
        and (value(row, "outcome"), value(row, "source_locator")) in {
            ("yield", "Table 3"), ("SOC", "Table 2"),
            ("GWP", "Table 3"), ("GHGI", "Table 3")
        }
        and (value(row, "treatment_arm"), value(row, "control_arm")) in {
            ("CTS-LN", "CT-LN"), ("CTS-MN", "CT-MN"), ("CTS-HN", "CT-HN")
        }
        and value(row, "nitrogen_rate") == {
            "LN": "55 kg N ha-1", "MN": "110 kg N ha-1", "HN": "220 kg N ha-1"
        }[value(row, "control_arm").split("-")[-1]]
        and (value(row, "outcome") != "SOC" or (
            value(row, "soc_measure") == "SOC concentration"
            and value(row, "soil_depth") == "0-10 cm"
        ))
        and (value(row, "outcome") not in {"GWP", "GHGI"} or
             value(row, "gwp_version") == "AR4 CH4=25 N2O=298")
        and value(row, "latitude") == ""
        and value(row, "longitude") == ""
    ):
        raise ValueError(f"Du matched-N, matched-tillage source signature changed: {effect_id}")
    treatment_mean = number(row, "treatment_mean", positive=True)
    control_mean = number(row, "control_mean", positive=True)
    treatment_n = number(row, "treatment_n", positive=True)
    control_n = number(row, "control_n", positive=True)
    uses_se = bool(value(row, "treatment_se") or value(row, "control_se"))
    uses_sd = bool(value(row, "treatment_sd") or value(row, "control_sd"))
    if uses_se == uses_sd:
        raise ValueError(f"Primary addendum must report either SE or SD: {effect_id}")
    if (study_id == "panneerselvam_cuttack_2021_2022") != uses_sd:
        raise ValueError(f"Primary paper uncertainty type changed: {effect_id}")
    if treatment_n != 3 or control_n != 3:
        raise ValueError(f"Primary paper field replicate count changed: {effect_id}")
    if uses_se:
        treatment_se = number(row, "treatment_se")
        control_se = number(row, "control_se")
        treatment_sd = treatment_se * math.sqrt(treatment_n)
        control_sd = control_se * math.sqrt(control_n)
        provenance = "primary table mean +/- SE, n=3; converted to arm SD"
        tier = "A_primary_exact_pair_SE_converted"
    else:
        treatment_sd = number(row, "treatment_sd")
        control_sd = number(row, "control_sd")
        treatment_se = treatment_sd / math.sqrt(treatment_n)
        control_se = control_sd / math.sqrt(control_n)
        provenance = f"primary {value(row, 'source_locator')} mean +/- SD, n={compact(treatment_n)}; lnRR variance recomputed"
        tier = "A_primary_exact_pair_SD"
    if min(treatment_n, control_n) < 2 or min(treatment_sd, control_sd) < 0:
        raise ValueError(f"Invalid primary addendum uncertainty: {effect_id}")
    if not all(value(row, key) for key in (
        "study_id", "paper_doi", "outcome", "outcome_unit", "treatment_arm",
        "control_arm", "shared_control_group", "source_locator",
    )):
        raise ValueError(f"Incomplete primary addendum provenance: {effect_id}")
    lnrr = math.log(treatment_mean / control_mean)
    variance = (treatment_se / treatment_mean) ** 2 + (control_se / control_mean) ** 2
    result = {field: "" for field in FIELDS}
    for field in result:
        if field in row and field not in {"treatment_mean", "control_mean", "treatment_n", "control_n"}:
            result[field] = value(row, field)
    if study_id == "rice_primary_53":
        decision = "ADMIT_NPK_MATCHED_DIRECT_RETURN_VS_STRAW_REMOVAL"
        dependence = "Same field trial as rice_primary_53 burning arm; cluster repeated years/outcomes and shared NPK control"
    elif study_id == "panneerselvam_cuttack_2021_2022":
        decision = "ADMIT_MATCHED_RESIDUE_RETENTION_WITHIN_MICROBIAL_STRATUM"
        dependence = "One split-plot field trial; cluster 2021/2022 seasons and microbial strata by study_id"
    elif study_id == "huang_shangzhuang_2006_2013":
        decision = "ADMIT_FIXED_N_STRAW_RETURN_VS_REMOVAL"
        dependence = "One field trial established 2006; cluster 2010-2013 seasons, crops, N strata and outcomes by study_id"
    elif study_id == "sharma_ludhiana_2011_2018":
        decision = "ADMIT_MATCHED_TILLAGE_AND_GREEN_MANURE_STRAW_RETENTION"
        dependence = "One 2011-established split-plot trial; cluster seven-year pooled rice/wheat outcomes and green-manure strata by study_id"
    else:
        decision = "ADMIT_MATCHED_N_STRAW_INCORPORATION_VS_NO_STRAW"
        dependence = "One 2016-established split-plot trial; cluster 2021/2022 years, N strata and yield/SOC/GWP/GHGI outcomes by study_id"
    result.update({
        "treatment_mean": compact(treatment_mean),
        "control_mean": compact(control_mean),
        "treatment_sd": compact(treatment_sd),
        "control_sd": compact(control_sd),
        "treatment_n": compact(treatment_n),
        "control_n": compact(control_n),
        "lnrr": compact(lnrr),
        "variance_lnrr": compact(variance),
        "percent_change": compact(math.expm1(lnrr) * 100),
        "variance_provenance": provenance,
        "analysis_tier": tier,
        "source_analysis_tier": "primary_direct_transcription",
        "formal_decision": decision,
        "variance_origin_status": "documented_or_reconstructed",
        "independence_resolution": dependence,
        "extraction_method": "numeric table transcription",
    })
    if max(treatment_se / treatment_mean, control_se / control_mean) > 0.5:
        result["quality_flags"] = "large_relative_se_lnrr_delta_approx"
    if study_id == "sharma_ludhiana_2011_2018":
        result["variance_provenance"] = "primary Tables 2-3 pooled seven-year mean +/- SE; three field replicates; pooled SE denominator unspecified"
        result["quality_flags"] = ";".join(filter(None, [result["quality_flags"], "pooled_se_denominator_ambiguous"]))
        result["sensitivity_note"] = "Exclude this study in sensitivity analysis because treatment-by-year interaction was reported and pooled-SE denominator is not explicit"
    if study_id == "du_dingxi_2016_2022":
        result["quality_flags"] = ";".join(filter(None, [result["quality_flags"], "source_coordinates_malformed"]))
        if value(row, "outcome") in {"GWP", "GHGI"}:
            result["sensitivity_note"] = "Soil CH4+N2O growing-season boundary only; source AR4 factors 25/298 require harmonization and do not include upstream or open-burning emissions"
    return result


def build_csv(source: Path) -> tuple[str, int, int]:
    with source.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError("Source table has no header")
        records = [project(row) for row in reader]
    for addendum in PRIMARY_ADDENDA:
        with addendum.open("r", encoding="utf-8-sig", newline="") as stream:
            records.extend(project_primary_addendum(row) for row in csv.DictReader(stream))
    original = {row["effect_id"]: row for row in records if row["study_id"] == "rice_primary_53" and row["pathway"] == "open_burning"}
    for row in records:
        if row["study_id"] != "rice_primary_53" or row["pathway"] != "direct_return":
            continue
        burning_id = row["effect_id"].replace("_direct_", "_")
        peer = original.get(burning_id)
        if not peer or any(row[key] != peer[key] for key in (
            "study_id", "paper_doi", "outcome", "experiment_year", "control_mean",
            "control_sd", "control_n", "shared_control_group",
        )):
            raise ValueError(f"Primary addendum does not match shared NPK control: {row['effect_id']}")
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
