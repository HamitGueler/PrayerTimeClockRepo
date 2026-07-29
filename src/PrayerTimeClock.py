#!/usr/bin/env python3
import sys

from PySide6.QtWidgets import QApplication

from PyViews.PrayerTimeClockWindow_Impl import PrayerTimeClockWindow


def main():
    app = QApplication(sys.argv)
    window = PrayerTimeClockWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
