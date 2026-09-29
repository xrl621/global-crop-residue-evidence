"""Manuscript Fig. 1: theoretical 2020 three-crop residue geography.

The map is an OMD national estimate allocated with MapSPAM crop production.
It is not measured grid-cell residue, collectable biomass or burned residue.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/omd2025_residue_geography"
OMD_RAW = ROOT / "data/external/omd2025_crop_residues/Crop residues.csv"
WORLD = ROOT / "data/ne_110m/ne_110m_admin_0_countries.shp"
OUT = ROOT / "figures/manuscript_fig1_20260928"
PALETTE = ["#f4cee1", "#c5d9df", "#e16db7", "#908ebc", "#af88bb",
           "#dedbee", "#f07590", "#dfb9d5", "#b099b5", "#5394c3", "#b8a89f"]
CROPS = [("maiz", "Maize"), ("rice", "Rice"), ("whea", "Wheat")]
CONTINENTS = ["Asia", "Americas", "Europe", "Africa", "Oceania"]
CLIMATES = ["A", "B", "C", "D", "E"]
CLIMATE_LABELS = ["Tropical", "Arid", "Temperate", "Cold", "Polar"]
CROP_COLOR = {"maiz": PALETTE[9], "rice": PALETTE[2], "whea": PALETTE[3]}
OMD_DISPLAY = {
    "Maize": "Maize", "Wheat": "Wheat", "Rice, paddy": "Rice",
    "Soybeans": "Soybean", "Barley": "Barley",
    "Groundnuts, with shell": "Groundnut", "Sorghum": "Sorghum",
    "Potatoes": "Potato", "Millet": "Millet", "Beans, dry": "Dry beans",
    "Oats": "Oats", "Rye": "Rye",
}
OMD_FOCAL = {"Maize": "maiz", "Wheat": "whea", "Rice, paddy": "rice"}


def load():
    grid = pd.read_csv(SOURCE / "crop_grid_residue_2020.csv.gz",
                       usecols=["grid_id", "latitude", "longitude", "crop_code",
                                "residue_allocated_t", "allocation_status",
                                "continent_omd", "koppen_major_group"])
    continent = pd.read_csv(SOURCE / "crop_continent_residue_2020.csv")
    climate = pd.read_csv(SOURCE / "crop_climate_residue_2020.csv")
    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    if grid.crop_code.nunique() != 3 or len(grid) != manifest["grid_crop_system_rows"]:
        raise ValueError("Unexpected gridded crop coverage")
    missing = grid.residue_allocated_t.isna()
    if not grid.loc[missing, "allocation_status"].eq("no_omd_country_crop").all():
        raise ValueError("Missing mass outside the documented country-crop gap")
    if not grid.loc[~missing, "residue_allocated_t"].ge(0).all():
        raise ValueError("Negative allocated residue")
    total = grid.residue_allocated_t.sum()
    if not np.isclose(total, manifest["allocated_omd_residue_t"], rtol=1e-7):
        raise ValueError("Mapped residue differs from frozen mass balance")
    if not np.isclose(continent.residue_allocated_t.sum(), total, rtol=1e-7):
        raise ValueError("Continent summary differs from grid")
    if not np.isclose(climate.residue_allocated_t.sum(), total, rtol=1e-7):
        raise ValueError("Climate summary differs from grid")
    return grid, continent, climate, manifest


def grid_image(grid):
    cells = grid.groupby(["grid_id", "longitude", "latitude"], as_index=False).residue_allocated_t.sum()
    image = np.full((360, 720), np.nan)
    x = np.rint((cells.longitude.to_numpy() + 179.75) / .5).astype(int)
    y = np.rint((cells.latitude.to_numpy() + 89.75) / .5).astype(int)
    if (x < 0).any() or (x >= 720).any() or (y < 0).any() or (y >= 360).any():
        raise ValueError("Grid centres lie outside 0.5-degree global matrix")
    positive = cells.residue_allocated_t.to_numpy() > 0
    image[y[positive], x[positive]] = cells.residue_allocated_t.to_numpy()[positive]
    if not np.isclose(np.nansum(image), grid.residue_allocated_t.sum(), rtol=1e-7):
        raise ValueError("Map rasterization lost mass")
    return image, len(cells), int(positive.sum())


def crop_continent_climate(grid):
    """Return all 75 strata, conserving allocated mass without imputing gaps."""
    assigned = grid.loc[grid.residue_allocated_t.notna()].copy()
    outside = assigned.loc[~assigned.continent_omd.isin(CONTINENTS) |
                           ~assigned.koppen_major_group.isin(CLIMATES)]
    if not outside.empty and outside.residue_allocated_t.sum() > 0:
        raise ValueError("Positive allocated mass lacks continent or climate")
    grouped = assigned.groupby(["crop_code", "continent_omd", "koppen_major_group"],
                               observed=True).residue_allocated_t.sum()
    index = pd.MultiIndex.from_product(
        [[crop for crop, _ in CROPS], CONTINENTS, CLIMATES],
        names=["crop_code", "continent_omd", "koppen_major_group"])
    strata = grouped.reindex(index, fill_value=0).rename("residue_allocated_t").reset_index()
    if len(strata) != 75 or not np.isclose(strata.residue_allocated_t.sum(),
                                          grid.residue_allocated_t.sum(), rtol=1e-7):
        raise ValueError("Crop–continent–climate grouping lost mass")
    return strata


def all_crop_ranking(raw: pd.DataFrame, focal_total_t: float) -> pd.DataFrame:
    """Summarize all OMD 2020 categories; keep focal and non-focal scopes separate."""
    current = raw.loc[raw.Year.eq(2020), ["Item", "Resid production (tonnes/year)"]].copy()
    current["Resid production (tonnes/year)"] = pd.to_numeric(
        current["Resid production (tonnes/year)"], errors="raise")
    if set(current.Item) != set(OMD_DISPLAY):
        raise ValueError("OMD 2020 crop categories changed")
    if current.iloc[:, 1].lt(0).any():
        raise ValueError("Negative OMD residue mass")
    ranking = (current.groupby("Item", as_index=False)
               .agg(residue_production_t=("Resid production (tonnes/year)",
                                          lambda values: values.sum(min_count=1)),
                    source_rows=("Resid production (tonnes/year)", "size"),
                    numeric_source_rows=("Resid production (tonnes/year)", "count"))
               .sort_values("residue_production_t", ascending=False).reset_index(drop=True))
    if ranking.residue_production_t.isna().any():
        raise ValueError("A crop has no reported OMD residue mass")
    ranking["missing_source_rows"] = ranking.source_rows - ranking.numeric_source_rows
    ranking["display_crop"] = ranking.Item.map(OMD_DISPLAY)
    ranking["focal_crop_code"] = ranking.Item.map(OMD_FOCAL).fillna("")
    ranking["share_of_all_omd_crops_pct"] = 100 * ranking.residue_production_t / ranking.residue_production_t.sum()
    focal = ranking.loc[ranking.focal_crop_code.ne(""), "residue_production_t"].sum()
    if not np.isclose(focal, focal_total_t, rtol=1e-9):
        raise ValueError("Three-crop OMD total differs from the mapped source")
    return ranking


def plot(source: Path = SOURCE, out: Path = OUT, qa_scripts: Path | None = None):
    if qa_scripts:
        sys.path.insert(0, str(qa_scripts))
    from audit_panel_alignment import require_matplotlib_panel_alignment

    grid, continent, climate, manifest = load()
    image, cells, positive_cells = grid_image(grid)
    strata = crop_continent_climate(grid)
    if hashlib.sha256(OMD_RAW.read_bytes()).hexdigest() != manifest["omd_source_sha256"]:
        raise ValueError("OMD raw file differs from frozen geography input")
    ranking = all_crop_ranking(pd.read_csv(OMD_RAW), manifest["omd_2020_residue_t"])
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 7.2, "axes.labelsize": 7.3, "xtick.labelsize": 6.8,
        "ytick.labelsize": 7, "axes.linewidth": .65, "legend.frameon": False,
        "axes.spines.top": False, "axes.spines.right": False,
        "pdf.fonttype": 42, "svg.fonttype": "none",
    })
    width, height = 183 / 25.4, 173 / 25.4
    fig = plt.figure(figsize=(width, height))
    gs = fig.add_gridspec(2, 2, height_ratios=[.85, 1.25], left=.18,
                          right=.975, top=.97, bottom=.105, hspace=.38, wspace=.30)
    top = gs[0, :].subgridspec(1, 2, width_ratios=[1.65, 1], wspace=.38)
    map_ax = fig.add_subplot(top[0, 0])
    rank_ax = fig.add_subplot(top[0, 1])
    continent_ax = fig.add_subplot(gs[1, 0])
    climate_ax = fig.add_subplot(gs[1, 1])
    world = gpd.read_file(WORLD)
    cmap = LinearSegmentedColormap.from_list(
        "project_residue", ["#ffffff", PALETTE[0], PALETTE[4], PALETTE[3], PALETTE[9]], N=256)
    cmap.set_bad("#ffffff")
    cmap.set_under(PALETTE[0])
    norm = LogNorm(vmin=1, vmax=1_000_000)
    raster = map_ax.imshow(image, extent=(-180, 180, -90, 90), origin="lower",
                           interpolation="nearest", cmap=cmap, norm=norm,
                           rasterized=True, zorder=1)
    world.boundary.plot(ax=map_ax, color="#a5a5a5", linewidth=.24, zorder=2)
    map_ax.set_xlim(-180, 180)
    map_ax.set_ylim(-58, 82)
    map_ax.set_aspect("equal", adjustable="box")
    map_ax.axis("off")
    cbar = fig.colorbar(raster, ax=map_ax, orientation="horizontal",
                        fraction=.055, pad=.10, shrink=.78, anchor=(.5, 1))
    cbar.set_ticks([1, 1_000, 1_000_000])
    cbar.set_ticklabels(["1", "1,000", "1,000,000"])
    cbar.ax.minorticks_off()
    cbar.ax.tick_params(labelsize=6.2, length=0, pad=11)
    cbar.outline.set_visible(False)
    for spine in cbar.ax.spines.values():
        spine.set_visible(False)
    cbar.set_label("Three focal cereals: dry t per 0.5° cell", fontsize=6.4)

    rank_colors = [CROP_COLOR.get(code, PALETTE[1]) for code in ranking.focal_crop_code]
    rank_mass_gt = ranking.residue_production_t.to_numpy() / 1e9
    rank_y = np.arange(len(ranking))
    rank_ax.barh(rank_y, rank_mass_gt, height=.70, color=rank_colors, edgecolor="none")
    rank_ax.set_yticks(rank_y, ranking.display_crop)
    rank_ax.set_ylim(11.5, -.5)
    rank_ax.set_xlim(0, 1.52)
    rank_ax.set_xticks([0, .5, 1.0, 1.5])
    rank_ax.set_xlabel("OMD crop residues (Gt dry)")
    rank_ax.tick_params(axis="y", length=0, labelsize=6.1, pad=2)
    rank_ax.tick_params(axis="x", labelsize=6.1)
    for i, mass in enumerate(rank_mass_gt):
        rank_ax.text(mass + .025, i, f"{mass:.2f}", va="center", fontsize=6.1,
                     color="#333333")
    # Keep the correctly proportioned map and its colorbar as one compact group.
    fig.canvas.draw()
    map_box, rank_box, bar_box = (axis.get_position() for axis in
                                   (map_ax, rank_ax, cbar.ax))
    map_bottom = rank_box.y1 - .025 - map_box.height
    map_ax.set_aspect("auto")
    map_ax.set_position([map_box.x0, map_bottom,
                         map_box.width, map_box.height])
    cbar.ax.set_position([bar_box.x0, map_bottom - .014 - bar_box.height,
                          bar_box.width, bar_box.height])

    # Paired rows: where each crop's mass sits, then its within-region climate mix.
    regional = (strata.groupby(["crop_code", "continent_omd"], observed=True)
                .residue_allocated_t.sum())
    row_keys = [(crop, region) for crop, _ in CROPS for region in CONTINENTS]
    row_labels = [f"{name} · {region}" for crop, name in CROPS for region in CONTINENTS]
    region_share = np.array([100 * regional.loc[crop, region] /
                             regional.loc[crop].sum() for crop, region in row_keys])
    y = np.arange(len(row_keys))
    continent_ax.barh(y, region_share, height=.76,
                      color=[CROP_COLOR[crop] for crop, _ in row_keys],
                      edgecolor="none")
    for i, value in enumerate(region_share):
        if value >= 2:
            continent_ax.text(value + 1, i, f"{value:.0f}", va="center",
                              fontsize=6.1, color="#333333")
    continent_ax.set_yticks(y, row_labels)
    continent_ax.set_ylim(14.5, -.5)
    continent_ax.set_xlim(0, 102)
    continent_ax.set_xticks([0, 25, 50, 75, 100])
    continent_ax.set_xlabel("Share of each crop's global residue (%)")
    continent_ax.set_axisbelow(True)
    continent_ax.tick_params(axis="y", length=0)
    for cut in (4.5, 9.5):
        continent_ax.axhline(cut, color="#b5b1b9", linewidth=.65)

    # Each of 15 rows has its own denominator; the adjacent bar supplies its weight.
    matrix = np.array([[100 * strata.loc[
        strata.crop_code.eq(crop) & strata.continent_omd.eq(region) &
        strata.koppen_major_group.eq(climate_code), "residue_allocated_t"].sum() /
        regional.loc[crop, region] for climate_code in CLIMATES]
        for crop, region in row_keys])
    if not np.allclose(matrix.sum(axis=1), 100, atol=1e-7):
        raise ValueError("Climate shares do not sum to 100 within each row")
    heat = LinearSegmentedColormap.from_list("project_climate", ["#ffffff", PALETTE[0], PALETTE[2]])
    climate_ax.imshow(matrix, cmap=heat, vmin=0, vmax=100, aspect="auto")
    climate_ax.set_xticks(range(5), CLIMATE_LABELS, rotation=24, ha="right",
                          rotation_mode="anchor")
    climate_ax.set_yticks(y, [])
    climate_ax.tick_params(length=0, pad=3)
    climate_ax.set_xlabel("Climate share within crop–continent (%)")
    for row in range(15):
        for col in range(5):
            value = matrix[row, col]
            label = f"{value:.0f}" if value >= 1 else "·"
            climate_ax.text(col, row, label, ha="center", va="center",
                            fontsize=6.5, color="white" if value >= 58 else "#24242a")
    for cut in (4.5, 9.5):
        climate_ax.axhline(cut, color="#b5b1b9", linewidth=.65)
    for spine in climate_ax.spines.values():
        spine.set_visible(False)

    fig.canvas.draw()
    out.mkdir(parents=True, exist_ok=True)
    strata.to_csv(out / "crop_continent_climate_source.csv", index=False)
    ranking.to_csv(out / "omd_all_12_crop_residue_2020.csv", index=False)
    require_matplotlib_panel_alignment(
        fig, json_out=str(out / "fig1_resource.alignment.json"),
        exclude_axes=[cbar.ax], tolerance_pt=1.5, gutter_tolerance_pt=1.5,
        panel_ids={map_ax: "map", rank_ax: "ranking", continent_ax: "continent",
                   climate_ax: "climate"},
        row_groups=[["continent", "climate"]],
        require_panel_labels=False, strict=True)
    base = out / "fig1_resource"
    fig.savefig(base.with_suffix(".pdf"))
    fig.savefig(base.with_suffix(".svg"))
    fig.savefig(base.with_suffix(".png"), dpi=600)
    fig.savefig(base.with_suffix(".tiff"), dpi=600)
    # Crop the final canvas only; do not redraw panels or change their type size.
    fw, fh = fig.get_size_inches()
    renderer = fig.canvas.get_renderer()
    axes = [(map_ax, "resource_map"), (rank_ax, "crop_scope"),
            (continent_ax, "continent_mix"),
            (climate_ax, "climate_mix")]
    for index, (ax, name) in enumerate(axes):
        # Keep other axes invisible so that off-panel artists are not exported.
        for j, (panel, _) in enumerate(axes):
            panel.set_visible(j == index)
        cbar.ax.set_visible(index == 0)
        tight = [ax.get_tightbbox(renderer)]
        if index == 0:
            tight.append(cbar.ax.get_tightbbox(renderer))
        box = Bbox.union(tight).transformed(fig.dpi_scale_trans.inverted())
        pad = .07
        box = Bbox.from_extents(max(0, box.x0 - pad), max(0, box.y0 - pad),
                                min(fw, box.x1 + pad), min(fh, box.y1 + pad))
        fig.savefig(out / f"{name}.png", dpi=600, bbox_inches=box, pad_inches=0)
        fig.savefig(out / f"{name}.pdf", bbox_inches=box, pad_inches=0)
        fig.savefig(out / f"{name}.svg", bbox_inches=box, pad_inches=0)
    plt.close(fig)
    for svg in out.glob("*.svg"):
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
                       encoding="utf-8")
    (out / "render_manifest.json").write_text(json.dumps({
        "omd_input_sha256": manifest["omd_source_sha256"],
        "grid_source_sha256": hashlib.sha256((SOURCE / "crop_grid_residue_2020.csv.gz").read_bytes()).hexdigest(),
        "grid_cells": cells, "positive_grid_cells": positive_cells,
        "mapped_dry_t": float(grid.residue_allocated_t.sum()),
        "national_total_dry_t": manifest["omd_2020_residue_t"],
        "all_12_omd_crops_dry_t": float(ranking.residue_production_t.sum()),
        "all_12_omd_2020_source_rows": int(ranking.source_rows.sum()),
        "all_12_omd_2020_missing_mass_rows": int(ranking.missing_source_rows.sum()),
        "focal_3_share_of_all_12": float(ranking.loc[ranking.focal_crop_code.ne(""),
                                                "residue_production_t"].sum() /
                                       ranking.residue_production_t.sum()),
        "mapped_share": manifest["allocated_share_of_omd_residue"],
        "map": "Only three focal cereals: 0.5-degree national OMD allocation by MapSPAM production weights; no interpolation",
        "crop_ranking": "All 12 OMD crop-residue categories, national 2020 theoretical dry tonnes; includes non-straw residues",
        "crop_ranking_source": "omd_all_12_crop_residue_2020.csv",
        "bar_and_matrix": "15 crop-continent regional shares paired with 75 conditional climate shares",
        "strata_source": "crop_continent_climate_source.csv",
        "source_layer": "theoretical modeled resource, not collectable or burned residue",
        "split": "crop final assembled Python canvas to PNG, editable-text PDF and SVG without rescaling; no panel letters or figure title",
        "palette": PALETTE, "matplotlib": matplotlib.__version__,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa-scripts", type=Path)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    plot(out=args.out, qa_scripts=args.qa_scripts)
