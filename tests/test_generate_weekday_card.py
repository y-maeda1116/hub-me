import contextlib
import io
import json
import math
import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from scripts.generate_weekday_card import (
    _fetch_window,
    count_by_weekday,
    fetch_commit_dates,
    generate_svg,
    main,
    parse_commit_date,
)

SINCE = datetime(2026, 1, 1, tzinfo=timezone.utc)
FROZEN_NOW = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)


class _FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return FROZEN_NOW


def _expected_bounds():
    span = FROZEN_NOW - SINCE
    count = max(1, math.ceil(span.total_seconds() / (30 * 86400)))
    return [SINCE + (span / count) * i for i in range(count + 1)]


class TestCountByWeekday(unittest.TestCase):
    def test_counts_monday(self):
        dates = ["2026-05-04T10:00:00Z"]
        result = count_by_weekday(dates, utc_offset=0)
        self.assertEqual(result[0], 1)
        self.assertEqual(sum(result), 1)

    def test_counts_sunday(self):
        dates = ["2026-05-10T10:00:00Z"]
        result = count_by_weekday(dates, utc_offset=0)
        self.assertEqual(result[6], 1)

    def test_applies_utc_offset(self):
        dates = ["2026-05-04T20:00:00Z"]
        result = count_by_weekday(dates, utc_offset=9)
        self.assertEqual(result[1], 1)

    def test_empty_dates(self):
        result = count_by_weekday([], utc_offset=0)
        self.assertEqual(result, [0, 0, 0, 0, 0, 0, 0])

    def test_multiple_commits(self):
        dates = ["2026-05-04T10:00:00Z", "2026-05-04T12:00:00Z", "2026-05-05T10:00:00Z"]
        result = count_by_weekday(dates, utc_offset=0)
        self.assertEqual(result[0], 2)
        self.assertEqual(result[1], 1)


class TestFetchCommitDates(unittest.TestCase):
    @patch("scripts.generate_weekday_card.subprocess.run")
    def test_single_page(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='["2026-05-04T10:00:00Z", "2026-05-05T12:00:00Z"]',
        )
        dates = fetch_commit_dates("testuser")
        self.assertEqual(len(dates), 2)

    @patch("scripts.generate_weekday_card.time.sleep")
    @patch("scripts.generate_weekday_card.subprocess.run")
    def test_pagination(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps(["2026-05-04T10:00:00Z"] * 100)),
            MagicMock(returncode=0, stdout='["2026-05-05T12:00:00Z"]'),
            MagicMock(returncode=0, stdout="[]"),
        ]
        dates = fetch_commit_dates("testuser")
        self.assertEqual(len(dates), 101)

    @patch("scripts.generate_weekday_card.time.sleep")
    @patch("scripts.generate_weekday_card.subprocess.run")
    def test_stops_at_search_api_1000_results_cap(self, mock_run, mock_sleep):
        full_page = json.dumps(["2026-05-04T10:00:00Z"] * 100)
        mock_run.return_value = MagicMock(returncode=0, stdout=full_page)
        with contextlib.redirect_stderr(io.StringIO()) as err:
            dates = fetch_commit_dates("testuser")
        self.assertEqual(len(dates), 1000)
        self.assertEqual(mock_run.call_count, 10)
        self.assertIn("truncated", err.getvalue())

    @patch("scripts.generate_weekday_card.time.sleep")
    @patch("scripts.generate_weekday_card.subprocess.run")
    def test_pauses_between_pages(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps(["2026-05-04T10:00:00Z"] * 100)),
            MagicMock(returncode=0, stdout=json.dumps(["2026-05-04T10:00:00Z"] * 100)),
            MagicMock(returncode=0, stdout='["2026-05-05T12:00:00Z"]'),
        ]
        dates = fetch_commit_dates("testuser")
        self.assertEqual(len(dates), 201)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("scripts.generate_weekday_card.time.sleep")
    @patch("scripts.generate_weekday_card.subprocess.run")
    def test_api_error(self, mock_run, mock_sleep):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        dates = fetch_commit_dates("testuser")
        self.assertIsNone(dates)

    @patch("scripts.generate_weekday_card.time.sleep")
    @patch("scripts.generate_weekday_card.subprocess.run")
    def test_error_mid_pagination(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps(["2026-05-04T10:00:00Z"] * 100)),
            MagicMock(returncode=1, stdout=""),
            MagicMock(returncode=1, stdout=""),
            MagicMock(returncode=1, stdout=""),
        ]
        dates = fetch_commit_dates("testuser")
        self.assertIsNone(dates)

    @patch("scripts.generate_weekday_card.time.sleep")
    @patch("scripts.generate_weekday_card.subprocess.run")
    def test_retries_transient_failure_then_succeeds(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="secondary rate limit"),
            MagicMock(returncode=0, stdout='["2026-05-04T10:00:00Z"]'),
        ]
        dates = fetch_commit_dates("testuser")
        self.assertEqual(dates, ["2026-05-04T10:00:00Z"])
        self.assertEqual(mock_run.call_count, 2)
        mock_sleep.assert_called_once_with(60)

    @patch("scripts.generate_weekday_card.time.sleep")
    @patch("scripts.generate_weekday_card.subprocess.run")
    def test_returns_none_after_exhausting_retries(self, mock_run, mock_sleep):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertIsNone(fetch_commit_dates("testuser"))
        self.assertEqual(mock_run.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("scripts.generate_weekday_card.subprocess.run")
    def test_invalid_json(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="not json")
        dates = fetch_commit_dates("testuser")
        self.assertIsNone(dates)

class TestFetchWindow(unittest.TestCase):
    @patch("scripts.generate_weekday_card.subprocess.run")
    def test_without_dates_omits_range_qualifier(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='["2026-05-04T10:00:00Z"]')
        dates = _fetch_window("testuser")
        self.assertEqual(dates, ["2026-05-04T10:00:00Z"])
        query = mock_run.call_args[0][0][2]
        self.assertIn("author:testuser", query)
        self.assertNotIn("committer-date:", query)

    @patch("scripts.generate_weekday_card.subprocess.run")
    def test_with_dates_includes_range_qualifier(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='["2026-05-04T10:00:00Z"]')
        _fetch_window("testuser", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
        query = mock_run.call_args[0][0][2]
        self.assertIn("author-date:2026-01-01..2026-01-31", query)

    @patch("scripts.generate_weekday_card.time.sleep")
    @patch("scripts.generate_weekday_card.subprocess.run")
    def test_returns_none_on_api_error(self, mock_run, mock_sleep):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertIsNone(_fetch_window("testuser"))

    @patch("scripts.generate_weekday_card.time.sleep")
    @patch("scripts.generate_weekday_card.subprocess.run")
    def test_paginates_until_short_page(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps(["2026-05-04T10:00:00Z"] * 100)),
            MagicMock(returncode=0, stdout='["2026-05-05T12:00:00Z"]'),
        ]
        dates = _fetch_window(
            "testuser", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31)
        )
        self.assertEqual(len(dates), 101)


class TestFetchCommitDatesWithinWindow(unittest.TestCase):
    def setUp(self):
        patcher = patch("scripts.generate_weekday_card.datetime", _FrozenDateTime)
        patcher.start()
        self.addCleanup(patcher.stop)

    @patch("scripts.generate_weekday_card._fetch_window")
    def test_tiles_span_with_date_range_windows(self, mock_window):
        mock_window.return_value = []
        self.assertIsNotNone(fetch_commit_dates("testuser", since=SINCE))
        calls = mock_window.call_args_list
        # 255.5-day fixture span / ~30-day windows = 9 windows
        self.assertEqual(len(calls), 9)
        self.assertEqual(calls[0].kwargs["start_date"], SINCE.date())
        for i, call in enumerate(calls):
            self.assertEqual(call.args[0], "testuser")
            self.assertLess(call.kwargs["start_date"], call.kwargs["end_date"])
            if i + 1 < len(calls):
                self.assertEqual(
                    calls[i].kwargs["end_date"], calls[i + 1].kwargs["start_date"]
                )

    @patch("scripts.generate_weekday_card._fetch_window")
    def test_accepts_window_just_under_search_cap(self, mock_window):
        mock_window.return_value = ["2026-05-04T10:00:00Z"] * 999
        self.assertIsNotNone(fetch_commit_dates("testuser", since=SINCE))

    @patch("scripts.generate_weekday_card._fetch_window")
    def test_skips_offset_naive_dates_without_crashing(self, mock_window):
        def fake_window(owner, start_date=None, end_date=None):
            if start_date == SINCE.date():
                return ["2026-05-04T10:00:00"]
            return []

        mock_window.side_effect = fake_window
        dates = fetch_commit_dates("testuser", since=SINCE)
        self.assertEqual(dates, [])

    @patch("scripts.generate_weekday_card._fetch_window")
    def test_keeps_only_dates_inside_half_open_window(self, mock_window):
        bounds = _expected_bounds()
        window0_raw = [
            SINCE.isoformat(),           # exactly at since: kept
            bounds[1].isoformat(),       # window0 end boundary: belongs to window1
            bounds[2].isoformat(),       # beyond window0: dropped
            "2025-12-25T00:00:00+00:00",  # before since: dropped
        ]
        window1_raw = [
            bounds[1].isoformat(),       # window1 start boundary: kept exactly once
            bounds[2].isoformat(),       # window1 end boundary: belongs to window2
        ]

        def fake_window(owner, start_date=None, end_date=None):
            if start_date == SINCE.date():
                return window0_raw
            if start_date == bounds[1].date():
                return window1_raw
            return []

        mock_window.side_effect = fake_window
        dates = fetch_commit_dates("testuser", since=SINCE)
        self.assertEqual(dates, [SINCE.isoformat(), bounds[1].isoformat()])

    @patch("scripts.generate_weekday_card._fetch_window")
    def test_returns_none_when_window_hits_search_cap(self, mock_window):
        mock_window.return_value = ["2026-05-04T10:00:00Z"] * 1000
        self.assertIsNone(fetch_commit_dates("testuser", since=SINCE))

    @patch("scripts.generate_weekday_card._fetch_window")
    def test_returns_none_on_window_api_failure(self, mock_window):
        mock_window.return_value = None
        self.assertIsNone(fetch_commit_dates("testuser", since=SINCE))


class TestMain(unittest.TestCase):
    def test_exits_nonzero_when_fetch_fails(self):
        with patch("scripts.generate_weekday_card.fetch_commit_dates", return_value=None), \
             patch("sys.argv", ["prog", "--output", "/tmp/unused.svg"]):
            with self.assertRaises(SystemExit) as ctx:
                main()
        self.assertEqual(ctx.exception.code, 1)

    def test_defaults_to_one_year_window(self):
        with patch("scripts.generate_weekday_card.fetch_commit_dates", return_value=[]) as mock_fetch, \
             patch("sys.argv", ["prog", "--output", "/dev/null"]):
            main()
        since = mock_fetch.call_args.kwargs["since"]
        expected = datetime.now(timezone.utc) - timedelta(days=365)
        self.assertAlmostEqual(since.timestamp(), expected.timestamp(), delta=60)

    def test_days_option_sets_window(self):
        with patch("scripts.generate_weekday_card.fetch_commit_dates", return_value=[]) as mock_fetch, \
             patch("sys.argv", ["prog", "--output", "/dev/null", "--days", "30"]):
            main()
        since = mock_fetch.call_args.kwargs["since"]
        expected = datetime.now(timezone.utc) - timedelta(days=30)
        self.assertAlmostEqual(since.timestamp(), expected.timestamp(), delta=60)

    def test_days_option_rejects_nonpositive_values(self):
        for invalid in ("0", "-30"):
            with patch("sys.argv", ["prog", "--output", "/dev/null", "--days", invalid]), \
                 patch("scripts.generate_weekday_card.fetch_commit_dates") as mock_fetch:
                with self.assertRaises(SystemExit) as ctx:
                    main()
            self.assertEqual(ctx.exception.code, 2)
            mock_fetch.assert_not_called()


class TestParseCommitDate(unittest.TestCase):
    def test_parses_z_suffix(self):
        self.assertEqual(
            parse_commit_date("2026-05-04T10:00:00Z"),
            datetime(2026, 5, 4, 10, 0, tzinfo=timezone.utc),
        )

    def test_parses_numeric_offset(self):
        self.assertEqual(
            parse_commit_date("2026-05-04T10:00:00+09:00"),
            datetime(2026, 5, 4, 10, 0, tzinfo=timezone(timedelta(hours=9))),
        )

    def test_returns_none_on_malformed_input(self):
        self.assertIsNone(parse_commit_date("not a date"))

    def test_returns_none_on_none_input(self):
        self.assertIsNone(parse_commit_date(None))


class TestGenerateSvg(unittest.TestCase):
    def test_generates_valid_svg(self):
        counts = [10, 5, 8, 3, 7, 1, 2]
        svg = generate_svg(counts)
        self.assertIn("<svg", svg)
        self.assertIn("</svg>", svg)
        self.assertIn("Commits per Day", svg)

    def test_includes_all_weekdays(self):
        counts = [1, 2, 3, 4, 5, 6, 7]
        svg = generate_svg(counts)
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            self.assertIn(day, svg)

    def test_zero_counts(self):
        counts = [0, 0, 0, 0, 0, 0, 0]
        svg = generate_svg(counts)
        self.assertIn("<svg", svg)
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            self.assertIn(day, svg)

    def test_single_count(self):
        counts = [5, 0, 0, 0, 0, 0, 0]
        svg = generate_svg(counts)
        self.assertIn(">5<", svg)


if __name__ == "__main__":
    unittest.main()
