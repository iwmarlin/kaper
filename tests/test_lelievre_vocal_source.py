import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def records(name):
    return {r['id']: r for r in json.loads((ROOT / 'data/public/v1' / f'{name}.json').read_text())['records']}


class LelievreVocalSourceTests(unittest.TestCase):
    def test_distinct_catalogue_and_copyright_date(self):
        source = records('sources')['SRC0951']
        self.assertEqual(source['primaryUrl'], 'https://catalogue.bnf.fr/ark:/12148/cb425381729')
        self.assertEqual(source['sourceType'], 'sheet_music_catalogue')
        self.assertEqual(source['dateRole'], 'described_item')
        self.assertIn('© 1934', source['fullCitation'])
        self.assertIn('1899–1966', source['researchNote'])
        self.assertIn('printed copies have not been compared', source['researchNote'])
        for ident in source['contributionIds']:
            self.assertIn('SRC0951', records('contributions')[ident]['sourceIds'])

    def test_prior_catalogue_is_not_an_orchestral_arrangement(self):
        source = records('sources')['SRC0057']
        self.assertIn('Voice and piano', source['fullCitation'])
        self.assertNotIn('Saegel', source['fullCitation'])
        credit = records('contributions')['CON-S112-L-P051']
        self.assertEqual(credit['certainty'], 'probable')
        self.assertIn('SRC0951', credit['sourceIds'])
        self.assertIn('voice-and-piano entry does not list him', credit['scopeNote'])


if __name__ == '__main__':
    unittest.main()
