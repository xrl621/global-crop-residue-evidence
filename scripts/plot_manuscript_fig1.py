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
from matplotlib.patches import Patch
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/omd2025_residue_geography"
WORLD = ROOT / "data/ne_110m/ne_110m_admin_0_countries.shp"
OUT = ROOT / "figures/manuscript_fig1_20260928"
PALETTE = ["#f4cee1", "#c5d9df", "#e16db7", "#908ebc", "#af88bb",
           "#dedbee", "#f07590", "#dfb9d5", "#b099b5", "#5394c3", "#b8a89f"]
CROPS = [("maiz", "Maize"), ("rice", "Rice"), ("whea", "Wheat")]
CONTINENTS = ["Asia", "Americas", "Europe", "Africa", "Oceania"]
CLIMATES = ["A", "B", "C", "D", "E"]
CLIMATE_LABELS = ["Tropical", "Arid", "Temperate", "Cold", "Polar"]
CONTINENT_COLOR = dict(zip(CONTINENTS, [
    PALETTE[3], PALETTE[9], PALETTE[2], PALETTE[10], PALETTE[5],
]))


def load():
    grid = pd.read_csv(SOURCE / "crop_grid_residue_2020.csv.gz",
                       usecols=["grid_id", "latitude", "longitude", "crop_code",
                                "residue_allocated_t", "allocation_status"])
    continent = pd.read_csv(SOURCE / "crop_continent_residue_2020.csv")
    climate = pd.read_csv(SOURCE / "crop_climate_residue_2020.csv")
    annual = pd.read_csv(SOURCE / "global_crop_residue_2015_2020.csv")
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
    return grid, continent, climate, annual, manifest


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


def plot(source: Path = SOURCE, out: Path = OUT, qa_scripts: Path | None = None):
    if qa_scripts:
        sys.path.insert(0, str(qa_scripts))
    from audit_panel_alignment import require_matplotlib_panel_alignment

    grid, continent, climate, annual, manifest = load()
    image, cells, positive_cells = grid_image(grid)
    crop_gt = (annual[annual.Year.eq(2020)].set_index("crop_code")
               .residue_production_t / 1e9)
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 7.2, "axes.labelsize": 7.3, "xtick.labelsize": 6.8,
        "ytick.labelsize": 7, "axes.linewidth": .65, "legend.frameon": False,
        "axes.spines.top": False, "axes.spines.right": False,
        "pdf.fonttype": 42, "svg.fonttype": "none",
    })
    width, height = 183 / 25.4, 133 / 25.4
    fig = plt.figure(figsize=(width, height))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.35, 1], left=.09,
                          right=.975, top=.95, bottom=.13, hspace=.55, wspace=.38)
    map_ax = fig.add_subplot(gs[0, :])
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
    map_ax.set_aspect("auto")
    map_ax.axis("off")
    cbar = fig.colorbar(raster, ax=map_ax, orientation="horizontal",
                        fraction=.046, pad=.07, shrink=.64, anchor=(.5, 1))
    cbar.set_ticks([1, 1_000, 1_000_000])
    cbar.set_ticklabels(["1", "1,000", "1,000,000"])
    cbar.ax.tick_params(labelsize=6.5, length=0, pad=16)
    cbar.outline.set_visible(False)
    for spine in cbar.ax.spines.values():
        spine.set_visible(False)
    cbar.set_label("Allocated theoretical residue per 0.5° cell (dry t)", fontsize=6.8)

    # Crop-level absolute mass and continent decomposition.
    for i, (crop, name) in enumerate(CROPS):
        sub = continent[continent.crop_code.eq(crop)].set_index("continent_omd")
        left = 0
        for region in CONTINENTS:
            mass = sub.loc[region, "residue_allocated_t"] / 1e9 if region in sub.index else 0
            continent_ax.barh(i, mass, left=left, height=.55,
                              color=CONTINENT_COLOR[region], edgecolor="none", linewidth=0)
            if mass >= .12:
                continent_ax.text(left + mass / 2, i, f"{mass:.2f}", ha="center", va="center",
                                  color="#22222a", fontsize=6.1)
            left += mass
        continent_ax.text(left + .023, i, f"{crop_gt[crop]:.2f}", va="center",
                          fontsize=6.8, color="#333333")
    continent_ax.set_yticks(range(3), [name for _, name in CROPS])
    continent_ax.set_ylim(2.5, -.5)
    continent_ax.set_xlim(0, 1.55)
    continent_ax.set_xticks([0, .5, 1.0, 1.5])
    continent_ax.set_xlabel("Theoretical residue (Gt dry)")
    continent_ax.set_axisbelow(True)
    continent_ax.tick_params(axis="y", length=0)
    continent_ax.legend(handles=[Patch(color=CONTINENT_COLOR[r], label=r)
                                 for r in CONTINENTS],
                        loc="lower left", bbox_to_anchor=(0, 1.04), ncol=3,
                        fontsize=6.25, handlelength=.9, columnspacing=.55,
                        handletextpad=.25, borderaxespad=0)

    # Climate shares are fractions of each crop's theoretical mass, not effect.
    matrix = (climate.pivot(index="crop_code", columns="koppen_major_group",
                            values="residue_allocated_t")
              .reindex(index=[code for code, _ in CROPS], columns=CLIMATES).fillna(0))
    matrix = 100 * matrix.div(matrix.sum(axis=1), axis=0)
    heat = LinearSegmentedColormap.from_list("project_climate", ["#ffffff", PALETTE[0], PALETTE[2]])
    climate_ax.imshow(matrix.to_numpy(), cmap=heat, vmin=0, vmax=50, aspect="auto")
    climate_ax.set_xticks(range(5), CLIMATE_LABELS, rotation=24, ha="right",
                          rotation_mode="anchor")
    climate_ax.set_yticks(range(3), [name for _, name in CROPS])
    climate_ax.tick_params(length=0, pad=3)
    climate_ax.set_xlabel("Share of crop's theoretical residue (%)")
    for row in range(3):
        for col in range(5):
            value = matrix.iloc[row, col]
            climate_ax.text(col, row, f"{value:.0f}", ha="center", va="center",
                            fontsize=7.1, color="white" if value >= 36 else "#24242a")
    for spine in climate_ax.spines.values():
        spine.set_visible(False)

    fig.canvas.draw()
    out.mkdir(parents=True, exist_ok=True)
    require_matplotlib_panel_alignment(
        fig, json_out=str(out / "fig1_resource.alignment.json"),
        exclude_axes=[cbar.ax], tolerance_pt=1.5, gutter_tolerance_pt=1.5,
        require_panel_labels=False, strict=True)
    base = out / "fig1_resource"
    fig.savefig(base.with_suffix(".pdf"))
    fig.savefig(base.with_suffix(".svg"))
    fig.savefig(base.with_suffix(".png"), dpi=600)
    fig.savefig(base.with_suffix(".tiff"), dpi=600)
    # Crop the final canvas only; do not redraw panels or change their type size.
    fw, fh = fig.get_size_inches()
    renderer = fig.canvas.get_renderer()
    axes = [(map_ax, "resource_map"), (continent_ax, "continent_mix"),
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
        "mapped_share": manifest["allocated_share_of_omd_residue"],
        "map": "0.5-degree crop allocation of national OMD residue by MapSPAM production weights; no interpolation",
        "bar_and_matrix": "crop/continent absolute dry mass and crop-conditional climate shares",
        "source_layer": "theoretical modeled resource, not collectable or burned residue",
        "split": "crop final assembled Python canvas without rescaling; no panel letters or figure title",
        "palette": PALETTE, "matplotlib": matplotlib.__version__,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa-scripts", type=Path)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    plot(out=args.out, qa_scripts=args.qa_scripts)
