"""Two-layer descriptive response profile for the three focal residue pathways.

Small points are all eligible treatment-control comparisons; large points are
one study_id × pathway × endpoint. Neither layer is a pooled meta-analysis.
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
from matplotlib.lines import Line2D
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/processed/pathway_endpoint_v2_20260928/trial_level.csv"
EFFECT_INPUT = ROOT / "data/processed/stage_20260928/screened_effects.csv"
OUTPUT = ROOT / "figures/manuscript_fig2_trial_response_20260929"
PATHWAYS = ("direct_return", "biochar_return", "open_burning")
ENDPOINTS = ("yield", "SOC_concentration", "CH4", "N2O")
COLORS = {"direct_return": "#5394c3", "biochar_return": "#e16db7",
          "open_burning": "#908ebc"}
PATH_LABELS = {"direct_return": "Direct return", "biochar_return": "Biochar",
               "open_burning": "Open burning"}
ENDPOINT_LABELS = {"yield": "Grain yield", "SOC_concentration": "SOC concentration",
                   "CH4": "Soil CH₄ · symlog axis", "N2O": "Soil N₂O"}
# Different endpoint ranges are intentional and explicitly printed on each axis.
AXES = {"yield": (-18, 42, [-10, 0, 10, 20, 30, 40]),
        "SOC_concentration": (-8, 65, [0, 20, 40, 60]),
        "CH4": (-65, 2300, [-50, 0, 50, 200, 1000]),
        "N2O": (-70, 230, [-50, 0, 50, 100, 200])}


def prepare(source: Path, effect_source: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(source)
    required = {"study_id", "pathway", "crop", "endpoint", "trial_mean_lnrr",
                "countries", "effect_records"}
    if missing := required - set(raw.columns):
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    focused = raw.loc[raw.pathway.isin(PATHWAYS) & raw.endpoint.isin(ENDPOINTS)].copy()
    if len(focused) == 0 or focused.trial_mean_lnrr.isna().any():
        raise ValueError("No valid trial-level response rows for Fig 2")
    key = ["study_id", "pathway", "endpoint"]
    if focused.duplicated(key + ["crop"]).any():
        raise ValueError("Duplicate trial-pathway-endpoint-crop rows")
    trial = (focused.groupby(key, sort=True)
             .agg(mean_lnrr=("trial_mean_lnrr", "mean"),
                  crop_units=("crop", "nunique"),
                  crops=("crop", lambda x: "|".join(sorted(set(x)))),
                  countries=("countries", lambda x: "|".join(sorted(set(x)))),
                  effect_records=("effect_records", "sum"))
             .reset_index())
    trial["response_percent"] = 100 * np.expm1(trial.mean_lnrr)
    summary = (trial.groupby(["pathway", "endpoint"], sort=True)
               .agg(independent_trial_keys=("study_id", "nunique"),
                    positive_trials=("mean_lnrr", lambda x: int((x > 0).sum())),
                    negative_trials=("mean_lnrr", lambda x: int((x < 0).sum())),
                    median_trial_percent=("response_percent", "median"),
                    min_trial_percent=("response_percent", "min"),
                    max_trial_percent=("response_percent", "max"))
               .reset_index())
    if len(summary) != len(PATHWAYS) * len(ENDPOINTS):
        raise ValueError("Some pathway-endpoint cells are empty")
    effects = pd.read_csv(effect_source, keep_default_na=False)
    effects["endpoint"] = np.where(effects.outcome.eq("SOC"),
                                   effects.soc_kind, effects.outcome)
    effects = effects.loc[effects.pathway.isin(PATHWAYS) &
                          effects.endpoint.isin(ENDPOINTS) &
                          effects.crop_display.isin(("rice", "maize", "wheat"))].copy()
    expected = {eid for value in focused.effect_ids for eid in str(value).split("|")}
    if effects.effect_id.duplicated().any() or set(effects.effect_id) != expected:
        raise ValueError("Effect-level and trial-level source IDs do not match")
    effects["response_percent"] = 100 * np.expm1(pd.to_numeric(effects.lnrr))
    if len(effects) != int(trial.effect_records.sum()):
        raise ValueError("Effect-level and trial-level record counts do not match")
    return trial, summary, effects


def plot(trial: pd.DataFrame, summary: pd.DataFrame, effects: pd.DataFrame,
         out: Path, qa_scripts: Path, source: Path, effect_source: Path):
    sys.path.insert(0, str(qa_scripts))
    from audit_panel_alignment import require_matplotlib_panel_alignment

    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial"],
        "font.size": 7, "axes.labelsize": 7, "xtick.labelsize": 6.5,
        "ytick.labelsize": 7, "pdf.fonttype": 42, "svg.fonttype": "none",
        "axes.linewidth": 0.6, "axes.spines.top": False,
        "axes.spines.right": False, "savefig.facecolor": "white",
    })
    fig, axes = plt.subplots(2, 2, figsize=(183 / 25.4, 132 / 25.4))
    fig.subplots_adjust(left=.155, right=.975, top=.94, bottom=.16,
                        wspace=.46, hspace=.52)
    for ax, endpoint in zip(axes.flat, ENDPOINTS):
        low, high, ticks = AXES[endpoint]
        if endpoint == "CH4":
            ax.set_xscale("symlog", linthresh=50)
        ax.set_xlim(low, high)
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{tick:,}" for tick in ticks])
        ax.set_ylim(2.55, -.55)
        ax.set_yticks(range(3))
        counts = {p: int(summary.loc[(summary.pathway == p) &
                                     (summary.endpoint == endpoint),
                                     "independent_trial_keys"].iloc[0])
                  for p in PATHWAYS}
        ax.set_yticklabels([f"{PATH_LABELS[p]} ({counts[p]})" for p in PATHWAYS])
        ax.axvline(0, color="#4f4f4f", lw=.85, zorder=1)
        ax.grid(axis="x", color="#e9e9e9", lw=.5, zorder=0)
        ax.tick_params(axis="both", length=2.5, width=.6, pad=3)
        ax.set_axisbelow(True)
        ax.text(0, 1.09, ENDPOINT_LABELS[endpoint], transform=ax.transAxes,
                ha="left", va="bottom", fontsize=8, fontweight="bold")
        ax.set_xlabel("Change relative to study control (%)", labelpad=4)
        for row, pathway in enumerate(PATHWAYS):
            individual = effects.loc[(effects.endpoint == endpoint) &
                                     (effects.pathway == pathway)].sort_values("effect_id")
            raw_offsets = (np.linspace(-.08, .08, len(individual))
                           if len(individual) > 1 else np.zeros(len(individual)))
            ax.scatter(individual.response_percent, row + .14 + raw_offsets,
                       s=8, color=COLORS[pathway], edgecolors="none",
                       alpha=.28, zorder=2)
            subset = trial.loc[(trial.endpoint == endpoint) &
                               (trial.pathway == pathway)].sort_values("study_id")
            count = len(subset)
            offsets = np.linspace(-.08, .08, count) if count > 1 else np.zeros(count)
            ax.scatter(subset.response_percent, row - .14 + offsets,
                       s=28, color=COLORS[pathway], edgecolors="#454545",
                       linewidths=.4, alpha=.88, zorder=3)
    legend = fig.legend(handles=[
        Line2D([], [], marker="o", linestyle="none", markersize=3,
               markerfacecolor="#a9a9a9", markeredgecolor="none",
               label="Individual comparisons (light)"),
        Line2D([], [], marker="o", linestyle="none", markersize=5,
               markerfacecolor="#666666", markeredgecolor="#454545",
               label="Independent trial summaries (dark)"),
    ], loc="lower center", bbox_to_anchor=(.5, .015), ncol=2,
       frameon=False, fontsize=6.5, handletextpad=.4, columnspacing=2)
    fig.canvas.draw()
    require_matplotlib_panel_alignment(
        fig, json_out=str(out / "fig2_trial_response.alignment.json"),
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
        require_panel_labels=False,
    )
    full = out / "fig2_trial_response"
    fig.savefig(full.with_suffix(".pdf"))
    fig.savefig(full.with_suffix(".svg"))
    fig.savefig(full.with_suffix(".png"), dpi=600)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [ax.get_tightbbox(renderer) for ax in axes.flat]
    left_right = max(boxes[0].x1, boxes[2].x1)
    right_left = min(boxes[1].x0, boxes[3].x0)
    lower_high = max(boxes[2].y1, boxes[3].y1)
    upper_low = min(boxes[0].y0, boxes[1].y0)
    if not (left_right < right_left and lower_high < upper_low):
        raise ValueError("No safe 2×2 cut gutters for standalone panels")
    x_cut = (left_right + right_left) / 2
    y_cut = (lower_high + upper_low) / 2
    width, height = fig.bbox.width, fig.bbox.height
    (out / "panel_slots.json").write_text(json.dumps({
        "x_cut_fraction": x_cut / width,
        "y_cut_fraction": y_cut / height,
        "left_width_mm": x_cut / width * 183,
        "right_width_mm": (1 - x_cut / width) * 183,
        "top_height_mm": (1 - y_cut / height) * 132,
        "bottom_height_mm": y_cut / height * 132,
    }, indent=2), encoding="utf-8")
    legend.set_visible(False)
    for index, endpoint in enumerate(ENDPOINTS):
        left = 0 if index % 2 == 0 else x_cut
        right = x_cut if index % 2 == 0 else width
        bottom = y_cut if index < 2 else 0
        top = height if index < 2 else y_cut
        box = Bbox.from_extents(left, bottom, right, top).transformed(
            fig.dpi_scale_trans.inverted())
        for j, ax in enumerate(axes.flat):
            ax.set_visible(j == index)
        base = out / endpoint
        fig.savefig(base.with_suffix(".pdf"), bbox_inches=box, pad_inches=0)
        fig.savefig(base.with_suffix(".svg"), bbox_inches=box, pad_inches=0)
        fig.savefig(base.with_suffix(".png"), dpi=600, bbox_inches=box, pad_inches=0)
    plt.close(fig)
    for svg in out.glob("*.svg"):
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
                       encoding="utf-8")
    trial.to_csv(out / "fig2_trial_source.csv", index=False)
    summary.to_csv(out / "fig2_cell_summary.csv", index=False)
    effects.to_csv(out / "fig2_effect_source.csv", index=False)
    def source_name(path: Path) -> str:
        try:
            return path.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            return path.name
    (out / "render_manifest.json").write_text(json.dumps({
        "trial_source": source_name(source),
        "trial_input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "effect_source": source_name(effect_source),
        "effect_input_sha256": hashlib.sha256(effect_source.read_bytes()).hexdigest(),
        "effect_records_plotted": len(effects),
        "trial_pathway_endpoint_summaries_plotted": len(trial),
        "independent_trial_keys": int(trial.study_id.nunique()),
        "unit": "light: every eligible comparison; dark: one independent study_id per pathway and endpoint, crop units averaged within trial",
        "analysis": "descriptive points only; no pooled effects, confidence intervals or significance tests",
        "endpoint_boundary": "CH4 and N2O are soil emissions; open-burning pulse and full life-cycle emissions excluded",
        "panel_order": ENDPOINTS,
        "pathway_colors": COLORS,
        "axes_are_endpoint_specific": True,
        "CH4_axis": "symmetric logarithmic above absolute 50%; all raw effect values visible",
        "full_size_mm": [183, 132],
        "split_layout": "panel_slots.json",
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=INPUT)
    parser.add_argument("--effect-source", type=Path, default=EFFECT_INPUT)
    parser.add_argument("--out", type=Path, default=OUTPUT)
    parser.add_argument("--qa-scripts", type=Path, required=True)
    args = parser.parse_args()
    frame, cell, effects = prepare(args.source, args.effect_source)
    plot(frame, cell, effects, args.out, args.qa_scripts, args.source,
         args.effect_source)
