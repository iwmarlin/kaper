import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def records(name):
    path = ROOT / 'data' / 'public' / 'v1' / f'{name}.json'
    return {row['id']: row for row in json.loads(path.read_text())['records']}


class DirectorCreditEvidenceTest(unittest.TestCase):
    def test_song_sources_are_not_presented_as_director_evidence(self):
        contributions = records('contributions')
        sources = records('sources')
        inappropriate = {
            'SRC0486': ('CON-F034-D-P018',),
            'SRC0306': ('CON-F004-D-P044', 'CON-F011-D-P022', 'CON-F034-D-P018',
                        'CON-F035-D-P067', 'CON-F040-D-P037', 'CON-F044-D-P013'),
            'SRC0238': ('CON-F047-D-P070', 'CON-F047-D-P082'),
            'SRC0240': ('CON-F047-D-P070', 'CON-F047-D-P082'),
            'SRC0280': ('CON-F050-D-P067',),
            'SRC0281': ('CON-F055-D-P095',),
            'SRC0108': ('CON-F012-D-P048',),
            'SRC0356': ('CON-F012-D-P048',),
            'SRC0173': ('CON-F045-D-P029',),
        }
        for source_id, credit_ids in inappropriate.items():
            for credit_id in credit_ids:
                with self.subTest(source=source_id, credit=credit_id):
                    self.assertNotIn(source_id, contributions[credit_id]['sourceIds'])
                    self.assertNotIn(credit_id, sources[source_id].get('contributionIds', []))
                    self.assertTrue(sources[source_id].get('workIds'))

    def test_balalaika_has_a_director_source(self):
        credit = records('contributions')['CON-F055-D-P095']
        source = records('sources')['SRC0530']
        self.assertIn('SRC0530', credit['sourceIds'])
        self.assertIn(credit['id'], source['contributionIds'])

    def test_last_of_the_pagans_reuses_existing_afi_source(self):
        credit = records('contributions')['CON-F035-D-P067']
        source = records('sources')['SRC0402']
        self.assertIn('SRC0402', credit['sourceIds'])
        self.assertIn(credit['id'], source['contributionIds'])
        self.assertIn('P067', source['personIds'])

    def test_maytime_credits_distinguish_the_production_stages(self):
        contributions = records('contributions')
        sources = records('sources')
        goulding = contributions['CON-F047-D-P082']
        self.assertIn('initial 1936 production', goulding['scopeNote'])
        self.assertIn('some earlier footage may have been included', goulding['scopeNote'])
        for credit_id in ('CON-F047-D-P070', 'CON-F047-D-P082'):
            self.assertIn('SRC0949', contributions[credit_id]['sourceIds'])
            self.assertIn(credit_id, sources['SRC0949']['contributionIds'])

    def test_qualified_director_credit_is_visible_on_person_and_work(self):
        person = (ROOT / 'records/person/P082/index.html').read_text()
        work = (ROOT / 'records/work/W-F047/index.html').read_text()
        self.assertIn('Directed the initial 1936 production', person)
        self.assertIn('Directed the initial 1936 production', work)


if __name__ == '__main__':
    unittest.main()
