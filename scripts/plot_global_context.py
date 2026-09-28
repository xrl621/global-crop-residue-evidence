"""Plot audited global crop context; no trial-effect surfaces are inferred.

The multi-panel chart is assembled and alignment-audited before the individual
panels are cropped without changing data, positions or font sizes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/global_context_20260928"
OUT = ROOT / "figures/global_context_20260928"
CLIMATE_GRID = ROOT / "data/enrichment/outputs/mapspam2020_crop_system_koppen_0p5deg.csv.gz"
STRICT = ROOT / "data/processed/stage_20260928/screened_effects.csv"
WORLD = ROOT / "data/ne_110m/ne_110m_admin_0_countries.shp"
CROP_COLORS = {"Rice": "#e16db7", "Maize": "#5394c3", "Wheat": "#908ebc"}


def save(fig, name: str, out: Path) -> None:
    fig.savefig(out / f"{name}.pdf")
    fig.savefig(out / f"{name}.svg")
    fig.savefig(out / f"{name}.png", dpi=600)
    fig.savefig(out / f"{name}.tiff", dpi=600)


def crop_panels(fig, axes, name: str, out: Path) -> None:
    width, height = fig.get_size_inches()
    split = (axes[0].get_position().x1 + axes[1].get_position().x0) / 2
    for i, (side, lo, hi) in enumerate([("left", 0, split), ("right", split, 1)]):
        box = Bbox.from_extents(lo * width, 0, hi * width, height)
        for j, ax in enumerate(axes):
            ax.set_visible(i == j)
        fig.savefig(out / f"{name}_{side}.pdf", bbox_inches=box, pad_inches=0)
        fig.savefig(out / f"{name}_{side}.svg", bbox_inches=box, pad_inches=0)
        fig.savefig(out / f"{name}_{side}.png", dpi=600, bbox_inches=box, pad_inches=0)
    for ax in axes:
        ax.set_visible(True)


def plot_map(out: Path) -> None:
    grid = pd.read_csv(CLIMATE_GRID, usecols=["grid_id", "longitude", "latitude",
                                              "crop_name", "harvested_area_ha"])
    area = (grid.groupby(["grid_id", "longitude", "latitude", "crop_name"], as_index=False)
            .harvested_area_ha.sum())
    wide = area.pivot_table(index=["grid_id", "longitude", "latitude"], columns="crop_name",
                            values="harvested_area_ha", fill_value=0).reset_index()
    wide.columns.name = None
    wide["dominant_crop"] = wide[list(CROP_COLORS)].idxmax(axis=1)
    wide["three_crop_area_ha"] = wide[list(CROP_COLORS)].sum(axis=1)
    assert len(wide) == grid.grid_id.nunique()
    fig, ax = plt.subplots(figsize=(7.2047244094, 3.7007874016))  # 183 × 94 mm
    fig.subplots_adjust(left=0.02, right=0.99, top=0.97, bottom=0.14)
    world = gpd.read_file(WORLD)
    world.boundary.plot(ax=ax, color="#d6d6d6", linewidth=0.25,
                        rasterized=True, zorder=1)
    for crop in ["Rice", "Maize", "Wheat"]:
        q = wide[wide.dominant_crop == crop]
        point_size = np.clip(np.sqrt(q.three_crop_area_ha.to_numpy()) / 35, 0.15, 6)
        ax.scatter(q.longitude, q.latitude, s=point_size, marker="s",
                   color=CROP_COLORS[crop], alpha=0.7, edgecolors="none",
                   rasterized=True, zorder=2)
    strict = pd.read_csv(STRICT)
    sites = strict[["study_id", "longitude", "latitude"]].drop_duplicates("study_id")
    n_studies = len(sites)
    sites = sites.dropna(subset=["longitude", "latitude"]).drop_duplicates(["longitude", "latitude"])
    (out / "site_coordinate_coverage.json").write_text(json.dumps({
        "strict_trial_keys": n_studies,
        "geocoded_unique_site_coordinates": len(sites),
        "omission_rule": "Only study keys with both coordinates can be plotted; all remain in the analysis tables.",
    }, indent=2), encoding="utf-8")
    ax.scatter(sites.longitude, sites.latitude, s=19, facecolors="none", edgecolors="#242424",
               linewidths=0.75, zorder=4)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 82)
    ax.set_aspect("auto")
    ax.axis("off")
    handles = [Line2D([], [], marker="s", linestyle="none", color=CROP_COLORS[c],
                      markersize=5, label=c) for c in CROP_COLORS]
    handles.append(Line2D([], [], marker="o", linestyle="none", markerfacecolor="white",
                          markeredgecolor="#242424", markersize=5, label="Geocoded trial site"))
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.012),
               ncol=4, fontsize=7, frameon=False)
    save(fig, "global_crop_footprint", out)
    plt.close(fig)


def plot_context(out: Path) -> None:
    from audit_panel_alignment import require_matplotlib_panel_alignment
    a = pd.read_csv(DATA / "crop_climate_system.csv")
    support = pd.read_csv(DATA / "trial_country_area_coverage.csv")
    fig, (left, right) = plt.subplots(1, 2, figsize=(7.2047244094, 3.8188976378))  # 183 × 97 mm
    fig.subplots_adjust(left=0.11, right=0.97, bottom=0.23, top=0.87, wspace=0.39)
    crops = ["Rice", "Maize", "Wheat"]
    climates = ["A", "B", "C", "D", "E"]
    matrix = (a.pivot(index="crop", columns="koppen_major_group", values="share_within_crop")
              .reindex(index=crops, columns=climates).fillna(0) * 100)
    cmap = LinearSegmentedColormap.from_list("rose", ["#ffffff", "#f4cee1", "#e16db7"])
    left.imshow(matrix.to_numpy(), cmap=cmap, vmin=0, vmax=50, aspect="auto")
    left.set_xticks(range(5), ["Tropical", "Arid", "Temperate", "Cold", "Polar"])
    left.set_yticks(range(3), crops)
    left.tick_params(length=0, pad=3)
    for y in range(3):
        for x in range(5):
            val = matrix.iloc[y, x]
            left.text(x, y, f"{val:.1f}", ha="center", va="center",
                      color="white" if val > 37 else "#333333", fontsize=7)
    left.set_xlabel("Share of each crop's harvested area (%)")
    for spine in left.spines.values():
        spine.set_visible(False)
    right.set_yticks(range(3), crops)
    right.set_ylim(2.5, -0.5)
    right.set_xlim(0, 100)
    right.set_xticks([0, 25, 50, 75, 100])
    right.grid(axis="x", color="#ededed", linewidth=0.55)
    right.set_axisbelow(True)
    for i, crop in enumerate(crops):
        share = 100 * support.loc[support.crop == crop, "country_with_trial_area_share"].iloc[0]
        right.barh(i, 100, height=0.49, color="#dedbee")
        right.barh(i, share, height=0.49, color=CROP_COLORS[crop])
        right.text(3, i, f"{share:.1f}%", va="center", ha="left",
                   color="#242424", fontsize=7)
    right.set_xlabel("Global area in countries with ≥1 crop trial (%)")
    right.spines[["top", "right", "left"]].set_visible(False)
    right.tick_params(axis="y", length=0)
    right.legend(handles=[Patch(color="#dedbee", label="No strict crop trial in country")],
                 loc="lower center", bbox_to_anchor=(0.5, 1.035), fontsize=6.5,
                 frameon=False, ncol=1)
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig, json_out=str(out / "global_climate_support.alignment.json"),
          tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
          require_panel_labels=False)
    save(fig, "global_climate_support", out)
    crop_panels(fig, [left, right], "global_climate_support", out)
    plt.close(fig)


def plot_season(out: Path) -> None:
    d = pd.read_csv(DATA / "maize_maturity_quarter.csv")
    fig, ax = plt.subplots(figsize=(3.5039370079, 3.0708661417))  # 89 × 78 mm
    fig.subplots_adjust(left=0.17, right=0.97, bottom=0.2, top=0.88)
    for hemisphere, color in [("Northern", "#5394c3"), ("Southern", "#e16db7")]:
        q = d[d.hemisphere == hemisphere].sort_values("quarter")
        ax.plot(q.quarter, q.share_within_hemisphere * 100, marker="o", lw=1.5,
                markersize=4, color=color, label=hemisphere)
    ax.set_xticks([1, 2, 3, 4], ["Jan–Mar", "Apr–Jun", "Jul–Sep", "Oct–Dec"])
    ax.set_xlim(0.85, 4.15)
    ax.set_ylim(0, 72)
    ax.set_yticks([0, 20, 40, 60])
    ax.set_ylabel("Share of maize harvested area (%)")
    ax.grid(axis="y", color="#eeeeee", linewidth=0.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=7, loc="upper right")
    save(fig, "maize_maturity_hemisphere", out)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa-scripts", type=Path)
    args = parser.parse_args()
    if args.qa_scripts:
        sys.path.insert(0, str(args.qa_scripts))
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
                         "font.size": 7.5, "axes.labelsize": 7.5, "xtick.labelsize": 6.5,
                         "ytick.labelsize": 7, "axes.linewidth": 0.6,
                         "pdf.fonttype": 42, "svg.fonttype": "none", "legend.frameon": False})
    OUT.mkdir(parents=True, exist_ok=True)
    plot_map(OUT)
    plot_context(OUT)
    plot_season(OUT)
    (OUT / "render_manifest.json").write_text(json.dumps({
        "input_manifest": "data/processed/global_context_20260928/manifest.json",
        "panel_letters": False, "titles": False,
        "split_method": "crop aligned final canvas; no rescaling or redraw",
        "maps": "dominant among three crops per 0.5-degree grid; symbols show only geocoded strict trial sites",
        "statistics": "descriptive gridded area and modelled calendar, no treatment-effect prediction",
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
