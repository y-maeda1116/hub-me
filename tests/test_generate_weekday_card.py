import unittest
from collections import Counter

from scripts.generate_weekday_card import count_by_weekday, generate_svg


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
