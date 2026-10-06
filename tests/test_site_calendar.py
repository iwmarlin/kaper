import contextlib
import io
import sys
import unittest
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_static_records
import public_data_dates
import validate_site
from site_calendar import publication_today


class PublicationCalendarTests(unittest.TestCase):
    def test_actual_failed_run_instant_is_october_6_in_warsaw(self):
        instant = datetime(2026, 10, 5, 22, 17, tzinfo=timezone.utc)
        self.assertEqual(publication_today(instant), date(2026, 10, 6))

    def test_summer_midnight_boundary(self):
        self.assertEqual(publication_today(datetime(2026, 7, 1, 21, 59, tzinfo=timezone.utc)), date(2026, 7, 1))
        self.assertEqual(publication_today(datetime(2026, 7, 1, 22, 0, tzinfo=timezone.utc)), date(2026, 7, 2))

    def test_winter_midnight_boundary(self):
        self.assertEqual(publication_today(datetime(2026, 1, 1, 22, 59, tzinfo=timezone.utc)), date(2026, 1, 1))
        self.assertEqual(publication_today(datetime(2026, 1, 1, 23, 0, tzinfo=timezone.utc)), date(2026, 1, 2))

    def test_same_instant_in_different_timezones_has_same_date(self):
        instant = datetime(2026, 10, 5, 22, 17, tzinfo=timezone.utc)
        pacific = instant.astimezone(timezone(timedelta(hours=-7)))
        self.assertEqual(publication_today(instant), publication_today(pacific))

    def test_naive_timestamp_is_not_interpreted_in_host_timezone(self):
        with self.assertRaises(ValueError):
            publication_today(datetime(2026, 10, 5, 22, 17))

    def test_default_clock_requests_warsaw_timezone(self):
        with patch("site_calendar.datetime") as clock:
            clock.now.return_value = datetime(2026, 10, 5, 22, 17, tzinfo=timezone.utc)
            self.assertEqual(publication_today(), date(2026, 10, 6))
            self.assertEqual(clock.now.call_args.args[0].key, "Europe/Warsaw")

    def test_manifest_uses_publication_calendar(self):
        with patch.object(public_data_dates, "publication_today", return_value=date(2026, 10, 6)):
            self.assertEqual(public_data_dates.resolve_public_data_updated_at("2026-10-05", data_changed=True), "2026-10-06")

    def test_sitemap_builder_uses_publication_calendar(self):
        with patch.object(sys, "argv", ["build_static_records.py", "--root", str(ROOT)]), patch.object(build_static_records, "publication_today", return_value=date(2026, 10, 6)), patch.object(build_static_records, "build", return_value={}) as build, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(build_static_records.main(), 0)
            build.assert_called_once_with(ROOT, "2026-10-06")

    def test_validator_accepts_october_6_when_it_is_already_that_day_in_warsaw(self):
        with patch.object(validate_site, "publication_today", return_value=date(2026, 10, 6)):
            self.assertFalse(validate_site.sitemap_date_is_future(date(2026, 10, 6)))

    def test_validator_still_rejects_genuinely_future_dates(self):
        with patch.object(validate_site, "publication_today", return_value=date(2026, 10, 5)):
            self.assertTrue(validate_site.sitemap_date_is_future(date(2026, 10, 6)))


if __name__ == "__main__":
    unittest.main()
