"""Link published national crop-residue estimates to 2020 crop geography.

OMD national 2020 residue production is spatially allocated in proportion to
MapSPAM 2020 production for the same country and crop. This is a modelled
redistribution, not an observed grid-cell residue measurement. No management
pathway or burning amount is inferred from this allocation.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OMD = ROOT / "data/external/omd2025_crop_residues/Crop residues.csv"
FAO = ROOT / "data/enrichment/outputs/faostat_qcl_rice_maize_wheat_2001_2020.csv"
MAP = ROOT / "data/enrichment/outputs/mapspam2020_crop_system_koppen_0p5deg.csv.gz"
COUNTRIES = ROOT / "data/enrichment/outputs/mapspam2020_grid_country_assignment.csv"
CALENDAR = ROOT / "data/enrichment/outputs/mapspam_ggcmi_season_windows_0p5deg.csv.gz"
RASTERS = ROOT / "data/enrichment/raw/mapspam2020_v2r2"
OUT = ROOT / "data/processed/omd2025_residue_geography"

CROPS = {"Maize": "maiz", "Rice, paddy": "rice", "Wheat": "whea"}
TECH = ("irrigated", "rainfed")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def allocate_national_mass(frame: pd.DataFrame) -> pd.DataFrame:
    """Conserve observed national OMD tonnes within mapped country-crop groups."""
    out = frame.copy()
    keys = ["country_m49", "crop_code"]
    out["mapspam_country_crop_production_t"] = out.groupby(keys, dropna=False)[
        "mapspam_production_t"
    ].transform("sum")
    denominator = out["mapspam_country_crop_production_t"].to_numpy(dtype=float)
    numerator = out["mapspam_production_t"].to_numpy(dtype=float)
    weight = np.divide(numerator, denominator, out=np.zeros(len(out)), where=denominator > 0)
    out["within_country_crop_production_weight"] = weight
    out["residue_allocated_t"] = out["omd_residue_production_t"] * weight
    return out


def load_omd() -> pd.DataFrame:
    raw = pd.read_csv(OMD)
    raw = raw[raw["Item"].isin(CROPS)].copy()
    assert not raw.duplicated(["Area Code", "Item", "Year"]).any()
    bridge = pd.read_csv(FAO, usecols=["Area Code", "Area Code (M49)"]).drop_duplicates()
    assert not bridge["Area Code"].duplicated().any()
    bridge["country_m49"] = pd.to_numeric(
        bridge["Area Code (M49)"].astype(str).str.replace("'", "", regex=False),
        errors="coerce",
    ).astype("Int64")
    raw = raw.merge(bridge[["Area Code", "country_m49"]], on="Area Code", how="left", validate="many_to_one")
    if raw["country_m49"].isna().any():
        raise ValueError("OMD country codes failed to map to FAOSTAT M49 bridge")
    return raw.rename(columns={
        "Area": "country_name_omd",
        "Area Code": "country_code_fao",
        "Continent_Group_En": "continent_omd",
        "GeoRegion_Group_En": "subregion_omd",
        "Area.1": "omd_harvested_area_ha",
        "Production (tonnes)": "omd_grain_production_t",
        "Grain Yield (tonnes/ha)": "omd_grain_yield_t_ha",
        "Residue yield (tonnes/ha)": "omd_residue_yield_t_ha",
        "Resid production (tonnes/year)": "omd_residue_production_t",
    }).assign(crop_code=lambda x: x["Item"].map(CROPS))


def load_mapspam() -> tuple[pd.DataFrame, list[dict]]:
    sys.path.insert(0, str(ROOT))
    from data.enrichment.process_mapspam2020 import aggregate_band

    usecols = [
        "grid_id", "longitude", "latitude", "crop_code", "crop_name", "technology",
        "harvested_area_ha", "koppen_class", "koppen_major_group", "koppen_major_name",
    ]
    grid = pd.read_csv(MAP, usecols=usecols)
    country = pd.read_csv(COUNTRIES, usecols=["grid_id", "country_m49", "iso3", "continent", "subregion"])
    grid = grid.merge(country, on="grid_id", how="left", validate="many_to_one")
    grid["country_m49"] = pd.to_numeric(grid["country_m49"], errors="coerce").astype("Int64")
    row = grid["grid_id"].str.slice(1, 4).astype(int).to_numpy()
    col = grid["grid_id"].str.slice(5, 8).astype(int).to_numpy()
    grid["mapspam_production_t"] = 0.0
    raster_checks = []
    for technology in TECH:
        raster = RASTERS / f"spam2020-production-{technology}.tif"
        for crop in CROPS.values():
            matrix, check = aggregate_band(raster, crop)
            mask = grid["crop_code"].eq(crop) & grid["technology"].eq(technology)
            grid.loc[mask, "mapspam_production_t"] = matrix[row[mask], col[mask]]
            check.update({"technology": technology, "crop_code": crop})
            check["production_in_base_grid_t"] = float(grid.loc[mask, "mapspam_production_t"].sum())
            raster_checks.append(check)
    if (grid["mapspam_production_t"] < 0).any():
        raise ValueError("Negative MapSPAM production after invalid-value screening")
    return grid, raster_checks


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    omd = load_omd()
    annual = (omd.groupby(["Year", "crop_code", "Item"], as_index=False)
              .agg(residue_production_t=("omd_residue_production_t", "sum"),
                   grain_production_t=("omd_grain_production_t", "sum"),
                   harvested_area_ha=("omd_harvested_area_ha", "sum"),
                   countries=("country_code_fao", "nunique")))
    annual.to_csv(OUT / "global_crop_residue_2015_2020.csv", index=False)

    national = omd[omd.Year.eq(2020)].copy()
    national["omd_residue_production_t"] = pd.to_numeric(national["omd_residue_production_t"], errors="raise")
    national["country_m49"] = national["country_m49"].astype("Int64")
    country_cols = [
        "country_m49", "crop_code", "country_name_omd", "continent_omd", "subregion_omd",
        "omd_residue_production_t", "omd_grain_production_t", "omd_harvested_area_ha",
    ]
    grid, raster_checks = load_mapspam()
    linked = grid.merge(national[country_cols], on=["country_m49", "crop_code"], how="left", validate="many_to_one")
    linked = allocate_national_mass(linked)
    linked["allocation_status"] = np.select(
        [linked.country_m49.isna(), linked.omd_residue_production_t.isna(),
         linked.mapspam_country_crop_production_t.le(0)],
        ["country_unassigned", "no_omd_country_crop", "no_mapspam_production"],
        default="allocated_from_national_omd",
    )

    mapped = linked[linked.allocation_status.eq("allocated_from_national_omd")].copy()
    closure = (mapped.groupby(["country_m49", "crop_code"], as_index=False)
               .agg(source_t=("omd_residue_production_t", "first"),
                    allocated_t=("residue_allocated_t", "sum"),
                    grid_rows=("grid_id", "size")))
    closure["relative_error"] = (closure.allocated_t - closure.source_t).abs() / closure.source_t.clip(lower=1)
    if closure.relative_error.max() > 1e-8:
        raise AssertionError("National residue mass balance failed")
    closure.to_csv(OUT / "country_crop_allocation_audit.csv", index=False)

    continent = (mapped.groupby(["continent_omd", "crop_code"], as_index=False)
                 .agg(residue_allocated_t=("residue_allocated_t", "sum"),
                      country_crop_groups=("country_m49", "nunique")))
    continent.to_csv(OUT / "crop_continent_residue_2020.csv", index=False)
    climate = (mapped.groupby(["crop_code", "koppen_major_group"], dropna=False, as_index=False)
               .agg(residue_allocated_t=("residue_allocated_t", "sum"),
                    crop_harvested_area_ha=("harvested_area_ha", "sum"),
                    grid_crop_system_rows=("grid_id", "size")))
    climate.to_csv(OUT / "crop_climate_residue_2020.csv", index=False)

    # GGCMI rice/wheat calendars are alternatives or unallocated seasons. Only
    # maize has a unique calendar per crop-system row and can carry mass.
    maize = mapped[mapped.crop_code.eq("maiz")].copy()
    cal = pd.read_csv(CALENDAR, usecols=[
        "grid_id", "crop_code", "technology", "calendar_id", "area_allocation_status", "maturity_day",
    ])
    cal = cal[(cal.crop_code.eq("maiz")) & (cal.area_allocation_status.eq("single_calendar"))]
    maize = maize.merge(cal, on=["grid_id", "crop_code", "technology"], how="left", validate="one_to_one")
    date = pd.Timestamp("2020-01-01") + pd.to_timedelta(maize.maturity_day - 1, unit="D")
    maize["maturity_quarter"] = date.dt.quarter
    season = (maize.groupby(["continent_omd", "maturity_quarter"], dropna=False, as_index=False)
              .agg(residue_allocated_t=("residue_allocated_t", "sum"),
                   crop_harvested_area_ha=("harvested_area_ha", "sum")))
    season.to_csv(OUT / "maize_residue_maturity_quarter_2020.csv", index=False)

    with gzip.open(OUT / "crop_grid_residue_2020.csv.gz", "wt", encoding="utf-8", newline="") as handle:
        linked.to_csv(handle, index=False, float_format="%.8g")
    pd.DataFrame(raster_checks).to_csv(OUT / "mapspam_production_raster_audit.csv", index=False)
    full_total = float(national.omd_residue_production_t.sum())
    mapped_total = float(closure.source_t.sum())
    manifest = {
        "omd_source_doi": "10.5281/zenodo.10450921",
        "omd_paper_doi": "10.5194/essd-17-369-2025",
        "mapspam_doi": "10.7910/DVN/SWPENT",
        "omd_source_sha256": digest(OMD),
        "omd_crop_country_year_rows": int(len(omd)),
        "omd_2020_country_crop_rows": int(len(national)),
        "omd_2020_residue_t": full_total,
        "allocated_country_crop_groups": int(len(closure)),
        "allocated_omd_residue_t": mapped_total,
        "allocated_share_of_omd_residue": mapped_total / full_total,
        "grid_crop_system_rows": int(len(linked)),
        "allocated_grid_crop_system_rows": int(len(mapped)),
        "max_national_mass_balance_error": float(closure.relative_error.max()),
        "mapspam_production_rasters": [
            {"file": p.name, "sha256": digest(p)}
            for p in (RASTERS / f"spam2020-production-{tech}.tif" for tech in TECH)
        ],
        "method": "Allocate OMD 2020 national crop residue dry tonnes over 0.5-degree crop-system cells in proportion to MapSPAM 2020 crop production within each country.",
        "limitations": [
            "Grid tonnes are modelled downscaling, not independent observations or measured crop-residue management.",
            "OMD residue production is theoretical above-ground dry matter, not collectable or burned tonnes.",
            "OMD and MapSPAM may differ in country definitions and source-statistics vintages; national OMD totals are conserved only for mapped groups.",
            "The irrigation split is inherited from MapSPAM production, not separately measured by OMD.",
            "Only maize has a single allocated GGCMI calendar; no rice/wheat residue tonnage is assigned to alternative seasons.",
        ],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ["omd_crop_country_year_rows", "omd_2020_country_crop_rows", "allocated_share_of_omd_residue", "grid_crop_system_rows", "max_national_mass_balance_error"]}, indent=2))


if __name__ == "__main__":
    build()
