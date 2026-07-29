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
        return times[1:7] if len(times) >= 7 else []

    def get_prayer_times(self):
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        today_text = today.strftime("%d.%m.%Y")
        tomorrow_text = tomorrow.strftime("%d.%m.%Y")
        result = {
            "requestSuccess": [False, today_text],
            "Prayers": [],
            "nextDayPrayers": {"date": tomorrow_text, "prayers": []},
        }

        try:
            response = self.session.get(self.URL, timeout=(4, 12))
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            today_cell = soup.find("td", string=today_text)
            tomorrow_cell = soup.find("td", string=tomorrow_text)
            if not today_cell or not tomorrow_cell:
                return result

            today_times = self._extract_times_from_row(today_cell.parent)
            tomorrow_times = self._extract_times_from_row(tomorrow_cell.parent)
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
