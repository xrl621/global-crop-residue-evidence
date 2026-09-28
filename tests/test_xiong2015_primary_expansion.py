"""Regressions for a publisher-table extraction, not for secondary estimates."""
import csv
import math
import unittest
from pathlib import Path

from scripts.export_evidence_database import build_csv


ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / 'literature/primary_extractions/xiong2015_rice_season_table2.csv'
MASTER = ROOT / 'literature/evidence_database.csv'
OLD = ROOT / 'data/processed/stage_20260927/row_audit.csv'
NEW = ROOT / 'data/processed/stage_20260928/row_audit.csv'


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


class XiongPrimaryExpansionTests(unittest.TestCase):
    def test_exact_source_rows_and_one_trial(self):
        source = rows(PRIMARY)
        self.assertEqual((len(source), len({r['effect_id'] for r in source}),
                          {r['study_id'] for r in source}),
                         (54, 54, {'xiong_moling_2008_2011'}))
        self.assertEqual({r['outcome'] for r in source}, {'yield', 'CH4', 'N2O'})
        self.assertEqual({r['experiment_year'] for r in source}, {'2009', '2010', '2011'})
        self.assertEqual({r['season'] for r in source}, {'single_rice', 'early_rice', 'late_rice'})
        self.assertEqual({r['treatment_arm'] for r in source}, {'UR-S1', 'UR-S2', 'DR-S1', 'DR-S2'})
        self.assertTrue(all(r['treatment_n'] == r['control_n'] == '3' for r in source))
        self.assertTrue(all(r['quality_flags'] == 'straw_feedstock_species_unreported' for r in source))
        by_id = {r['effect_id']: r for r in source}
        ch4 = by_id['xiong_UR_2009_single_rice_S1_CH4']
        yield_late = by_id['xiong_DR_2011_late_rice_S1_yield']
        self.assertEqual((ch4['treatment_mean'], ch4['treatment_sd']), ('220', '57.7'))
        self.assertEqual((yield_late['control_mean'], yield_late['control_sd']), ('9.93', '2.59'))
        for r in source:
            self.assertEqual(r['control_arm'], r['treatment_arm'].split('-')[0] + '-S0')
            self.assertEqual(r['shared_control_group'],
                f"xiong_{r['treatment_arm'].split('-')[0]}_{r['experiment_year']}_{r['season']}_S0_{r['outcome']}")

    def test_master_is_reproducible_and_prior_effects_preserved(self):
        expected, n, trials = build_csv(ROOT / 'data/formal_analysis_v1/outputs/formal_validated_staging_v0.csv')
        self.assertEqual((n, trials), (607, 34))
        self.assertEqual(MASTER.read_text(encoding='utf-8'), expected)
        old = {r['effect_id']: r for r in rows(OLD)}
        new = {r['effect_id']: r for r in rows(NEW)}
        self.assertEqual(len(set(new) - set(old)), 54)
        for effect_id, prior in old.items():
            current = new[effect_id]
            for field in ('treatment_mean', 'control_mean', 'treatment_sd',
                          'control_sd', 'lnrr', 'variance_lnrr'):
                self.assertTrue(math.isclose(float(prior[field]), float(current[field]),
                                rel_tol=0, abs_tol=1e-11), (effect_id, field))

    def test_quality_screen_uses_source_flags_and_cluster_key(self):
        current = [r for r in rows(NEW) if r['study_id'] == 'xiong_moling_2008_2011']
        self.assertEqual(len(current), 54)
        screened = [r for r in current if not r['screen_exclusion']]
        held = [r for r in current if r['screen_exclusion']]
        self.assertEqual((len(screened), len(held)), (48, 6))
        self.assertEqual({r['outcome'] for r in held}, {'N2O'})
        self.assertEqual({r['screen_exclusion'] for r in held},
                         {'large_relative_se_lnrr_delta_approx'})
        self.assertTrue(all('straw_feedstock_species_unreported' in r['quality_flags']
                            for r in current))

    @unittest.skipUnless((ROOT / 'data/processed/xiong2015_review_20260928/source_numeric_audit.csv').exists(),
                         'Local third-party candidate table not distributed')
    def test_secondary_conflicts_documented_not_imported(self):
        audit = rows(ROOT / 'data/processed/xiong2015_review_20260928/source_numeric_audit.csv')
        self.assertEqual(len(audit), 216)
        conflicts = [r for r in audit if r['status'] == 'secondary_numeric_conflict']
        self.assertEqual(len(conflicts), 3)  # One shared control appears in two pair rows.
        self.assertEqual({(r['source_ES_ID'], r['statistic']) for r in conflicts},
                         {('96.2', 'sd'), ('96.25', 'mean')})


if __name__ == '__main__':
    unittest.main()
