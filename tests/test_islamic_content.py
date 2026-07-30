import unittest
from datetime import datetime
from unittest.mock import patch

from src.PyViews.IslamicContent import (
    get_hijri_info,
    special_day_status,
    special_day_statuses,
    special_day_tomorrow_notice,
    special_day_tomorrow_notices,
    uses_celebration_palette,
)


class SpecialDayStatusTests(unittest.TestCase):
    def test_berlin_calendar_default_makes_july_30_third_white_day(self):
        with patch.dict("os.environ", {}, clear=True):
            tomorrow = get_hijri_info(datetime(2026, 7, 30))
        self.assertEqual((15, 2), (tomorrow["day"], tomorrow["month"]))
        self.assertEqual(
            ["DONNERSTAG", "15. WEISSER TAG", "FASTEN EMPFOHLEN"],
            special_day_tomorrow_notices(tomorrow["day"], tomorrow["month"], weekday=3),
        )

    def test_hijri_adjustment_can_be_selected_in_settings(self):
        previous = get_hijri_info(datetime(2026, 7, 30), adjustment=-2)
        default = get_hijri_info(datetime(2026, 7, 30), adjustment=-1)
        following = get_hijri_info(datetime(2026, 7, 30), adjustment=0)
        self.assertEqual(default["day"] - 1, previous["day"])
        self.assertEqual(default["day"] + 1, following["day"])

    def test_white_days_have_today_and_tomorrow_indicators(self):
        self.assertIn("HEUTE", special_day_status(13, 2))
        self.assertIn("FASTEN", special_day_status(13, 2))
        self.assertIn("FASTEN EMPFOHLEN", special_day_tomorrow_notice(14, 2))
        self.assertNotIn("MORGEN", special_day_tomorrow_notice(14, 2))

    def test_arafah_shows_both_matching_tags(self):
        self.assertEqual(
            "HEUTE · | 9. TAG VON DHŪ L-ḤIDDSCHA | | ʿARAFAH | | FASTEN EMPFOHLEN |",
            special_day_status(9, 12),
        )
        self.assertEqual(1, special_day_status(9, 12).count("HEUTE"))

    def test_odd_ramadan_nights_show_both_matching_tags(self):
        for day in (21, 23, 25, 27, 29):
            with self.subTest(day=day):
                status = special_day_status(day, 9)
                self.assertIn("LAYLAT AL-QADR SUCHEN", status)
                self.assertIn("LETZTE ZEHN NÄCHTE RAMAḌĀN", status)

    def test_arafah_tomorrow_shows_both_matching_tags(self):
        notice = special_day_tomorrow_notice(9, 12)
        self.assertIn("ʿARAFAH", notice)
        self.assertIn("9. TAG VON DHŪ L-ḤIDDSCHA", notice)

    def test_eid_tomorrow_shows_both_matching_tags(self):
        notice = special_day_tomorrow_notice(10, 12)
        self.assertEqual("| 10. TAG VON DHŪ L-ḤIDDSCHA | | ʿĪD AL-AḌḤĀ |", notice)

    def test_monday_and_thursday_are_announced_for_tomorrow(self):
        self.assertEqual(
            ["MONTAG", "FASTEN EMPFOHLEN"],
            special_day_tomorrow_notices(8, 2, weekday=0),
        )
        self.assertEqual(
            ["DONNERSTAG", "FASTEN EMPFOHLEN"],
            special_day_tomorrow_notices(8, 2, weekday=3),
        )

    def test_jumuah_is_shown_today_and_in_tomorrow_panel(self):
        self.assertEqual(["JUMUʿAH"], special_day_statuses(8, 2, weekday=4))
        self.assertEqual(["JUMUʿAH"], special_day_tomorrow_notices(8, 2, weekday=4))

    def test_jumuah_keeps_other_matching_events(self):
        statuses = special_day_statuses(27, 9, weekday=4)
        self.assertIn("JUMUʿAH", statuses)
        self.assertIn("27. NACHT · LAYLAT AL-QADR SUCHEN", statuses)
        self.assertIn("LETZTE ZEHN NÄCHTE RAMAḌĀN", statuses)

    def test_rare_highlights_use_celebration_palette(self):
        for month, day in ((1, 10), (9, 1), (9, 27), (10, 1), (12, 9), (12, 10)):
            with self.subTest(month=month, day=day):
                self.assertTrue(uses_celebration_palette(day, month))
        self.assertFalse(uses_celebration_palette(8, 2))

    def test_overlapping_fasting_reasons_show_recommendation_once(self):
        notices = special_day_tomorrow_notices(14, 2, weekday=0)
        self.assertEqual(["MONTAG", "14. WEISSER TAG", "FASTEN EMPFOHLEN"], notices)
        self.assertEqual(1, notices.count("FASTEN EMPFOHLEN"))

    def test_no_voluntary_fasting_prompt_on_eid_or_tashriq(self):
        self.assertNotIn("FASTEN EMPFOHLEN", special_day_tomorrow_notices(1, 10, weekday=0))
        self.assertNotIn("FASTEN EMPFOHLEN", special_day_tomorrow_notices(10, 12, weekday=3))
        self.assertNotIn("WEISSER TAG", special_day_tomorrow_notices(13, 12, weekday=0))

    def test_even_last_night_stays_general(self):
        self.assertEqual(
            "HEUTE · | LETZTE ZEHN NÄCHTE RAMAḌĀN |",
            special_day_status(22, 9),
        )

    def test_regular_day_has_no_indicator(self):
        self.assertEqual("", special_day_status(8, 2))
        self.assertEqual("", special_day_tomorrow_notice(8, 2))


if __name__ == "__main__":
    unittest.main()
