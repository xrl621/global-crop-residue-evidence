"""Mean-only direct-pathway evidence must never inflate removal controls."""
import csv
import hashlib
import math
import unittest
from pathlib import Path

from scripts.extract_hoang2019_vietnam_mean_only import OUT, PDF_SHA256, csv_text, extract


ROOT = Path(__file__).resolve().parents[1]


class HoangMeanOnlyTests(unittest.TestCase):
    def test_source_transcription_and_dependence(self):
        rows = extract()
        self.assertEqual((len(rows), len({r['effect_id'] for r in rows}),
                          len({r['study_id'] for r in rows})), (24, 24, 1))
        self.assertEqual({r['outcome'] for r in rows}, {'yield', 'CH4', 'N2O'})
        self.assertEqual({r['water_regime'] for r in rows},
                         {'CF', 'AWD_minus_5_cm', 'AWD_minus_10_cm', 'AWD_minus_15_cm'})
        self.assertEqual({r['season'] for r in rows}, {'summer_2014', 'spring_2015'})
        self.assertTrue(all(r['treatment_pathway'] == 'direct_return'
                            and r['control_pathway'] == 'open_burning' for r in rows))
        self.assertTrue(all(r['treatment_sd'] == r['control_sd'] == r['variance_lnrr'] == ''
                            for r in rows))
        self.assertTrue(all('burning_pulse_excluded' in r['quality_flags'] for r in rows))
        self.assertTrue(all(float(r['lnrr']) > 0 for r in rows))
        anchor = {r['effect_id']: r for r in rows}
        self.assertEqual((anchor['hoang2019_summer_2014_CF_yield']['treatment_mean'],
                          anchor['hoang2019_summer_2014_CF_yield']['control_mean']),
                         ('5', '4.6'))
        self.assertEqual((anchor['hoang2019_spring_2015_AWD_minus_10_cm_CH4']['treatment_mean'],
                          anchor['hoang2019_spring_2015_AWD_minus_10_cm_CH4']['control_mean']),
                         ('258', '221'))
        for r in rows:
            self.assertTrue(math.isclose(float(r['lnrr']),
                              math.log(float(r['treatment_mean'])/float(r['control_mean'])),
                              rel_tol=0, abs_tol=1e-11))

    def test_csv_reproducible_and_separate_from_main(self):
        self.assertEqual(OUT.read_text(encoding='utf-8'), csv_text())
        with (ROOT / 'literature/evidence_database.csv').open(encoding='utf-8', newline='') as stream:
            main = list(csv.DictReader(stream))
        self.assertEqual(len(main), 607)
        self.assertNotIn('hoang_huong_an_2014_2015', {r['study_id'] for r in main})

    @unittest.skipUnless((ROOT / 'data/raw/hoang2019_vietnam_primary.pdf').exists(),
                         'Primary PDF is intentionally not distributed')
    def test_local_primary_pdf_hash(self):
        digest = hashlib.sha256((ROOT / 'data/raw/hoang2019_vietnam_primary.pdf').read_bytes()).hexdigest()
        self.assertEqual(digest, PDF_SHA256)


if __name__ == '__main__':
    unittest.main()
