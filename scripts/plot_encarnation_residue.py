"""Plot source-grounded global residue-return patterns from paper-balanced data.

The crop/climate panels are aligned in one canvas, then exported separately
without panel letters or titles. These are secondary descriptive analyses.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd

plt.rcParams.update({"font.family": "Arial", "pdf.fonttype": 42, "svg.fonttype": "none"})

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/encarnation2026_residue_reanalysis"
OUT = ROOT / "figures/encarnation2026_residue_reanalysis"
sys.path.insert(0, str(Path.home() / ".codex/plugins/cache/nature-skills/nature-skills/0.1.0/skills/nature-figure/scripts"))
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402
PINK, BLUE, LAVENDER, GREY = "#e16db7", "#5394c3", "#908ebc", "#a1a1a1"


def save(fig, stem: str) -> None:
    fig.savefig(OUT / f"{stem}.pdf")
    fig.savefig(OUT / f"{stem}.svg")
    fig.savefig(OUT / f"{stem}.png", dpi=600)
    fig.savefig(OUT / f"{stem}.tiff", dpi=600)


def plot_joint() -> dict:
    d = pd.read_csv(DATA / "paper_medians_return_vs_removal.csv")
    x = 100 * np.expm1(d.yield_log_ratio.to_numpy())
    y = 100 * np.expm1(d.soc_log_ratio.to_numpy())
    limits = (-45, 80, -45, 80)
    inside = (x >= limits[0]) & (x <= limits[1]) & (y >= limits[2]) & (y <= limits[3])
    joint = (x > 0) & (y > 0)
    fig, ax = plt.subplots(figsize=(7.2047244094, 4.0))
    fig.subplots_adjust(left=0.13, right=0.73, bottom=0.16, top=0.96)
    ax.axvspan(0, limits[1], ymin=(0-limits[2])/(limits[3]-limits[2]),
               color=PINK, alpha=0.055, zorder=0)
    ax.axhline(0, color="#777777", lw=0.7, zorder=1)
    ax.axvline(0, color="#777777", lw=0.7, zorder=1)
    ax.scatter(x[inside & ~joint], y[inside & ~joint], s=25, c=GREY,
               alpha=0.8, edgecolors="white", linewidths=0.25, rasterized=True, zorder=2)
    ax.scatter(x[inside & joint], y[inside & joint], s=25, c=PINK,
               alpha=0.7, edgecolors="white", linewidths=0.25, rasterized=True, zorder=3)
    # Boundary triangles show all observations outside the display window.
    xx = np.clip(x[~inside], limits[0]+1, limits[1]-1)
    yy = np.clip(y[~inside], limits[2]+1, limits[3]-1)
    ax.scatter(xx, yy, marker="^", s=48, facecolors="none", edgecolors="#444444",
               linewidths=0.9, zorder=4)
    ax.set(xlim=limits[:2], ylim=limits[2:], xlabel="Yield change vs removal (%)",
           ylabel="Topsoil SOC stock change vs removal (%)")
    ax.set_xticks([-40, -20, 0, 20, 40, 60, 80])
    ax.set_yticks([-40, -20, 0, 20, 40, 60, 80])
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8)
    ax.xaxis.label.set_size(9)
    ax.yaxis.label.set_size(9)
    n_joint = int(joint.sum())
    fig.text(0.775, 0.82, f"{n_joint}/{len(d)}", fontsize=16,
             fontweight="bold", color=PINK, ha="left")
    fig.text(0.775, 0.755, "papers with both\noutcomes positive", fontsize=8,
             color="#333333", ha="left", va="top")
    fig.text(0.775, 0.56, f"{int((~inside).sum())} boundary markers", fontsize=7,
             color="#555555", ha="left")
    fig.text(0.775, 0.49, "one dot = one paper\n(median paired contrast)",
             fontsize=7, color="#555555", ha="left", va="top")
    save(fig, "global_residue_joint_response")
    plt.close(fig)
    return {"papers": len(d), "positive_both": n_joint, "boundary_markers": int((~inside).sum())}


def panel(ax, summary: pd.DataFrame, dimension: str, groups: list[str], labels: list[str]) -> None:
    d = summary[(summary.dimension == dimension) & summary.group.isin(groups)]
    loc = np.arange(len(groups))[::-1]
    for outcome, color, offset in [("Yield", PINK, 0.12), ("Topsoil SOC", BLUE, -0.12)]:
        part = d[d.outcome == outcome].set_index("group").loc[groups]
        effect = part.median_pct.to_numpy()
        low = part.bootstrap_95_lo_pct.to_numpy()
        high = part.bootstrap_95_hi_pct.to_numpy()
        ax.errorbar(effect, loc + offset,
                    xerr=np.vstack([effect-low, high-effect]), fmt="o", color=color,
                    ecolor=color, capsize=1.8, markersize=4, elinewidth=1.0,
                    markeredgecolor="white", markeredgewidth=0.4, zorder=3)
    ax.axvline(0, color="#999999", linewidth=0.7, zorder=1)
    ax.set_yticks(loc, labels)
    ax.set_ylim(-0.6, len(groups)-0.4)
    ax.set_xlim(-2, 40)
    ax.set_xticks([0, 10, 20, 30, 40])
    ax.grid(axis="x", color="#e6e6e6", lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", labelsize=7.5, length=2)
    ax.tick_params(axis="y", labelsize=7.5, length=0)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#888888")
    ax.set_xlabel("Change vs residue removal (%)", fontsize=8)
    for i, group in enumerate(groups):
        n = int(d[d.group == group].papers.iloc[0])
        ax.text(39.7, loc[i] + 0.32, f"{n} papers", ha="right", va="center",
                fontsize=6.5, color="#666666")


def plot_heterogeneity() -> None:
    d = pd.read_csv(DATA / "paper_balanced_summaries.csv")
    fig, axes = plt.subplots(2, 1, figsize=(7.2047244094, 5.3))
    fig.subplots_adjust(left=0.24, right=0.96, bottom=0.10, top=0.85, hspace=0.72)
    crop = ["Maize", "Rice", "Wheat", "Soybean"]
    climate = ["Tropical Dry", "Tropical Moist", "Subtropical Dry",
               "Subtropical Moist", "Temperate Dry", "Temperate Moist"]
    panel(axes[0], d, "Main_Crop", crop, crop)
    panel(axes[1], d, "Combined_Climate_Class", climate,
          ["Tropical · dry", "Tropical · moist", "Subtropical · dry",
           "Subtropical · moist", "Temperate · dry", "Temperate · moist"])
    handles = [Line2D([0], [0], marker="o", linestyle="none", color=PINK, label="Yield"),
               Line2D([0], [0], marker="o", linestyle="none", color=BLUE, label="Topsoil SOC stock")]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, 0.985), fontsize=8)
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig, json_out=OUT / "alignment_audit.json")
    save(fig, "global_residue_heterogeneity")
    width, height = fig.get_size_inches()
    positions = [ax.get_position() for ax in axes]
    split = (positions[0].y0 + positions[1].y1)/2
    for i, (side, lo, hi) in enumerate([("crop", split, 1), ("climate", 0, split)]):
        # For standalone panels, keep the original coordinate system and font sizes.
        for j, ax in enumerate(axes):
            ax.set_visible(i == j)
        fig.legends[0].set_visible(i == 0)
        box = Bbox.from_extents(0, lo*height, width, hi*height)
        for ext in ["pdf", "svg"]:
            fig.savefig(OUT / f"global_residue_heterogeneity_{side}.{ext}",
                        bbox_inches=box, pad_inches=0)
        fig.savefig(OUT / f"global_residue_heterogeneity_{side}.png", dpi=600,
                    bbox_inches=box, pad_inches=0)
    for ax in axes:
        ax.set_visible(True)
    fig.legends[0].set_visible(True)
    (OUT / "alignment.json").write_text(json.dumps({
        "axes_lefts": [float(x.x0) for x in positions],
        "axes_rights": [float(x.x1) for x in positions],
        "same_left": bool(abs(positions[0].x0-positions[1].x0) < 1e-10),
        "same_right": bool(abs(positions[0].x1-positions[1].x1) < 1e-10),
        "panel_split_fraction": split,
    }, indent=2), encoding="utf-8")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    joint = plot_joint()
    plot_heterogeneity()
    (OUT / "render_manifest.json").write_text(json.dumps(joint, indent=2), encoding="utf-8")
