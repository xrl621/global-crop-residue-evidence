"""Increment, extraction checks and descriptive sensitivity; no pooled inference."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/processed/stage_20260927"


def main():
    old = pd.read_csv(ROOT / "data/processed/stage_20260926/row_audit.csv", keep_default_na=False)
    current = pd.read_csv(OUT / "row_audit.csv", keep_default_na=False)
    eligible = current[current.descriptive_eligible].copy()
    added = current[~current.effect_id.isin(old.effect_id)]
    added.to_csv(OUT / "new_effects.csv", index=False)
    added.groupby(["study_id", "outcome"], as_index=False).agg(
        added_effects=("effect_id", "size"), source_doi=("paper_doi", "first")
    ).to_csv(OUT / "increment_by_source.csv", index=False)
    sensitivity = []
    # Flag scope is explicit: this audit excludes the newly identified Yang
    # lysimeter and Dong digitization, not all historical digitized observations.
    for scenario, data in [
        ("strict_stage", eligible),
        ("without_Dong_vector_yield", eligible[~eligible.effect_id.str.startswith("dong_2024_yield_")]),
        ("without_Yang_outdoor_lysimeter", eligible[eligible.study_id!="biochar_li2024SD_176"]),
    ]:
        for (path, endpoint), group in data.groupby(["pathway", "outcome"]):
            means = group.groupby("study_id").lnrr.mean()
            sensitivity.append(dict(scenario=scenario, pathway=path, outcome=endpoint,
                                    effects=len(group), trials=len(means),
                                    median_trial_response=100*np.expm1(means.median()),
                                    positive_trials=int((means>0).sum()), negative_trials=int((means<0).sum())))
    pd.DataFrame(sensitivity).to_csv(OUT / "descriptive_sensitivity.csv", index=False)
    sun_rows = []
    for label, data in [("all_reported_means_unweighted",current),("strict_stage",eligible)]:
        for endpoint, g in data[data.study_id=="sun_zhuanghang_2012_2016"].groupby("outcome"):
            sun_rows.append(dict(selection=label, outcome=endpoint, effects=len(g), trials=1,
                                 response=100*np.expm1(g.lnrr.mean()),
                                 min_response=100*np.expm1(g.lnrr.min()), max_response=100*np.expm1(g.lnrr.max())))
    pd.DataFrame(sun_rows).to_csv(OUT / "sun_all_mean_vs_strict.csv", index=False)
    # Independent extraction cross-check only. Mean(GWP/yield) need not equal
    # mean(GWP)/mean(yield); discrepancies are queries, not automatically errors.
    arms = pd.read_csv(ROOT / "literature/primary_extractions/dong2024_figure7_vector_arms.csv")
    dong = current[current.study_id=="dong_harbin_2015_2017"]
    checks = []
    for _, arm in arms.iterrows():
        g = dong[dong.experiment_year.astype(str)==str(arm.year)]
        is_control = arm.arm.endswith("C0")
        g = g[g.control_arm==arm.arm] if is_control else g[g.treatment_arm==arm.arm]
        col = "control_mean" if is_control else "treatment_mean"
        gwp = float(g[g.outcome=="GWP"][col].iloc[0])
        ghgi = float(g[g.outcome=="GHGI"][col].iloc[0])
        check = gwp/(1000*ghgi)
        delta = 100*(arm["mean"]/check-1)
        checks.append(dict(year=arm.year, arm=arm.arm, vector_yield_t_ha=arm["mean"],
                           gwp_kg_co2eq_ha=gwp, ghgi_kg_co2eq_kg_grain=ghgi,
                           ratio_of_reported_means_t_ha=check, relative_difference_pct=delta,
                           query_over_5pct=abs(delta)>5,
                           interpretation="QA only; ratio of reported means is not necessarily mean of ratios; no replacement"))
    pd.DataFrame(checks).to_csv(OUT / "dong_cross_endpoint_diagnostic.csv", index=False)
    print(pd.DataFrame(sun_rows).to_string(index=False))
    print(pd.DataFrame(checks).query("query_over_5pct").to_string(index=False))


if __name__ == "__main__":
    main()
