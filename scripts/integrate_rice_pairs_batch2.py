"""Reconstruct residue contrasts without trusting non-unique source ES_IDs.

All outputs are secondary candidates, not primary admissions. Missing matching
covariates are explicitly flagged. Multiple arms only pair when doses distinguish
them and the comparator is unique. Existing source files are immutable.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import sqlite3

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/external/figshare_29817482_rice_ghg'
OUT=ROOT/'data/processed/integration_batch2_rice_20260927'
MATCH=['StudyID','ExY','Site','Lat','Long','Sea','FaS','TiM','GrDu','GrD','PlM',
       'WaR','Nitrogen','NiA','Pho','Pot','FirT','CoMa','GsM']
REQUIRED=['StudyID','ExY','Site','Lat','Long','ReM']
NUMERIC_MATCH={'ExY','Nitrogen','Pho','Pot','FirT','GrDu'}
CONTRASTS=[('Incorporated_Straw','Removed','direct_return_vs_removal'),
           ('Onfield_Burned','Removed','burning_vs_removal'),
           ('Incorporated_Straw','Onfield_Burned','direct_return_vs_burning')]
ENDPOINTS={'GY':'yield','CH4':'CH4','N2O':'N2O','GWP':'GWP','GHGI':'GHGI'}


def number(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else np.nan
    except (TypeError,ValueError): return np.nan


def canonical(x,field=''):
    s=str(x).strip()
    if s.lower() in {'','nan','n/a','na','none','null'}: return '<MISSING>'
    if field in NUMERIC_MATCH and math.isfinite(number(s)): return format(number(s),'.12g')
    return s


def uid(prefix,values):
    return prefix+hashlib.sha256(json.dumps(values,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()[:20]


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(d,n): d.to_csv(OUT/(n+'.csv'),index=False,encoding='utf-8-sig')


def coord_valid(s,axis):
    """Validate only; do not silently repair malformed degree/minute strings."""
    s=str(s).strip()
    if math.isfinite(number(s)): return abs(number(s)) <= (90 if axis=='lat' else 180)
    match=re.fullmatch(r'''\s*(\d+(?:\.\d+)?)\s*[°º]\s*(\d+(?:\.\d+)?)\s*['′]\s*(\d+(?:\.\d+)?)\s*["″]\s*([NSEW])\s*''',s,re.I)
    if not match: return False
    deg,minute,sec=map(float,match.groups()[:3]); direction=match.group(4).upper()
    return minute<60 and sec<60 and deg+minute/60+sec/3600 <= (90 if axis=='lat' else 180) and direction in ('NS' if axis=='lat' else 'EW')


def pair_stratum(g, treatment, control):
    """No Cartesian products, no matching on outcomes, no missing-dose invention."""
    t=g[g.ReM.eq(treatment)]; c=g[g.ReM.eq(control)]
    if t.empty or c.empty: return [],'no_comparator_in_same_stratum'
    if len(c)!=1: return [],'multiple_comparator_arms_unresolved'
    if len(t)>1:
        dose=t.ReQ.map(number)
        if dose.isna().any() or not dose.gt(0).all() or not dose.is_unique:
            return [],'multiple_treatment_arms_without_unique_positive_doses'
    return [(r,c.iloc[0]) for _,r in t.iterrows()],''


def effect(t,c,col):
    mt,mc=number(t[col]),number(c[col])
    st,sc=number(t['SD.'+col]),number(c['SD.'+col])
    et,ec=number(t['SE.'+col]),number(c['SE.'+col])
    nt,nc=number(t.Duplicates),number(c.Duplicates)
    finite=math.isfinite(mt) and math.isfinite(mc)
    positive=finite and min(mt,mc)>0
    l=math.log(mt/mc) if positive else np.nan
    valid_n=all(math.isfinite(v) and v>=2 and v.is_integer() for v in (nt,nc))
    v=(st/mt)**2/nt+(sc/mc)**2/nc if positive and valid_n and all(math.isfinite(s) and s>=0 for s in (st,sc)) else np.nan
    error_checks=[]
    for sd,se,n in [(st,et,nt),(sc,ec,nc)]:
        if all(math.isfinite(z) for z in (sd,se,n)) and n>=2:
            # Source is rounded to three decimals; relative tolerance alone
            # would wrongly quarantine near-zero but consistent values.
            error_checks.append(abs(sd-se*math.sqrt(n)) <= .002*(1+math.sqrt(n)))
    return dict(outcome=ENDPOINTS[col],control_mean=mc,treatment_mean=mt,control_sd=sc,treatment_sd=st,
        control_se=ec,treatment_se=et,control_n=nc,treatment_n=nt,
        mean_difference=mt-mc if finite else np.nan,lnrr=l,
        percent_change=100*math.expm1(l) if positive else np.nan,
        variance_candidate_independent_arms=v,
        mean_status='positive_lnrr_available' if positive else ('nonpositive_mean_difference_only' if finite else 'missing_endpoint_mean'),
        uncertainty_arithmetic='inconsistent_SD_SE_n' if error_checks and not all(error_checks) else ('consistent_with_rounding' if len(error_checks)==2 else 'not_fully_checkable'),
        variance_origin='secondary_dataset; row_observed_vs_imputed_unresolved',
        endpoint_boundary='reported_yield_scale_pending_primary' if col=='GY' else 'reported_gas_or_derived_boundary_pending_primary',
        primary_analysis_eligible=False)


def previous_reviews():
    """Carry existing holds forward; old ledger admission is not fresh approval."""
    p=ROOT/'data/formal_analysis_v1/outputs/formal_review_ledger.csv'
    ledger=pd.read_csv(p,keep_default_na=False)
    lookup={}
    for _,r in ledger.iterrows():
        if r.independent_study_key.startswith('rice_primary_'):
            lookup[r.independent_study_key.removeprefix('rice_primary_')]=dict(
                prior_review_status=r.review_status,prior_review_notes=r.notes,
                prior_review_locator=str(p.relative_to(ROOT)))
    for sid,status in [('33','HOLD_RESIDUE_TREATMENT_PROVENANCE_UNVERIFIED'),
                       ('212','HOLD_FACTORIAL_WATER_STRATA_COLLAPSED')]:
        review=ROOT/f'data/formal_analysis_v1/outputs/validated_staging/study_{sid}/FULLTEXT_REVIEW.md'
        if review.exists():
            lookup[sid]=dict(prior_review_status=status,
                prior_review_notes='Existing hold remains binding; secondary matching does not resolve it.',
                prior_review_locator=str(review.relative_to(ROOT)))
    return lookup


def attach_reviewed_means(e,base,reviewed):
    """Separate primary mean overlay; never overwrite raw transcription or impute SD."""
    e.update(reviewed_control_mean=np.nan,reviewed_treatment_mean=np.nan,
             reviewed_lnrr=np.nan,primary_mean_overlay_status='not_available',
             primary_mean_overlay_locator='',primary_correction_note='')
    if base['source_study_id']!='117': return e
    rows=reviewed[reviewed.experiment_year.astype(str).eq(base['year']) &
                  reviewed.water_regime.eq(base['water_regime']) &
                  reviewed.analysis_outcome.eq(e['outcome'])]
    if len(rows)!=1:
        e['primary_mean_overlay_status']='existing_review_unresolved_row_link'
        return e
    r=rows.iloc[0]
    e.update(reviewed_control_mean=r.control_mean,reviewed_treatment_mean=r.treatment_mean,
             reviewed_lnrr=r.analysis_lnRR,primary_mean_overlay_status='primary_means_only_variance_held',
             primary_mean_overlay_locator=r.primary_table_locator,
             primary_correction_note=r.correction_audit,
             variance_origin='known_secondary_imputation_not_primary_observed')
    return e


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    raw=SRC/'data_Full.csv'; main=ROOT/'literature/evidence_database.csv'
    reviewed_path=ROOT/'data/formal_analysis_v1/outputs/validated_staging/study_117/study_117_validated_means_held.csv'
    provenance_inputs=[raw,main,SRC/'candidate_study_metadata_openalex.csv',
        SRC/'residue_contrast_candidates.csv',reviewed_path,
        ROOT/'data/formal_analysis_v1/outputs/formal_review_ledger.csv']
    provenance_inputs.extend(ROOT/f'data/formal_analysis_v1/outputs/validated_staging/study_{sid}/FULLTEXT_REVIEW.md' for sid in ['33','212'])
    before={str(p.relative_to(ROOT)):sha(p) for p in provenance_inputs}
    reviews=previous_reviews()
    reviewed=pd.read_csv(reviewed_path,keep_default_na=False)
    d=pd.read_csv(raw,dtype=str,keep_default_na=False)
    original=d.copy()
    d['source_csv_line']=np.arange(len(d))+2
    d['observation_id']=d.source_csv_line.map(lambda n:f'rice29817482v1_line_{n:05d}')
    d['source_id_collision']=d.duplicated(['StudyID','ES_ID'],keep=False)
    d['full_source_duplicate']=original.duplicated(keep=False)
    d['coordinate_valid']=d.apply(lambda r:coord_valid(r.Lat,'lat') and coord_valid(r.Long,'lon'),axis=1)
    for f in MATCH+['ReM','ExC']: d[f]=d[f].map(lambda x:canonical(x,f))
    # Original field missingness remains visible instead of becoming equality evidence.
    d['missing_matching_fields']=d.apply(lambda r:';'.join(f for f in MATCH if r[f]=='<MISSING>'),axis=1)
    d['stratum_id']=d.apply(lambda r:uid('stratum_',[r[f] for f in MATCH]),axis=1)
    d['source_locator']=d.source_csv_line.map(lambda n:f'data_Full.csv:line {n}')
    meta=pd.read_csv(SRC/'candidate_study_metadata_openalex.csv',keep_default_na=False)
    doi_lookup={}
    for sid,g in meta[meta.metadata_status.eq('HIGH_CONFIDENCE')].groupby('external_StudyID'):
        vals={re.sub(r'^https?://(?:dx\.)?doi.org/','',v.lower()).strip() for v in g.doi if v}
        if len(vals)==1: doi_lookup[str(sid)]=next(iter(vals))
    master=pd.read_csv(main,keep_default_na=False)
    titlekey=lambda s:re.sub('[^a-z0-9]','',str(s).lower())
    mtitles={titlekey(r.paper_title):r.paper_doi.lower() for _,r in master.iterrows() if r.paper_title and r.paper_doi}
    for sid,g in d.groupby('StudyID'):
        found={mtitles[titlekey(v)] for v in g.Title if titlekey(v) in mtitles}
        if len(found)==1: doi_lookup[sid]=next(iter(found))
    primary_dois=set(master.paper_doi.str.lower())-{''}
    primary_titles=set(master.paper_title.map(titlekey))-{''}
    field=d[d.ExC.eq('Field') & ~d.full_source_duplicate].copy()
    eligible=field[~field[REQUIRED].eq('<MISSING>').any(axis=1)]
    pair_rows=[];effect_rows=[];rejects=[]
    for treatment,control,label in CONTRASTS:
        relevant=eligible[eligible.ReM.isin([treatment,control])]
        for sid,g in relevant.groupby('stratum_id',sort=True):
            # Audit all target treatment strata, including those lacking control.
            if not g.ReM.eq(treatment).any(): continue
            pairs,why=pair_stratum(g,treatment,control)
            if why:
                rejects.append(dict(contrast=label,stratum_id=sid,source_study_id=g.StudyID.iloc[0],
                    treatment_rows=int(g.ReM.eq(treatment).sum()),control_rows=int(g.ReM.eq(control).sum()),
                    source_observations='|'.join(g.observation_id),reason=why))
                continue
            for t,c in pairs:
                pair_id=uid('rice_pair_',[t.observation_id,c.observation_id])
                missing=t.missing_matching_fields
                paper_doi=doi_lookup.get(t.StudyID,'')
                overlap=paper_doi in primary_dois or titlekey(t.Title) in primary_titles
                base=dict(pair_id=pair_id,stratum_id=sid,contrast=label,source_study_id=t.StudyID,
                    paper_doi=paper_doi,paper_title=t.Title,citation=t.Cite,country=t.Site,
                    year=t.ExY,season=t.Sea,latitude_raw=t.Lat,longitude_raw=t.Long,
                    water_regime=t.WaR,nitrogen=t.Nitrogen,phosphorus=t.Pho,potassium=t.Pot,
                    treatment_management=treatment,control_management=control,residue_quantity=t.ReQ,
                    treatment_observation_id=t.observation_id,control_observation_id=c.observation_id,
                    treatment_source_ES_ID=t.ES_ID,control_source_ES_ID=c.ES_ID,
                    treatment_source_line=int(t.source_csv_line),control_source_line=int(c.source_csv_line),
                    shared_control_group=c.observation_id,missing_matching_fields=missing,
                    match_tier='RECORDED_FIELDS_COMPLETE' if not missing else 'RECORDED_MATCH_WITH_UNKNOWN_COVARIATES',
                    coordinate_valid=bool(t.coordinate_valid and c.coordinate_valid),
                    source_id_collision=bool(t.source_id_collision or c.source_id_collision),
                    paper_overlaps_primary=overlap,
                    independence_status='source_StudyID_cluster_not_verified_independent_trial',
                    admission_status='SECONDARY_CANDIDATE_NOT_PRIMARY_ADMITTED')
                base.update(reviews.get(t.StudyID,dict(prior_review_status='NO_LINKED_PRIOR_REVIEW',
                    prior_review_notes='',prior_review_locator='')))
                base['feedstock_scope_flag']='TITLE_REQUIRES_FEEDSTOCK_CHECK' if re.search(
                    r'green biomass|green manure|cover crop',t.Title,re.I) else 'PRIMARY_FEEDSTOCK_CHECK_PENDING'
                pair_rows.append(base)
                for col in ENDPOINTS:
                    e=attach_reviewed_means(effect(t,c,col),base,reviewed)
                    effect_rows.append(dict(**base,**e,effect_id=pair_id+'_'+e['outcome']))
    pairs=pd.DataFrame(pair_rows);effects=pd.DataFrame(effect_rows)
    old=pd.read_csv(SRC/'residue_contrast_candidates.csv',keep_default_na=False)
    # Old ES_ID values were read as floats in the legacy pipeline. Comparing
    # them can be ambiguous; explicitly map cardinalities rather than selecting
    # the first matching row or claiming each reconstructed pair is new.
    legacy=[]
    source_id_counts=d.groupby(['StudyID','ES_ID']).size().to_dict()
    for oldid,g in old.groupby('pair_id'):
        r=g.iloc[0];s=str(r.external_StudyID)
        ct=source_id_counts.get((s,str(r.control_external_ES_ID)),0)
        tt=source_id_counts.get((s,str(r.treatment_external_ES_ID)),0)
        legacy.append(dict(legacy_pair_id=oldid,source_study_id=s,control_ES_ID=r.control_external_ES_ID,
            treatment_ES_ID=r.treatment_external_ES_ID,control_source_matches=ct,treatment_source_matches=tt,
            legacy_link_status='unique_source_ids' if ct==1 and tt==1 else 'ambiguous_or_unmatched_source_ids'))
    coverage=effects.groupby(['contrast','outcome','mean_status']).agg(records=('effect_id','size'),pairs=('pair_id','nunique'),
        source_study_ids=('source_study_id','nunique')).reset_index()
    valid=effects[effects.mean_status.eq('positive_lnrr_available')]
    frontier=valid[~valid.paper_overlaps_primary].groupby(['source_study_id','paper_title','paper_doi','country','prior_review_status','feedstock_scope_flag']).agg(
        records=('effect_id','size'),pairs=('pair_id','nunique'),outcomes=('outcome',lambda s:'|'.join(sorted(set(s)))),
        contrasts=('contrast',lambda s:'|'.join(sorted(set(s)))),all_coordinates_valid=('coordinate_valid','all'),
        complete_metadata_endpoint_records=('match_tier',lambda s:int(s.eq('RECORDED_FIELDS_COMPLETE').sum()))).reset_index()
    frontier['next_action']=np.select([
        frontier.prior_review_status.ne('NO_LINKED_PRIOR_REVIEW'),
        frontier.feedstock_scope_flag.eq('TITLE_REQUIRES_FEEDSTOCK_CHECK'),
        frontier.paper_doi.eq('')],['RESOLVE_EXISTING_HOLD_NOT_NEW_SOURCE',
        'CHECK_HARVEST_RESIDUE_SCOPE_BEFORE_EXTRACTION','RESOLVE_PRIMARY_IDENTITY_THEN_EXTRACT'],
        default='EXTRACT_PRIMARY_ARMS_AND_UNCERTAINTY')
    frontier=frontier.sort_values(['next_action','records'],ascending=[True,False])
    # Joint outcomes are aligned by exact source-arm IDs, never by paper title.
    joint=valid[valid.outcome.isin(['yield','CH4','N2O','GWP'])].pivot(index='pair_id',columns='outcome',values='lnrr').reset_index()
    joint=joint.merge(pairs[['pair_id','source_study_id','contrast','paper_overlaps_primary','match_tier','prior_review_status','feedstock_scope_flag']],on='pair_id',validate='one_to_one')
    joint['value_layer']='unharmonized_secondary_raw_means_not_analysis_ready'
    linked=pd.DataFrame(legacy)
    tables={'raw_observations':d,'pairs':pairs,'effects':effects,'pairing_rejections':pd.DataFrame(rejects),
        'coverage':coverage,'legacy_pair_id_audit':linked,'primary_review_frontier':frontier,
        'joint_endpoint_candidates':joint}
    for name,table in tables.items(): save(table,name)
    with sqlite3.connect(OUT/'rice_pairs.sqlite') as db:
        for name,table in tables.items(): table.to_sql(name,db,if_exists='replace',index=False)
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS raw_observation_key ON raw_observations(observation_id)')
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS paired_effect_key ON effects(effect_id)')
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    manifest=dict(source_doi='10.6084/m9.figshare.29817482.v1',input_sha256=before,
        raw_observations=len(d),source_study_ids=d.StudyID.nunique(),
        unique_source_ES_IDs=d.ES_ID.nunique(),source_ID_collision_rows=int(d.source_id_collision.sum()),
        full_row_duplicates=int(d.full_source_duplicate.sum()),matched_pairs=len(pairs),
        pair_source_study_ids=pairs.source_study_id.nunique(),endpoint_audit_records=len(effects),
        positive_mean_effect_candidates=len(valid),complete_recorded_metadata_pairs=int(pairs.match_tier.eq('RECORDED_FIELDS_COMPLETE').sum()),
        invalid_coordinate_pairs=int((~pairs.coordinate_valid).sum()),
        primary_overlap_pairs=int(pairs.paper_overlaps_primary.sum()),
        non_primary_source_study_ids=frontier.source_study_id.nunique(),
        no_linked_prior_review_non_primary_source_ids=int(frontier.loc[frontier.prior_review_status.eq('NO_LINKED_PRIOR_REVIEW'),'source_study_id'].nunique()),
        prior_review_linked_pairs=int(pairs.prior_review_status.ne('NO_LINKED_PRIOR_REVIEW').sum()),
        primary_mean_overlay_records=int(effects.primary_mean_overlay_status.eq('primary_means_only_variance_held').sum()),
        legacy_candidate_pairs=old.pair_id.nunique(),legacy_ambiguous_id_pairs=int(linked.legacy_link_status.ne('unique_source_ids').sum()),
        contrast_pair_counts=pairs.contrast.value_counts().to_dict(),
        positive_endpoint_counts=valid.outcome.value_counts().to_dict(),
        joint_yield_CH4_pairs=int(joint[['yield','CH4']].notna().all(axis=1).sum()),
        joint_yield_N2O_pairs=int(joint[['yield','N2O']].notna().all(axis=1).sum()),
        new_primary_trials=0,primary_master_unchanged=sha(main)==before[str(main.relative_to(ROOT))],
        raw_source_unchanged=sha(raw)==before[str(raw.relative_to(ROOT))],
        final_analysis_admitted=False,missing_values_are_not_evidence_of_equal_management=True)
    manifest['all_input_files_unchanged']=all(sha(ROOT/p)==v for p,v in before.items())
    manifest['output_csv_sha256']={n+'.csv':sha(OUT/(n+'.csv')) for n in tables}
    assert manifest['all_input_files_unchanged']
    assert manifest['primary_master_unchanged'] and manifest['raw_source_unchanged']
    assert effects.effect_id.is_unique and pairs.pair_id.is_unique
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))


if __name__=='__main__': build()
