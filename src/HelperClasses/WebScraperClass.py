import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup


TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class WebScraperClass:
    URL = "https://namazvakitleri.diyanet.gov.tr/de-DE/11002/gebetszeit-fur-berlin"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "PrayerTimeClock/2.0"})

    @staticmethod
    def _extract_times_from_row(row):
        cells = [cell.get_text(strip=True).replace("\xa0", " ") for cell in row.find_all("td")]
        times = [cell for cell in cells if TIME_RE.fullmatch(cell)]
        return times[:6] if len(times) >= 6 else []

    def get_prayer_times(self):
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        today_text = today.strftime("%d.%m.%Y")
        tomorrow_text = tomorrow.strftime("%d.%m.%Y")
        result = {
            "requestSuccess": [False, today_text],
            "Prayers": [],
            "nextDayPrayers": {"date": tomorrow_text, "prayers": []},
            "days": {},
        }

        try:
            response = self.session.get(self.URL, timeout=(4, 12))
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for offset in range(8):
                day_text = (today + timedelta(days=offset)).strftime("%d.%m.%Y")
                day_cell = soup.find("td", string=day_text)
                if day_cell:
                    times = self._extract_times_from_row(day_cell.parent)
                    if len(times) == 6:
                        result["days"][day_text] = times

            today_times = result["days"].get(today_text, [])
            tomorrow_times = result["days"].get(tomorrow_text, [])
            if len(today_times) != 6 or len(tomorrow_times) != 6:
                return result

            result["requestSuccess"][0] = True
            result["Prayers"] = today_times
            result["nextDayPrayers"]["prayers"] = tomorrow_times
        except (requests.RequestException, AttributeError, ValueError):
            pass

        return result

    @staticmethod
    def has_valid_prayer_times(data):
        try:
            today = data["Prayers"]
            tomorrow = data["nextDayPrayers"]["prayers"]
            return (
                len(today) == 6
                and len(tomorrow) == 6
                and all(TIME_RE.fullmatch(value) for value in today + tomorrow)
            )
        except (KeyError, TypeError):
            return False

    @staticmethod
    def prayer_data_date(data):
        try:
            today = datetime.strptime(data["requestSuccess"][1], "%d.%m.%Y").date()
            tomorrow = datetime.strptime(data["nextDayPrayers"]["date"], "%d.%m.%Y").date()
            return today if tomorrow == today + timedelta(days=1) else None
        except (IndexError, KeyError, TypeError, ValueError):
            return None

    @classmethod
    def has_expected_dates(cls, data, expected_date=None):
        expected_date = expected_date or datetime.now().date()
        return cls.prayer_data_date(data) == expected_date

    @staticmethod
    def _dated_prayers(data):
        dated_prayers = {}
        for day_text, prayers in data.get("days", {}).items():
            try:
                day = datetime.strptime(day_text, "%d.%m.%Y").date()
            except (TypeError, ValueError):
                continue
            if (
                isinstance(prayers, list)
                and len(prayers) == 6
                and all(isinstance(value, str) and TIME_RE.fullmatch(value) for value in prayers)
            ):
                dated_prayers[day] = prayers

        if not dated_prayers:
            try:
                today = datetime.strptime(data["requestSuccess"][1], "%d.%m.%Y").date()
                tomorrow = datetime.strptime(data["nextDayPrayers"]["date"], "%d.%m.%Y").date()
                dated_prayers[today] = data["Prayers"]
                dated_prayers[tomorrow] = data["nextDayPrayers"]["prayers"]
            except (IndexError, KeyError, TypeError, ValueError):
                pass
        return dated_prayers

    @classmethod
    def data_for_date(cls, data, target_date):
        dated_prayers = cls._dated_prayers(data)
        tomorrow = target_date + timedelta(days=1)
        if target_date not in dated_prayers or tomorrow not in dated_prayers:
            return None
        return {
            "requestSuccess": [True, target_date.strftime("%d.%m.%Y")],
            "Prayers": dated_prayers[target_date],
            "nextDayPrayers": {
                "date": tomorrow.strftime("%d.%m.%Y"),
                "prayers": dated_prayers[tomorrow],
            },
            "days": data.get("days", {}),
        }

    @classmethod
    def last_available_date(cls, data, today):
        dated_prayers = cls._dated_prayers(data)
        last_available = None
        cursor = today
        while cursor in dated_prayers and cursor + timedelta(days=1) in dated_prayers:
            last_available = cursor
            cursor += timedelta(days=1)
        return last_available
