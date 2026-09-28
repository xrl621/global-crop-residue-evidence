import importlib.util
import json
import math
from pathlib import Path
import sqlite3
import unittest

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('integration',ROOT/'scripts/integrate_evidence_batch1.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class IntegrationTests(unittest.TestCase):
    def test_title_parser_plural_and_in_search(self):
        self.assertEqual(mod.paper_title_from_ref('Li, Z., Wu, P. Effects of straw return. Journal, 2018.'),'Effects of straw return')
        self.assertEqual(mod.paper_title_from_ref('Li, Z., Wu, P. In search of sustainable straw practices. Journal, 2018.'),'In search of sustainable straw practices')

    def test_numeric_audit_recalculates_without_imputing(self):
        r=dict(treatment_mean=110.,control_mean=100.,treatment_sd=11.,control_sd=10.,treatment_n=4.,control_n=4.,source_lnrr=math.log(1.1),source_variance=.005)
        l,v,status,vs=mod.numeric_audit(r)
        self.assertAlmostEqual(l,math.log(1.1))
        self.assertAlmostEqual(v,.005)
        self.assertEqual((status,vs),('consistent','consistent'))
        r['treatment_sd']=float('nan')
        self.assertTrue(math.isnan(mod.numeric_audit(r)[1]))

    def test_nonpositive_and_fractional_n_not_repaired(self):
        self.assertEqual(mod.first_value(0.0, 21.0),0.0)
        self.assertEqual(mod.first_value('', 0.0),0.0)
        r=dict(treatment_mean=0.,control_mean=100.,treatment_sd=11.,control_sd=10.,treatment_n=4.,control_n=4.,source_lnrr=0.,source_variance=.1)
        self.assertTrue(math.isnan(mod.numeric_audit(r)[0]))
        r.update(treatment_mean=110.,treatment_n=3.5)
        self.assertTrue(math.isnan(mod.numeric_audit(r)[1]))

    def test_batch1_input_snapshot_remains_pinned(self):
        # The primary master is append-only; batch 1 remains a frozen 2026-09-27 snapshot.
        manifest=json.loads((ROOT/'data/processed/stage_20260927/manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['sha256'],'7c2d51acc551d8bd1581e5595f2ed871c625c675d5b0ea04d2bc311652b1ecbe')
        self.assertEqual((manifest['all_rows'],manifest['all_trials']),(553,33))

    @unittest.skipUnless((mod.OUT/'evidence_integrated.sqlite').exists(),'Run local integration with documented third-party inputs first')
    def test_all_records_retained_and_tiers_separate(self):
        with sqlite3.connect(mod.OUT/'evidence_integrated.sqlite') as db:
            self.assertEqual(db.execute('select count(*) from effects_integrated').fetchone()[0],12953)
            self.assertEqual(db.execute('select count(distinct record_id) from effects_integrated').fetchone()[0],12953)
            self.assertEqual(db.execute('select count(*) from primary_strict').fetchone()[0],437)
            self.assertEqual(db.execute('select count(*) from effects_integrated where primary_reviewed=0 and primary_analysis_eligible=1').fetchone()[0],0)
            self.assertEqual(db.execute('select count(*) from secondary_descriptive where paper_overlaps_primary=1').fetchone()[0],0)
            self.assertEqual(db.execute('select count(*) from source_observations').fetchone()[0],db.execute('select count(distinct observation_id) from source_observations').fetchone()[0])
            self.assertEqual(db.execute('pragma integrity_check').fetchone()[0],'ok')

    @unittest.skipUnless(mod.LU.exists(),'Third-party source workbook stays local')
    def test_lu_source_font_provenance(self):
        rows=mod.lu_raw_audit()
        self.assertEqual(len(rows),153)
        self.assertEqual(sum(r['variance_origin']=='source_CV_imputed' for r in rows.values()),108)
        self.assertTrue(all('bold characters' in r['source_footnote'] for r in rows.values()))

    @unittest.skipUnless(mod.CANDIDATE.exists() and mod.LU_REFS.exists(),'Local source registry and reference supplement required')
    def test_lu_refs_do_not_invent_ambiguous_wang_or_wrong_year(self):
        c=pd.read_csv(mod.CANDIDATE,keep_default_na=False,low_memory=False)
        refs=mod.lu_reference_map(c)
        self.assertEqual(refs['Lu2020_9']['title'],'Effects of wheat-residue application on soil water and water use efficiency in the Weibei Loess Plateau')
        self.assertEqual(refs['Lu2020_10']['reference_status'],'ambiguous_source_reference')
        self.assertEqual(refs['Lu2020_28']['reference_status'],'no_matching_author_year_reference')
        self.assertTrue(refs['Lu2020_39']['title'].startswith('In search'))

    @unittest.skipUnless((mod.OUT/'lu2020_source_audit.csv').exists(),'Run local integration first')
    def test_source_audit_all_means_match_and_bad_countries_held(self):
        d=pd.read_csv(mod.OUT/'lu2020_source_audit.csv',keep_default_na=False)
        self.assertTrue(d.mean_ratio_check.eq('consistent').all())
        self.assertTrue(d.variance_check.eq('consistent').all())
        z=d[d.source_study_id.isin(['Lu2020_34','Lu2020_36'])]
        self.assertTrue(z.country.eq('').all())
        self.assertFalse(z.secondary_descriptive_eligible.any())


if __name__=='__main__': unittest.main()
