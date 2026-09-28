"""Compare crop-residue geography with return-vs-removal literature geography.

These are different denominators: OMD modelled 2020 dry-matter tonnes versus
unique source titles in the Encarnation yield+SOC subset. The comparison is a
descriptive geography of research attention, not a policy effect or sampling
weight for treatment-effect extrapolation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = ROOT / "data/processed/omd2025_residue_geography/crop_continent_residue_2020.csv"
EVIDENCE = ROOT / "data/processed/encarnation2026_residue_reanalysis/selected_comparisons.csv"
OUT = ROOT / "data/processed/omd2025_residue_geography"
CROPS = {"maiz": "Maize", "rice": "Rice", "whea": "Wheat"}
REGIONS = {
    "Africa": "Africa", "Asia": "Asia", "Europe": "Europe",
    "North America": "Americas", "Latin America": "Americas", "Oceania": "Oceania",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def calculate(resource: pd.DataFrame, evidence: pd.DataFrame) -> pd.DataFrame:
    resource = resource.copy()
    resource["crop"] = resource.crop_code.map(CROPS)
    resource = resource.rename(columns={"continent_omd": "continent"})
    resource = resource.groupby(["crop", "continent"], as_index=False).agg(
        residue_t=("residue_allocated_t", "sum")
    )
    resource["residue_share"] = resource.residue_t / resource.groupby("crop").residue_t.transform("sum")

    evidence = evidence[evidence.CRR_Comparison.str.startswith("Removed-")].copy()
    evidence = evidence[evidence.Main_Crop.isin(CROPS.values())]
    evidence["continent"] = evidence.Region.map(REGIONS)
    if evidence.continent.isna().any():
        raise ValueError("Unknown literature region; do not silently drop source papers")
    evidence = evidence.drop_duplicates(["Title", "Main_Crop", "continent"])
    papers = evidence.groupby(["Main_Crop", "continent"], as_index=False).agg(
        papers_by_title=("Title", "nunique")
    ).rename(columns={"Main_Crop": "crop"})
    papers["paper_share"] = papers.papers_by_title / papers.groupby("crop").papers_by_title.transform("sum")

    out = resource.merge(papers, on=["crop", "continent"], how="outer", validate="one_to_one")
    out[["residue_t", "residue_share", "papers_by_title", "paper_share"]] = out[[
        "residue_t", "residue_share", "papers_by_title", "paper_share"
    ]].fillna(0)
    out["paper_minus_residue_share_pp"] = 100 * (out.paper_share - out.residue_share)
    return out.sort_values(["crop", "continent"]).reset_index(drop=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = calculate(pd.read_csv(RESOURCE), pd.read_csv(EVIDENCE))
    frame.to_csv(OUT / "evidence_resource_geography_2020.csv", index=False, float_format="%.8g")
    assert (frame.groupby("crop").residue_share.sum() - 1).abs().max() < 1e-9
    assert (frame.groupby("crop").paper_share.sum() - 1).abs().max() < 1e-9
    manifest = {
        "resource_file_sha256": sha256(RESOURCE),
        "literature_file_sha256": sha256(EVIDENCE),
        "scope": "2020 OMD theoretical residue dry mass against unique titles reporting both yield and SOC for crop-residue return vs removal in Encarnation public data",
        "paper_identity": "Exact source Title, deduplicated within crop and continent",
        "region_mapping": REGIONS,
        "limitations": [
            "The resource and literature shares are different denominators, not comparable effect sizes.",
            "Source paper search/selection can bias geographic counts; this is not a formal bibliometric census.",
            "One paper can contribute to multiple crops; crop paper totals must not be summed as independent papers.",
            "OMD is modelled theoretical production; it is not burned, returned, or collectible residue.",
            "No treatment effect is extrapolated by these ratios.",
        ],
    }
    (OUT / "alignment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
