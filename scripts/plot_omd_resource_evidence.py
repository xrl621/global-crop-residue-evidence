"""Plot the geographic mismatch between modelled crop-residue resource and papers.

The three crop panels are composed and aligned together, then cropped from the
same canvas without panel letters so that they can be reassembled in a talk.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.transforms import Bbox
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/omd2025_residue_geography/evidence_resource_geography_2020.csv"
OUT = ROOT / "figures/omd2025_resource_evidence"
sys.path.insert(0, str(Path.home() / ".codex/plugins/cache/nature-skills/nature-skills/0.1.0/skills/nature-figure/scripts"))
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402

BLUE = "#5394c3"  # User-selected palette: residue resource.
PINK = "#e16db7"  # User-selected palette: paper geography.
PALE = "#dedbee"
INK = "#25252b"
CONTINENTS = ["Asia", "Americas", "Europe", "Africa", "Oceania"]
CROPS = ["Maize", "Rice", "Wheat"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(DATA)
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 8.5,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "axes.linewidth": 0.6,
            "savefig.facecolor": "white",
        }
    )
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 7.25))
    fig.subplots_adjust(left=0.185, right=0.975, bottom=0.105, top=0.955, hspace=0.53)
    for ax, crop in zip(axes, CROPS):
        rows = data[data.crop == crop].set_index("continent").loc[CONTINENTS]
        if not (rows.residue_share.sum() > 0.999 and rows.paper_share.sum() > 0.999):
            raise ValueError(f"Geographic shares do not close for {crop}")
        y = list(range(len(CONTINENTS)))
        a = 100 * rows.residue_share.to_numpy()
        b = 100 * rows.paper_share.to_numpy()
        for yi, x1, x2 in zip(y, a, b):
            ax.plot([x1, x2], [yi, yi], color=PALE, lw=3.3, solid_capstyle="round", zorder=1)
        ax.scatter(a, y, s=48, color=BLUE, edgecolor="white", linewidth=0.5, zorder=3)
        ax.scatter(b, y, s=48, color=PINK, edgecolor="white", linewidth=0.5, zorder=4)
        ax.set_yticks(y, CONTINENTS)
        ax.invert_yaxis()
        ax.set_xlim(-2, 102)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_xlabel("Share of crop total (%)", fontsize=8.5)
        ax.set_title(f"{crop}   ·   {rows.papers_by_title.sum():.0f} source titles",
                     loc="left", color=INK, fontsize=10, fontweight="bold", pad=14)
        ax.grid(axis="x", color="#e8e8e8", lw=0.5, zorder=0)
        ax.tick_params(axis="x", length=3, color="#777777", labelsize=8)
        ax.tick_params(axis="y", length=0, labelsize=8.5, pad=7)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#777777")
        legend = [
            Line2D([], [], marker="o", linestyle="none", color=BLUE,
                   markersize=6, label="Residue production"),
            Line2D([], [], marker="o", linestyle="none", color=PINK,
                   markersize=6, label="Return-study titles"),
        ]
        ax.legend(handles=legend, ncol=2, loc="upper right", bbox_to_anchor=(1, 1.20),
                  frameon=False, columnspacing=1.0, handletextpad=0.3, fontsize=7.5)

    fig.text(0.185, 0.016,
             "Resource: OMD theoretical dry matter, 2020, allocated with MapSPAM production.\n"
             "Evidence: unique titles with yield + SOC in public return-versus-removal data.",
             ha="left", va="bottom", color="#555555", fontsize=7.2, linespacing=1.3)

    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig, json_out=OUT / "alignment_audit.json")
    fig.savefig(OUT / "resource_evidence_geography.pdf")
    fig.savefig(OUT / "resource_evidence_geography.svg")
    fig.savefig(OUT / "resource_evidence_geography.png", dpi=600)
    fig.savefig(OUT / "resource_evidence_geography.tiff", dpi=600)

    # Export each panel from the composed canvas, preserving identical axes widths.
    fig_w, fig_h = fig.get_size_inches()
    for ax, crop in zip(axes, CROPS):
        p = ax.get_position()
        bounds = Bbox.from_extents(0.12, p.y0 * fig_h - 0.39,
                                  fig_w - 0.06, p.y1 * fig_h + 0.42)
        fig.savefig(OUT / f"resource_evidence_{crop.lower()}.png",
                    bbox_inches=bounds, dpi=600)
    plt.close(fig)


if __name__ == "__main__":
    main()
