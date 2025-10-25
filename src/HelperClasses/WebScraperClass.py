import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

TIME_RE = re.compile(r"^\d{2}:\d{2}$")

class WebScraperClass:
    def __init__(self):
        self.url = "https://namazvakitleri.diyanet.gov.tr/de-DE/11002/gebetszeit-fur-berlin"

    def _extract_times_from_row(self, tr):
        # Alle Zellen holen
        cells = [td.get_text(strip=True).replace("\xa0", " ") for td in tr.find_all("td")]
        # Nur echte Uhrzeiten
        times_all = [c for c in cells if TIME_RE.fullmatch(c)]
        # Erste HH:MM ist die Beschreibungszeit -> weg
        if times_all:
            times = times_all[1:]
        else:
            times = []
        # Sicherheit: Auf 7 Zeiten begrenzen
        return times[:7]

    def get_prayer_times(self):
        today = datetime.now()
        tomorrow = today + timedelta(days=1)

        today_s = today.strftime("%d.%m.%Y")
        tomorrow_s = tomorrow.strftime("%d.%m.%Y")

        out = {
            "requestSuccess": [False, today_s],
            "Prayers": [],
            "nextDayPrayers": {"date": tomorrow_s, "prayers": []},
        }

        try:
            resp = requests.get(self.url, timeout=20)
            if resp.status_code != 200:
                return out

            soup = BeautifulSoup(resp.text, "html.parser")
            out["requestSuccess"][0] = True

            td_today = soup.find("td", string=today_s)
            if td_today and td_today.parent:
                out["Prayers"] = self._extract_times_from_row(td_today.parent)

            td_tom = soup.find("td", string=tomorrow_s)
            if td_tom and td_tom.parent:
                out["nextDayPrayers"]["prayers"] = self._extract_times_from_row(td_tom.parent)

            return out
        except Exception:
            return out
