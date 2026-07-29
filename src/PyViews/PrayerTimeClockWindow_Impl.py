import json
import os
from datetime import datetime, timedelta

from PySide6.QtCore import QTimer, Qt, QUrl, Slot
from PySide6.QtGui import QCursor
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QMainWindow

from PyViews.PrayerTimeClockWindow import Ui_MainWindow
from PyViews.IslamicContent import (
    daily_verse,
    get_hijri_info,
    special_day_statuses,
    special_day_tomorrow_notices,
)
from HelperClasses.WebScraperClass import WebScraperClass


class PrayerTimeClockWindow(QMainWindow, Ui_MainWindow):
    # Diyanet order: Fajr/Imsak, sunrise, Dhuhr, Asr, Maghrib, Isha.
    ACTUAL_PRAYER_INDICES = (0, 2, 3, 4, 5)
    PRAYER_NAMES = ("FAJR", "SHURŪQ", "DHUHR", "ASR", "MAGHRIB", "ISHA")

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("PrayerTimeClock")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.showFullScreen()

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(os.path.join(self.current_dir, "..", ".."))
        self.src_dir = os.path.abspath(os.path.join(self.current_dir, ".."))
        self.cache_path = os.path.join(self.src_dir, "prayer_times_cache.json")
        self.fajr_adhan_path = os.path.join(self.src_dir, "AudioFiles", "fajr_adhan.mp3")
        self.adhan_path = os.path.join(self.src_dir, "AudioFiles", "adhan.mp3")
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(1.0)
        self.audio_player = QMediaPlayer(self)
        self.audio_player.setAudioOutput(self.audio_output)
        self.audio_player.playbackStateChanged.connect(self._on_audio_state_changed)
        self.adhan_blink_timer = QTimer(self)
        self.adhan_blink_timer.setInterval(450)
        self.adhan_blink_timer.timeout.connect(self._toggle_adhan_blink)
        self.adhan_blink_visible = False
        self.active_prayer_index = None

        self.scraper = WebScraperClass()
        self.prayer_times = {}
        self.fetch_in_progress = False
        self.last_fetch_date = None
        self.last_adhan_key = None
        self.last_content_date = None

        self.current_prayers = [
            self.current_day_fajr_time, self.current_day_shroq_time, self.current_day_zohr_time,
            self.current_day_asr_time, self.current_day_magrb_time, self.current_day_isha_time,
        ]
        self.tomorrows_prayers = [
            self.next_day_fajr_time, self.next_day_shroq_time, self.next_day_zohr_time,
            self.next_day_asr_time, self.next_day_magrb_time, self.next_day_isha_time,
        ]
        self.prayer_boxes = [
            self.fajr_box, self.shroq_box, self.zohr_box,
            self.asr_box, self.magrb_box, self.isha_box,
        ]

        style_path = os.path.join(self.project_root, "style.css")
        with open(style_path, encoding="utf-8") as style_file:
            self.setStyleSheet(style_file.read())

        self.refresh_button.clicked.connect(self.refresh_data)
        self.refresh_button.setCursor(QCursor(Qt.PointingHandCursor))

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        self.retry_timer = QTimer(self)
        self.retry_timer.setInterval(5 * 60 * 1000)
        self.retry_timer.timeout.connect(self.refresh_data)
        self.retry_time.hide()

        self.update_clock()
        self._load_cached_prayer_times()
        self.refresh_data()

    @Slot()
    def refresh_data(self):
        if self.fetch_in_progress:
            return
        self.fetch_in_progress = True
        self.refresh_button.setDisabled(True)
        try:
            self._apply_prayer_times(self.scraper.get_prayer_times())
        finally:
            self.fetch_in_progress = False
            self.refresh_button.setDisabled(False)

    @Slot(dict)
    def _apply_prayer_times(self, data):
        now = datetime.now()
        if data.get("requestSuccess", [False])[0] and self.scraper.has_valid_prayer_times(data):
            self.prayer_times = data
            self.last_fetch_date = now.date()
            self.retry_timer.stop()
            self.retry_time.hide()
            self.led_sign.setProperty("online", True)
            self.last_updated_time.setText(now.strftime("%d.%m.%Y · %H:%M"))
            for index in range(6):
                self.current_prayers[index].setText(data["Prayers"][index])
                self.tomorrows_prayers[index].setText(data["nextDayPrayers"]["prayers"][index])
            self._update_midnight()
            self._save_prayer_times_cache(data, now)
        else:
            # Keep the last valid times visible. Avoid nmcli/sudo here:
            # they can trigger desktop authentication or connection dialogs.
            self.led_sign.setProperty("online", False)
            self.retry_time.setText("Offline · erneuter Versuch in 5 Minuten")
            self.retry_time.show()
            if not self.retry_timer.isActive():
                self.retry_timer.start()
        self.led_sign.style().unpolish(self.led_sign)
        self.led_sign.style().polish(self.led_sign)

    def _load_cached_prayer_times(self):
        try:
            with open(self.cache_path, encoding="utf-8") as cache_file:
                cached = json.load(cache_file)
            data = cached["data"]
            saved_at = datetime.fromisoformat(cached["savedAt"])
            if saved_at.date() != datetime.now().date() or not self.scraper.has_valid_prayer_times(data):
                return
            self.prayer_times = data
            self.last_fetch_date = saved_at.date()
            for index in range(6):
                self.current_prayers[index].setText(data["Prayers"][index])
                self.tomorrows_prayers[index].setText(data["nextDayPrayers"]["prayers"][index])
            self.last_updated_time.setText(saved_at.strftime("%d.%m.%Y · %H:%M"))
            self._update_midnight()
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return

    def _save_prayer_times_cache(self, data, saved_at):
        temporary_path = f"{self.cache_path}.tmp"
        try:
            with open(temporary_path, "w", encoding="utf-8") as cache_file:
                json.dump({"savedAt": saved_at.isoformat(), "data": data}, cache_file)
            os.replace(temporary_path, self.cache_path)
        except OSError:
            try:
                os.remove(temporary_path)
            except OSError:
                pass

    def update_clock(self):
        now = datetime.now()
        self.current_time.setText(now.strftime("%H:%M"))
        self.current_location.setText("BERLIN")
        self.current_date.setText(self._german_date(now))
        self._update_islamic_content(now)

        if self.last_fetch_date is not None and now.date() != self.last_fetch_date:
            self.refresh_data()
        if self.prayer_times:
            self._update_prayer_state(now)

    def _update_prayer_state(self, now):
        today = now.date()
        events = []
        for index in self.ACTUAL_PRAYER_INDICES:
            prayer_at = datetime.combine(
                today, datetime.strptime(self.prayer_times["Prayers"][index], "%H:%M").time()
            )
            events.append((prayer_at, index))
        tomorrow_fajr = datetime.combine(
            today + timedelta(days=1),
            datetime.strptime(self.prayer_times["nextDayPrayers"]["prayers"][0], "%H:%M").time(),
        )
        next_at, next_index = next(
            ((prayer_at, index) for prayer_at, index in events if prayer_at > now),
            (tomorrow_fajr, 0),
        )
        remaining = max(0, int((next_at - now).total_seconds()))
        self.rest_time_description.setText(f"NÄCHSTES GEBET · {self.PRAYER_NAMES[next_index]}")
        self.rest_time.setText(
            f"{remaining // 3600:02d}:{remaining % 3600 // 60:02d}:{remaining % 60:02d}"
        )

        active_index = next((index for prayer_at, index in reversed(events) if prayer_at <= now), 5)
        self._style_active_prayer(active_index)

        for prayer_at, index in events:
            adhan_key = (prayer_at.date(), index)
            if 0 <= (now - prayer_at).total_seconds() < 1.5 and self.last_adhan_key != adhan_key:
                self.last_adhan_key = adhan_key
                self._call_to_prayer(index)

    def _call_to_prayer(self, index):
        path = self.fajr_adhan_path if index == 0 else self.adhan_path
        self._play_audio(path)

    def _play_audio(self, path):
        if os.path.exists(path):
            self.audio_player.stop()
            self.audio_player.setSource(QUrl.fromLocalFile(path))
            self.audio_player.play()

    @Slot()
    def _on_audio_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.adhan_blink_visible = True
            self._apply_adhan_blink()
            self.adhan_blink_timer.start()
        else:
            self.adhan_blink_timer.stop()
            self.adhan_blink_visible = False
            self._apply_adhan_blink()

    def _toggle_adhan_blink(self):
        self.adhan_blink_visible = not self.adhan_blink_visible
        self._apply_adhan_blink()

    def _apply_adhan_blink(self):
        for index, box in enumerate(self.prayer_boxes):
            box.setProperty(
                "adhanBlink",
                self.adhan_blink_visible and index == self.active_prayer_index,
            )
            box.style().unpolish(box)
            box.style().polish(box)
            box.update()

    def _style_active_prayer(self, active_index):
        self.active_prayer_index = active_index
        for index, box in enumerate(self.prayer_boxes):
            box.setProperty("activePrayer", index == active_index and index != 1)
            box.setProperty("sunrise", index == 1)
            box.style().unpolish(box)
            box.style().polish(box)
            box.update()

    def _update_midnight(self):
        maghrib = datetime.strptime(self.prayer_times["Prayers"][4], "%H:%M")
        fajr = datetime.strptime(
            self.prayer_times["nextDayPrayers"]["prayers"][0], "%H:%M"
        ) + timedelta(days=1)
        self.midnight_time.setText((maghrib + (fajr - maghrib) / 2).strftime("%H:%M"))

    @staticmethod
    def _german_date(value):
        weekdays = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
        months = (
            "Januar", "Februar", "März", "April", "Mai", "Juni",
            "Juli", "August", "September", "Oktober", "November", "Dezember",
        )
        return f"{weekdays[value.weekday()]}, {value.day:02d}. {months[value.month - 1]} {value.year}"

    def _update_islamic_content(self, value):
        if self.last_content_date == value.date():
            return
        try:
            info = get_hijri_info(value)
            if info["sacred_month"]:
                self.hijri_date.setText(
                    f"{info['day']}. <span style=\"color:#e0b85f; font-weight:800;\">"
                    f"{info['month_name']}</span> {info['year']} AH"
                )
            else:
                self.hijri_date.setText(info["date"])
            self.islamic_event.setTags(special_day_statuses(info["day"], info["month"]))
            tomorrow_info = get_hijri_info(value + timedelta(days=1))
            self.tomorrow_islamic_notice.setTags(
                special_day_tomorrow_notices(
                    tomorrow_info["day"],
                    tomorrow_info["month"],
                    (value + timedelta(days=1)).weekday(),
                )
            )
            self.clockPanel.setProperty("sacredMonth", info["sacred_month"])
            self.clockPanel.style().unpolish(self.clockPanel)
            self.clockPanel.style().polish(self.clockPanel)
            arabic, translation, reference = daily_verse(value.date())
            self.quran_arabic.setText(arabic)
            self.quran_translation.setText(f"„{translation}“ · Qurʾān {reference}")
            self.last_content_date = value.date()
        except (ImportError, ValueError):
            self.hijri_date.setText("Islamisches Datum derzeit nicht verfügbar")
            self.islamic_event.hide()
            self.tomorrow_islamic_notice.hide()
