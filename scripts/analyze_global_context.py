"""Recompute global crop/climate/calendar context without extrapolating trial effects.

Inputs are the locally cached MapSPAM 2020 v2r2, Köppen–Geiger 1991–2020,
GGCMI Phase 3 v1.01, country assignment and the frozen strict evidence set.
The optional Zeng et al. 2026 workbook is audited separately: it is a
secondary comparison dataset, never appended to the reviewed master.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/enrichment/outputs"
OUTPUT = ROOT / "data/processed/global_context_20260928"
STRICT = ROOT / "data/processed/stage_20260928/screened_effects.csv"
CROP = {"maiz": "Maize", "rice": "Rice", "whea": "Wheat"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_context(output: Path = OUTPUT) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    climate_file = INPUT / "mapspam2020_crop_system_koppen_0p5deg.csv.gz"
    calendar_file = INPUT / "mapspam_ggcmi_season_windows_0p5deg.csv.gz"
    country_file = INPUT / "country_crop_spatial_policy_frame.csv"
    climate = pd.read_csv(climate_file)
    calendar = pd.read_csv(calendar_file)
    country = pd.read_csv(country_file)
    strict = pd.read_csv(STRICT)

    assert len(climate) == 85493
    assert set(climate.crop_code) == set(CROP)
    assert set(climate.technology) == {"irrigated", "rainfed"}
    assert climate.koppen_major_group.notna().all()
    global_area = climate.harvested_area_ha.sum()
    assert abs(global_area - country.harvested_area_ha_total.sum()) / global_area < 1e-6

    a = (climate.groupby(["crop_code", "koppen_major_group", "technology"],
                         as_index=False).harvested_area_ha.sum())
    a = a.pivot_table(index=["crop_code", "koppen_major_group"],
                      columns="technology", values="harvested_area_ha", fill_value=0).reset_index()
    a.columns.name = None
    a["crop"] = a.crop_code.map(CROP)
    a["total_ha"] = a.irrigated + a.rainfed
    a["share_within_crop"] = a.total_ha / a.groupby("crop_code").total_ha.transform("sum")
    a["irrigated_share"] = a.irrigated / a.total_ha
    a.rename(columns={"irrigated": "irrigated_ha", "rainfed": "rainfed_ha"}, inplace=True)
    a.to_csv(output / "crop_climate_system.csv", index=False)

    totals = (climate.groupby(["crop_code", "technology"], as_index=False)
              .harvested_area_ha.sum().pivot_table(index="crop_code", columns="technology",
               values="harvested_area_ha", fill_value=0).reset_index())
    totals.columns.name = None
    totals["crop"] = totals.crop_code.map(CROP)
    totals["total_ha"] = totals.irrigated + totals.rainfed
    totals["irrigated_share"] = totals.irrigated / totals.total_ha
    totals.rename(columns={"irrigated": "irrigated_ha", "rainfed": "rainfed_ha"}, inplace=True)
    totals.to_csv(output / "crop_area_totals.csv", index=False)

    continent = (country.groupby(["continent", "crop_code"], as_index=False)
                 .harvested_area_ha_total.sum())
    continent["crop"] = continent.crop_code.map(CROP)
    continent.to_csv(output / "continent_crop_area.csv", index=False)

    # A country having ≥1 crop-specific strict trial is only a coarse upper
    # bound on geographic support, not proof of support across that country.
    rows = []
    for code, name in CROP.items():
        crop_country = country[country.crop_code == code]
        studies = strict[strict.crop_display == name.lower()]
        eligible_countries = sorted(set(studies.country.dropna()))
        supported = crop_country[crop_country.country_name_ne.isin(eligible_countries)]
        area = crop_country.harvested_area_ha_total.sum()
        rows.append({
            "crop_code": code, "crop": name, "global_harvested_area_ha": area,
            "country_with_trial_area_ha": supported.harvested_area_ha_total.sum(),
            "country_with_trial_area_share": supported.harvested_area_ha_total.sum() / area,
            "outside_trial_country_area_share": 1 - supported.harvested_area_ha_total.sum() / area,
            "strict_trial_keys": studies.study_id.nunique(),
            "strict_trial_countries": "|".join(eligible_countries),
        })
    pd.DataFrame(rows).to_csv(output / "trial_country_area_coverage.csv", index=False)

    # Maize has one calendar per production system. Rice's two seasons and
    # wheat's spring/winter alternatives lack area allocation, so summing
    # those rows would double-count harvested area.
    maize = calendar[(calendar.calendar_id == "maize") &
                     (calendar.calendar_available == 1)].copy()
    assert maize.maturity_day.between(1, 365).all()
    maize["hemisphere"] = maize.latitude.ge(0).map({True: "Northern", False: "Southern"})
    maize["month"] = (pd.Timestamp("2021-01-01") +
                      pd.to_timedelta(maize.maturity_day.astype(int) - 1, unit="D")).dt.month
    maize["quarter"] = (maize.month - 1) // 3 + 1
    season = maize.groupby(["hemisphere", "quarter"], as_index=False).harvested_area_ha.sum()
    season["share_within_hemisphere"] = (season.harvested_area_ha /
                                          season.groupby("hemisphere").harvested_area_ha.transform("sum"))
    season.to_csv(output / "maize_maturity_quarter.csv", index=False)

    manifest = {
        "analysis": "global crop distribution, climate and maize calendar; no treatment-effect extrapolation",
        "grid_rows": len(climate), "global_three_crop_harvested_area_ha": global_area,
        "strict_effects": len(strict), "strict_trial_keys": strict.study_id.nunique(),
        "maize_calendar_coverage_fraction": maize.harvested_area_ha.sum() /
        totals.loc[totals.crop_code == "maiz", "total_ha"].iloc[0],
        "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in
                         [climate_file, calendar_file, country_file, STRICT]},
        "limitations": [
            "Harvested area is not residue mass, managed area, or independent physical land area.",
            "Country-with-trial coverage is an upper bound on site-level effect transportability.",
            "GGCMI maturity day is a static multi-year modelled calendar, not annual observed harvest.",
            "Rice dual seasons and wheat seasonal alternatives were not summed.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(build_context(), indent=2))
