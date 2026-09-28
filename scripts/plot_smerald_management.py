"""Three-role figure: global change, climate composition, and burning hotspots.

The figure is composed and aligned first; unnumbered PNG panels are cropped
from the same canvas for slide assembly. These are modelled cereal-aggregate
management quantities, not crop-specific effects or observed policy outcomes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/smerald2023_management"
NETCDF = ROOT / "data/external/smerald2023_residue_management/crop_residue_usage_mean.nc"
COUNTRIES = (
    ROOT / "data/enrichment/raw/natural_earth_110m_v5_1_1"
    / "ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp"
)
OUT = ROOT / "figures/smerald2023_management"
sys.path.insert(0, str(Path.home() / ".codex/plugins/cache/nature-skills/nature-skills/0.1.0/skills/nature-figure/scripts"))
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

BLUE = "#5394c3"
PINK = "#e16db7"
PURPLE = "#908ebc"
PALE = "#dedbee"
GREY = "#b8a89f"
INK = "#2b2a32"
PATHWAY_COLORS = [PINK, PURPLE, GREY, BLUE]
PATHWAY_KEYS = ["burnt_residues", "animal_usage", "other_usage", "left_on_field"]
PATHWAY_LABELS = ["Burnt", "Feed / bedding", "Other off-field", "Left on field"]


def configure_axis(ax: plt.Axes) -> None:
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#777777")
    ax.tick_params(axis="y", length=0, labelsize=8, pad=5)
    ax.tick_params(axis="x", labelsize=8, colors=INK, length=3)


def plot() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "Arial", "font.size": 8, "pdf.fonttype": 42,
        "svg.fonttype": "none", "axes.linewidth": 0.6, "savefig.facecolor": "white",
    })
    annual = pd.read_csv(DATA / "annual_global_management.csv")
    climate = pd.read_csv(DATA / "climate_2020_management.csv").set_index("koppen_major_group")
    climate = climate.loc[["A", "B", "C", "D", "E"]]
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 8.1),
                             gridspec_kw={"height_ratios": [1.1, 1.35, 1.65]})
    fig.subplots_adjust(left=0.145, right=0.97, bottom=0.115, top=0.954, hspace=0.53)

    # Change through time: production and burnt mass indexed to the same 1997 base.
    ax = axes[0]
    x = annual.year.to_numpy()
    p = annual.residue_production_Mg.to_numpy() / annual.residue_production_Mg.iloc[0] * 100
    b = annual.burnt_residues_Mg.to_numpy() / annual.burnt_residues_Mg.iloc[0] * 100
    ax.plot(x, p, color=BLUE, lw=2.1, label="Cereal residue production")
    ax.plot(x, b, color=PINK, lw=2.1, label="Field-burnt residue")
    ax.axhline(100, color="#c8c8c8", lw=0.7, ls="--", zorder=0)
    ax.set_xlim(1997, 2021)
    ax.set_ylim(75, 175)
    ax.set_xticks([1997, 2003, 2009, 2015, 2021])
    ax.set_yticks([100, 125, 150, 175])
    ax.grid(axis="y", lw=0.5, color="#e7e7e7")
    ax.set_ylabel("Index (1997 = 100)", fontsize=8.5)
    ax.set_title("Global change", loc="left", fontsize=9.5, fontweight="bold", pad=9)
    ax.legend(handles=[Patch(facecolor=BLUE, edgecolor="none", label="Cereal residue production"),
                       Patch(facecolor=PINK, edgecolor="none", label="Field-burnt residue")],
              frameon=False, ncol=2, loc="upper left", fontsize=7.7,
              bbox_to_anchor=(0.25, 1.25), handlelength=1.7, columnspacing=1.4)
    configure_axis(ax)

    # Pathway composition by climate: all fractions share the same denominator.
    ax = axes[1]
    y = np.arange(5)
    left = np.zeros(5)
    for key, label, color in zip(PATHWAY_KEYS, PATHWAY_LABELS, PATHWAY_COLORS):
        share = 100 * climate[key + "_share"].to_numpy()
        ax.barh(y, share, left=left, color=color, height=0.63, edgecolor="white",
                linewidth=0.45, label=label)
        left += share
    if not np.allclose(left, 100, atol=1e-6):
        raise ValueError("Climate pathway percentages do not sum to 100")
    ax.set_yticks(y, ["A  Tropical", "B  Arid", "C  Temperate", "D  Cold", "E  Polar"])
    ax.invert_yaxis()
    ax.set_xlim(0, 117)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.grid(axis="x", color="#e7e7e7", lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("Share of climate-zone residue production (%)", fontsize=8.5)
    ax.set_title("Management mix across climate zones, 2020", loc="left",
                 fontsize=9.5, fontweight="bold", pad=15)
    for yi, total in zip(y, climate.residue_production_Mg.to_numpy()):
        ax.text(102, yi, f"{total / 1e6:,.0f} Mt", va="center", ha="left", fontsize=7.5, color=INK)
    ax.legend(frameon=False, ncol=4, loc="upper right", bbox_to_anchor=(1, 1.20),
              fontsize=7.2, columnspacing=0.75, handlelength=1.15, handletextpad=0.3)
    configure_axis(ax)

    # Geographic concentration, expressed in absolute Mg per 0.5-degree cell.
    ax = axes[2]
    with h5py.File(NETCDF, "r") as source:
        years = source["time"][:]
        index = int(np.flatnonzero(years == 2020)[0])
        mass = source["burnt_residues"][index]
    classes = np.zeros(mass.shape, dtype="uint8")
    positive = np.isfinite(mass) & (mass > 0)
    classes[positive] = 1 + np.digitize(mass[positive], [1000, 5000, 20000, 100000])
    colors = ["#ffffff", "#f4cee1", "#dfb9d5", "#b099b5", PURPLE, BLUE]
    ax.imshow(classes, origin="lower", extent=(-180, 180, -90, 90),
              cmap=ListedColormap(colors), norm=BoundaryNorm(np.arange(-0.5, 6.5), 6),
              interpolation="nearest", aspect="auto", rasterized=True)
    world = gpd.read_file(COUNTRIES, columns=["geometry"])
    world.boundary.plot(ax=ax, color="#8e8b91", linewidth=0.28, zorder=2, rasterized=True)
    ax.set_aspect("auto")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)
    ax.set_xticks([-120, -60, 0, 60, 120], ["120°W", "60°W", "0°", "60°E", "120°E"])
    ax.set_yticks([-30, 0, 30, 60], ["30°S", "0°", "30°N", "60°N"])
    ax.set_title("Modelled field-burnt cereal residue, 2020", loc="left",
                 fontsize=9.5, fontweight="bold", pad=8)
    ax.spines[:].set_visible(False)
    ax.tick_params(length=0, labelsize=7.5, pad=3)

    legend_items = [Patch(facecolor=color, edgecolor="none", label=label)
                    for color, label in zip(colors[1:],
                        ["<1k", "1–5k", "5–20k", "20–100k", ">100k"])]
    fig.legend(handles=legend_items, loc="lower center", ncol=5, frameon=False,
               bbox_to_anchor=(0.56, 0.050), fontsize=7.5, columnspacing=1.7,
               handlelength=1.2)
    fig.text(0.145, 0.069, "Mg / 0.5° cell", fontsize=7.5, color=INK)
    fig.text(0.145, 0.019,
             "Smerald et al. default model · all cereals combined · 1997–2021 / 2020 · not observed crop-specific burning",
             fontsize=7.2, color="#555555", ha="left")

    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig, json_out=OUT / "alignment_audit.json",
                                       exclude_axes=[])
    fig.savefig(OUT / "cereal_management_context.pdf")
    fig.savefig(OUT / "cereal_management_context.svg")
    fig.savefig(OUT / "cereal_management_context.png", dpi=600)
    fig.savefig(OUT / "cereal_management_context.tiff", dpi=600)

    fig_w, fig_h = fig.get_size_inches()
    for ax, name in zip(axes, ["global_change", "climate_mix", "burning_map"]):
        p = ax.get_position()
        upper = 0.42
        lower = 0.45 if name != "burning_map" else 0.85
        bounds = Bbox.from_extents(0.08, p.y0 * fig_h - lower,
                                  fig_w - 0.06, p.y1 * fig_h + upper)
        fig.savefig(OUT / f"{name}.png", bbox_inches=bounds, dpi=600)
    plt.close(fig)


if __name__ == "__main__":
    plot()
