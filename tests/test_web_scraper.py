from bs4 import BeautifulSoup

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
