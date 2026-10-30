import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def records(name):
    data = json.loads((ROOT / 'data/public/v1' / f'{name}.json').read_text())
    return {r['id']: r for r in data['records']}


class MusicDirectionAndRossiEvidenceTests(unittest.TestCase):
    def test_jurmann_credit_and_filmportal_are_linked_both_ways(self):
        ident = 'CON-F019-MD-P077'
        credit = records('contributions')[ident]
        self.assertEqual(credit['role'], 'music_director')
        self.assertEqual(credit['personIds'], ['P077'])
        self.assertEqual(credit['sourceIds'], ['SRC0130'])
        for table, record in [('works', 'W-F019'), ('people', 'P077'), ('sources', 'SRC0130')]:
            self.assertIn(ident, records(table)[record]['contributionIds'])
        overrides = json.loads((ROOT / 'scripts/public_export_overrides.json').read_text())
        self.assertIn(ident, overrides['additions']['Contributions'])

    def test_lavry_biography_is_retained_but_not_used_as_film_credit(self):
        credit = records('contributions')['CON-F006-MD-P147']
        source = records('sources')['SRC0610']
        self.assertEqual(credit['sourceIds'], ['SRC0120'])
        self.assertNotIn(credit['id'], source.get('contributionIds', []))
        self.assertIn('P147', source['personIds'])
        self.assertIn('SRC0610', records('people')['P147']['sourceIds'])

    def test_rossi_distinguishes_disc_and_listening_reference(self):
        credits = records('contributions')
        for ident, disc in [('CON-S105-P-P198', 'DF 1622'), ('CON-S112-P-P198', 'DF 1606'),
                            ('CON-S114-P-P198', 'DF 1610'), ('CON-S115-P-P198', 'DF 1606')]:
            with self.subTest(credit=ident):
                note = credits[ident]['scopeNote']
                self.assertIn(disc, note)
                self.assertIn('Internet Archive collection lists the same disc', note)
                self.assertIn('not been independently established', note)


if __name__ == '__main__':
    unittest.main()
