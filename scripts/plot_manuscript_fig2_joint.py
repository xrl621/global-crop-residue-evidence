"""Claim-led Fig 2: cereal residue return, paired yield and SOC response.

The input is a secondary public compilation summarized once per paper title;
point intervals are paper-resampling intervals, not inverse-variance meta CIs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/manuscript_fig2_joint_20260929"
OUT = ROOT / "figures/manuscript_fig2_joint_20260929"
PALETTE = {"Yield": "#e16db7", "Topsoil SOC stock": "#5394c3",
           "Both positive": "#908ebc", "Other": "#b8a89f"}
CROPS = ("Three cereals", "Maize", "Rice", "Wheat")


def load(source: Path):
    effects = pd.read_csv(source / "effect_summary.csv")
    joint = pd.read_csv(source / "joint_direction.csv")
    paper = pd.read_csv(source / "paper_global.csv")
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    if manifest["focal_paper_titles"] != len(paper) or len(paper) != 215:
        raise ValueError("Paper-level input differs from audited 215-title snapshot")
    if len(effects) != 24 or len(joint) != 16:
        raise ValueError("Expected 12 groups × 2 outcomes and 4 groups × 4 directions")
    return effects, joint, paper, manifest


def get_row(data: pd.DataFrame, dimension: str, group: str, outcome: str):
    row = data.loc[data.dimension.eq(dimension) & data.group.eq(group) &
                   data.outcome.eq(outcome)]
    if len(row) != 1:
        raise ValueError(f"Missing unique estimate: {dimension}/{group}/{outcome}")
    return row.iloc[0]


def decorate(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#e7e7e7", linewidth=.55)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=2.5, width=.6, pad=3)


def interval_pair(ax, y, source: pd.DataFrame, dimension: str, group: str):
    for outcome, offset, marker in (("Yield", -.15, "o"),
                                    ("Topsoil SOC stock", .15, "s")):
        row = get_row(source, dimension, group, outcome)
        center = float(row.median_percent)
        left = center - float(row.bootstrap_95_lo_percent)
        right = float(row.bootstrap_95_hi_percent) - center
        if min(left, right) < -1e-8:
            raise ValueError("Median lies outside its bootstrap interval")
        ax.errorbar(center, y + offset, xerr=[[left], [right]], fmt=marker,
                    color=PALETTE[outcome], ecolor=PALETTE[outcome],
                    markersize=5, markeredgecolor="#4a4a4a", markeredgewidth=.35,
                    capsize=2.2, elinewidth=1.35, zorder=4)


def plot(source: Path, out: Path, qa_scripts: Path):
    sys.path.insert(0, str(qa_scripts))
    from audit_panel_alignment import require_matplotlib_panel_alignment

    effects, joint, paper, source_manifest = load(source)
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial"],
        "font.size": 7, "axes.labelsize": 7, "xtick.labelsize": 6.5,
        "ytick.labelsize": 7, "pdf.fonttype": 42, "svg.fonttype": "none",
        "axes.linewidth": .65, "savefig.facecolor": "white",
    })
    fig = plt.figure(figsize=(183 / 25.4, 125 / 25.4))
    gs = fig.add_gridspec(2, 2, left=.11, right=.965, top=.83, bottom=.15,
                          width_ratios=[1.07, 1], height_ratios=[.9, 1.2],
                          wspace=.52, hspace=.72)
    hero = fig.add_subplot(gs[:, 0])
    joint_ax = fig.add_subplot(gs[0, 1])
    region = fig.add_subplot(gs[1, 1])
    for ax in (hero, joint_ax, region):
        decorate(ax)

    # Paper-title level pairs make the joint response visible rather than
    # substituting a small set of summary points for the underlying evidence.
    x = np.expm1(paper.yield_lnrr.to_numpy()) * 100
    y = np.expm1(paper.soc_lnrr.to_numpy()) * 100
    in_frame = (x >= -45) & (x <= 100) & (y >= -45) & (y <= 70)
    both = (x > 0) & (y > 0)
    if int(np.sum(both)) != 172 or int(np.sum(in_frame)) != 213:
        raise ValueError("Paired paper direction or plotting window changed")
    hero.add_patch(Rectangle((0, 0), 100, 70, facecolor="#f4cee1",
                             edgecolor="none", alpha=.22, zorder=0))
    hero.axhline(0, color="#646464", linewidth=.8, zorder=2)
    hero.axvline(0, color="#646464", linewidth=.8, zorder=2)
    for mask, color, label, z in (
        (in_frame & ~both, PALETTE["Other"], "Other directions", 3),
        (in_frame & both, PALETTE["Both positive"], "Both higher", 4),
    ):
        hero.scatter(x[mask], y[mask], s=14, facecolor=color, edgecolor="white",
                     linewidth=.25, alpha=.78, zorder=z, label=label)
    hero.set_xlim(-45, 100)
    hero.set_ylim(-45, 70)
    hero.set_xticks([-40, 0, 40, 80])
    hero.set_yticks([-40, 0, 40])
    hero.set_xlabel("Yield change relative to removal (%)", labelpad=4)
    hero.set_ylabel("Topsoil SOC stock change (%)", labelpad=4)
    hero.legend(loc="lower left", bbox_to_anchor=(0, 1.005), ncol=2,
                frameon=False, fontsize=6.5, markerscale=1.2,
                handletextpad=.2, borderaxespad=0, columnspacing=1.0)
    hero.text(0, 1.18, "Paired outcomes (213 shown)", transform=hero.transAxes,
              ha="left", va="bottom", fontsize=8, fontweight="bold")
    hero.text(0, 1.115, "172/215 (80%) jointly higher",
              transform=hero.transAxes, ha="left", va="bottom",
              color="#6b5f83", fontsize=6.3)

    sizes = {"Three cereals": 215, "Maize": 109, "Rice": 71, "Wheat": 107}
    joint_ax.axhspan(-.43, .43, color="#f6f5f8", zorder=0)
    joint_ax.axvline(0, color="#555555", linewidth=.8, zorder=2)
    for row_y, group in enumerate(CROPS):
        dim = "All" if row_y == 0 else "Crop"
        interval_pair(joint_ax, row_y, effects, dim, group)
    joint_ax.set_yticks(range(4), [f"{name} ({sizes[name]})" for name in CROPS])
    joint_ax.set_ylim(3.55, -.55)
    joint_ax.set_xlim(-2.5, 23)
    joint_ax.set_xticks([0, 5, 10, 15, 20])
    joint_ax.set_xlabel("Median change (%)", labelpad=4)
    joint_ax.text(0, 1.18, "Response by crop", transform=joint_ax.transAxes,
                  ha="left", va="bottom", fontsize=8, fontweight="bold")
    joint_ax.text(0, 1.07, "●  Yield", transform=joint_ax.transAxes,
                  ha="left", va="bottom", fontsize=6.5, color=PALETTE["Yield"])
    joint_ax.text(.29, 1.07, "■  SOC stock", transform=joint_ax.transAxes,
                  ha="left", va="bottom", fontsize=6.5,
                  color=PALETTE["Topsoil SOC stock"])

    region.axvline(0, color="#555555", linewidth=.8, zorder=2)
    climates = ("Temperate Moist", "Temperate Dry", "Subtropical Moist",
                "Subtropical Dry", "Tropical Moist", "Tropical Dry")
    climate_sizes = {"Temperate Moist": 83, "Temperate Dry": 31,
                     "Subtropical Moist": 34, "Subtropical Dry": 39,
                     "Tropical Moist": 25, "Tropical Dry": 9}
    for row_y, group in enumerate(climates):
        interval_pair(region, row_y, effects, "Climate", group)
    region.set_yticks(range(6), [f"{name.lower()} ({climate_sizes[name]})"
                                   for name in climates])
    region.set_ylim(5.55, -.55)
    region.set_xlim(-5, 45)
    region.set_xticks([0, 10, 20, 30, 40])
    region.set_xlabel("Change relative to removal (%)", labelpad=4)
    region.text(0, 1.10, "Response by climate class", transform=region.transAxes,
                ha="left", va="bottom", fontsize=8, fontweight="bold")

    fig.canvas.draw()
    require_matplotlib_panel_alignment(
        fig, json_out=str(out / "fig2_joint.alignment.json"),
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
        require_panel_labels=False,
    )
    full = out / "fig2_joint"
    fig.savefig(full.with_suffix(".pdf"))
    fig.savefig(full.with_suffix(".svg"))
    fig.savefig(full.with_suffix(".png"), dpi=600)
    renderer = fig.canvas.get_renderer()
    content = [ax.get_tightbbox(renderer) for ax in (hero, joint_ax, region)]
    x_right = content[0].x1
    x_left = min(content[1].x0, content[2].x0)
    y_top = content[2].y1
    y_bottom = content[1].y0
    if not (x_right < x_left and y_top < y_bottom):
        raise ValueError(f"No safe panel gutters for exact canvas slicing: horizontal={x_left-x_right:.1f}px vertical={y_bottom-y_top:.1f}px")
    x_cut = (x_right + x_left) / 2
    y_cut = (y_top + y_bottom) / 2
    fw, fh = fig.bbox.width, fig.bbox.height
    slots = {
        "paired_response": Bbox.from_extents(0, 0, x_cut, fh),
        "crop_response": Bbox.from_extents(x_cut, y_cut, fw, fh),
        "climate_response": Bbox.from_extents(x_cut, 0, fw, y_cut),
    }
    (out / "panel_slots.json").write_text(json.dumps({
        "full_size_mm": [183, 125],
        "left_width_mm": x_cut / fw * 183,
        "right_width_mm": (1 - x_cut / fw) * 183,
        "right_top_height_mm": (1 - y_cut / fh) * 125,
        "right_bottom_height_mm": y_cut / fh * 125,
        "horizontal_gutter_pt": (x_left - x_right) * 72 / fig.dpi,
        "right_vertical_gutter_pt": (y_bottom - y_top) * 72 / fig.dpi,
    }, indent=2), encoding="utf-8")
    panels = (hero, joint_ax, region)
    for index, (name, box) in enumerate(slots.items()):
        for j, ax in enumerate(panels):
            ax.set_visible(j == index)
        inches = box.transformed(fig.dpi_scale_trans.inverted())
        base = out / name
        fig.savefig(base.with_suffix(".pdf"), bbox_inches=inches, pad_inches=0)
        fig.savefig(base.with_suffix(".svg"), bbox_inches=inches, pad_inches=0)
        fig.savefig(base.with_suffix(".png"), dpi=600, bbox_inches=inches, pad_inches=0)
    plt.close(fig)
    for svg in out.glob("*.svg"):
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
                       encoding="utf-8")
    effects.to_csv(out / "fig2_effect_source.csv", index=False)
    joint.to_csv(out / "fig2_joint_source.csv", index=False)
    (out / "render_manifest.json").write_text(json.dumps({
        "analysis_manifest_sha256": hashlib.sha256((source / "manifest.json").read_bytes()).hexdigest(),
        "secondary_source_sha256": source_manifest["source_sha256"],
        "panel_roles": ["paired title-level joint response",
                        "crop-specific title-bootstrap intervals", "climate-stratified descriptive intervals"],
        "scatter_pairs_displayed": 213,
        "scatter_pairs_outside_axis": 2,
        "source_layer": "secondary paper-balanced cereal return vs removal; no biochar or burning",
        "no_global_causal_or_three_pathway_ranking": True,
        "palette": PALETTE,
        "dimensions_mm": [183, 125],
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--qa-scripts", type=Path, required=True)
    args = parser.parse_args()
    plot(args.source, args.out, args.qa_scripts)
