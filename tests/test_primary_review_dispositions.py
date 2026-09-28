import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def records(path):
    with (ROOT / path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


class PrimaryReviewDispositionTests(unittest.TestCase):
    def test_overlay_preserves_independent_review_layers(self):
        rows = records('literature/primary_review_dispositions_20260928.csv')
        by_id = {r['source_study_id']: r for r in rows}
        self.assertEqual(len(by_id), len(rows))
        self.assertEqual(set(by_id), {'96', '213', '412', '394', '325'})
        old = records('data/processed/integration_batch2_rice_20260927/primary_review_frontier.csv')
        self.assertTrue(set(by_id).issubset({r['source_study_id'] for r in old}))
        self.assertEqual(sum(int(r['main_added_effects']) for r in rows), 54)
        self.assertEqual(sum(int(r['main_added_trial_keys']) for r in rows), 1)
        self.assertEqual(sum(int(r['mean_only_added_comparisons']) for r in rows), 24)
        main = records('literature/evidence_database.csv')
        self.assertEqual(sum(r['study_id'] == 'xiong_moling_2008_2011' for r in main), 54)
        self.assertFalse(any(r['paper_doi'] in {
            '10.1080/03650340.2018.1487553', '10.1029/91GB02586'} for r in main))


if __name__ == '__main__':
    unittest.main()
