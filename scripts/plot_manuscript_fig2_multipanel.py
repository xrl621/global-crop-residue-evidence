"""Fig. 2: global paired response and three crop-specific joint-response views.

This is a descriptive visualization of a published secondary compilation.
Small pale points are treatment contrasts; larger coloured points are source
title or crop-by-title summaries. The two layers are never pooled as peers.
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
from scipy.stats import gaussian_kde


ROOT = Path(__file__).resolve().parents[1]
GLOBAL_SOURCE = ROOT / "data/processed/manuscript_fig2_joint_20260929/paper_global.csv"
CROP_SOURCE = ROOT / "data/processed/manuscript_fig2_joint_20260929/paper_crop.csv"
COMPARISON_SOURCE = ROOT / "data/processed/encarnation2026_residue_reanalysis/selected_comparisons.csv"
OUT = ROOT / "figures/manuscript_fig2_multipanel_20260929"
XLIM = (-45.0, 90.0)
YLIM = (-20.0, 65.0)
PALETTE = {
    "global": "#908ebc", "yield": "#e16db7", "soc": "#5394c3",
    "maize": "#e16db7", "rice": "#5394c3", "wheat": "#908ebc",
    "joint": "#f4cee1", "zero": "#77747c", "contour": "#b099b5",
    "comparisons": "#b8a89f",
}


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    paper = pd.read_csv(GLOBAL_SOURCE)
    crop = pd.read_csv(CROP_SOURCE)
    if not COMPARISON_SOURCE.exists():
        raise FileNotFoundError(
            "Local secondary-comparison source is missing; regenerate it from "
            "the cited open compilation before rendering the comparison layer")
    comparison = pd.read_csv(COMPARISON_SOURCE)
    return_paths = {"Incorporated vs removed", "Surface-retained vs removed"}
    comparison = comparison.loc[
        comparison.Pathway.isin(return_paths) &
        comparison.Main_Crop.isin(("Maize", "Rice", "Wheat"))].copy()
    needed_comparison = {"Comparison_ID", "Title", "Main_Crop",
                         "yield_log_ratio", "soc_log_ratio"}
    if not needed_comparison <= set(comparison):
        raise ValueError("Missing comparison source columns")
    if comparison.Comparison_ID.duplicated().any():
        raise ValueError("Comparison IDs are duplicated")
    if len(comparison) != 1151 or comparison.Title.nunique() != 215:
        raise ValueError("Underlying paired comparison count changed")
    if not np.isfinite(comparison[["yield_log_ratio", "soc_log_ratio"]]).all().all():
        raise ValueError("Non-finite comparison log ratios")
    comparison["yield_pct"] = 100 * np.expm1(comparison.yield_log_ratio)
    comparison["soc_pct"] = 100 * np.expm1(comparison.soc_log_ratio)
    comparison["visible"] = (comparison.yield_pct.between(*XLIM) &
                             comparison.soc_pct.between(*YLIM))
    for table, needed in ((paper, {"Title", "yield_lnrr", "soc_lnrr"}),
                          (crop, {"Title", "Main_Crop", "yield_lnrr", "soc_lnrr"})):
        if not needed <= set(table):
            raise ValueError(f"Missing source columns: {sorted(needed - set(table))}")
        if not np.isfinite(table[["yield_lnrr", "soc_lnrr"]]).all().all():
            raise ValueError("Non-finite log response ratio")
        table["yield_pct"] = 100 * np.expm1(table.yield_lnrr)
        table["soc_pct"] = 100 * np.expm1(table.soc_lnrr)
        table["visible"] = (table.yield_pct.between(*XLIM) &
                            table.soc_pct.between(*YLIM))
    if len(paper) != 215 or paper.Title.nunique() != 215:
        raise ValueError("Global title count changed")
    expected = {"Maize": 109, "Rice": 71, "Wheat": 107}
    observed = crop.groupby("Main_Crop").size().to_dict()
    if observed != expected or crop.Title.nunique() != 215:
        raise ValueError(f"Crop-title source changed: {observed}")
    if crop.duplicated(["Main_Crop", "Title"]).any():
        raise ValueError("Crop-title source contains duplicate units")
    if int(comparison.visible.sum()) != 1108:
        raise ValueError("The recorded comparison-level visual window changed")
    # Ensure the faint layer and the paper-level points come from identical
    # source rows, rather than quietly mixing versions of the compilation.
    check_global = comparison.groupby("Title")[["yield_log_ratio", "soc_log_ratio"]].median()
    paper_check = paper.set_index("Title")[["yield_lnrr", "soc_lnrr"]]
    if (not check_global.index.equals(paper_check.index) or
        not np.allclose(check_global.to_numpy(), paper_check.to_numpy(), rtol=0, atol=1e-12)):
        raise ValueError("Global paper points do not match the comparison source")
    check_crop = comparison.groupby(["Main_Crop", "Title"])[["yield_log_ratio", "soc_log_ratio"]].median()
    crop_check = crop.set_index(["Main_Crop", "Title"])[["yield_lnrr", "soc_lnrr"]]
    if (not check_crop.index.equals(crop_check.index) or
        not np.allclose(check_crop.to_numpy(), crop_check.to_numpy(), rtol=0, atol=1e-12)):
        raise ValueError("Crop-paper points do not match the comparison source")
    return paper, crop, comparison


def clean_axis(ax, *, xlabels=True, ylabels=True) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_linewidth(.65)
    ax.tick_params(labelsize=6.7, width=.55, length=2.5, pad=2,
                   labelbottom=xlabels, labelleft=ylabels)
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_xticks([-40, 0, 40, 80])
    ax.set_yticks([-20, 0, 20, 40, 60])
    ax.add_patch(Rectangle((0, 0), XLIM[1], YLIM[1],
                           facecolor=PALETTE["joint"], alpha=.22,
                           edgecolor="none", zorder=0))
    ax.axhline(0, color=PALETTE["zero"], linewidth=.65, zorder=1)
    ax.axvline(0, color=PALETTE["zero"], linewidth=.65, zorder=1)


def point_cloud(ax, frame: pd.DataFrame, comparisons: pd.DataFrame,
                color: str, *, small: bool) -> None:
    raw = comparisons.loc[comparisons.visible]
    ax.scatter(raw.yield_pct, raw.soc_pct, s=6 if small else 9,
               color=PALETTE["comparisons"], alpha=.26 if small else .24,
               linewidths=0, zorder=2)
    shown = frame.loc[frame.visible]
    x, y = shown.yield_pct.to_numpy(), shown.soc_pct.to_numpy()
    density = gaussian_kde(np.vstack([x, y]))
    grid_x, grid_y = np.meshgrid(np.linspace(*XLIM, 180),
                                 np.linspace(*YLIM, 180))
    surface = density(np.vstack([grid_x.ravel(), grid_y.ravel()])).reshape(grid_x.shape)
    at_points = density(np.vstack([x, y]))
    levels = np.unique(np.quantile(at_points, [.30, .62] if small else [.15, .4, .68]))
    if len(levels) >= 2:
        ax.contour(grid_x, grid_y, surface, levels=levels, colors=color,
                   linewidths=[.7] * len(levels), alpha=.8, zorder=2)
    ax.scatter(x, y, s=9 if small else 17, c=color, alpha=.80,
               edgecolors="white", linewidths=.20 if small else .3, zorder=3)
    if small:
        ax.scatter([frame.yield_pct.median()], [frame.soc_pct.median()],
                   marker="D", s=19, facecolor=color, edgecolor="white",
                   linewidth=.5, zorder=4)


def plot(out: Path, qa_scripts: Path) -> None:
    sys.path.insert(0, str(qa_scripts))
    from audit_panel_alignment import require_matplotlib_panel_alignment

    paper, crop, comparison = load_data()
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 7.5, "axes.labelsize": 7.8,
        "svg.fonttype": "none", "pdf.fonttype": 42,
        "savefig.facecolor": "white",
    })
    fig = plt.figure(figsize=(7.204724409448819, 6.102362204724409), facecolor="white")
    main = fig.add_axes([.095, .135, .45, .655])
    top = fig.add_axes([.095, .805, .45, .115], sharex=main)
    right = fig.add_axes([.555, .135, .068, .655], sharey=main)
    crop_axes = [fig.add_axes([.705, y, .265, .235])
                 for y in (.685, .405, .125)]
    clean_axis(main)
    main.set_xlabel("Yield change vs removal (%)", labelpad=4)
    main.set_ylabel("Topsoil SOC stock change vs removal (%)", labelpad=5)
    point_cloud(main, paper, comparison, PALETTE["global"], small=False)

    for ax in (top, right):
        ax.spines[:].set_visible(False)
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    x = paper.loc[paper.visible, "yield_pct"].to_numpy()
    y = paper.loc[paper.visible, "soc_pct"].to_numpy()
    xgrid = np.linspace(*XLIM, 400)
    ygrid = np.linspace(*YLIM, 400)
    xd = gaussian_kde(x)(xgrid); xd /= xd.max()
    yd = gaussian_kde(y)(ygrid); yd /= yd.max()
    top.fill_between(xgrid, 0, xd, color=PALETTE["yield"], alpha=.60, linewidth=0)
    top.plot(xgrid, xd, color=PALETTE["yield"], linewidth=1.05)
    top.axvline(paper.yield_pct.median(), color=PALETTE["yield"],
                linewidth=.85, linestyle="--")
    top.set_xlim(*XLIM); top.set_ylim(0, 1.08)
    right.fill_betweenx(ygrid, 0, yd, color=PALETTE["soc"], alpha=.60, linewidth=0)
    right.plot(yd, ygrid, color=PALETTE["soc"], linewidth=1.05)
    right.axhline(paper.soc_pct.median(), color=PALETTE["soc"],
                  linewidth=.85, linestyle="--")
    right.set_ylim(*YLIM); right.set_xlim(0, 1.08)

    crop_names = ["Maize", "Rice", "Wheat"]
    for ax, name in zip(crop_axes, crop_names):
        sub = crop.loc[crop.Main_Crop.eq(name)]
        clean_axis(ax, xlabels=(name == "Wheat"))
        raw_sub = comparison.loc[comparison.Main_Crop.eq(name)]
        point_cloud(ax, sub, raw_sub, PALETTE[name.lower()], small=True)
        ax.text(0, 1.035, name, transform=ax.transAxes, ha="left", va="bottom",
                fontsize=7.6, weight="normal", color="#242228", clip_on=False)
    crop_axes[-1].set_xlabel("Yield change (%)", labelpad=3)

    fig.canvas.draw()
    # The right column is a comparable three-panel series. Hero marginals are
    # integrated orthogonal views, so their unequal rectangles are exempt.
    require_matplotlib_panel_alignment(
        fig, json_out=str(out / "fig2_multipanel.alignment.json"),
        exclude_axes=[main, top, right],
        panel_ids={axis: name for axis, name in zip(crop_axes, crop_names)},
        column_groups=[crop_names], strict=True,
        require_panel_labels=False)
    hero_box, top_box, right_box = (a.get_position().bounds for a in (main, top, right))
    if (abs(hero_box[0] - top_box[0]) > 1e-10 or
        abs(hero_box[2] - top_box[2]) > 1e-10 or
        abs(hero_box[1] - right_box[1]) > 1e-10 or
        abs(hero_box[3] - right_box[3]) > 1e-10):
        raise ValueError("Hero marginals lost exact edge alignment")
    (out / "hero_marginal_alignment.json").write_text(json.dumps({
        "hero": hero_box, "yield_strip": top_box, "soc_strip": right_box,
        "rule": "exact shared data-area edges; unequal integrated views exempt from comparable-panel audit",
    }, indent=2), encoding="utf-8")

    base = out / "fig2_multipanel"
    fig.savefig(base.with_suffix(".pdf"))
    fig.savefig(base.with_suffix(".svg"))
    fig.savefig(base.with_suffix(".png"), dpi=600)
    fig.savefig(base.with_suffix(".tiff"), dpi=600,
                pil_kwargs={"compression": "tiff_lzw"})

    # Fixed slots retain all content and enable lossless reassembly in a
    # graphics editor. The plot contains no a/b/c letters or overall title.
    slots = {
        "global_joint": (0, 0, .675, 1),
        "maize_joint": (.675, .665, 1, 1),
        "rice_joint": (.675, .385, 1, .665),
        "wheat_joint": (.675, 0, 1, .385),
    }
    (out / "panel_slots.json").write_text(json.dumps({
        "full_canvas_mm": [183, 155],
        "slots_fraction_xyxy": slots,
        "reassembly": "place pieces at their original slot rectangles without trimming transparent/white margins",
    }, indent=2), encoding="utf-8")
    all_axes = [main, top, right, *crop_axes]
    for name, bounds in slots.items():
        selected = [main, top, right] if name == "global_joint" else [
            crop_axes[crop_names.index(name.split("_")[0].capitalize())]]
        for ax in all_axes:
            ax.set_visible(ax in selected)
        x0, y0, x1, y1 = bounds
        box = Bbox.from_extents(x0 * fig.bbox.width, y0 * fig.bbox.height,
                                x1 * fig.bbox.width, y1 * fig.bbox.height)
        inches = box.transformed(fig.dpi_scale_trans.inverted())
        for extension in ("pdf", "svg", "png"):
            fig.savefig((out / name).with_suffix("." + extension),
                        bbox_inches=inches, pad_inches=0,
                        dpi=600 if extension == "png" else None)
    plt.close(fig)
    for svg in out.glob("*.svg"):
        svg.write_text("\n".join(line.rstrip() for line in
                                  svg.read_text(encoding="utf-8").splitlines()) + "\n",
                       encoding="utf-8")

    paper[["Title", "yield_lnrr", "soc_lnrr", "yield_pct", "soc_pct", "visible"]].to_csv(
        out / "global_source.csv", index=False)
    crop[["Main_Crop", "Title", "yield_lnrr", "soc_lnrr", "yield_pct", "soc_pct", "visible"]].to_csv(
        out / "crop_source.csv", index=False)
    by_crop = {}
    for name in crop_names:
        sub = crop.loc[crop.Main_Crop.eq(name)]
        by_crop[name] = {
            "crop_title_units": len(sub), "plotted": int(sub.visible.sum()),
            "both_positive": int(((sub.yield_lnrr > 0) & (sub.soc_lnrr > 0)).sum()),
            "median_yield_pct": float(sub.yield_pct.median()),
            "median_soc_pct": float(sub.soc_pct.median()),
        }
    (out / "render_manifest.json").write_text(json.dumps({
        "global_source_sha256": hashlib.sha256(GLOBAL_SOURCE.read_bytes()).hexdigest(),
        "crop_source_sha256": hashlib.sha256(CROP_SOURCE.read_bytes()).hexdigest(),
        "comparison_source_sha256": hashlib.sha256(COMPARISON_SOURCE.read_bytes()).hexdigest(),
        "comparison_rows": len(comparison),
        "comparison_rows_plotted": int(comparison.visible.sum()),
        "comparison_rows_outside_view": int((~comparison.visible).sum()),
        "global_titles": len(paper), "global_plotted": int(paper.visible.sum()),
        "crop_title_units": len(crop), "unique_titles_across_crops": crop.Title.nunique(),
        "by_crop": by_crop, "palette": PALETTE,
        "interpretation": "descriptive secondary compilation, not trial-level causal/meta estimate",
        "point_layers": {
            "light_small": "paired treatment contrasts; dependent within source titles",
            "colored_large": "title-balanced medians or crop-by-title medians",
        },
        "kde": "visual smoothing of visible points, not uncertainty",
        "out_of_view_rule": "axis window only; all units remain in source and descriptive counts",
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--qa-scripts", type=Path, required=True)
    arguments = parser.parse_args()
    plot(arguments.out, arguments.qa_scripts)
