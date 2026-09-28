import importlib.util
import math
from pathlib import Path
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('separate', ROOT/'scripts/analyze_pathways_separately.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SeparatePathwayTests(unittest.TestCase):
    def test_endpoint_subtypes_never_merged(self):
        self.assertEqual(mod.endpoint_class(dict(outcome='SOC', soc_kind='SOM_proxy')),'SOM_proxy')
        self.assertEqual(mod.endpoint_class(dict(outcome='SOC', soc_kind='SOC_concentration')),'SOC_concentration')
        self.assertEqual(mod.endpoint_class(dict(outcome='GWP',system_boundary='soil growing season')),
                         'soil_GWP_unharmonized')
        self.assertEqual(mod.endpoint_class(dict(outcome='GWP',system_boundary='full life cycle')),
                         'GWP_boundary_unresolved')

    def test_count_threshold_does_not_mean_model_admission(self):
        self.assertEqual(mod.evidence_label(10),'TEN_OR_MORE_TRIALS_DESCRIPTIVE_ONLY')
        self.assertEqual(mod.evidence_label(0),'NO_PRIMARY_STRICT_TRIAL')

    def test_one_study_many_rows_does_not_inflate_trial_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            rows=[]
            for eid,pathway,endpoint,value,study in [
                ('y1','direct_return','yield',110,'trial_1'),
                ('y2','direct_return','yield',120,'trial_1'),
                ('g1','direct_return','CH4',10,'trial_1'),
                ('y3','biochar_return','yield',130,'trial_1'),
                ('y4','open_burning','yield',90,'trial_2')]:
                rows.append(dict(effect_id=eid,study_id=study,pathway=pathway,outcome=endpoint,
                    crop_display='rice',soc_kind='not_SOC',system_boundary='soil growing season',
                    treatment_mean=value,control_mean=100,lnrr=math.log(value/100),
                    descriptive_eligible=True,country='China',paper_doi='',control_arm='C',
                    outcome_unit='unit',variance_origin_status='documented_or_reconstructed'))
            source=temp/'input.csv';pd.DataFrame(rows).to_csv(source,index=False)
            manifest=mod.build(source,temp/'out')
            self.assertEqual(manifest['core_effects'],5)
            table=pd.read_csv(temp/'out/pathway_outcome.csv')
            r=table[(table.pathway=='direct_return') & (table.endpoint=='yield')].iloc[0]
            self.assertEqual((r.independent_trial_keys,r.effect_records),(1,2))
            self.assertAlmostEqual(r.median_trial_percent,100*math.expm1((math.log(1.1)+math.log(1.2))/2))
            self.assertEqual(table[(table.pathway=='biochar_return') & (table.endpoint=='CH4')].iloc[0].independent_trial_keys,0)
            support=pd.read_csv(temp/'out/comparison_support.csv')
            shared=support[(support.endpoint=='yield') & (support.crop=='rice') &
                           (support.pathway_a=='direct_return') & (support.pathway_b=='biochar_return')].iloc[0]
            self.assertEqual(shared.shared_trial_keys,1)
            self.assertEqual(shared.comparison_status,'SHARED_TRIAL_REQUIRES_ARM_LEVEL_CHECK')
            self.assertFalse(shared.direct_effect_estimate_present)

    @unittest.skipUnless(mod.DEFAULT_SOURCE.exists(),'Strict source snapshot required')
    def test_current_snapshot_accounting(self):
        out=mod.DEFAULT_OUT
        if not (out/'manifest.json').exists():
            self.skipTest('Run pathway analysis first')
        import json
        m=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual((m['strict_input_effects'],m['strict_input_trial_keys']),(485,27))
        self.assertEqual((m['core_effects'],m['separate_boundary_or_crop_effects']),(472,13))
        self.assertTrue(m['all_effects_accounted_for'])
        self.assertTrue(m['no_cross_pathway_ranking'])


if __name__=='__main__': unittest.main()
