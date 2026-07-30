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
