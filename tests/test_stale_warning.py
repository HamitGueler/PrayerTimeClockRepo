import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from HelperClasses.PrayerTimeFreshness import is_critical_stale


class StaleWarningTests(unittest.TestCase):
    def test_warning_stays_off_before_seven_days(self):
        now = datetime(2026, 7, 30, 12, 0)

        self.assertFalse(
            is_critical_stale(
                now - timedelta(days=6, hours=23, minutes=59),
                now,
                False,
                timedelta(days=7),
            )
        )

    def test_warning_turns_on_after_seven_days_without_current_times(self):
        now = datetime(2026, 7, 30, 12, 0)

        self.assertTrue(
            is_critical_stale(
                now - timedelta(days=7),
                now,
                False,
                timedelta(days=7),
            )
        )

    def test_warning_stays_off_when_current_times_are_available(self):
        now = datetime(2026, 7, 30, 12, 0)

        self.assertFalse(
            is_critical_stale(
                now - timedelta(days=8),
                now,
                True,
                timedelta(days=7),
            )
        )


if __name__ == "__main__":
    unittest.main()
