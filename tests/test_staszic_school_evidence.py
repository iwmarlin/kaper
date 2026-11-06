import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def records(name):
    return {row['id']: row for row in json.loads((ROOT / 'data/public/v1' / (name + '.json')).read_text())['records']}


class StaszicSchoolEvidenceTest(unittest.TestCase):
    def test_school_opening_is_not_presented_as_personal_admission(self):
        event = records('timeline-events')['TE0002']
        source = records('sources')['SRC0948']
        media = records('media')['M464']
        self.assertEqual(event['displayDate'], '1915/16 school year')
        self.assertEqual(event['dateStart'], '1915-01-01')
        self.assertIn('6 September 1915', event['longDescription'])
        self.assertIn('does not name them', event['longDescription'])
        self.assertIn('Skrynnikov’s school was private', source['researchNote'])
        self.assertIn('M464', event['mediaIds'])
        self.assertIn('M464', source['mediaIds'])
        self.assertEqual(media['sourceIds'], ['SRC0948'])
        self.assertIn('TE0002', media['timelineEventIds'])
        self.assertTrue((ROOT / media['assetPath']).is_file())

    def test_later_school_site_is_linked_with_date_qualification(self):
        event = records('timeline-events')['TE0002']
        place = records('places')['PL009']
        self.assertIn('PL009', event['placeIds'])
        self.assertIn('TE0002', place['timelineEventIds'])
        self.assertIn('later school site', event['longDescription'])
        self.assertIn('not as a confirmed location of the transfer', place['publicNote'])
