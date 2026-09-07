"""Render the real Qt UI with offline example data, never live Pi settings.

Run from the project root: PYTHONPATH=src QT_QPA_PLATFORM=offscreen \
python scripts/render_qt_preview.py --output /tmp/prayerclock-preview
The displayed prayer times are illustrative, not a prayer-time source.
"""
import argparse
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication
from PyViews import PrayerTimeClockWindow_Impl as impl


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 9, 7, 11, 42, 0)


class FrozenAnimation:
    def elapsed(self):
        return 10000


def example_data(now):
    today = ['04:48', '06:25', '13:07', '16:42', '19:39', '21:09']
    tomorrow = ['04:50', '06:27', '13:07', '16:40', '19:37', '21:07']
    day = now.strftime('%d.%m.%Y')
    next_day = (now + timedelta(days=1)).strftime('%d.%m.%Y')
    return {'requestSuccess': [True, day], 'Prayers': today,
            'nextDayPrayers': {'date': next_day, 'prayers': tomorrow},
            'days': {day: today, next_day: tomorrow}}


def build_preview(app, profile='10 Zoll'):
    window = impl.PrayerTimeClockWindow()
    window.display_profile = profile
    window._apply_display_profile(profile)
    window.showNormal()
    window.resize(1920, 1200)
    for timer in window.findChildren(QTimer):
        timer.stop()
    for widget in (window.islamic_ornament, window.clockPanel):
        widget._animation_clock = FrozenAnimation()
    window._apply_prayer_times(example_data(FrozenDateTime.now()))
    window.update_clock()
    window.wifi_status_button.setIcon(window._wifi_icon(True))
    from PySide6.QtCore import QSize
    window.wifi_status_button.setIconSize(QSize(40, 40))
    window.wifi_status_button.setProperty('connected', True)
    window.wifi_status_button.style().polish(window.wifi_status_button)
    settle(app)
    return window


def settle(app):
    for _ in range(5):
        app.processEvents()


def geometry(window):
    names = ['time_panel', 'clockPanel', 'current_time', 'islamic_ornament', 'current_date',
             'hijri_date', 'islamic_event', 'rest_time', 'midnight_time',
             'quran_arabic', 'quran_translation', 'update_status_panel',
             'retry_time', 'fallback_horizon', 'next_day_prayers_box',
             'current_day_fajr_time', 'next_day_fajr_time']
    return {name: [*getattr(window, name).mapTo(window, getattr(window, name).rect().topLeft()).toTuple(),
                   *getattr(window, name).size().toTuple()] for name in names}


def red_state(window):
    old = FrozenDateTime.now() - timedelta(days=9)
    window.prayer_times_cache = example_data(old)
    window.prayer_times = example_data(old)
    window.last_successful_update_at = old
    window.last_updated_time.setText(old.strftime('%d.%m.%Y · %H:%M'))
    window._apply_prayer_times({'requestSuccess': [False]})
    for timer in window.findChildren(QTimer):
        timer.stop()
    window.update_clock()
    window.wifi_status_button.setIcon(window._wifi_icon(False))
    window.wifi_status_button.setProperty('connected', False)
    window.wifi_status_button.style().polish(window.wifi_status_button)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--tags', action='store_true')
    parser.add_argument('--settings', action='store_true')
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as settings_dir:
        settings = QSettings(str(Path(settings_dir) / 'preview.ini'), QSettings.IniFormat)
        settings.setValue('displayProfile', '10 Zoll')
        with patch.object(impl, 'datetime', FrozenDateTime), \
             patch.object(impl, 'QSettings', return_value=settings), \
             patch.object(impl.PrayerTimeClockWindow, '_refresh_network_status'), \
             patch.object(impl.PrayerTimeClockWindow, 'refresh_data'), \
             patch.object(impl.PrayerTimeClockWindow, '_load_cached_prayer_times'), \
             patch.object(impl.PrayerTimeClockWindow, '_save_prayer_times_cache'), \
             patch.object(impl.PrayerTimeClockWindow, '_apply_brightness'), \
             patch.object(impl.PrayerTimeClockWindow, '_apply_system_audio_gain'):
            window = build_preview(app)
            if args.tags:
                window.islamic_event.setTags(['Weiße Tage', 'Fasten empfohlen'])
                window.tomorrow_islamic_notice.setTags(['Donnerstag', 'Fasten empfohlen'])
                settle(app)
            normal = geometry(window)
            assert normal['islamic_ornament'][1] + normal['islamic_ornament'][3] <= normal['current_date'][1], 'Ornament overlaps date'
            assert window.current_day_fajr_time.font().pixelSize() == window.next_day_fajr_time.font().pixelSize() == 64
            window.grab().save(str(output / 'prayerclock-normal.png'))
            red_state(window)
            settle(app)
            warning = geometry(window)
            window.grab().save(str(output / 'prayerclock-warning.png'))
            difference = {name: [normal[name], warning[name]] for name in normal if normal[name] != warning[name]}
            report = {'window': list(window.size().toTuple()), 'normal': normal,
                      'warning': warning, 'moved_widgets': difference}
            (output / 'geometry.json').write_text(json.dumps(report, indent=2))
            print(json.dumps({'window': report['window'], 'moved_widgets': difference}))
            if args.settings:
                with patch.object(window.update_service, 'available_commits', return_value=0):
                    window.open_settings()
                    dialog = window.settings_dialog
                    dialog.setMinimumSize(0, 0)
                    dialog.resize(1680, 1060)
                    settle(app)
                    dialog.grab().save(str(output / 'prayerclock-settings.png'))
                    dialog.reject()
            window.close()
            if difference:
                raise SystemExit('Layout changes between states')


if __name__ == '__main__':
    main()
