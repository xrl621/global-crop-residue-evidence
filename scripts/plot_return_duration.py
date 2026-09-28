"""Two-panel duration figure, assembled and aligned before unnumbered panel crops."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/return_duration_20260928/duration_summary.csv"
OUT = ROOT / "figures/return_duration_20260928"
PALETTE = ["#f4cee1", "#c5d9df", "#e16db7", "#908ebc", "#af88bb", "#dedbee",
           "#f07590", "#dfb9d5", "#b099b5", "#5394c3", "#b8a89f"]
COLORS = {
    "yield": PALETTE[2],
    "soc": PALETTE[9],
    "both_positive": PALETTE[3],
    "yield_only_positive": PALETTE[6],
    "soc_only_positive": PALETTE[9],
    "neither_positive": PALETTE[10],
}


def build(source: Path = SOURCE, out: Path = OUT, qa_scripts: Path | None = None) -> None:
    if qa_scripts:
        sys.path.insert(0, str(qa_scripts))
    from audit_panel_alignment import require_matplotlib_panel_alignment

    d = pd.read_csv(source)
    if len(d) != 5 or d.papers.sum() != 218:
        raise ValueError("Expected five bins and 218 paper titles")
    if not (d[["both_positive", "yield_only_positive", "soc_only_positive",
               "neither_positive"]].sum(axis=1) == d.papers).all():
        raise ValueError("Joint-response categories do not close within each duration bin")
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 7.4, "axes.labelsize": 7.5, "xtick.labelsize": 7.1,
        "ytick.labelsize": 7, "axes.linewidth": 0.65,
        "axes.spines.top": False, "axes.spines.right": False,
        "pdf.fonttype": 42, "svg.fonttype": "none", "legend.frameon": False,
    })
    width, height = 183 / 25.4, 92 / 25.4
    fig, axes = plt.subplots(1, 2, figsize=(width, height))
    fig.subplots_adjust(left=.095, right=.98, bottom=.22, top=.83, wspace=.34)
    x = np.arange(5)
    labels = [f"{r.duration_bin}\nn={int(r.papers)}" for r in d.itertuples()]
    # Magnitudes: two outcomes from the same paper set in each bin. Intervals
    # resample publication titles, not the many dependent within-paper contrasts.
    ax = axes[0]
    for key, shift, name, marker in (
        ("yield", -.09, "Yield", "o"), ("soc", .09, "Topsoil SOC stock", "s")
    ):
        center = d[f"{key}_median_percent"].to_numpy()
        low = d[f"{key}_bootstrap_lo_percent"].to_numpy()
        high = d[f"{key}_bootstrap_hi_percent"].to_numpy()
        ax.errorbar(x + shift, center, yerr=[center - low, high - center],
                    fmt=marker, linestyle="none", color=COLORS[key], ecolor=COLORS[key],
                    mec="#404040", mew=.4, markersize=5.2, elinewidth=1.05,
                    capsize=2.0, capthick=.85, zorder=3, label=name)
    ax.axhline(0, color="#777777", lw=.6, ls="--", zorder=1)
    ax.set_ylim(-4, 31)
    ax.set_yticks([0, 10, 20, 30])
    ax.set_ylabel("Change vs residue removal (%)")
    ax.set_xlabel("Reported experiment duration (years)")
    ax.legend(handles=[
        Line2D([], [], marker="o", linestyle="none", color=COLORS["yield"],
               mec="#404040", mew=.4, markersize=5, label="Yield"),
        Line2D([], [], marker="s", linestyle="none", color=COLORS["soc"],
               mec="#404040", mew=.4, markersize=5, label="Topsoil SOC stock"),
    ], loc="lower left", bbox_to_anchor=(0, 1.03), ncol=2,
       handletextpad=.3, columnspacing=.9, borderaxespad=0)
    ax.grid(axis="y", color="#ebebeb", lw=.5, zorder=0)

    # Directional co-benefit: a separate question from the median magnitude.
    ax = axes[1]
    bottom = np.zeros(5)
    groups = [
        ("both_positive", "Both positive"),
        ("yield_only_positive", "Yield only positive"),
        ("soc_only_positive", "SOC only positive"),
        ("neither_positive", "Neither positive"),
    ]
    for key, name in groups:
        fraction = 100 * d[key].to_numpy() / d.papers.to_numpy()
        ax.bar(x, fraction, bottom=bottom, width=.68, color=COLORS[key],
               edgecolor="white", linewidth=.45, label=name, zorder=2)
        if key == "both_positive":
            for xpos, base, value in zip(x, bottom, fraction):
                ax.text(xpos, base + value / 2, f"{value:.0f}%", ha="center",
                        va="center", fontsize=7.2, color="#202020")
        bottom += fraction
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Share of papers (%)")
    ax.set_xlabel("Reported experiment duration (years)")
    ax.legend(handles=[Patch(facecolor=COLORS[key], label=name) for key, name in groups],
              loc="lower left", bbox_to_anchor=(0, 1.03), ncol=2,
              handlelength=1.2, columnspacing=.65, borderaxespad=0, fontsize=6.6)
    for ax in axes:
        ax.set_xticks(x, labels)
        ax.set_xlim(-.52, 4.52)
        ax.tick_params(length=2.5, width=.6, pad=3)
        ax.set_axisbelow(True)
    fig.canvas.draw()
    out.mkdir(parents=True, exist_ok=True)
    require_matplotlib_panel_alignment(fig, json_out=str(out / "duration_response.alignment.json"),
                                       tolerance_pt=1.5, gutter_tolerance_pt=1.5,
                                       require_panel_labels=False, strict=True)
    assembled = out / "duration_response"
    fig.savefig(assembled.with_suffix(".pdf"))
    fig.savefig(assembled.with_suffix(".svg"))
    fig.savefig(assembled.with_suffix(".png"), dpi=600)
    cut = (axes[0].get_position().x1 + axes[1].get_position().x0) / 2
    for index, (name, left, right) in enumerate((
        ("duration_magnitude", 0, cut), ("duration_joint_direction", cut, 1)
    )):
        for j, panel in enumerate(axes):
            panel.set_visible(j == index)
        box = Bbox.from_extents(left * width, 0, right * width, height)
        fig.savefig(out / f"{name}.png", dpi=600, bbox_inches=box, pad_inches=0)
    plt.close(fig)
    for svg in out.glob("*.svg"):
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
                       encoding="utf-8")
    (out / "render_manifest.json").write_text(json.dumps({
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "matplotlib": matplotlib.__version__, "palette": PALETTE,
        "width_mm": 183, "height_mm": 92, "panel_letters": False,
        "split": "crop the aligned assembled canvas; PNG panels retain physical sizing",
        "interval": "paper-level bootstrap percentile interval, 4000 resamples",
        "n": "unique exact publication titles, not independent field trials",
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--qa-scripts", type=Path)
    args = parser.parse_args()
    build(args.source, args.out, args.qa_scripts)
