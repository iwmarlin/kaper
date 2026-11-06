import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def records(table):
    return {r['id']: r for r in json.loads((ROOT / 'data/public/v1' / f'{table}.json').read_text())['records']}


class PerformanceCreditEvidenceTests(unittest.TestCase):
    def test_filmography_and_recordings_are_distinguished(self):
        credits = records('contributions')
        sources = records('sources')
        for ident in ('CON-S058-P-P164', 'CON-S084-P-P164', 'CON-S080-P-P153',
                      'CON-S081-P-P153', 'CON-S082-P-P153'):
            with self.subTest(credit=ident):
                self.assertIn('SRC0373', credits[ident]['sourceIds'])
                self.assertIn(ident, sources['SRC0373']['contributionIds'])
                self.assertIn('separately', credits[ident]['scopeNote'])
        for ident in ('CON-S058-P-P164', 'CON-S084-P-P164'):
            for source in ('SRC0186', 'SRC0690'):
                self.assertNotIn(source, credits[ident]['sourceIds'])
                self.assertNotIn(ident, sources[source]['contributionIds'])

    def test_filmography_music_credit_is_not_music_direction(self):
        credits = records('contributions')
        source = records('sources')['SRC0373']
        for ident in ('CON-F009-MD-P009', 'CON-F019-MD-P009',
                      'CON-F022-MD-P009', 'CON-F022-MD-P077'):
            with self.subTest(credit=ident):
                self.assertNotIn('SRC0373', credits[ident]['sourceIds'])
                self.assertNotIn(ident, source['contributionIds'])
                self.assertTrue(credits[ident]['sourceIds'])
        for ident in ('CON-F009-C-P009', 'CON-F022-C-P009', 'CON-F022-C-P077'):
            self.assertIn('SRC0373', credits[ident]['sourceIds'])

    def test_poster_is_not_a_director_credit(self):
        self.assertNotIn('SRC0384', records('contributions')['CON-F052-D-P157']['sourceIds'])
        self.assertNotIn('CON-F052-D-P157', records('sources')['SRC0384']['contributionIds'])


if __name__ == '__main__':
    unittest.main()
