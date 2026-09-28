"""Audit geographic support of Zeng et al. 2026 without admitting its rows.

Download data.xlsx from https://github.com/Zengjia1998/Yield-N2O-meta and
place it in data/external/zeng2026_yield_n2o_global/ (ignored by Git).
This script exports aggregate counts only, not third-party raw observations.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "data/external/zeng2026_yield_n2o_global/data.xlsx"
COUNTRIES = ROOT / "data/ne_110m/ne_110m_admin_0_countries.shp"
OUTPUT = ROOT / "data/processed/global_context_20260928"
MANAGEMENT = ["Straw return", "Biochar"]


def build_audit(output: Path = OUTPUT) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    data = pd.read_excel(WORKBOOK)
    assert len(data) == 6678
    sub = data[data["agricultural management"].isin(MANAGEMENT)].copy()
    assert sub[["Longitude", "Latitude"]].notna().all().all()
    countries = gpd.read_file(COUNTRIES)[["CONTINENT", "geometry"]]
    points = gpd.GeoDataFrame(sub, geometry=gpd.points_from_xy(sub.Longitude, sub.Latitude),
                              crs="EPSG:4326")
    joined = gpd.sjoin(points, countries, how="left", predicate="within")
    assert len(joined) == len(sub), "Coordinate matched more than one country polygon"
    joined["continent"] = joined.CONTINENT.fillna("unassigned")
    table = (joined.groupby(["agricultural management", "continent"], as_index=False)
             .agg(effect_rows=("Num", "size"), raw_study_labels=("Study_id", "nunique"),
                  raw_title_strings=("Title1", "nunique")))
    table["row_share_within_management"] = table.effect_rows / table.groupby(
        "agricultural management").effect_rows.transform("sum")
    table.to_csv(output / "zeng2026_secondary_geography_audit.csv", index=False)
    issues = {}
    for path, frame in joined.groupby("agricultural management"):
        key = frame.groupby("Study_id").agg(titles=("Title1", "nunique"),
                                             longitudes=("Longitude", "nunique"),
                                             latitudes=("Latitude", "nunique"))
        issues[path] = {
            "effect_rows": len(frame),
            "raw_study_labels_not_independent_trial_count": frame.Study_id.nunique(),
            "raw_keys_with_multiple_title_strings": int((key.titles > 1).sum()),
            "raw_keys_with_multiple_coordinates": int(((key.longitudes > 1) |
                                                          (key.latitudes > 1)).sum()),
            "unassigned_coordinate_rows": int(frame.CONTINENT.isna().sum()),
        }
    manifest = {
        "source": "Zeng et al. 2026, Resources Conservation and Recycling, DOI 10.1016/j.resconrec.2025.108703",
        "source_repository": "https://github.com/Zengjia1998/Yield-N2O-meta",
        "workbook_sha256": hashlib.sha256(WORKBOOK.read_bytes()).hexdigest(),
        "workbook_rows": len(data), "subset": issues,
        "decision": "Secondary geographic audit only. Do not append to reviewed 607-effect master: original comparator, overlapping papers, source identity and independent experimental units are not reconciled.",
        "license_note": "No repository license observed; do not redistribute the raw workbook in this project.",
    }
    (output / "zeng2026_secondary_audit_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(build_audit(), indent=2))
