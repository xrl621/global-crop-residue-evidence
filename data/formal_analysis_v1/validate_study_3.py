"""Manual full-text validation for Li2024SD StudyID 3 (Zhang et al. 2010)."""
from pathlib import Path
import json
import math
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'data/enrichment/outputs/analysis_ready_v1/tiered_effects_for_exploratory_analysis.csv'
OUT=ROOT/'data/formal_analysis_v1/outputs/validated_staging/study_3'
OUT.mkdir(parents=True,exist_ok=True)

# Zhang et al. 2010, Table 1 (SOC) and Table 3 (yield, CH4-C, N2O-N):
# mean ± SD, n=3. These are the no-N, C1N0/C2N0 vs C0N0 contrasts.
PRIMARY_TABLE = {
    ('yield', 10.0): ('Table 3', 'Mg grain ha-1', 8.6, 0.38, 9.6, 0.19),
    ('yield', 40.0): ('Table 3', 'Mg grain ha-1', 8.6, 0.38, 9.8, 0.26),
    ('SOC', 10.0): ('Table 1', 'g SOC kg-1 soil, 0-15 cm', 23.5, 1.7, 25.9, 2.1),
    ('SOC', 40.0): ('Table 1', 'g SOC kg-1 soil, 0-15 cm', 23.5, 1.7, 36.9, 2.0),
    ('CH4', 10.0): ('Table 3', 'kg CH4-C ha-1 growing season-1', 62.6, 1.8, 103.2, 2.0),
    ('CH4', 40.0): ('Table 3', 'kg CH4-C ha-1 growing season-1', 62.6, 1.8, 104.9, 10.4),
    ('N2O', 10.0): ('Table 3', 'kg N2O-N ha-1 growing season-1', 0.76, 0.07, 0.55, 0.06),
    ('N2O', 40.0): ('Table 3', 'kg N2O-N ha-1 growing season-1', 0.76, 0.07, 0.60, 0.07),
}

def main():
    d=pd.read_csv(SRC,low_memory=False)
    x=d[d.independent_study_key.eq('biochar_li2024SD_3')].copy()
    if len(x) != len(PRIMARY_TABLE):
        raise ValueError('unexpected number of Study 3 contrasts')
    x['secondary_analysis_tier'] = x['analysis_tier']
    for idx, row in x.iterrows():
        key = (row.analysis_outcome, float(row.BiocharAddition))
        locator, unit, cm, cs, tm, ts = PRIMARY_TABLE[key]
        for field, expected in {'control_mean':cm, 'control_sd':cs,
                                'treatment_mean':tm, 'treatment_sd':ts}.items():
            if not math.isclose(float(row[field]), expected, abs_tol=1e-9):
                raise ValueError(f'{row.effect_id}: {field} does not match primary {locator}')
        x.at[idx,'primary_table_locator'] = locator
        x.at[idx,'unit'] = unit
        x.at[idx,'published_uncertainty_type'] = 'SD'
        x.at[idx,'analysis_tier'] = 'A_primary_exact_table_mean_SD'
        x.at[idx,'tier_reconciliation'] = 'primary_tables_verified_2026-09-23'
        x.at[idx,'variance_provenance'] = f'primary {locator} mean ± SD, n=3; delta-method lnRR variance'
        x.at[idx,'data_extraction_method'] = 'primary numeric table cross-check'
        x.at[idx,'analysis_lnRR'] = math.log(tm/cm)
        x.at[idx,'analysis_variance'] = ts**2/(3*tm**2) + cs**2/(3*cm**2)
    x['formal_decision']='ADMIT_WITH_SHARED_CONTROL'
    x['primary_paper_doi']='10.1016/j.agee.2010.09.003'
    x['primary_paper_pdf']='data/new_papers/zhang2010AGEE.pdf'
    x['field_setting_verified']=True
    x['field_setting_detail']='randomized complete block paddy field; 4 m x 5 m plots; three replicates'
    x['crop_verified']='rice';x['experiment_year']=2009
    x['biochar_feedstock_verified']='wheat straw'
    x['water_regime_verified_manual']='conventional flooding-drainage-reflooding-intermittent irrigation'
    x['nitrogen_context']='N0; contrasts extracted within no-N stratum'
    x['control_arm']='C0N0';x['treatment_arm']=x.BiocharAddition.map({10.0:'C1N0',40.0:'C2N0'})
    x['shared_control_group']='study3_2009_'+x.analysis_outcome.astype(str)+'_C0N0'
    x['uncertainty_verified']='article Table 3 reports mean ± SD, n=3 for yield/CH4/N2O; Table 1 reports SOC mean ± spread used by source'
    x['independence_resolution']='10 and 40 t ha-1 contrasts share C0N0 within outcome; retain covariance/cluster structure'
    x['reviewed_against_fulltext']=True;x['review_date']='2026-09-21'
    x.to_csv(OUT/'study_3_formal_admitted_staging.csv',index=False,encoding='utf-8-sig')
    manifest={'study_key':'biochar_li2024SD_3','doi':'10.1016/j.agee.2010.09.003','reviewed_records':len(x),
              'admitted_records':len(x),'excluded_records':0,'independent_experiments_years':1,
              'admission_scope':'biochar dose effects within the no-N stratum; shared control retained','formal_model_ready_alone':False}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
