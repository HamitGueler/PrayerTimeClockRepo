#!/path/to/your/venv/bin/python
import sys
from PySide6.QtWidgets import (QApplication)
from PyViews.PrayerTimeClockWindow_Impl import PrayerTimeClockWindow


def main():
    print("Hello World")

    with open("startup.log", "a") as f:
        f.write(">>> App gestartet\n")
    app = QApplication(sys.argv)
    PrayerClock = PrayerTimeClockWindow()
    PrayerClock.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()