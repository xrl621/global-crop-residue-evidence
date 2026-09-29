"""Integrated main-text Fig 2: paired yield–SOC response landscape.

The two marginal density strips are aligned views of the same title-level
pairs, not additional inferential panels. All statistics remain descriptive.
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
from scipy.stats import fisher_exact, gaussian_kde, spearmanr


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/manuscript_fig2_joint_20260929/paper_global.csv"
OUT = ROOT / "figures/manuscript_fig2_joint_density_20260929"
PALETTE = {"yield": "#e16db7", "soc": "#5394c3", "points": "#908ebc",
           "quadrant": "#f4cee1", "contour": "#b099b5", "zero": "#7b7780"}
XLIM = (-45.0, 90.0)
YLIM = (-20.0, 65.0)


def load(source: Path) -> pd.DataFrame:
    paper = pd.read_csv(source)
    required = {"Title", "yield_lnrr", "soc_lnrr"}
    if required - set(paper.columns):
        raise ValueError(f"Missing fields: {sorted(required - set(paper.columns))}")
    if len(paper) != 215 or paper.Title.nunique() != 215:
        raise ValueError("The expected 215 distinct source titles are not present")
    if not np.isfinite(paper[["yield_lnrr", "soc_lnrr"]]).all().all():
        raise ValueError("Non-finite paired log response ratios")
    paper["yield_pct"] = 100 * np.expm1(paper.yield_lnrr)
    paper["soc_pct"] = 100 * np.expm1(paper.soc_lnrr)
    paper["visible"] = (paper.yield_pct.between(*XLIM) &
                        paper.soc_pct.between(*YLIM))
    if int(paper.visible.sum()) != 213:
        raise ValueError("The documented plotting window no longer contains 213 pairs")
    if int((paper.yield_lnrr.gt(0) & paper.soc_lnrr.gt(0)).sum()) != 172:
        raise ValueError("The documented joint direction count changed")
    return paper


def style_axes(ax, top, right):
    ax.set_facecolor("white")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_linewidth(.7)
    ax.tick_params(labelsize=7, width=.6, length=3, pad=3)
    if top:
        ax.spines[["left", "bottom", "top", "right"]].set_visible(False)
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    if right:
        ax.spines[["left", "bottom", "top", "right"]].set_visible(False)
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)


def plot(source: Path, out: Path, qa_scripts: Path) -> None:
    sys.path.insert(0, str(qa_scripts))
    from audit_panel_alignment import require_matplotlib_panel_alignment

    paper = load(source)
    shown = paper.loc[paper.visible]
    x, y = shown.yield_pct.to_numpy(), shown.soc_pct.to_numpy()
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 7.5, "axes.labelsize": 8, "xtick.labelsize": 7,
        "ytick.labelsize": 7, "axes.linewidth": .7,
        "svg.fonttype": "none", "pdf.fonttype": 42,
        "savefig.facecolor": "white",
    })
    fig = plt.figure(figsize=(183 / 25.4, 140 / 25.4), facecolor="white")
    gs = fig.add_gridspec(2, 2, left=.14, right=.90, bottom=.15, top=.93,
                          width_ratios=[5.4, 1], height_ratios=[1, 5.4],
                          wspace=.035, hspace=.035)
    marginal_x = fig.add_subplot(gs[0, 0])
    main = fig.add_subplot(gs[1, 0], sharex=marginal_x)
    marginal_y = fig.add_subplot(gs[1, 1], sharey=main)
    for ax, top, right in ((main, False, False),
                           (marginal_x, True, False),
                           (marginal_y, False, True)):
        style_axes(ax, top, right)

    main.set_xlim(*XLIM)
    main.set_ylim(*YLIM)
    main.set_xticks([-40, 0, 40, 80])
    main.set_yticks([-20, 0, 20, 40, 60])
    main.set_xlabel("Yield change vs removal (%)", labelpad=5)
    main.set_ylabel("Topsoil SOC stock change vs removal (%)", labelpad=6)
    main.add_patch(Rectangle((0, 0), XLIM[1], YLIM[1],
                             facecolor=PALETTE["quadrant"], alpha=.24,
                             edgecolor="none", zorder=0))
    main.axhline(0, color=PALETTE["zero"], linewidth=.8, zorder=2)
    main.axvline(0, color=PALETTE["zero"], linewidth=.8, zorder=2)

    # Restrained kernel contours show where titles concentrate; contour levels
    # are visual density thresholds, not confidence or prediction regions.
    density = gaussian_kde(np.vstack([x, y]))
    xx, yy = np.meshgrid(np.linspace(*XLIM, 220), np.linspace(*YLIM, 220))
    zz = density(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
    point_density = density(np.vstack([x, y]))
    levels = np.unique(np.quantile(point_density, [.15, .4, .68]))
    if len(levels) != 3 or not np.all(np.diff(levels) > 0):
        raise ValueError("KDE contour thresholds are not strictly ordered")
    main.contour(xx, yy, zz, levels=levels, colors=[PALETTE["contour"]] * 3,
                 linewidths=[.8, 1.0, 1.2], alpha=.75, zorder=1)
    main.scatter(x, y, s=14, facecolor=PALETTE["points"], edgecolor="white",
                 linewidth=.25, alpha=.67, zorder=3, rasterized=False)

    x_grid = np.linspace(*XLIM, 500)
    x_density = gaussian_kde(x)(x_grid)
    x_density /= x_density.max()
    marginal_x.fill_between(x_grid, 0, x_density, color=PALETTE["yield"],
                            alpha=.62, linewidth=0)
    marginal_x.plot(x_grid, x_density, color=PALETTE["yield"], linewidth=1.2)
    marginal_x.axvline(float(paper.yield_pct.median()), color=PALETTE["yield"],
                       linewidth=.9, linestyle="--")
    marginal_x.set_ylim(0, 1.08)
    marginal_x.set_xlim(*XLIM)

    y_grid = np.linspace(*YLIM, 500)
    y_density = gaussian_kde(y)(y_grid)
    y_density /= y_density.max()
    marginal_y.fill_betweenx(y_grid, 0, y_density, color=PALETTE["soc"],
                             alpha=.62, linewidth=0)
    marginal_y.plot(y_density, y_grid, color=PALETTE["soc"], linewidth=1.2)
    marginal_y.axhline(float(paper.soc_pct.median()), color=PALETTE["soc"],
                       linewidth=.9, linestyle="--")
    marginal_y.set_xlim(0, 1.08)
    marginal_y.set_ylim(*YLIM)

    fig.canvas.draw()
    # One integrated joint plot: marginal strips are subordinate inset views,
    # not comparable scientific panels. Their matched data-rectangle edges are
    # independently checked below; the panel auditor records N/A for the hero.
    require_matplotlib_panel_alignment(
        fig, json_out=str(out / "fig2_density.alignment.json"),
        exclude_axes=[marginal_x, marginal_y], strict=True,
        require_panel_labels=False)
    p_main, p_x, p_y = (a.get_position().bounds for a in
                        (main, marginal_x, marginal_y))
    eps = 1e-10
    if abs(p_main[0] - p_x[0]) > eps or abs(p_main[2] - p_x[2]) > eps:
        raise ValueError("Yield marginal does not share hero horizontal geometry")
    if abs(p_main[1] - p_y[1]) > eps or abs(p_main[3] - p_y[3]) > eps:
        raise ValueError("SOC marginal does not share hero vertical geometry")
    (out / "marginal_geometry.json").write_text(json.dumps({
        "hero_bbox_fraction": p_main, "yield_marginal_bbox_fraction": p_x,
        "soc_marginal_bbox_fraction": p_y,
        "alignment": "exact shared edges; marginal strips intentionally excluded from comparative-panel audit",
    }, indent=2), encoding="utf-8")
    base = out / "fig2_joint_density"
    fig.savefig(base.with_suffix(".pdf"))
    fig.savefig(base.with_suffix(".svg"))
    fig.savefig(base.with_suffix(".png"), dpi=600)
    renderer = fig.canvas.get_renderer()
    main_box, top_box, right_box = (a.get_tightbbox(renderer) for a in
                                     (main, marginal_x, marginal_y))
    x_gap_start = max(main_box.x1, top_box.x1)
    y_gap_start = max(main_box.y1, right_box.y1)
    if not (x_gap_start < right_box.x0 and y_gap_start < top_box.y0):
        raise ValueError("Integrated figure lacks safe cut gutters")
    x_cut = (x_gap_start + right_box.x0) / 2
    y_cut = (y_gap_start + top_box.y0) / 2
    fw, fh = fig.bbox.width, fig.bbox.height
    slots = {
        "paired_scatter": Bbox.from_extents(0, 0, x_cut, y_cut),
        "yield_marginal": Bbox.from_extents(0, y_cut, x_cut, fh),
        "soc_marginal": Bbox.from_extents(x_cut, 0, fw, y_cut),
    }
    (out / "panel_slots.json").write_text(json.dumps({
        "full_canvas_mm": [183, 140],
        "left_width_mm": x_cut / fw * 183,
        "right_width_mm": (1 - x_cut / fw) * 183,
        "top_height_mm": (1 - y_cut / fh) * 140,
        "bottom_height_mm": y_cut / fh * 140,
        "horizontal_gutter_pt": (right_box.x0 - x_gap_start) * 72 / fig.dpi,
        "vertical_gutter_pt": (top_box.y0 - y_gap_start) * 72 / fig.dpi,
    }, indent=2), encoding="utf-8")
    parts = (main, marginal_x, marginal_y)
    for index, (name, box) in enumerate(slots.items()):
        for part_index, ax in enumerate(parts):
            ax.set_visible(index == part_index)
        inches = box.transformed(fig.dpi_scale_trans.inverted())
        part_base = out / name
        fig.savefig(part_base.with_suffix(".pdf"), bbox_inches=inches, pad_inches=0)
        fig.savefig(part_base.with_suffix(".svg"), bbox_inches=inches, pad_inches=0)
        fig.savefig(part_base.with_suffix(".png"), dpi=600,
                    bbox_inches=inches, pad_inches=0)
    plt.close(fig)
    for svg in out.glob("*.svg"):
        svg.write_text("\n".join(line.rstrip() for line in
                                  svg.read_text(encoding="utf-8").splitlines()) + "\n",
                       encoding="utf-8")

    source_frame = paper[["Title", "yield_lnrr", "soc_lnrr", "yield_pct",
                          "soc_pct", "visible"]].copy()
    source_frame.to_csv(out / "fig2_joint_density_source.csv", index=False)
    pos_y, pos_s = paper.yield_lnrr.gt(0), paper.soc_lnrr.gt(0)
    cells = [[int((pos_y & pos_s).sum()), int((pos_y & ~pos_s).sum())],
             [int((~pos_y & pos_s).sum()), int((~pos_y & ~pos_s).sum())]]
    odds, fisher_p = fisher_exact(cells)
    rho, spearman_p = spearmanr(paper.yield_lnrr, paper.soc_lnrr)
    (out / "render_manifest.json").write_text(json.dumps({
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_titles": len(paper), "titles_visible": len(shown),
        "out_of_window_titles": int((~paper.visible).sum()),
        "quadrant_counts": cells, "yield_median_percent": float(paper.yield_pct.median()),
        "soc_median_percent": float(paper.soc_pct.median()),
        "spearman_rho": float(rho), "spearman_p_descriptive": float(spearman_p),
        "fisher_sign_odds_ratio": float(odds), "fisher_p_descriptive": float(fisher_p),
        "source_level": "secondary compilation, paper-title balanced; not independent field-trial meta-analysis",
        "kde_role": "descriptive visual smoothing only; no uncertainty or causal interpretation",
        "palette": PALETTE, "canvas_mm": [183, 140],
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--qa-scripts", type=Path, required=True)
    args = parser.parse_args()
    plot(args.source, args.out, args.qa_scripts)
