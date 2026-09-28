"""Audit and summarize Smerald et al. cereal-residue management NetCDF.

All five mass layers are Mg/year and cover cereals collectively. The output is
never relabelled as maize/rice/wheat-specific management. National summaries
are approximate 0.5-degree grid-centre allocations for screening, not official
country inventories.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import h5py
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/external/smerald2023_residue_management/crop_residue_usage_mean.nc"
KOPPEN = ROOT / "data/enrichment/raw/koppen_geiger_v2/selected/koppen_geiger_0p5.tif"
COUNTRIES = (
    ROOT / "data/enrichment/raw/natural_earth_10m_v5_1_1"
    / "ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp"
)
OUT = ROOT / "data/processed/smerald2023_management"
KEYS = ["residue_production", "burnt_residues", "animal_usage", "other_usage", "left_on_field"]
USES = KEYS[1:]
EXPECTED_MD5 = "f860dd189990126277d5911024347877"


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize_mass(arrays: dict[str, np.ndarray]) -> dict[str, float]:
    production = arrays["residue_production"]
    finite = np.isfinite(production)
    if any(not np.array_equal(np.isfinite(arrays[key]), finite) for key in KEYS):
        raise ValueError("The five management layers have inconsistent valid-cell masks")
    if any(np.nanmin(arrays[key]) < -1e-8 for key in KEYS):
        raise ValueError("Negative residue mass found")
    difference = production[finite] - sum(arrays[key][finite] for key in USES)
    scale = max(float(np.nansum(production)), 1.0)
    if abs(float(difference.sum())) / scale > 1e-9:
        raise ValueError("Management pathways fail global mass closure")
    if np.any(np.abs(difference) > np.maximum(1e-5, np.abs(production[finite]) * 1e-9)):
        raise ValueError("Management pathways fail cell-level mass closure")
    return {key + "_Mg": float(np.nansum(arrays[key])) for key in KEYS}


def koppen_major_grid(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    local_deps = ROOT / "tmp/pydeps"
    if local_deps.exists():
        sys.path.insert(0, str(local_deps))
    import rasterio

    with rasterio.open(KOPPEN) as raster:
        if raster.shape != (len(lat), len(lon)) or not np.isclose(raster.transform.a, 0.5):
            raise ValueError("Koppen and residue grids differ in resolution/shape")
        if not (np.isclose(raster.transform.c, -180) and np.isclose(raster.transform.f, 90)):
            raise ValueError("Unexpected Koppen grid bounds")
        codes = raster.read(1)[::-1, :]
    if not (np.isclose(lat[0], -89.75) and np.isclose(lon[0], -179.75)):
        raise ValueError("Unexpected Smerald coordinate order")
    major = np.full(codes.shape, "Unknown", dtype="U7")
    for letter, low, high in [("A", 1, 3), ("B", 4, 7), ("C", 8, 16), ("D", 17, 28), ("E", 29, 30)]:
        major[(codes >= low) & (codes <= high)] = letter
    return major


def assign_country(active: pd.DataFrame) -> pd.DataFrame:
    polygons = gpd.read_file(COUNTRIES, columns=["ADMIN", "CONTINENT", "ISO_A3_EH"])
    points = gpd.GeoDataFrame(
        active.copy(),
        geometry=gpd.points_from_xy(active.longitude, active.latitude),
        crs="EPSG:4326",
    )
    matched = gpd.sjoin(points, polygons, how="left", predicate="within")
    matched = matched.sort_values(["grid_row", "grid_col", "ADMIN"], na_position="last")
    matched = matched.drop_duplicates(["grid_row", "grid_col"])
    matched["assignment_method"] = np.where(matched.ADMIN.notna(), "centre_within", "unassigned")
    missing = matched[matched.ADMIN.isna()].drop(columns=["index_right", "ADMIN", "CONTINENT", "ISO_A3_EH", "assignment_method"])
    if not missing.empty:
        nearest = gpd.sjoin_nearest(
            missing.to_crs(6933), polygons.to_crs(6933), how="left",
            max_distance=150_000, distance_col="distance_m",
        )
        nearest = nearest.sort_values(["grid_row", "grid_col", "distance_m", "ADMIN"], na_position="last")
        nearest = nearest.drop_duplicates(["grid_row", "grid_col"])
        lookup = nearest.set_index(["grid_row", "grid_col"])
        mask = matched.ADMIN.isna()
        idx = pd.MultiIndex.from_frame(matched.loc[mask, ["grid_row", "grid_col"]])
        for field in ["ADMIN", "CONTINENT", "ISO_A3_EH"]:
            matched.loc[mask, field] = lookup[field].reindex(idx).to_numpy()
        matched.loc[mask & matched.ADMIN.notna(), "assignment_method"] = "nearest_within_150km"
    return pd.DataFrame(matched.drop(columns=["geometry", "index_right"]))


def main() -> None:
    if md5(SOURCE) != EXPECTED_MD5:
        raise ValueError("Smerald source MD5 does not match RADAR published file")
    OUT.mkdir(parents=True, exist_ok=True)
    with h5py.File(SOURCE, "r") as source:
        years = source["time"][:].astype(int)
        lat, lon = source["lat"][:], source["lon"][:]
        if not np.array_equal(years, np.arange(1997, 2022)):
            raise ValueError("Unexpected source years")
        annual = []
        for index, year in enumerate(years):
            masses = {key: source[key][index] for key in KEYS}
            annual.append({"year": int(year), **summarize_mass(masses)})
        annual_frame = pd.DataFrame(annual)
        for usage in USES:
            annual_frame[usage + "_share"] = annual_frame[usage + "_Mg"] / annual_frame["residue_production_Mg"]
        annual_frame.to_csv(OUT / "annual_global_management.csv", index=False)

        index = int(np.flatnonzero(years == 2020)[0])
        masses = {key: source[key][index] for key in KEYS}
        major = koppen_major_grid(lat, lon)
        climate = []
        for letter in ["A", "B", "C", "D", "E", "Unknown"]:
            mask = major == letter
            row = {key + "_Mg": float(np.nansum(masses[key][mask])) for key in KEYS}
            if row["residue_production_Mg"] <= 0:
                continue
            climate.append({"koppen_major_group": letter, **row})
        climate_frame = pd.DataFrame(climate)
        for usage in USES:
            climate_frame[usage + "_share"] = climate_frame[usage + "_Mg"] / climate_frame["residue_production_Mg"]
        climate_frame.to_csv(OUT / "climate_2020_management.csv", index=False)

        active_mask = np.isfinite(masses["residue_production"]) & (masses["residue_production"] > 0)
        row, col = np.nonzero(active_mask)
        active = pd.DataFrame({
            "grid_row": row, "grid_col": col, "latitude": lat[row], "longitude": lon[col],
            "koppen_major_group": major[active_mask],
            **{key + "_Mg": masses[key][active_mask] for key in KEYS},
        })
        assigned = assign_country(active)
        if len(assigned) != len(active):
            raise ValueError("Country assignment changed active grid count")
        assigned.to_csv(OUT / "active_grid_2020.csv.gz", index=False, compression="gzip")
        country = assigned.dropna(subset=["ADMIN"]).groupby(
            ["ADMIN", "CONTINENT", "ISO_A3_EH"], as_index=False
        )[[key + "_Mg" for key in KEYS]].sum()
        country = country.rename(columns={"ADMIN": "country", "CONTINENT": "continent", "ISO_A3_EH": "iso3"})
        country["burnt_share"] = country.burnt_residues_Mg / country.residue_production_Mg
        country.sort_values("burnt_residues_Mg", ascending=False).to_csv(
            OUT / "country_2020_management.csv", index=False
        )
        continent = country.groupby("continent", as_index=False)[[key + "_Mg" for key in KEYS]].sum()
        continent["burnt_share"] = continent.burnt_residues_Mg / continent.residue_production_Mg
        continent.sort_values("burnt_residues_Mg", ascending=False).to_csv(
            OUT / "continent_2020_management.csv", index=False
        )

        global2020 = annual_frame.loc[annual_frame.year == 2020].iloc[0]
        audit = {
            "dataset_doi": "10.35097/989",
            "paper_doi": "10.1038/s41597-023-02587-0",
            "source_file_md5": EXPECTED_MD5,
            "source_file_bytes": SOURCE.stat().st_size,
            "units": "Mg/year, equal to metric tonnes/year",
            "scope": "all cereals combined, not crop-specific",
            "year_range": [int(years.min()), int(years.max())],
            "active_cells_2020": int(active_mask.sum()),
            "assigned_cells_2020": int(assigned.ADMIN.notna().sum()),
            "assigned_production_fraction_2020": float(country.residue_production_Mg.sum() / global2020.residue_production_Mg),
            "assigned_burnt_fraction_2020": float(country.burnt_residues_Mg.sum() / global2020.burnt_residues_Mg),
            "unassigned_cells_2020": int(assigned.ADMIN.isna().sum()),
            "country_assignment_methods": assigned.assignment_method.value_counts(dropna=False).to_dict(),
            "source_license_conflict": "RADAR landing page says CC BY 4.0; embedded NetCDF global attribute says CC BY-SA 4.0. Preserve both and seek clarification before redistributing raw file.",
            "limitations": [
                "Management quantities are modelled, not direct observed burn/return amounts.",
                "The default mean dataset combines input-source assumptions; 18 alternatives are not yet analysed.",
                "Leaving residues on field is not equivalent to deliberate incorporation or measured SOC gain.",
                "Country assignment uses Natural Earth polygons and a 150 km coastal nearest fallback.",
                "The 2020 Köppen stratum is a 1991-2020 climatology, not 2020 weather.",
            ],
        }
        (OUT / "manifest.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
