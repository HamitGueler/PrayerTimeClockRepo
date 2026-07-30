import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta

from PySide6.QtCore import QSettings, QTimer, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QCursor
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from PyViews.PrayerTimeClockWindow import Ui_MainWindow
from PyViews.IslamicContent import (
    daily_verse,
    get_hijri_info,
    special_day_statuses,
    special_day_tomorrow_notices,
)
from HelperClasses.WebScraperClass import WebScraperClass


class SettingsDialog(QDialog):
    test_adhan_requested = Signal()

    def __init__(self, volume, brightness, display_profile, hijri_adjustment, parent=None):
        super().__init__(parent)
        self.setObjectName("settings_dialog")
        self.setWindowTitle("Einstellungen")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        page = QVBoxLayout(self)
        page.setContentsMargins(32, 26, 32, 24)
        title = QLabel("EINSTELLUNGEN")
        title.setObjectName("settings_title")
        page.addWidget(title)
        subtitle = QLabel("Änderungen werden nach dem Speichern dauerhaft übernommen.")
        subtitle.setObjectName("settings_subtitle")
        page.addWidget(subtitle)

        form = QFormLayout()
        form.setHorizontalSpacing(26)
        form.setVerticalSpacing(18)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(volume)
        self.volume_value = QLabel()
        self.volume_slider.valueChanged.connect(
            lambda value: self.volume_value.setText(f"{value} %")
        )
        self.volume_value.setText(f"{volume} %")
        volume_row = QHBoxLayout()
        volume_row.addWidget(self.volume_slider, 1)
        volume_row.addWidget(self.volume_value)
        form.addRow("Adhān-Lautstärke", volume_row)

        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(10, 100)
        self.brightness_slider.setValue(brightness)
        self.brightness_value = QLabel()
        self.brightness_slider.valueChanged.connect(
            lambda value: self.brightness_value.setText(f"{value} %")
        )
        self.brightness_value.setText(f"{brightness} %")
        brightness_row = QHBoxLayout()
        brightness_row.addWidget(self.brightness_slider, 1)
        brightness_row.addWidget(self.brightness_value)
        form.addRow("Bildschirmhelligkeit", brightness_row)

        self.display_profile = QComboBox()
        self.display_profile.addItems(("7 Zoll", "10 Zoll", "14 Zoll"))
        self.display_profile.setCurrentText(display_profile)
        form.addRow("Displayprofil", self.display_profile)

        self.hijri_adjustment = QSpinBox()
        self.hijri_adjustment.setRange(-2, 2)
        self.hijri_adjustment.setValue(hijri_adjustment)
        self.hijri_adjustment.setSuffix(" Tage")
        form.addRow("Hijri-Korrektur", self.hijri_adjustment)
        page.addLayout(form)

        hint = QLabel(
            "Die Helligkeitssteuerung funktioniert, wenn der angeschlossene "
            "Bildschirm sie dem Raspberry Pi zur Verfügung stellt."
        )
        hint.setObjectName("settings_hint")
        hint.setWordWrap(True)
        page.addWidget(hint)

        test_button = QPushButton("Adhān testen")
        test_button.setObjectName("test_adhan_button")
        test_button.clicked.connect(self.test_adhan_requested)
        page.addWidget(test_button)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Speichern")
        buttons.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        page.addWidget(buttons)


class PrayerTimeClockWindow(QMainWindow, Ui_MainWindow):
    # Diyanet order: Fajr/Imsak, sunrise, Dhuhr, Asr, Maghrib, Isha.
    ACTUAL_PRAYER_INDICES = (0, 2, 3, 4, 5)
    PRAYER_NAMES = ("FAJR", "SHURŪQ", "DHUHR", "ASR", "MAGHRIB", "ISHA")
    DISPLAY_SCALES = {"7 Zoll": 1.0, "10 Zoll": 1.14, "14 Zoll": 1.28}

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
        self.settings = QSettings("PrayerTimeClock", "PrayerTimeClock")
        self.volume = self.settings.value("volume", 100, int)
        self.brightness = self.settings.value("brightness", 100, int)
        self.display_profile = self.settings.value("displayProfile", "7 Zoll", str)
        self.hijri_adjustment = self.settings.value("hijriAdjustment", -1, int)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(self.volume / 100.0)
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
        self.prayer_times_are_current = False
        self.fetch_in_progress = False
        self.last_fetch_date = None
        self.last_daily_refresh_attempt_date = datetime.now().date()
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
            self.base_style_sheet = style_file.read()
        self._apply_display_profile(self.display_profile)
        self._apply_brightness(self.brightness)

        self.refresh_button.clicked.connect(self.refresh_data)
        self.refresh_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setCursor(QCursor(Qt.PointingHandCursor))

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
    def open_settings(self):
        dialog = SettingsDialog(
            self.volume,
            self.brightness,
            self.display_profile,
            self.hijri_adjustment,
            self,
        )
        dialog.setStyleSheet(self.styleSheet())
        dialog.test_adhan_requested.connect(
            lambda: self._preview_adhan(dialog.volume_slider.value())
        )
        if dialog.exec() != QDialog.Accepted:
            self.audio_player.stop()
            self.audio_output.setVolume(self.volume / 100.0)
            return
        self.volume = dialog.volume_slider.value()
        self.brightness = dialog.brightness_slider.value()
        self.display_profile = dialog.display_profile.currentText()
        self.hijri_adjustment = dialog.hijri_adjustment.value()
        self.settings.setValue("volume", self.volume)
        self.settings.setValue("brightness", self.brightness)
        self.settings.setValue("displayProfile", self.display_profile)
        self.settings.setValue("hijriAdjustment", self.hijri_adjustment)
        self.settings.sync()
        self.audio_output.setVolume(self.volume / 100.0)
        self._apply_brightness(self.brightness)
        self._apply_display_profile(self.display_profile)
        self.last_content_date = None
        self._update_islamic_content(datetime.now())

    def _preview_adhan(self, volume):
        self.audio_output.setVolume(volume / 100.0)
        self._play_audio(self.adhan_path)

    def _apply_display_profile(self, profile):
        scale = self.DISPLAY_SCALES.get(profile, 1.0)

        def scale_pixels(match):
            value = float(match.group(1))
            return f"{max(1, round(value * scale))}px"

        scaled_style = re.sub(r"(\d+(?:\.\d+)?)px", scale_pixels, self.base_style_sheet)
        self.setStyleSheet(scaled_style)
        ornament_size = round(154 * scale)
        self.islamic_ornament.setFixedSize(ornament_size, ornament_size)

    @staticmethod
    def _apply_brightness(value):
        if shutil.which("brightnessctl"):
            result = subprocess.run(
                ["brightnessctl", "set", f"{value}%"],
                check=False,
                capture_output=True,
                timeout=3,
            )
            if result.returncode == 0:
                return True
        backlight_root = "/sys/class/backlight"
        if os.path.isdir(backlight_root):
            for device in os.listdir(backlight_root):
                device_path = os.path.join(backlight_root, device)
                try:
                    with open(os.path.join(device_path, "max_brightness"), encoding="utf-8") as file:
                        maximum = int(file.read().strip())
                    brightness_path = os.path.join(device_path, "brightness")
                    with open(brightness_path, "w", encoding="utf-8") as file:
                        file.write(str(max(1, round(maximum * value / 100))))
                    return True
                except (OSError, ValueError):
                    continue
        return False

    @Slot()
    def refresh_data(self):
        if self.fetch_in_progress:
            return
        self.last_daily_refresh_attempt_date = datetime.now().date()
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
        if (
            data.get("requestSuccess", [False])[0]
            and self.scraper.has_valid_prayer_times(data)
            and self.scraper.has_expected_dates(data, now.date())
        ):
            self.prayer_times = data
            self.prayer_times_are_current = True
            self.last_fetch_date = now.date()
            self.retry_timer.stop()
            self.retry_time.hide()
            self._set_update_status("current")
            self.last_updated_time.setText(now.strftime("%d.%m.%Y · %H:%M"))
            for index in range(6):
                self.current_prayers[index].setText(data["Prayers"][index])
                self.tomorrows_prayers[index].setText(data["nextDayPrayers"]["prayers"][index])
            self._update_midnight()
            self._save_prayer_times_cache(data, now)
        else:
            # Keep the last valid times visible. Avoid nmcli/sudo here:
            # they can trigger desktop authentication or connection dialogs.
            data_date = self.scraper.prayer_data_date(self.prayer_times)
            if self.prayer_times and self.prayer_times_are_current:
                self._set_update_status("cached")
                self.retry_time.setText("Offline · gespeicherte Daten · neuer Versuch in 5 Minuten")
            elif self.prayer_times and data_date is not None:
                self._set_update_status("stale")
                self.retry_time.setText(self._stale_warning(data_date, now.date()))
            else:
                self._set_update_status("stale")
                self.retry_time.setText("Offline · keine gültigen Gebetszeiten verfügbar")
            self.retry_time.show()
            if not self.retry_timer.isActive():
                self.retry_timer.start()

    def _load_cached_prayer_times(self):
        try:
            with open(self.cache_path, encoding="utf-8") as cache_file:
                cached = json.load(cache_file)
            data = cached["data"]
            saved_at = datetime.fromisoformat(cached["savedAt"])
            data_date = self.scraper.prayer_data_date(data)
            today = datetime.now().date()
            if (
                not self.scraper.has_valid_prayer_times(data)
                or data_date is None
                or data_date > today
            ):
                return
            self.prayer_times = data
            self.prayer_times_are_current = data_date == today
            self.last_fetch_date = data_date
            for index in range(6):
                self.current_prayers[index].setText(data["Prayers"][index])
                self.tomorrows_prayers[index].setText(data["nextDayPrayers"]["prayers"][index])
            self.last_updated_time.setText(saved_at.strftime("%d.%m.%Y · %H:%M"))
            self._set_update_status("cached" if self.prayer_times_are_current else "stale")
            if not self.prayer_times_are_current:
                self.retry_time.setText(self._stale_warning(data_date, today))
                self.retry_time.show()
            self._update_midnight()
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return

    def _set_update_status(self, status):
        labels = {
            "current": "AKTUELL",
            "cached": "GESPEICHERT",
            "stale": "VERALTET",
        }
        self.last_updated_descrition.setText(labels[status])
        self.led_sign.setProperty("status", status)
        self.retry_time.setProperty("status", status)
        for widget in (self.led_sign, self.retry_time):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    @staticmethod
    def _stale_warning(data_date, today):
        age = (today - data_date).days
        day_label = "1 Tag" if age == 1 else f"{age} Tage"
        return f"Warnung · Gebetszeiten {day_label} alt · neuer Versuch in 5 Minuten"

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

        if self.last_daily_refresh_attempt_date != now.date():
            self.refresh_data()
        if self.prayer_times and self.prayer_times_are_current:
            self._update_prayer_state(now)
        elif self.prayer_times:
            self.rest_time_description.setText("NÄCHSTES GEBET")
            self.rest_time.setText("--:--:--")

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
            info = get_hijri_info(value, self.hijri_adjustment)
            if info["sacred_month"]:
                self.hijri_date.setText(
                    f"{info['day']}. <span style=\"color:#e0b85f; font-weight:800;\">"
                    f"{info['month_name']}</span> {info['year']} AH"
                )
            else:
                self.hijri_date.setText(info["date"])
            self.islamic_event.setTags(special_day_statuses(info["day"], info["month"]))
            tomorrow_info = get_hijri_info(
                value + timedelta(days=1),
                self.hijri_adjustment,
            )
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
