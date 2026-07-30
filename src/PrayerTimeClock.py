#!/usr/bin/env python3
import sys

from PySide6.QtWidgets import QApplication

from PyViews.PrayerTimeClockWindow_Impl import PrayerTimeClockWindow


def main():
    if "--health-check" in sys.argv:
        app = QApplication(sys.argv)
        if not issubclass(PrayerTimeClockWindow, object):
            raise RuntimeError("PrayerTimeClockWindow konnte nicht geladen werden.")
        app.quit()
        return
    app = QApplication(sys.argv)
    window = PrayerTimeClockWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
