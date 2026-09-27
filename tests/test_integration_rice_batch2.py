import importlib.util
import math
from pathlib import Path
import sqlite3
import unittest

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('rice_batch2',ROOT/'scripts/integrate_rice_pairs_batch2.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class RicePairTests(unittest.TestCase):
    def arms(self, doses=(10,20), controls=1):
        return pd.DataFrame([dict(ReM='T',ReQ=v) for v in doses]+[dict(ReM='C',ReQ=0) for _ in range(controls)])

    def test_distinct_doses_share_unique_control(self):
        pairs,reason=mod.pair_stratum(self.arms(),'T','C')
        self.assertEqual(len(pairs),2)
        self.assertEqual(reason,'')
        self.assertEqual(pairs[0][1].name,pairs[1][1].name)

    def test_ambiguous_controls_never_cartesian(self):
        pairs,reason=mod.pair_stratum(self.arms(controls=2),'T','C')
        self.assertEqual(pairs,[])
        self.assertEqual(reason,'multiple_comparator_arms_unresolved')

    def test_multiple_arms_require_distinct_positive_known_doses(self):
        for doses in [(10,10),(10,''),(0,10),(-1,10)]:
            self.assertEqual(mod.pair_stratum(self.arms(doses),'T','C')[0],[])
        self.assertEqual(len(mod.pair_stratum(self.arms(('',)),'T','C')[0]),1)

    def test_no_comparator_rejected(self):
        self.assertEqual(mod.pair_stratum(self.arms(controls=0),'T','C')[1],'no_comparator_in_same_stratum')

    def test_missing_is_explicit_not_zero(self):
        self.assertEqual(mod.canonical('NaN'),'<MISSING>')
        self.assertEqual(mod.canonical('None_Application'),'None_Application')
        self.assertEqual(mod.canonical('0','Nitrogen'),'0')
        self.assertEqual(mod.canonical('10.0','Nitrogen'),mod.canonical('10','Nitrogen'))
        self.assertIn('Lat',mod.MATCH)
        self.assertIn('Long',mod.MATCH)
        self.assertIn('ExY',mod.MATCH)

    def test_coordinate_validation_does_not_repair_bad_minutes(self):
        self.assertTrue(mod.coord_valid('30.5','lat'))
        self.assertFalse(mod.coord_valid('91','lat'))
        self.assertTrue(mod.coord_valid('30°20\'10"N','lat'))
        self.assertFalse(mod.coord_valid('30°70\'10"N','lat'))
        self.assertFalse(mod.coord_valid('30°20\'10"E','lat'))

    def row(self,mean=100,n=4):
        return pd.Series({'GY':mean,'SD.GY':10,'SE.GY':5,'Duplicates':n})

    def test_nonpositive_means_preserved_without_log_or_offset(self):
        e=mod.effect(self.row(-2),self.row(10),'GY')
        self.assertEqual(e['mean_difference'],-12)
        self.assertTrue(math.isnan(e['lnrr']))
        self.assertEqual(e['mean_status'],'nonpositive_mean_difference_only')

    def test_variance_not_claimed_as_observed(self):
        e=mod.effect(self.row(110),self.row(),'GY')
        self.assertAlmostEqual(e['lnrr'],math.log(1.1))
        self.assertIn('unresolved',e['variance_origin'])
        self.assertFalse(e['primary_analysis_eligible'])
        self.assertTrue(math.isnan(mod.effect(self.row(n=3.5),self.row(),'GY')['variance_candidate_independent_arms']))

    def test_review_overlay_preserves_raw_error(self):
        reviewed=pd.DataFrame([dict(experiment_year=2012,water_regime='AWD',analysis_outcome='CH4',
            control_mean=83.6,treatment_mean=186.4,analysis_lnRR=math.log(186.4/83.6),
            primary_table_locator='Table 6',correction_audit='168.4 to 186.4')])
        e=mod.attach_reviewed_means(dict(outcome='CH4',treatment_mean=168.4),
            dict(source_study_id='117',year='2012',water_regime='AWD'),reviewed)
        self.assertEqual(e['treatment_mean'],168.4)
        self.assertEqual(e['reviewed_treatment_mean'],186.4)
        self.assertEqual(e['variance_origin'],'known_secondary_imputation_not_primary_observed')

    @unittest.skipUnless((mod.OUT/'rice_pairs.sqlite').exists(),'Run local batch 2 with source files first')
    def test_local_integrity_and_admission_boundary(self):
        with sqlite3.connect(mod.OUT/'rice_pairs.sqlite') as db:
            self.assertEqual(db.execute('pragma integrity_check').fetchone()[0],'ok')
            self.assertEqual(db.execute('select count(distinct observation_id) from raw_observations').fetchone()[0],5322)
            self.assertEqual(db.execute('select count(*) from pairs').fetchone()[0],213)
            self.assertEqual(db.execute('select count(distinct effect_id) from effects').fetchone()[0],1065)
            self.assertEqual(db.execute('select count(*) from effects where primary_analysis_eligible=1').fetchone()[0],0)
            self.assertEqual(db.execute("select count(*) from effects where primary_mean_overlay_status='primary_means_only_variance_held'").fetchone()[0],20)
            self.assertEqual(db.execute('select count(*) from pairs p left join raw_observations r on p.control_observation_id=r.observation_id where r.observation_id is null').fetchone()[0],0)
            self.assertEqual(db.execute('select count(*) from joint_endpoint_candidates').fetchone()[0],213)


if __name__=='__main__': unittest.main()
