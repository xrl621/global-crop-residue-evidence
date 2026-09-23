"""Manual full-text validation for Li2024SD StudyID 176 (Yang et al. 2019)."""
from pathlib import Path
import json
import math
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'data/enrichment/outputs/analysis_ready_v1/tiered_effects_for_exploratory_analysis.csv'
OUT=ROOT/'data/formal_analysis_v1/outputs/validated_staging/study_176'
OUT.mkdir(parents=True,exist_ok=True)

# Yang et al. 2019, Tables 3 and 4: mean ± SD, n=3. Table 4 yield
# (kg ha-1) is converted to Mg ha-1. Figure 2 SOC is NOT in this map.
PRIMARY_TABLE = {
    ('176_1','yield',20.0): ('Table 4','Mg grain ha-1',7.38,0.137,8.07,0.569),
    ('176_1','yield',40.0): ('Table 4','Mg grain ha-1',7.38,0.137,8.55,0.347),
    ('176_2','yield',20.0): ('Table 4','Mg grain ha-1',5.37,0.584,6.66,0.199),
    ('176_2','yield',40.0): ('Table 4','Mg grain ha-1',5.37,0.584,7.32,0.843),
    ('176_1','CH4',20.0): ('Table 3','kg CH4 ha-1 season-1',75.6,8.43,53.1,7.51),
    ('176_1','CH4',40.0): ('Table 3','kg CH4 ha-1 season-1',75.6,8.43,70.8,10.5),
    ('176_2','CH4',20.0): ('Table 3','kg CH4 ha-1 season-1',154.0,12.0,108.0,7.62),
    ('176_2','CH4',40.0): ('Table 3','kg CH4 ha-1 season-1',154.0,12.0,130.0,9.24),
    ('176_1','N2O',20.0): ('Table 3','kg N2O ha-1 season-1',5.24,0.72,8.67,0.43),
    ('176_1','N2O',40.0): ('Table 3','kg N2O ha-1 season-1',5.24,0.72,4.63,0.50),
    ('176_2','N2O',20.0): ('Table 3','kg N2O ha-1 season-1',4.43,0.22,1.86,0.15),
    ('176_2','N2O',40.0): ('Table 3','kg N2O ha-1 season-1',4.43,0.22,2.52,0.18),
}

def main():
    d=pd.read_csv(SRC,low_memory=False)
    x=d[d.independent_study_key.eq('biochar_li2024SD_176')].copy()
    x['dose_occurrence']=x.groupby(['ExperimentID','analysis_outcome','BiocharAddition'],dropna=False).cumcount()+1
    x['manual_arm_label']='CB_20t_CI'
    x.loc[x.BiocharAddition.eq(40)&x.dose_occurrence.eq(1),'manual_arm_label']='CC_40t_CI'
    x.loc[x.BiocharAddition.eq(40)&x.dose_occurrence.eq(2),'manual_arm_label']='FC_40t_FI'
    x['formal_decision']=x.manual_arm_label.map({'CB_20t_CI':'ADMIT_WITH_SHARED_CONTROL','CC_40t_CI':'ADMIT_WITH_SHARED_CONTROL','FC_40t_FI':'EXCLUDE_COINTERVENTION_WATER_REGIME'})
    x['primary_paper_doi']='10.1016/j.atmosenv.2018.12.003'
    x['primary_paper_pdf']='data/new_papers/xia2014AGEE.pdf'
    x['field_setting_verified']=True
    x['field_setting_detail']='outdoor paddy lysimeter plots, 5 m2, three replicates'
    x['crop_verified']='rice'
    x['biochar_feedstock_verified']='rice straw'
    x['pyrolysis_temperature_C_verified']=600
    x['water_regime_verified_manual']=x.manual_arm_label.str.endswith('_CI').map({True:'controlled irrigation',False:'flooding irrigation'})
    x['control_arm']='CA_0t_CI'
    x['experiment_year']=x.ExperimentID.map({'176_1':2016,'176_2':2017})
    x['shared_control_group']=x.ExperimentID.astype(str)+'_'+x.analysis_outcome.astype(str)+'_CA'
    x['independence_resolution']='two biochar-dose contrasts share CA within each year/outcome; retain covariance/cluster structure'
    x['reviewed_against_fulltext']=True
    x['review_date']='2026-09-21'
    admitted=x[x.formal_decision.eq('ADMIT_WITH_SHARED_CONTROL')].copy()
    if len(admitted) != 14:
        raise ValueError('unexpected number of admitted Study 176 contrasts')
    admitted['secondary_analysis_tier'] = admitted['analysis_tier']
    for idx, row in admitted.iterrows():
        key = (row.ExperimentID, row.analysis_outcome, float(row.BiocharAddition))
        if key not in PRIMARY_TABLE:
            # The two Figure 2 SOC effects are still held at the variance
            # origin gate until row-level digitization is reproducible.
            if row.analysis_outcome != 'SOC':
                raise ValueError(f'unexpected non-SOC contrast {row.effect_id}')
            continue
        locator, unit, cm, cs, tm, ts = PRIMARY_TABLE[key]
        for field, expected in {'control_mean':cm, 'treatment_mean':tm}.items():
            if not math.isclose(float(row[field]), expected, abs_tol=1e-9):
                raise ValueError(f'{row.effect_id}: {field} does not match primary {locator}')
        for field, expected in {'control_sd':cs, 'treatment_sd':ts}.items():
            if not math.isclose(float(row[field]), expected, abs_tol=0.01):
                raise ValueError(f'{row.effect_id}: {field} differs from primary {locator} beyond rounding')
        for field, val in {'control_sd':cs, 'treatment_sd':ts}.items():
            admitted.at[idx,field] = val
        admitted.at[idx,'primary_table_locator'] = locator
        admitted.at[idx,'unit'] = unit
        admitted.at[idx,'published_uncertainty_type'] = 'SD'
        admitted.at[idx,'analysis_tier'] = 'A_primary_exact_table_mean_SD'
        admitted.at[idx,'tier_reconciliation'] = 'primary_tables_verified_2026-09-23'
        admitted.at[idx,'variance_provenance'] = f'primary {locator} mean ± SD, n=3; delta-method lnRR variance'
        admitted.at[idx,'data_extraction_method'] = 'primary numeric table cross-check; Table 4 yield converted kg to Mg'
        admitted.at[idx,'analysis_lnRR'] = math.log(tm/cm)
        admitted.at[idx,'analysis_variance'] = ts**2/(3*tm**2) + cs**2/(3*cm**2)
    for col in admitted.columns:
        if col not in x.columns:
            x[col] = pd.NA
        x.loc[admitted.index,col] = admitted[col]
    x.to_csv(OUT/'study_176_all_reviewed_effects.csv',index=False,encoding='utf-8-sig')
    admitted.to_csv(OUT/'study_176_formal_admitted_staging.csv',index=False,encoding='utf-8-sig')
    excluded=x[~x.formal_decision.eq('ADMIT_WITH_SHARED_CONTROL')].copy()
    excluded.to_csv(OUT/'study_176_excluded_effects.csv',index=False,encoding='utf-8-sig')
    manifest={'study_key':'biochar_li2024SD_176','doi':'10.1016/j.atmosenv.2018.12.003','reviewed_records':len(x),
              'admitted_records':len(admitted),'excluded_records':len(excluded),'independent_experiments_years':2,
              'admission_scope':'biochar dose effect within controlled irrigation only','formal_model_ready_alone':False}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
