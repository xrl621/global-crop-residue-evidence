"""Transcribe Table 3/4 direct-return versus burning contrasts, mean only.

The primary paper reports three split-plot blocks and mean ± SE for sampled
fluxes, but Tables 3 and 4 give no arm-specific SE for cumulative seasonal
emissions or grain yield. Do not infer variance from letters or secondary data.
This source has burning as the comparator, not straw removal, and therefore is
not part of the removal-referenced primary evidence master.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'literature/primary_extractions/hoang2019_vietnam_direct_vs_burning_MEAN_ONLY_NOT_MAIN.csv'
PDF_SHA256 = '55d404ad9815469654874e392f696a904d19327b062ea1a7345536cdc2800748'
DOI = '10.1080/03650340.2018.1487553'
TITLE = 'Incorporation of rice straw mitigates CH4 and N2O emissions in water saving paddy fields of Central Vietnam'

# For each water regime: season -> endpoint -> (incorporated, burned).
# Table 3: seasonal cumulative CH4 and N2O; Table 4: grain yield.
SOURCE_VALUES = {
    'CF': {
        'summer_2014': {'CH4': (728, 611), 'N2O': (.36, .32), 'yield': (5.00, 4.60)},
        'spring_2015': {'CH4': (377, 308), 'N2O': (.25, .18), 'yield': (5.81, 5.21)},
    },
    'AWD_minus_5_cm': {
        'summer_2014': {'CH4': (652, 577), 'N2O': (.49, .29), 'yield': (5.02, 4.76)},
        'spring_2015': {'CH4': (297, 231), 'N2O': (.29, .26), 'yield': (5.90, 5.43)},
    },
    'AWD_minus_10_cm': {
        'summer_2014': {'CH4': (547, 431), 'N2O': (.54, .39), 'yield': (5.84, 5.33)},
        'spring_2015': {'CH4': (258, 221), 'N2O': (.26, .22), 'yield': (6.17, 5.43)},
    },
    'AWD_minus_15_cm': {
        'summer_2014': {'CH4': (599, 499), 'N2O': (.54, .33), 'yield': (5.32, 5.01)},
        'spring_2015': {'CH4': (249, 196), 'N2O': (.34, .25), 'yield': (5.93, 5.80)},
    },
}
UNITS = {'CH4': 'kg CH4 ha-1 rice-season-1',
         'N2O': 'kg N2O ha-1 rice-season-1',
         'yield': 't rice grain ha-1'}
FIELDS = [
    'effect_id', 'study_id', 'paper_doi', 'paper_title', 'publication_year',
    'experiment_year', 'country', 'location', 'latitude', 'longitude',
    'crop_core', 'season', 'water_regime', 'residue_as_reported',
    'treatment_pathway', 'control_pathway', 'treatment_arm', 'control_arm',
    'outcome', 'outcome_unit', 'treatment_mean', 'control_mean',
    'treatment_sd', 'control_sd', 'treatment_n', 'control_n',
    'lnrr', 'variance_lnrr', 'percent_change', 'source_locator',
    'analysis_layer', 'variance_provenance', 'system_boundary',
    'independence_resolution', 'quality_flags',
]


def extract():
    rows = []
    for water, seasons in SOURCE_VALUES.items():
        for season, outcomes in seasons.items():
            for outcome, (treatment, control) in outcomes.items():
                if not (treatment > 0 and control > 0):
                    raise ValueError('Nonpositive Table 3/4 mean')
                lnrr = math.log(treatment / control)
                rows.append(dict(
                    effect_id=f'hoang2019_{season}_{water}_{outcome}',
                    study_id='hoang_huong_an_2014_2015', paper_doi=DOI,
                    paper_title=TITLE, publication_year='2019',
                    experiment_year=season.rsplit('_', 1)[1], country='Vietnam',
                    location='Huong An village, Huong Tra, Thua Thien Hue',
                    latitude='16.467222', longitude='107.517222', crop_core='rice',
                    season=season, water_regime=water,
                    residue_as_reported='rice straw, 5 t ha-1',
                    treatment_pathway='direct_return', control_pathway='open_burning',
                    treatment_arm=f'{water}: 5 t ha-1 rice straw incorporated into 0-15 cm soil',
                    control_arm=f'{water}: 5 t ha-1 rice straw distributed and burned in situ',
                    outcome=outcome, outcome_unit=UNITS[outcome],
                    treatment_mean=format(treatment, '.12g'),
                    control_mean=format(control, '.12g'),
                    treatment_sd='', control_sd='', treatment_n='3', control_n='3',
                    lnrr=format(lnrr, '.12g'), variance_lnrr='',
                    percent_change=format(math.expm1(lnrr) * 100, '.12g'),
                    source_locator='Table 4' if outcome == 'yield' else 'Table 3',
                    analysis_layer='PRIMARY_MEAN_ONLY_DIRECT_PATHWAY_COMPARISON_NOT_MAIN',
                    variance_provenance='arm-specific SD/SE for cumulative endpoint not numerically reported',
                    system_boundary=f'{season} rice-growing-season field outcome; burning pulse and upstream emissions excluded',
                    independence_resolution='One split-plot field experiment, n=3 blocks; water strata, two seasons and outcomes are dependent',
                    quality_flags='arm_variance_missing;burning_pulse_excluded;no_straw_removal_control',
                ))
    if len(rows) != 24 or len({r['effect_id'] for r in rows}) != 24:
        raise ValueError('Expected 2 seasons × 4 water strata × 3 endpoints')
    return rows


def csv_text():
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(extract())
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', type=Path, help='Optional local primary PDF for SHA-256 check')
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.pdf:
        digest = hashlib.sha256(args.pdf.read_bytes()).hexdigest()
        if digest != PDF_SHA256:
            raise ValueError(f'Primary PDF version changed: {digest}')
    content = csv_text()
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding='utf-8') != content:
            raise SystemExit('Mean-only source CSV missing or out of date')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding='utf-8', newline='')
    print('primary_mean_only_comparisons=24 one_trial=1 main_admissions=0')


if __name__ == '__main__':
    main()
