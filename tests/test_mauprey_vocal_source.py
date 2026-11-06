import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def records(name):
    return {r['id']: r for r in json.loads((ROOT / 'data/public/v1' / f'{name}.json').read_text())['records']}


class MaupreyVocalSourceTests(unittest.TestCase):
    def test_vocal_edition_documents_french_and_original_words(self):
        source = records('sources')['SRC0950']
        self.assertEqual(source['sourceType'], 'sheet_music_catalogue')
        self.assertEqual(source['primaryUrl'], 'https://catalogue.bnf.fr/ark:/12148/cb43069600z')
        self.assertIn('French words by André Mauprey', source['fullCitation'])
        self.assertIn('original words by Fritz Rotter', source['fullCitation'])
        self.assertIn('score itself was not examined', source['researchNote'])
        for ident in source['contributionIds']:
            with self.subTest(credit=ident):
                self.assertIn('SRC0950', records('contributions')[ident]['sourceIds'])

    def test_orchestral_catalogue_is_not_evidence_of_maupreys_words(self):
        credit = records('contributions')['CON-S050-L-P005']
        self.assertIn('SRC0950', credit['sourceIds'])
        self.assertNotIn('SRC0070', credit['sourceIds'])
        self.assertNotIn(credit['id'], records('sources')['SRC0070']['contributionIds'])
        self.assertIn('SRC0070', records('works')['W-S050']['sourceIds'])


if __name__ == '__main__':
    unittest.main()
