from bs4 import BeautifulSoup
from datetime import date

from HelperClasses.WebScraperClass import WebScraperClass


def test_extracts_six_prayer_times_from_current_diyanet_row():
    row = BeautifulSoup(
        """
        <tr>
            <td>29.07.2026</td>
            <td>15 Safer 1448</td>
            <td>03:34</td>
            <td>05:14</td>
            <td>13:18</td>
            <td>17:30</td>
            <td>21:12</td>
            <td>22:41</td>
        </tr>
        """,
        "html.parser",
    ).find("tr")

    assert WebScraperClass._extract_times_from_row(row) == [
        "03:34",
        "05:14",
        "13:18",
        "17:30",
        "21:12",
        "22:41",
    ]


def _valid_data(today="29.07.2026", tomorrow="30.07.2026"):
    return {
        "requestSuccess": [True, today],
        "Prayers": ["03:34", "05:14", "13:18", "17:30", "21:12", "22:41"],
        "nextDayPrayers": {
            "date": tomorrow,
            "prayers": ["03:36", "05:16", "13:18", "17:29", "21:10", "22:39"],
        },
    }


def test_validates_dates_contained_in_prayer_data():
    data = _valid_data()

    assert WebScraperClass.prayer_data_date(data) == date(2026, 7, 29)
    assert WebScraperClass.has_expected_dates(data, date(2026, 7, 29))
    assert not WebScraperClass.has_expected_dates(data, date(2026, 7, 30))


def test_rejects_non_consecutive_or_invalid_prayer_dates():
    assert WebScraperClass.prayer_data_date(_valid_data(tomorrow="31.07.2026")) is None
    assert WebScraperClass.prayer_data_date(_valid_data(today="invalid")) is None


def test_selects_fallback_by_exact_date_and_never_by_weekday():
    data = _valid_data()
    data["days"] = {
        "29.07.2026": data["Prayers"],
        "30.07.2026": data["nextDayPrayers"]["prayers"],
        "31.07.2026": ["03:38", "05:18", "13:18", "17:28", "21:08", "22:37"],
    }

    selected = WebScraperClass.data_for_date(data, date(2026, 7, 30))

    assert selected["Prayers"] == data["days"]["30.07.2026"]
    assert selected["nextDayPrayers"]["prayers"] == data["days"]["31.07.2026"]
    assert WebScraperClass.data_for_date(data, date(2026, 8, 5)) is None


def test_reports_last_date_with_a_complete_today_and_tomorrow_pair():
    data = _valid_data()
    data["days"] = {
        "29.07.2026": data["Prayers"],
        "30.07.2026": data["nextDayPrayers"]["prayers"],
        "31.07.2026": ["03:38", "05:18", "13:18", "17:28", "21:08", "22:37"],
    }

    assert WebScraperClass.last_available_date(data, date(2026, 7, 29)) == date(2026, 7, 30)


def test_fallback_horizon_stops_at_first_missing_date():
    data = _valid_data()
    data["days"] = {
        "29.07.2026": data["Prayers"],
        "30.07.2026": data["nextDayPrayers"]["prayers"],
        "01.08.2026": ["03:40", "05:20", "13:18", "17:27", "21:06", "22:35"],
        "02.08.2026": ["03:42", "05:22", "13:18", "17:26", "21:04", "22:33"],
    }

    assert WebScraperClass.last_available_date(data, date(2026, 7, 29)) == date(2026, 7, 29)
