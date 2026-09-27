"""Reviewed 2026-09-27 extraction batch; repeated years never become new trials.

Table values below are primary-source transcriptions, not secondary meta-effects.
Dong Figure 7 is recovered from PDF vector geometry with an exact-file checksum.
The committed arm CSV permits re-export without redistributing copyrighted PDFs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "literature/primary_extractions"
DONG_HASH = "0b35227a98da0815780ccb69698f33169f8ed59c75fb900c458c74b256535801"
YANG = "biochar_li2024SD_176"
SUN = "sun_zhuanghang_2012_2016"
DONG = "dong_harbin_2015_2017"


def save_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def digitize_dong(path):
    import fitz
    if hashlib.sha256(path.read_bytes()).hexdigest() != DONG_HASH:
        raise ValueError("Unreviewed Dong PDF version; re-audit geometry before extraction")
    with fitz.open(path) as pdf:
        page = pdf[8]
        text = page.get_text()
        if not all(x in text for x in ["Figure 7", "means ± SE (n = 3)", "2015", "2017"]):
            raise ValueError("Figure caption signature changed")
        drawings = page.get_drawings()
    axis = drawings[120]["rect"]
    yzero, ytwelve = axis.y1, axis.y0
    scale = 12 / (yzero - ytwelve)
    bars = [(i, d["rect"]) for i, d in enumerate(drawings)
            if d["type"] == "s" and len(d["items"]) == 1
            and d["items"][0][0] == "re" and 6.7 < d["rect"].width < 6.9
            and abs(d["rect"].y1 - yzero) < .001]
    errors = [(i, d["rect"]) for i, d in enumerate(drawings)
              if d["type"] == "f" and len(d["items"]) == 10
              and d["fill"] == (0., 0., 0.) and 3.99 < d["rect"].width < 4.01]
    if len(bars) != 24 or len(errors) != 24:
        raise ValueError("Expected 24 unique bars and 24 complete error bars")
    rows = []
    arms = [f"N{n}C{c}" for n in [1, 2] for c in range(4)]
    for j, (index, bar) in enumerate(sorted(bars, key=lambda x: x[1].x0)):
        center = (bar.x0 + bar.x1) / 2
        matches = [(i, e) for i, e in errors if abs((e.x0 + e.x1)/2-center) < .01]
        if len(matches) != 1:
            raise ValueError("Nonunique error-bar alignment")
        err_index, err = matches[0]
        if abs((err.y0+err.y1)/2-bar.y0) > .01:
            raise ValueError("Asymmetric or misplaced error bar")
        rows.append(dict(year=2015+j//8, arm=arms[j % 8],
                         mean=(yzero-bar.y0)*scale, se=err.height/2*scale, n=3,
                         unit="t grain ha-1", source_page=9, source_figure="Figure 7",
                         bar_drawing=index, error_drawing=err_index, x_center=center,
                         bar_top=bar.y0, error_top=err.y0, error_bottom=err.y1,
                         axis_y0=yzero, axis_y12=ytwelve,
                         source_sha256=DONG_HASH,
                         precision_note="vector-derived approximation; not reported numeric table precision"))
    return rows


def repair_yang(rows):
    """Backfill only source-verified numeric arms; keep unresolved SOC held."""
    signatures = {
        ("2016", "CB_20t_CI"): {"yield": (8.07, 7.38), "CH4": (53.1, 75.6), "N2O": (8.67, 5.24)},
        ("2016", "CC_40t_CI"): {"yield": (8.55, 7.38), "CH4": (70.8, 75.6), "N2O": (4.63, 5.24)},
        ("2017", "CB_20t_CI"): {"yield": (6.66, 5.37), "CH4": (108, 154), "N2O": (1.86, 4.43)},
        ("2017", "CC_40t_CI"): {"yield": (7.32, 5.37), "CH4": (130, 154), "N2O": (2.52, 4.43)},
    }
    ids = {"01259": ("2016", "CB_20t_CI"), "01260": ("2016", "CC_40t_CI"),
           "01262": ("2017", "CB_20t_CI"), "01263": ("2017", "CC_40t_CI")}
    repaired = 0
    for row in rows:
        if row["study_id"] != YANG:
            continue
        # The published latitude is malformed (34 degrees 63 minutes); do not
        # preserve the previous spurious decimal conversion as a measured site.
        row["latitude"] = row["longitude"] = ""
        row["quality_flags"] = ";".join(filter(None, [row["quality_flags"], "source_coordinates_malformed", "outdoor_lysimeter"]))
        if row["outcome"] == "SOC":
            continue
        key = ids[row["effect_id"].split("_")[3]]
        expected = signatures[key][row["outcome"]]
        if (row["paper_doi"] != "10.1016/j.atmosenv.2018.12.003"
                or row["control_arm"] != "CA_0t_CI" or row["experiment_year"] != key[0]
                or (float(row["treatment_mean"]), float(row["control_mean"])) != expected
                or row["variance_origin_status"] != "documented_or_reconstructed"):
            raise ValueError("Yang primary-table signature changed")
        row.update(treatment_arm=key[1], crop_as_reported="rice", crop_core="rice",
                   citation="Yang et al. 2019", publication_year="2019",
                   location="Kunshan Experimental Station, Jiangsu; 5 m2 outdoor lysimeter",
                   season="single rice season", water_regime="controlled irrigation",
                   nitrogen_rate="273" if key[0] == "2016" else "293.2",
                   sensitivity_note="Outdoor lysimeter; report a field-only sensitivity. Shared CA and repeated years are dependent; source coordinates malformed.")
        row["quality_flags"] += ";primary_table_metadata_backfilled"
        repaired += 1
    if repaired != 12:
        raise ValueError(f"Expected 12 Yang metadata repairs, got {repaired}")


def effect(template, outcome, unit, tm, cm, te, ce, error="SE", **metadata):
    row = dict(template)
    row.update(metadata)
    if min(tm, cm) <= 0 or min(te, ce) < 0 or error not in {"SD", "SE"}:
        raise ValueError("Invalid primary uncertainty")
    tsd, csd = (te, ce) if error == "SD" else (te*math.sqrt(3), ce*math.sqrt(3))
    lnrr = math.log(tm/cm)
    variance = (tsd/tm)**2/3 + (csd/cm)**2/3
    row.update(outcome=outcome, outcome_unit=unit, treatment_mean=tm, control_mean=cm,
               treatment_sd=tsd, control_sd=csd, treatment_n=3, control_n=3,
               lnrr=lnrr, variance_lnrr=variance, percent_change=100*math.expm1(lnrr),
               variance_provenance=f"primary {row['source_locator']} mean +/- {error}, n=3; SD=SE*sqrt(3) when SE; zero arm covariance for delta variance",
               analysis_tier=f"A_primary_table_{error}", source_analysis_tier="primary_direct_transcription",
               variance_origin_status="documented_or_reconstructed", extraction_method="numeric table transcription")
    flags = list(filter(None, row["quality_flags"].split(";")))
    if min(te, ce) == 0:
        flags.append("rounded_zero_standard_error")
    if max(tsd/tm, csd/cm)/math.sqrt(3) > .5:
        flags.append("large_relative_se_lnrr_delta_approx")
    row["quality_flags"] = ";".join(flags)
    return row


def additions(base):
    rows = []
    blank = {k: "" for k in base[0]}
    sun = dict(blank, study_id=SUN, paper_doi="10.1016/j.fcr.2020.107814",
               source_url="https://doi.org/10.1016/j.fcr.2020.107814",
               paper_title="Effects of controlled-release fertilizer on rice grain yield, nitrogen use efficiency, and greenhouse gas emissions in a paddy field with straw incorporation",
               citation="Sun et al. 2020", publication_year="2020", country="China",
               location="Zhuanghang Experimental Station, Shanghai", latitude="30.883333", longitude="121.383333",
               crop_core="rice", crop_as_reported="rice (Huayou 14)", season="single rice season",
               residue_as_reported="wheat straw; 3 t ha-1 incorporated to about 15 cm",
               pathway="direct_return", treatment_arm="CF+WS", control_arm="CF",
               water_regime="irrigation with mid-season and pre-harvest drainage", nitrogen_rate="225",
               formal_decision="ADMIT_SAME_FERTILIZER_CFWS_VS_CF; STRICT_SCREEN_FLAGS_APPLY",
               independence_resolution="One fixed-plot trial, three replicate plots per treatment, repeated 2012-2016; not five trials",
               sensitivity_note="Printed rounded means retained, including zero reported SE; 2016 gas sampling less frequent. CRU+WS and unfertilized C contrasts excluded as co-interventions.")
    # Order: year, control mean, control SE, treatment mean, treatment SE.
    tables = {
        "yield": ("Table 1, PDF p. 3", "t grain ha-1 (14.5% moisture)",
                  [(2012,8.9,0.,8.9,.1),(2013,9.5,.1,9.2,.1),(2014,10.,0.,10.2,.1),(2015,9.6,.3,10.,.1),(2016,7.1,.1,7.8,.2)]),
        "CH4": ("Table 3, PDF p. 4", "kg CH4 ha-1 per rice season",
                [(2013,127.1,29.7,335.2,66.6),(2014,32.3,8.6,150.,23.1),(2015,69.,35.3,208.1,72.1),(2016,22.2,1.8,96.6,2.5)]),
        "N2O": ("Table 5, PDF p. 5", "kg N2O ha-1 per rice season",
                [(2013,.19,.21,.17,.15),(2014,2.59,1.77,1.87,.61),(2015,.43,.56,1.53,.30),(2016,1.04,.63,.63,.64)]),
        "GHGI": ("Table 7, PDF p. 6", "kg CO2-eq t-1 grain",
                 [(2013,382.9,84.7,1016.8,191.2),(2014,159.8,60.,459.5,44.8),(2015,212.1,85.4,631.5,214.3),(2016,124.8,25.,368.4,23.7)]),
    }
    for outcome, (locator, unit, values) in tables.items():
        for year, cm, ce, tm, te in values:
            rows.append(effect(sun, outcome, unit, tm, cm, te, ce,
                               effect_id=f"sun2020_{year}_{outcome}_CFWS_vs_CF", experiment_year=str(year),
                               source_locator=locator, shared_control_group=f"sun2020_{year}_CF_{outcome}",
                               system_boundary="soil growing-season CH4+N2O per grain yield; excludes upstream and SOC" if outcome=="GHGI" else "",
                               gwp_version="AR5 CH4=28 N2O=265" if outcome=="GHGI" else ""))
    # Add only missing GWP/GHGI. Existing yield/gas rows are repaired, not duplicated.
    for year, c in [("2016", [(3.51,.43),(.48,.05)]), ("2017", [(5.49,.39),(1.03,.04)])]:
        for arm, values in (("CB_20t_CI", [(3.78,.33),(.47,.01)] if year=="2016" else [(3.53,.25),(.53,.02)]),
                            ("CC_40t_CI", [(3.21,.43),(.38,.04)] if year=="2016" else [(4.31,.31),(.59,.03)])):
            template = next(r for r in base if r["study_id"]==YANG and r["outcome"]=="yield"
                            and r["experiment_year"]==year and r["treatment_arm"]==arm)
            for i, outcome in enumerate(["GWP", "GHGI"]):
                rows.append(effect(template, outcome, "t CO2-eq ha-1" if i==0 else "t CO2-eq t-1 grain",
                                   *[values[i][0], c[i][0], values[i][1], c[i][1]], error="SD",
                                   effect_id=f"yang2019_{year}_{arm}_{outcome}", source_locator="Table 3, PDF p. 6",
                                   shared_control_group=f"176_{1 if year=='2016' else 2}_{outcome}_CA",
                                   tier_reconciliation="", source_url="https://doi.org/10.1016/j.atmosenv.2018.12.003",
                                   system_boundary="soil rice-season CH4+N2O only; excludes production, transport, SOC sequestration",
                                   gwp_version="AR5 CH4=28 N2O=265"))
    with (OUT / "dong2024_figure7_vector_arms.csv").open(encoding="utf-8", newline="") as stream:
        arms = {(r["year"], r["arm"]): r for r in csv.DictReader(stream)}
    if len(arms) != 24 or any(r["source_sha256"] != DONG_HASH for r in arms.values()):
        raise ValueError("Invalid digitized arm provenance")
    for (year, arm), treatment in sorted(arms.items()):
        if arm.endswith("C0"):
            continue
        control_arm = arm[:2]+"C0"
        control = arms[year, control_arm]
        template = next(r for r in base if r["study_id"]==DONG and r["outcome"]=="CH4"
                        and r["experiment_year"]==year and r["treatment_arm"]==arm)
        r = effect(template, "yield", "t grain ha-1", float(treatment["mean"]), float(control["mean"]),
                   float(treatment["se"]), float(control["se"]),
                   effect_id=f"dong_2024_yield_{year}_{arm}_vs_{control_arm}", source_locator="Figure 7, PDF p. 9",
                   shared_control_group=f"dong_2024_{year}_{control_arm}_yield")
        r.update(analysis_tier="B_primary_vector_figure_SE", source_analysis_tier="primary_vector_digitization",
                 extraction_method="PDF vector bars and complete SE whiskers; verified source checksum and geometry",
                 quality_flags="figure_digitized", source_url="https://doi.org/10.3390/agronomy14123050",
                 sensitivity_note="Approximate vector-derived mean/SE; exclude figure-digitized rows in sensitivity. Three years, two N strata and three doses remain one trial.")
        rows.append(r)
    if len(rows) != 43:
        raise ValueError("Expected 43 genuinely new outcome rows")
    return rows


def mean_only(fields):
    base = {k: "" for k in fields}
    base.update(study_id="somboon_khonkaen_2021", paper_doi="10.1038/s41598-024-59352-5",
                source_url="https://doi.org/10.1038/s41598-024-59352-5", citation="Somboon et al. 2024",
                paper_title="Mitigating methane emissions and global warming potential while increasing rice yield using biochar derived from leftover rice straw in a tropical paddy soil",
                publication_year="2024", experiment_year="2021", country="Thailand",
                location="Ban Non Muang, Sila, Mueang Khon Kaen", crop_core="rice", crop_as_reported="rice (RD6)",
                season="June-November", residue_as_reported="rice straw", control_arm="CF",
                treatment_n=3, control_n=3, analysis_tier="C_primary_mean_only", variance_origin_status="unreported",
                formal_decision="HOLD_FROM_VARIANCE_AND_MAIN_ANALYSIS; ARM_SD_SE_UNREPORTED",
                water_regime="continuous 5-7 cm flooding until one week before harvest", nitrogen_rate="188",
                independence_resolution="One field trial with three randomized blocks; shared CF across pathways and endpoints",
                quality_flags="arm_variance_missing", extraction_method="primary numeric table transcription",
                sensitivity_note="Only table CV percentages reported; do not infer arm SD/SE from CV. GWP includes soil CO2, excludes N2O; incompatible with main GWP boundary.")
    rows = []
    values = [("yield", "t grain ha-1", [6.3,10.6,11.8],1),
              ("CH4", "kg CH4 ha-1 per rice season", [474.8,1041.3,270.9],2),
              ("CO2", "kg CO2 ha-1 per rice season", [22660.4,11773.4,14176.8],2),
              ("GWP_CH4_CO2", "kg CO2-eq ha-1", [35955.1,40928.9,21760.5],2),
              ("GHGI_CH4_CO2", "kg CO2-eq t-1 grain", [5724.3,3823.3,1843.7],2)]
    for outcome, unit, means, table in values:
        for index, pathway, arm in [(1,"direct_return","RS+CF"),(2,"biochar_return","BC+CF")]:
            lnrr = math.log(means[index]/means[0])
            row = dict(base, outcome=outcome, outcome_unit=unit, treatment_mean=means[index], control_mean=means[0],
                       lnrr=lnrr, percent_change=100*math.expm1(lnrr), pathway=pathway, treatment_arm=arm,
                       effect_id=f"somboon2024_2021_{arm}_{outcome}", shared_control_group=f"somboon2024_CF_{outcome}",
                       source_locator=f"Table {table}, PDF p. 4")
            if "GWP" in outcome or "GHGI" in outcome:
                row.update(system_boundary="soil CH4 plus CO2 (including biogenic respiration); N2O excluded; NOT main CH4+N2O GWP",
                           gwp_version="CH4=28; CO2=1")
            rows.append(row)
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--digitize", action="store_true")
    args = parser.parse_args()
    if args.digitize:
        save_csv(OUT / "dong2024_figure7_vector_arms.csv", digitize_dong(ROOT / "data/new_papers/dong2024AGR.pdf"))
    # Freeze all original row keys; exporter applies metadata repairs itself.
    from export_evidence_database import FIELDS
    save_csv(OUT / "somboon2024_mean_only_NOT_IN_MAIN.csv", mean_only(FIELDS))
    print("Source extraction ready. Run export_evidence_database.py for integrated evidence.")
