"""Describe each residue pathway and endpoint independently at trial level.

No across-paper treatment ranking, pooled CI, causal claim or secondary-data
admission is produced. The input is the existing strict descriptive snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / 'data/processed/stage_20260927/screened_effects.csv'
DEFAULT_OUT = ROOT / 'data/processed/pathway_endpoint_v1_20260928'
PATHWAYS = ('direct_return', 'biochar_return', 'open_burning')
CORE_CROPS = ('rice', 'maize', 'wheat')
ENDPOINTS = ('yield', 'SOC_concentration', 'CH4', 'N2O',
             'soil_GWP_unharmonized', 'soil_GHGI_unharmonized')


def endpoint_class(row):
    outcome = row['outcome']
    if outcome == 'SOC':
        return row['soc_kind']
    if outcome in ('GWP', 'GHGI'):
        boundary = row['system_boundary'].lower()
        if 'soil' in boundary or 'paddy' in boundary:
            return f'soil_{outcome}_unharmonized'
        return f'{outcome}_boundary_unresolved'
    return outcome


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def join_distinct(values):
    return '|'.join(sorted({str(v) for v in values if str(v)}))


def evidence_label(n):
    if n == 0:
        return 'NO_PRIMARY_STRICT_TRIAL'
    if n < 3:
        return 'VERY_SPARSE_DESCRIPTIVE'
    if n < 10:
        return 'SPARSE_DESCRIPTIVE'
    return 'TEN_OR_MORE_TRIALS_DESCRIPTIVE_ONLY'


def build(source=DEFAULT_SOURCE, out=DEFAULT_OUT):
    source, out = Path(source), Path(out)
    d = pd.read_csv(source, keep_default_na=False)
    if not d.effect_id.is_unique:
        raise ValueError('effect_id must be unique')
    if not d.descriptive_eligible.astype(str).str.lower().eq('true').all():
        raise ValueError('Input includes non-screened effects')
    if not d.pathway.isin(PATHWAYS).all():
        raise ValueError('Unexpected pathway in strict snapshot')
    for field in ('lnrr', 'treatment_mean', 'control_mean'):
        d[field] = pd.to_numeric(d[field], errors='raise')
    if not np.isfinite(d[['lnrr', 'treatment_mean', 'control_mean']]).all().all():
        raise ValueError('Nonfinite effect or mean')
    if (d[['treatment_mean', 'control_mean']] <= 0).any().any():
        raise ValueError('lnRR requires positive means')
    if not np.allclose(d.lnrr, np.log(d.treatment_mean/d.control_mean), atol=1e-8):
        raise ValueError('Effect does not reconstruct from source means')
    d['endpoint_class'] = d.apply(endpoint_class, axis=1)
    d['scope'] = np.where(d.crop_display.isin(CORE_CROPS) &
                          d.endpoint_class.isin(ENDPOINTS), 'core_comparable_endpoint',
                          'separate_boundary_or_crop')
    excluded = d[d.scope.ne('core_comparable_endpoint')].copy()
    core = d[d.scope.eq('core_comparable_endpoint')].copy()
    rows = []
    # One study_id is one cluster; aggregate dependent years/doses only for
    # descriptive direction. Preserve every contributing effect ID for audit.
    for (study, pathway, crop, endpoint), g in core.groupby(
            ['study_id', 'pathway', 'crop_display', 'endpoint_class'], sort=True):
        mean_log = float(g.lnrr.mean())
        rows.append(dict(study_id=study, pathway=pathway, crop=crop, endpoint=endpoint,
            effect_records=len(g), trial_mean_lnrr=mean_log,
            trial_percent=100*float(np.expm1(mean_log)),
            effect_ids=join_distinct(g.effect_id), countries=join_distinct(g.country),
            paper_dois=join_distinct(g.paper_doi),
            control_arms=join_distinct(g.control_arm),
            boundary_descriptions=join_distinct(g.system_boundary),
            units=join_distinct(g.outcome_unit),
            variance_origins=join_distinct(g.variance_origin_status)))
    trial = pd.DataFrame(rows)
    summary_rows = []
    for pathway, endpoint in itertools.product(PATHWAYS, ENDPOINTS):
        g = trial[(trial.pathway.eq(pathway)) & (trial.endpoint.eq(endpoint))]
        ids = set(g.study_id)
        summary_rows.append(dict(pathway=pathway, endpoint=endpoint,
            independent_trial_keys=len(ids), trial_crop_units=len(g),
            effect_records=int(g.effect_records.sum()),
            countries=join_distinct('|'.join(g.countries).split('|')),
            crops=join_distinct(g.crop),
            positive_trial_crop_units=int(g.trial_mean_lnrr.gt(0).sum()),
            negative_trial_crop_units=int(g.trial_mean_lnrr.lt(0).sum()),
            zero_trial_crop_units=int(g.trial_mean_lnrr.eq(0).sum()),
            median_trial_percent=float(g.trial_percent.median()) if len(g) else np.nan,
            min_trial_percent=float(g.trial_percent.min()) if len(g) else np.nan,
            max_trial_percent=float(g.trial_percent.max()) if len(g) else np.nan,
            evidence_label=evidence_label(len(ids)),
            inference='descriptive_only_no_between_pathway_ranking'))
    summary = pd.DataFrame(summary_rows)
    grid_rows = []
    for pathway, endpoint, crop in itertools.product(PATHWAYS, ENDPOINTS, CORE_CROPS):
        g = trial[(trial.pathway.eq(pathway)) & (trial.endpoint.eq(endpoint)) &
                  (trial.crop.eq(crop))]
        n = g.study_id.nunique()
        grid_rows.append(dict(pathway=pathway, endpoint=endpoint, crop=crop,
            independent_trial_keys=n, effect_records=int(g.effect_records.sum()),
            median_trial_percent=float(g.trial_percent.median()) if n else np.nan,
            positive_trials=int(g.trial_mean_lnrr.gt(0).sum()),
            negative_trials=int(g.trial_mean_lnrr.lt(0).sum()),
            countries=join_distinct('|'.join(g.countries).split('|')),
            evidence_label=evidence_label(n),
            inference='within_pathway_descriptive_not_direct_superiority'))
    grid = pd.DataFrame(grid_rows)
    support_rows = []
    for endpoint, crop, pair in itertools.product(ENDPOINTS, CORE_CROPS,
                                                  itertools.combinations(PATHWAYS, 2)):
        a, b = pair
        left = set(trial.loc[trial.pathway.eq(a) & trial.endpoint.eq(endpoint) &
                             trial.crop.eq(crop), 'study_id'])
        right = set(trial.loc[trial.pathway.eq(b) & trial.endpoint.eq(endpoint) &
                              trial.crop.eq(crop), 'study_id'])
        both = left & right
        support_rows.append(dict(endpoint=endpoint, crop=crop, pathway_a=a, pathway_b=b,
            a_trial_keys=len(left), b_trial_keys=len(right),
            shared_trial_keys=len(both), shared_study_ids=join_distinct(both),
            comparison_status=('NO_TWO_PATHWAY_SUPPORT' if not left or not right else
                'SHARED_TRIAL_REQUIRES_ARM_LEVEL_CHECK' if both else
                'INDIRECT_CROSS_STUDY_ONLY'),
            direct_effect_estimate_present=False,
            inference='no_superiority_test_or_indirect_causal_claim'))
    support = pd.DataFrame(support_rows)
    assert int(trial.effect_records.sum()) == len(core)
    assert int(summary.effect_records.sum()) == len(core)
    assert int(grid.effect_records.sum()) == len(core)
    out.mkdir(parents=True, exist_ok=True)
    for name, frame in [('trial_level', trial), ('pathway_outcome', summary),
                        ('pathway_outcome_crop_grid', grid), ('comparison_support', support),
                        ('separate_boundary_audit', excluded)]:
        frame.to_csv(out/f'{name}.csv', index=False, encoding='utf-8-sig')
    manifest = dict(input=str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source),
        input_sha256=sha(source), strict_input_effects=len(d),
        strict_input_trial_keys=d.study_id.nunique(),
        core_effects=len(core), core_trial_keys=core.study_id.nunique(),
        separate_boundary_or_crop_effects=len(excluded),
        output_trial_crop_units=len(trial),
        all_effects_accounted_for=len(core)+len(excluded)==len(d),
        no_new_primary_admissions=True, no_cross_pathway_ranking=True,
        numeric_summary='unweighted_trial_level_descriptive_median_not_meta_estimate',
        secondary_rice_candidates_not_pooled=True,
        software=dict(pandas=pd.__version__, numpy=np.__version__),
        output_sha256={p.name:sha(p) for p in out.glob('*.csv')})
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.out), ensure_ascii=False, indent=2))
