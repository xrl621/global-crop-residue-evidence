"""Three aligned two-panel descriptive figures; split only after assembly.

Requires nature-figure audit scripts on PYTHONPATH (or --qa-scripts).
No panel letters, titles, fabricated values, inferential intervals or P values.
"""
from __future__ import annotations

import argparse
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

ROOT = Path(__file__).resolve().parents[1]
PALETTE = ["#f4cee1", "#c5d9df", "#e16db7", "#908ebc", "#af88bb", "#dedbee",
           "#f07590", "#dfb9d5", "#b099b5", "#5394c3", "#b8a89f"]
PATHWAYS = ["direct_return", "biochar_return", "open_burning"]
COLORS = dict(zip(PATHWAYS, [PALETTE[2], PALETTE[9], PALETTE[3]]))
NAMES = {"direct_return": "Direct return", "biochar_return": "Biochar", "open_burning": "Burning"}
STUDY_NAMES = {
    "amgain_bhairahawa_2019_2021": "Bhairahawa\n2019–2021",
    "jijnasa_bhubaneswar_2022_2024": "Bhubaneswar\n2022–2024",
    "nayak_bhubaneswar_2020_2021": "Bhubaneswar\n2020–2021",
    "rice_primary_53": "Mono-rice trial\n2011–2013",
    "qin_huizhou_2012_2015": "Huizhou\n2012–2015",
}
JOINT_LABELS = {"biochar_li2024SD_3": "Tai Lake trial", "du_dingxi_2016_2022": "Du 2024",
                "korav_2024": "Korav 2024", "rice_primary_53": "Mono-rice trial",
                "qin_huizhou_2012_2015": "Qin 2016", "rice_primary_164": "Hung 2022"}
MARKERS = {"biochar_li2024SD_3": "o", "du_dingxi_2016_2022": "s", "korav_2024": "^",
           "rice_primary_53": "D", "qin_huizhou_2012_2015": "o", "rice_primary_164": "^"}


def offsets(n, width=0.12):
    # Deterministic display offsets, not stochastic data or uncertainty.
    if n == 0:
        return np.array([])
    return np.linspace(-width, width, n) if n > 1 else np.array([0.0])


def setup(height=94):
    fig, axes = plt.subplots(1, 2, figsize=(7.2047244094, height / 25.4))  # 183 mm wide
    fig.subplots_adjust(left=0.14, right=0.98, bottom=0.23, top=0.84, wspace=0.65)
    for ax in axes:
        ax.set_axisbelow(True)
        ax.grid(axis="x", color="#eeeeee", linewidth=0.5)
        ax.tick_params(length=2.5, width=0.6, pad=3)
        ax.spines[["top", "right"]].set_visible(False)
    return fig, axes


def path_legend(ax):
    handles = [Line2D([], [], marker="o", linestyle="none", color=COLORS[p],
                      markersize=4, label=NAMES[p]) for p in PATHWAYS]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.035),
              ncol=3, handletextpad=0.3, columnspacing=0.7, fontsize=6.5, borderaxespad=0)


def export(fig, axes, name, output, require_matplotlib_panel_alignment):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig, json_out=str(output / f"{name}.alignment.json"),
          tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
          require_panel_labels=False)
    # PDF/SVG preserve editable text; PNG is the 600-dpi review preview.
    fig.savefig(output / f"{name}.pdf")
    fig.savefig(output / f"{name}.svg")
    fig.savefig(output / f"{name}.png", dpi=600)
    width, height = fig.get_size_inches()
    split = (axes[0].get_position().x1 + axes[1].get_position().x0) / 2
    bounds = [(0, split), (split, 1)]
    for index, (side, (left, right)) in enumerate(zip(["left", "right"], bounds)):
        # Same figure, fonts and physical geometry; no redraw or rescaling.
        box = Bbox.from_extents(left * width, 0, right * width, height)
        # Omit the other panel's off-page artists from the standalone vector
        # file, while keeping this panel's exact original positions and fonts.
        for j, ax in enumerate(axes):
            ax.set_visible(j == index)
        fig.savefig(output / f"{name}_{side}.pdf", bbox_inches=box, pad_inches=0)
        fig.savefig(output / f"{name}_{side}.svg", bbox_inches=box, pad_inches=0)
        fig.savefig(output / f"{name}_{side}.png", dpi=600, bbox_inches=box, pad_inches=0)
    for ax in axes:
        ax.set_visible(True)
    # Matplotlib puts trailing spaces inside multi-line path attributes.
    # Whitespace-only canonicalization keeps generated vector diffs clean.
    for svg in output.glob(f"{name}*.svg"):
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
                       encoding="utf-8")
    plt.close(fig)


def plot_yield(data, output, align):
    effects = pd.read_csv(data / "screened_effects.csv")
    trials = pd.read_csv(data / "trial_responses.csv")
    crops = pd.read_csv(data / "yield_by_crop.csv")
    effects, trials = effects[effects.outcome == "yield"], trials[trials.outcome == "yield"]
    fig, (left, right) = setup()
    for index, pathway in enumerate(PATHWAYS):
        raw = effects[effects.pathway == pathway].sort_values("effect_id")
        trial = trials[trials.pathway == pathway].sort_values("study_id")
        left.scatter(raw.response_percent, index + 0.12 + offsets(len(raw), 0.12),
                     s=10, color=COLORS[pathway], alpha=0.3, edgecolors="none")
        left.scatter(trial.percent, index - 0.14 + offsets(len(trial), 0.1),
                     s=31, color=COLORS[pathway], edgecolors="#333333", linewidths=0.45, zorder=4)
    left.set_yticks(range(3), [f"{NAMES[p]}\n{len(trials[trials.pathway == p])} trials" for p in PATHWAYS])
    left.set_ylim(2.55, -0.6)
    left.set_xlabel("Yield change vs study control (%)")
    left.legend(handles=[Line2D([], [], marker="o", linestyle="none", color="#aaaaaa", markersize=3, label="Individual contrast"),
                         Line2D([], [], marker="o", linestyle="none", markeredgecolor="#333333", color="#777777", markersize=5, label="Trial mean")],
                loc="lower center", bbox_to_anchor=(0.5, 1.035), fontsize=6.5, ncol=2, columnspacing=0.8)
    for index, crop in enumerate(["rice", "wheat", "maize"]):
        for j, pathway in enumerate(PATHWAYS):
            g = crops[(crops.crop_display == crop) & (crops.pathway == pathway)].sort_values("study_id")
            right.scatter(g.percent, index + (j - 1) * 0.22 + offsets(len(g), 0.065),
                          s=30, color=COLORS[pathway], marker=["o", "s", "^"][j],
                          edgecolors="#333333", linewidths=0.4, zorder=4)
    right.set_yticks(range(3), ["Rice", "Wheat", "Maize"])
    right.set_ylim(2.55, -0.6)
    right.set_xlabel("Trial–crop yield response (%)")
    path_legend(right)
    for ax in [left, right]:
        ax.axvline(0, color="#777777", linewidth=0.7, linestyle="--")
        ax.set_xlim(-22, 38)
        ax.set_xticks([-20, 0, 20])
    export(fig, [left, right], "stage1_yield", output, align)


def plot_joint(data, output, align):
    d = pd.read_csv(data / "joint_outcome_pairs.csv")
    fig, axes = setup(106)
    fig.subplots_adjust(bottom=0.28)
    for ax, endpoint in zip(axes, ["SOC", "GWP"]):
        frame = d[d.endpoint == endpoint]
        for (study, pathway), group in frame.groupby(["study_id", "pathway"]):
            ax.scatter(group.yield_percent, group.endpoint_percent, s=27,
                       marker=MARKERS[study], color=COLORS[pathway], alpha=0.85,
                       edgecolors="#333333", linewidths=0.4, zorder=4)
        ax.axhline(0, color="#777777", lw=0.7, ls="--")
        ax.axvline(0, color="#777777", lw=0.7, ls="--")
        ax.set_xlabel("Yield change vs study control (%)")
        ax.set_ylabel("SOC concentration change (%)" if endpoint == "SOC" else "Soil GWP change (%)")
        path_legend(ax)
        # Separate trial symbols below axes so point count cannot masquerade as n.
        for idx, study in enumerate(sorted(frame.study_id.unique())):
            column, row = idx % 2, idx // 2
            x, y = 0.05 + column * 0.57, -0.31 - row * 0.09
            ax.plot(x, y, marker=MARKERS[study], color="#777777", linestyle="none", ms=4,
                    transform=ax.transAxes, clip_on=False)
            ax.text(x + 0.045, y, JOINT_LABELS[study], transform=ax.transAxes,
                    ha="left", va="center", fontsize=6.5)
        ax.text(0.5, 1.14, f"{frame.study_id.nunique()} trials · {len(frame)} matched records",
                transform=ax.transAxes, ha="center", fontsize=7, color="#555555")
        ax.margins(x=0.15, y=0.12)
    export(fig, axes, "stage2_joint", output, align)


def plot_comparisons(data, output, align):
    trials = pd.read_csv(data / "matched_pathway_trials.csv")
    pairs = pd.read_csv(data / "matched_pathway_pairs.csv")
    fig, axes = setup(101)
    # Give long location labels room in the central gutter and preserve equal areas.
    fig.subplots_adjust(left=0.18, right=0.98, wspace=0.9)
    for ax, contrast, pathway in zip(axes,
            ["direct_return_vs_open_burning", "biochar_return_vs_direct_return"],
            ["direct_return", "biochar_return"]):
        frame = trials[trials.contrast == contrast].sort_values("percent")
        labels = []
        for y, (_, trial) in enumerate(frame.iterrows()):
            raw = pairs[(pairs.contrast == contrast) & (pairs.study_id == trial.study_id)]
            ax.hlines(y, raw.percent.min(), raw.percent.max(), color=COLORS[pathway], lw=1.2, alpha=0.65)
            ax.scatter(raw.percent, y + offsets(len(raw), 0.09), s=16, color=COLORS[pathway],
                       alpha=0.5, edgecolors="none")
            ax.scatter(trial.percent, y, marker="D", color=COLORS[pathway],
                       edgecolors="#333333", linewidths=0.5, s=42, zorder=5)
            labels.append(STUDY_NAMES[trial.study_id])
        ax.set_yticks(range(len(frame)), labels)
        ax.set_ylim(len(frame) - 0.5, -0.6)
        ax.set_xlim(-18, 36)
        ax.set_xticks([-10, 0, 10, 20, 30])
        ax.axvline(0, color="#777777", lw=0.7, ls="--")
        ax.set_xlabel("Yield: return vs burning (%)" if pathway == "direct_return" else "Yield: biochar vs return (%)")
        ax.legend(handles=[Line2D([], [], marker="D", linestyle="none", color=COLORS[pathway],
                                  markeredgecolor="#333333", ms=4.5, label="Trial mean"),
                           Line2D([], [], color=COLORS[pathway], lw=1.2, label="Observed range")],
                  loc="lower center", bbox_to_anchor=(0.5, 1.035), ncol=2, fontsize=6.5,
                  handlelength=1, columnspacing=0.8)
    export(fig, axes, "stage3_matched_paths", output, align)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data/processed/stage_20260926")
    parser.add_argument("--output", type=Path, default=ROOT / "figures/stage_20260926")
    parser.add_argument("--qa-scripts", type=Path)
    args = parser.parse_args()
    if args.qa_scripts:
        sys.path.insert(0, str(args.qa_scripts))
    from audit_panel_alignment import require_matplotlib_panel_alignment
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
                         "font.size": 7.5, "axes.labelsize": 7.5, "xtick.labelsize": 7,
                         "ytick.labelsize": 7, "axes.linewidth": 0.6, "legend.frameon": False,
                         "pdf.fonttype": 42, "svg.fonttype": "none"})
    args.output.mkdir(parents=True, exist_ok=True)
    for plot in [plot_yield, plot_joint, plot_comparisons]:
        plot(args.data, args.output, require_matplotlib_panel_alignment)
    (args.output / "render_manifest.json").write_text(json.dumps({
        "matplotlib": matplotlib.__version__, "palette": PALETTE,
        "panel_labels": False, "titles": False, "width_mm": 183,
        "split_method": "crop final assembled figure without rescaling fonts or data",
        "statistics": "descriptive; ranges are observed spread, not confidence intervals"
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
