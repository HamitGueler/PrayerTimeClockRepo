import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from HelperClasses.PrayerTimeFreshness import fallback_horizon_text


class FallbackHorizonTests(unittest.TestCase):
    def test_text_uses_real_remaining_dates(self):
        today = date(2026, 7, 30)

        self.assertEqual(fallback_horizon_text(date(2026, 8, 5), today), "Fallback noch 6 Tage verfügbar")
        self.assertEqual(fallback_horizon_text(date(2026, 7, 31), today), "Fallback noch 1 Tag verfügbar")
        self.assertEqual(fallback_horizon_text(today, today), "Fallback endet heute")
        self.assertEqual(fallback_horizon_text(None, today), "Kein Fallback verfügbar")


if __name__ == "__main__":
    unittest.main()
