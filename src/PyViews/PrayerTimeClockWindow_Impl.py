import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta

from PySide6.QtCore import QSize, QSettings, QTimer, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QCursor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QApplication,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from PyViews.PrayerTimeClockWindow import (
    IslamicGirihOrnament,
    OrientalClockPanel,
    Ui_MainWindow,
)
from PyViews.IslamicContent import (
    daily_verse,
    get_hijri_info,
    special_day_statuses,
    special_day_tomorrow_notices,
    uses_celebration_palette,
)
from HelperClasses.WebScraperClass import WebScraperClass
from HelperClasses.ApplicationUpdateService import ApplicationUpdateService
from HelperClasses.AdhanAudioProfile import load_adhan_profiles
from HelperClasses.PrayerTimeFreshness import fallback_horizon_after_request, is_critical_stale


class VisualEffectsPreview(QFrame):
    """Compact preview composed from the exact widgets used by the clock."""

    def __init__(self, touch_mode=False, parent=None):
        super().__init__(parent)
        self.setObjectName("visual_effects_preview")
        self.setMinimumHeight(270 if touch_mode else 178)
        self.panel = OrientalClockPanel(self)
        self.panel.setObjectName("preview_particle_panel")
        self.panel.set_particle_size(1.45 if touch_mode else 1.0)
        self.ornament = IslamicGirihOrnament(self.panel)
        preview_ornament_size = 180 if touch_mode else 112
        self.ornament.setFixedSize(preview_ornament_size, preview_ornament_size)
        self.caption = QLabel("LIVE-VORSCHAU", self.panel)
        self.caption.setObjectName("preview_caption")
        self._clock = 0
        self._external_level = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._animate)
        self._timer.start()

    def resizeEvent(self, event):
        self.panel.setGeometry(self.rect().adjusted(1, 1, -1, -1))
        self.ornament.move(
            (self.panel.width() - self.ornament.width()) // 2,
            (self.panel.height() - self.ornament.height()) // 2 + 8,
        )
        self.caption.adjustSize()
        self.caption.move((self.panel.width() - self.caption.width()) // 2, 12)
        super().resizeEvent(event)

    def _animate(self):
        self._clock += 1
        # Normal mode shows only the two standard-speed settings. The actual
        # Adhan profile takes over during the test playback, so reaction settings
        # can no longer be confused with an unrelated synthetic pulse.
        level = self._external_level
        self.ornament.set_audio_level(level)
        self.panel.set_audio_level(level)

    def set_adhan_level(self, level):
        self._external_level = 0.0 if level is None else max(0.0, min(1.0, float(level)))

    def set_effects(self, ornament_speed, particle_speed, particle_density, ornament_reaction, particle_reaction):
        self.ornament.set_animation_speed(ornament_speed / 100.0)
        self.panel.set_animation_speed(particle_speed / 100.0)
        self.panel.set_particle_density(particle_density / 100.0)
        self.ornament.set_reaction_strength(ornament_reaction / 100.0)
        self.panel.set_reaction_strength(particle_reaction / 100.0)


class SettingsDialog(QDialog):
    test_adhan_requested = Signal()
    close_requested = Signal()
    restart_requested = Signal()
    update_requested = Signal()
    reconnect_requested = Signal()
    wifi_settings_requested = Signal()
    volume_changed = Signal(int)
    brightness_changed = Signal(int)

    def __init__(
        self,
        volume,
        brightness,
        display_profile,
        hijri_adjustment,
        ornament_speed,
        particle_speed,
        particle_density,
        ornament_reaction,
        particle_reaction,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("settings_dialog")
        self.setWindowTitle("Einstellungen")
        self.setModal(True)
        touch_mode = display_profile == "10 Zoll"
        if touch_mode:
            screen = QApplication.primaryScreen()
            available = screen.availableGeometry() if screen else None
            width = min(1680, round(available.width() * 0.92)) if available else 1680
            height = min(1060, round(available.height() * 0.92)) if available else 1060
            self.resize(width, height)
            self.setMinimumSize(min(1180, width), min(720, height))
        else:
            self.setMinimumSize(940, 560)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area = QScrollArea()
        scroll_area.setObjectName("settings_scroll_area")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        settings_content = QWidget()
        settings_content.setObjectName("settings_content")
        scroll_area.setWidget(settings_content)
        dialog_layout.addWidget(scroll_area)

        page = QVBoxLayout(settings_content)
        page.setContentsMargins(26, 18, 26, 18)
        page.setSpacing(8)
        title = QLabel("EINSTELLUNGEN")
        title.setObjectName("settings_title")
        page.addWidget(title)
        subtitle = QLabel("Änderungen werden nach dem Speichern dauerhaft übernommen.")
        subtitle.setObjectName("settings_subtitle")
        page.addWidget(subtitle)

        columns = QHBoxLayout()
        columns.setSpacing(22)
        left_column = QVBoxLayout()
        left_column.setSpacing(7)
        right_column = QVBoxLayout()
        right_column.setSpacing(7)
        columns.addLayout(left_column, 11)
        columns.addLayout(right_column, 10)
        page.addLayout(columns, 1)

        form = QFormLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.WrapLongRows)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(volume)
        self.volume_value = QLabel()
        self.volume_slider.valueChanged.connect(
            lambda value: self.volume_value.setText(f"{value} %")
        )
        self.volume_slider.valueChanged.connect(self.volume_changed)
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
        self.brightness_slider.valueChanged.connect(self.brightness_changed)
        self.brightness_value.setText(f"{brightness} %")
        brightness_row = QHBoxLayout()
        brightness_row.addWidget(self.brightness_slider, 1)
        brightness_row.addWidget(self.brightness_value)
        form.addRow("Bildschirmhelligkeit", brightness_row)

        profile_row = QHBoxLayout()
        self.profile_group = QButtonGroup(self)
        self.profile_group.setExclusive(True)
        self.profile_buttons = {}
        for profile in ("7 Zoll", "10 Zoll", "14 Zoll"):
            button = QPushButton(profile)
            button.setCheckable(True)
            button.setProperty("profileButton", True)
            button.setMinimumHeight(48)
            button.setChecked(profile == display_profile)
            self.profile_group.addButton(button)
            self.profile_buttons[profile] = button
            profile_row.addWidget(button)
        form.addRow("Displayprofil", profile_row)

        self.hijri_adjustment = QSpinBox()
        self.hijri_adjustment.setRange(-2, 2)
        self.hijri_adjustment.setValue(hijri_adjustment)
        self.hijri_adjustment.setSuffix(" Tage")
        self.hijri_adjustment.setButtonSymbols(QSpinBox.NoButtons)
        self.hijri_adjustment.setAlignment(Qt.AlignCenter)
        hijri_row = QHBoxLayout()
        hijri_minus_button = QPushButton("−")
        hijri_minus_button.setObjectName("hijri_adjustment_button")
        hijri_minus_button.setMinimumSize(56, 48)
        hijri_minus_button.clicked.connect(self.hijri_adjustment.stepDown)
        hijri_row.addWidget(hijri_minus_button)
        hijri_row.addWidget(self.hijri_adjustment, 1)
        hijri_plus_button = QPushButton("+")
        hijri_plus_button.setObjectName("hijri_adjustment_button")
        hijri_plus_button.setMinimumSize(56, 48)
        hijri_plus_button.clicked.connect(self.hijri_adjustment.stepUp)
        hijri_row.addWidget(hijri_plus_button)
        form.addRow("Hijri-Korrektur", hijri_row)
        left_column.addLayout(form)

        hint = QLabel("Bei HDMI-Displays ohne Hardware-Regelung wird die Oberfläche softwareseitig abgedunkelt.")
        hint.setObjectName("settings_hint")
        hint.setWordWrap(True)
        left_column.addWidget(hint)

        self.test_adhan_button = QPushButton("Adhān abspielen")
        self.test_adhan_button.setObjectName("test_adhan_button")
        self.test_adhan_button.setMinimumHeight(38)
        self.test_adhan_button.clicked.connect(self.test_adhan_requested)
        left_column.addWidget(self.test_adhan_button)

        self.network_status = QLabel("WLAN-Status wird geprüft …")
        self.network_status.setObjectName("network_status")
        left_column.addWidget(self.network_status)
        network_row = QHBoxLayout()
        reconnect_button = QPushButton("Neu verbinden")
        reconnect_button.clicked.connect(self.reconnect_requested)
        network_row.addWidget(reconnect_button)
        wifi_button = QPushButton("WLAN auswählen / anmelden")
        wifi_button.clicked.connect(self.wifi_settings_requested)
        network_row.addWidget(wifi_button)
        left_column.addLayout(network_row)

        self.update_status = QLabel("Update-Stand wird beim Prüfen ermittelt.")
        self.update_status.setObjectName("application_update_status")
        left_column.addWidget(self.update_status)
        system_row = QHBoxLayout()
        self.check_update_button = QPushButton("Updates installieren")
        self.check_update_button.clicked.connect(self.update_requested)
        system_row.addWidget(self.check_update_button)
        restart_button = QPushButton("App neu starten")
        restart_button.clicked.connect(self.restart_requested)
        system_row.addWidget(restart_button)
        left_column.addLayout(system_row)

        self.effects_preview = VisualEffectsPreview(touch_mode=touch_mode)
        right_column.addWidget(self.effects_preview)
        effect_title = QLabel("BEWEGUNG & ADHĀN-REAKTION")
        effect_title.setObjectName("settings_section_title")
        right_column.addWidget(effect_title)
        effects_form = QFormLayout()
        effects_form.setHorizontalSpacing(12)
        effects_form.setVerticalSpacing(7)
        effects_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        effects_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        effects_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        self.ornament_speed_slider = self._effect_slider(
            effects_form, "Ornament · normal", ornament_speed, "Tempo"
        )
        self.particle_speed_slider = self._effect_slider(
            effects_form, "Partikel · Tempo", particle_speed, "Tempo"
        )
        self.particle_density_slider = self._effect_slider(
            effects_form, "Partikel · Anzahl", particle_density, "Dichte"
        )
        self.ornament_reaction_slider = self._effect_slider(
            effects_form, "Ornament · Adhān", ornament_reaction, "Stärke"
        )
        self.particle_reaction_slider = self._effect_slider(
            effects_form, "Partikel · Adhān", particle_reaction, "Stärke"
        )
        right_column.addLayout(effects_form)
        reaction_hint = QLabel(
            "Die Reaktion folgt weiterhin dem geglätteten Verlauf des Adhāns. "
            "Der Regler verändert nur die sichtbare Stärke."
        )
        reaction_hint.setObjectName("settings_hint")
        reaction_hint.setWordWrap(True)
        right_column.addWidget(reaction_hint)
        self._update_effects_preview()

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Speichern")
        buttons.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        close_button = QPushButton("App schließen")
        close_button.clicked.connect(self.close_requested)
        buttons.addButton(close_button, QDialogButtonBox.ActionRole)
        page.addWidget(buttons)

    def _effect_slider(self, form, label, value, value_suffix):
        slider = QSlider(Qt.Horizontal)
        if value_suffix == "Tempo":
            slider.setRange(20, 300)
        elif value_suffix == "Dichte":
            slider.setRange(40, 200)
        else:
            slider.setRange(0, 300)
        slider.setValue(value)
        value_label = QLabel(f"{value} %")
        value_label.setObjectName("effect_value")
        row = QHBoxLayout()
        row.addWidget(slider, 1)
        row.addWidget(value_label)
        slider.valueChanged.connect(lambda current: value_label.setText(f"{current} %"))
        slider.valueChanged.connect(self._update_effects_preview)
        form.addRow(label, row)
        return slider

    def _update_effects_preview(self, _value=None):
        self.effects_preview.set_effects(
            self.ornament_speed_slider.value(),
            self.particle_speed_slider.value(),
            self.particle_density_slider.value(),
            self.ornament_reaction_slider.value(),
            self.particle_reaction_slider.value(),
        )

    def selected_display_profile(self):
        for profile, button in self.profile_buttons.items():
            if button.isChecked():
                return profile
        return "7 Zoll"

    def set_adhan_playing(self, playing):
        self.test_adhan_button.setText(
            "Adhān stoppen" if playing else "Adhān abspielen"
        )
        self.test_adhan_button.setProperty("playing", playing)
        self.test_adhan_button.style().unpolish(self.test_adhan_button)
        self.test_adhan_button.style().polish(self.test_adhan_button)
        if not playing:
            self.effects_preview.set_adhan_level(None)

    def set_network_status(self, connected, network_name=""):
        if connected:
            suffix = f" · {network_name}" if network_name else ""
            self.network_status.setText(f"● WLAN verbunden{suffix}")
            self.network_status.setProperty("connected", True)
        else:
            self.network_status.setText("● WLAN nicht verbunden")
            self.network_status.setProperty("connected", False)
        self.network_status.style().unpolish(self.network_status)
        self.network_status.style().polish(self.network_status)


class PrayerTimeClockWindow(QMainWindow, Ui_MainWindow):
    # Diyanet order: Fajr/Imsak, sunrise, Dhuhr, Asr, Maghrib, Isha.
    ACTUAL_PRAYER_INDICES = (0, 2, 3, 4, 5)
    PRAYER_NAMES = ("FAJR", "SHURŪQ", "DHUHR", "ASR", "MAGHRIB", "ISHA")
    DISPLAY_SCALES = {"7 Zoll": 1.0, "10 Zoll": 1.42, "14 Zoll": 1.28}
    CRITICAL_STALE_AFTER = timedelta(days=7)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("PrayerTimeClock")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.showFullScreen()

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(os.path.join(self.current_dir, "..", ".."))
        self.update_service = ApplicationUpdateService(self.project_root)
        self.src_dir = os.path.abspath(os.path.join(self.current_dir, ".."))
        self.cache_path = os.path.join(self.src_dir, "prayer_times_cache.json")
        self.fajr_adhan_path = os.path.join(self.src_dir, "AudioFiles", "fajr_adhan.mp3")
        self.adhan_path = os.path.join(self.src_dir, "AudioFiles", "adhan.mp3")
        self.settings = QSettings("PrayerTimeClock", "PrayerTimeClock")
        self.volume = self.settings.value("volume", 100, int)
        self.brightness = self.settings.value("brightness", 100, int)
        self.display_profile = self.settings.value("displayProfile", "7 Zoll", str)
        self.hijri_adjustment = self.settings.value("hijriAdjustment", -1, int)
        self.ornament_speed = self.settings.value("ornamentSpeed", 100, int)
        self.particle_speed = self.settings.value("particleSpeed", 100, int)
        self.particle_density = self.settings.value("particleDensity", 100, int)
        self.ornament_reaction = self.settings.value("ornamentAdhanReaction", 100, int)
        self.particle_reaction = self.settings.value("particleAdhanReaction", 100, int)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(self.volume / 100.0)
        self.audio_player = QMediaPlayer(self)
        self.audio_player.setAudioOutput(self.audio_output)
        self.audio_player.playbackStateChanged.connect(self._on_audio_state_changed)
        self.adhan_profiles = load_adhan_profiles(os.path.join(self.src_dir, "AudioProfiles"))
        self.active_adhan_profile = None
        self.adhan_visual_level = 0.0
        self.adhan_visualizer_timer = QTimer(self)
        self.adhan_visualizer_timer.setInterval(40)
        self.adhan_visualizer_timer.timeout.connect(self._update_adhan_visualizer)
        self.previewing_adhan = False
        self.settings_dialog = None
        self.adhan_blink_timer = QTimer(self)
        self.adhan_blink_timer.setInterval(450)
        self.adhan_blink_timer.timeout.connect(self._toggle_adhan_blink)
        self.adhan_blink_visible = False
        self.active_prayer_index = None

        self.scraper = WebScraperClass()
        self.prayer_times = {}
        self.prayer_times_cache = {}
        self.prayer_times_are_current = False
        self.last_successful_update_at = None
        self.fetch_in_progress = False
        self.last_fetch_date = None
        self.last_daily_refresh_attempt_date = datetime.now().date()
        self.last_adhan_key = None
        self.last_content_date = None
        self.brightness_overlay = QWidget(self.centralwidget)
        self.brightness_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.brightness_overlay.setObjectName("brightness_overlay")
        self.brightness_overlay.hide()
        self.network_timer = QTimer(self)
        self.network_timer.setInterval(60000)
        self.network_timer.timeout.connect(self._refresh_network_status)

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

        # The large display has enough horizontal room to show the prayer
        # names in both languages without making the time column narrower.
        arabic_prayer_names = ("الفجر", "الشروق", "الظهر", "العصر", "المغرب", "العشاء")
        current_prayer_labels = (
            self.current_day_fajr, self.current_day_shroq, self.current_day_zohr,
            self.current_day_asr, self.current_day_magrb, self.current_day_isha,
        )
        for label, arabic_name in zip(current_prayer_labels, arabic_prayer_names):
            label.setText(f"{label.text()}  {arabic_name}")

        style_path = os.path.join(self.project_root, "style.css")
        with open(style_path, encoding="utf-8") as style_file:
            self.base_style_sheet = style_file.read()
        self._apply_display_profile(self.display_profile)
        self._apply_brightness(self.brightness)
        self._apply_visual_effect_settings()

        self.refresh_button.clicked.connect(self.refresh_data)
        self.refresh_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.wifi_status_button.clicked.connect(self.open_settings)
        self.wifi_status_button.setCursor(QCursor(Qt.PointingHandCursor))

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        self.retry_timer = QTimer(self)
        self.retry_timer.setInterval(5 * 60 * 1000)
        self.retry_timer.timeout.connect(self.refresh_data)
        self.retry_time.hide()
        self.network_timer.start()
        self._refresh_network_status()

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
            self.ornament_speed,
            self.particle_speed,
            self.particle_density,
            self.ornament_reaction,
            self.particle_reaction,
            self,
        )
        dialog.setStyleSheet(self.styleSheet())
        dialog.test_adhan_requested.connect(
            lambda: self._toggle_adhan_preview(dialog)
        )
        dialog.volume_changed.connect(lambda value: self.audio_output.setVolume(value / 100.0))
        dialog.brightness_changed.connect(self._apply_brightness)
        dialog.reconnect_requested.connect(lambda: self._reconnect_wifi(dialog))
        dialog.wifi_settings_requested.connect(lambda: self._open_wifi_settings(dialog))
        dialog.update_requested.connect(lambda: self._handle_update(dialog))
        dialog.restart_requested.connect(lambda: self._restart_application(dialog, True))
        dialog.close_requested.connect(lambda: self._close_application(dialog))
        QTimer.singleShot(0, lambda: self._check_update_status(dialog))
        self._update_dialog_network_status(dialog)
        self.settings_dialog = dialog
        result = dialog.exec()
        self.settings_dialog = None
        if self.previewing_adhan:
            self.audio_player.stop()
            self.previewing_adhan = False
        if result != QDialog.Accepted:
            self.audio_output.setVolume(self.volume / 100.0)
            return
        self.volume = dialog.volume_slider.value()
        self.brightness = dialog.brightness_slider.value()
        self.display_profile = dialog.selected_display_profile()
        self.hijri_adjustment = dialog.hijri_adjustment.value()
        self.ornament_speed = dialog.ornament_speed_slider.value()
        self.particle_speed = dialog.particle_speed_slider.value()
        self.particle_density = dialog.particle_density_slider.value()
        self.ornament_reaction = dialog.ornament_reaction_slider.value()
        self.particle_reaction = dialog.particle_reaction_slider.value()
        self.settings.setValue("volume", self.volume)
        self.settings.setValue("brightness", self.brightness)
        self.settings.setValue("displayProfile", self.display_profile)
        self.settings.setValue("hijriAdjustment", self.hijri_adjustment)
        self.settings.setValue("ornamentSpeed", self.ornament_speed)
        self.settings.setValue("particleSpeed", self.particle_speed)
        self.settings.setValue("particleDensity", self.particle_density)
        self.settings.setValue("ornamentAdhanReaction", self.ornament_reaction)
        self.settings.setValue("particleAdhanReaction", self.particle_reaction)
        self.settings.sync()
        self.audio_output.setVolume(self.volume / 100.0)
        self._apply_brightness(self.brightness)
        self._apply_display_profile(self.display_profile)
        self._apply_visual_effect_settings()
        self.last_content_date = None
        self._update_islamic_content(datetime.now())

    def _apply_visual_effect_settings(self):
        self.islamic_ornament.set_animation_speed(self.ornament_speed / 100.0)
        self.clockPanel.set_animation_speed(self.particle_speed / 100.0)
        self.clockPanel.set_particle_density(self.particle_density / 100.0)
        self.islamic_ornament.set_reaction_strength(self.ornament_reaction / 100.0)
        self.clockPanel.set_reaction_strength(self.particle_reaction / 100.0)

    def _handle_update(self, dialog):
        dialog.check_update_button.setDisabled(True)
        dialog.update_status.setText("Suche nach Updates …")
        QApplication.processEvents()
        try:
            count = self.update_service.available_commits()
            if count == 0:
                dialog.update_status.setText("Die Anwendung ist aktuell.")
                return
            dialog.update_status.setText(
                f"{count} Update{'s' if count != 1 else ''} verfügbar."
            )
            confirmed = self._ask_confirmation(
                dialog,
                "Update installieren",
                "Der neue Stand wird zuerst getestet. Erst bei Erfolg wird die "
                "Anwendung aktualisiert. Danach kannst du sie über „App neu "
                "starten“ anwenden.",
            )
            if not confirmed:
                return
            dialog.update_status.setText("Update wird geprüft und vorbereitet …")
            QApplication.processEvents()
            success, message = self.update_service.install_and_validate()
            dialog.update_status.setText(message)
            if success:
                restart_message = (
                    f"{message}\n\nDie laufende Anwendung bleibt geöffnet. "
                    "Starte sie neu, um das Update zu sehen."
                )
                dialog.update_status.setText(
                    "Update installiert · Neustart erforderlich"
                )
                self._show_message(dialog, QMessageBox.Information, "Update erfolgreich", restart_message)
            else:
                self._show_message(dialog, QMessageBox.Warning, "Update nicht übernommen", message)
        except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
            dialog.update_status.setText(str(error))
            self._show_message(dialog, QMessageBox.Warning, "Update fehlgeschlagen", str(error))
        finally:
            dialog.check_update_button.setDisabled(False)

    def _check_update_status(self, dialog):
        dialog.update_status.setText("Update-Stand wird geprüft …")
        QApplication.processEvents()
        try:
            count = self.update_service.available_commits()
            dialog.update_status.setText(
                "Die Anwendung ist aktuell."
                if count == 0
                else f"{count} Update{'s' if count != 1 else ''} verfügbar."
            )
        except (OSError, RuntimeError, subprocess.SubprocessError, ValueError):
            dialog.update_status.setText("Update-Stand derzeit nicht verfügbar.")

    @staticmethod
    def _show_message(parent, icon, title, text):
        box = QMessageBox(icon, title, text, parent=parent)
        box.setTextFormat(Qt.PlainText)
        for label in box.findChildren(QLabel):
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setMinimumWidth(0)
            label.setMaximumWidth(720)
        box.exec()

    @staticmethod
    def _ask_confirmation(parent, title, text):
        box = QMessageBox(QMessageBox.Question, title, text, parent=parent)
        box.setTextFormat(Qt.PlainText)
        yes_button = box.addButton("Ja", QMessageBox.YesRole)
        no_button = box.addButton("Nein", QMessageBox.NoRole)
        box.setDefaultButton(yes_button)
        # On the Raspberry Pi touch display the first tap otherwise only moves
        # keyboard focus to a QMessageBox button.  These are touch actions, not
        # keyboard controls, so activate them without an intermediate focus step.
        for button in (yes_button, no_button):
            button.setAutoDefault(False)
            button.setDefault(False)
            button.setFocusPolicy(Qt.NoFocus)
        for label in box.findChildren(QLabel):
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setMinimumWidth(0)
            label.setMaximumWidth(720)
        box.exec()
        return box.clickedButton() is yes_button

    @staticmethod
    def _close_application(dialog):
        if PrayerTimeClockWindow._ask_confirmation(dialog, "App schließen", "Anwendung wirklich schließen?"):
            dialog.accept()
            QApplication.quit()

    def _restart_application(self, dialog, ask_for_confirmation):
        if ask_for_confirmation:
            if not self._ask_confirmation(dialog, "App neu starten", "Anwendung jetzt neu starten?"):
                return
        dialog.accept()
        QApplication.quit()
        subprocess.Popen(
            [sys.executable, os.path.join(self.src_dir, "PrayerTimeClock.py")],
            cwd=self.project_root,
            start_new_session=True,
        )

    def _toggle_adhan_preview(self, dialog):
        if self.previewing_adhan:
            self.audio_player.stop()
            self.previewing_adhan = False
            dialog.set_adhan_playing(False)
            return
        if not os.path.exists(self.adhan_path):
            dialog.set_adhan_playing(False)
            return
        self.audio_output.setVolume(dialog.volume_slider.value() / 100.0)
        self.audio_player.stop()
        self.audio_player.setSource(QUrl.fromLocalFile(self.adhan_path))
        self._select_adhan_profile(self.adhan_path)
        self.previewing_adhan = True
        dialog.set_adhan_playing(True)
        self.audio_player.play()

    def _apply_display_profile(self, profile):
        scale = self.DISPLAY_SCALES.get(profile, 1.0)

        def scale_pixels(match):
            value = float(match.group(1))
            return f"{max(1, round(value * scale))}px"

        scaled_style = re.sub(r"(\d+(?:\.\d+)?)px", scale_pixels, self.base_style_sheet)
        if profile == "10 Zoll":
            scaled_style += """
                #current_time { font-size: 198px; }
                #current_location { font-size: 42px; }
                #current_date { font-size: 50px; }
                #hijri_date { font-size: 46px; padding-bottom: 8px; }
                #islamic_event #eventHeading,
                #islamic_event #eventTag,
                #tomorrow_islamic_notice #eventTag { font-size: 28px; padding: 8px 15px; }
                #quran_arabic { font-size: 60px; padding-top: 8px; }
                #quran_translation { font-size: 33px; }
                #rest_time { font-size: 86px; }
                #midnight_time { font-size: 64px; }
                #sectionTitle, #rest_time_description, #midnight_label,
                #last_updated_descrition { font-size: 25px; }
                #last_updated_time { font-size: 21px; }
                #fallback_horizon { font-size: 18px; }
                #led_sign { font-size: 24px; }
                #todayPanel QGroupBox QLabel { font-size: 46px; }
                #current_day_fajr_time, #current_day_shroq_time, #current_day_zohr_time,
                #current_day_asr_time, #current_day_magrb_time, #current_day_isha_time {
                    font-size: 64px;
                }
                #next_day_description { font-size: 44px; }
                #next_day_date { font-size: 40px; }
                #next_day_fajr, #next_day_shroq, #next_day_zohr,
                #next_day_asr, #next_day_magrb, #next_day_isha { font-size: 36px; }
                #next_day_fajr_time, #next_day_shroq_time, #next_day_zohr_time,
                #next_day_asr_time, #next_day_magrb_time, #next_day_isha_time {
                    font-size: 64px;
                }
                #refresh_button, #settings_button { font-size: 38px; border-radius: 34px; }
                #wifi_status_button { border-radius: 22px; }
                #settings_title { font-size: 42px; }
                #settings_subtitle, #settings_hint { font-size: 23px; }
                #settings_dialog QLabel, #settings_dialog QSpinBox,
                #settings_dialog QComboBox, #settings_dialog QPushButton { font-size: 25px; }
                #preview_caption, #settings_section_title { font-size: 23px; }
                #network_status, #effect_value { font-size: 24px; }
                #settings_dialog QPushButton, #settings_dialog QSpinBox {
                    min-height: 70px;
                }
                #settings_dialog QSlider { min-height: 58px; }
                #settings_dialog QSlider::groove:horizontal { height: 18px; }
                #settings_dialog QSlider::handle:horizontal {
                    width: 44px;
                    margin: -14px 0;
                    border-radius: 22px;
                }
                QMessageBox { min-width: 760px; }
                QMessageBox QLabel { min-width: 610px; font-size: 27px; }
                QMessageBox QPushButton {
                    min-width: 210px;
                    min-height: 76px;
                    font-size: 27px;
                }
            """
        self.setStyleSheet(scaled_style)
        is_ten_inch = profile == "10 Zoll"
        ornament_size = 370 if is_ten_inch else round(154 * scale)
        self.islamic_ornament.setFixedSize(ornament_size, ornament_size)
        self.clockPanel.set_particle_size(1.55 if is_ten_inch else 1.0)
        if is_ten_inch:
            self.time_row.setStretch(0, 12)
            self.time_row.setStretch(1, 9)
            self.ornament_column.setContentsMargins(0, 6, 0, 0)

        control_size = 60 if is_ten_inch else 34
        self.refresh_button.setFixedSize(control_size, control_size)
        self.settings_button.setFixedSize(control_size, control_size)
        self.wifi_status_button.setFixedSize(58 if is_ten_inch else 28, 58 if is_ten_inch else 28)
        self.led_sign.setFixedSize(32 if is_ten_inch else 18, 42 if is_ten_inch else 24)
        self.last_updated_time.setMinimumWidth(220 if is_ten_inch else 132)

        # Font scaling alone leaves most of a 1920 x 1200 panel unused because
        # Qt keeps the tomorrow panel and prayer cards at their compact size
        # hints. Give the 10-inch profile a real large-screen geometry while
        # keeping the 7- and 14-inch layouts unchanged.
        self.next_day_prayers_box.setMinimumHeight(270 if is_ten_inch else 0)
        self.next_day_prayers_box.setMaximumHeight(290 if is_ten_inch else 16777215)
        for box in self.prayer_boxes:
            box.setMinimumHeight(136 if is_ten_inch else 0)
        for box in (
            self.next_day_fajr_box, self.next_day_shroq_box, self.next_day_zohr_box,
            self.next_day_asr_box, self.next_day_magrb_box, self.next_day_isha_box,
        ):
            box.setMinimumHeight(148 if is_ten_inch else 0)

    def _apply_brightness(self, value):
        if shutil.which("brightnessctl"):
            result = subprocess.run(
                ["brightnessctl", "set", f"{value}%"],
                check=False,
                capture_output=True,
                timeout=3,
            )
            if result.returncode == 0:
                self.brightness_overlay.hide()
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
                    self.brightness_overlay.hide()
                    return True
                except (OSError, ValueError):
                    continue
        opacity = max(0, min(0.82, (100 - value) / 100))
        self.brightness_overlay.setStyleSheet(
            f"background-color: rgba(0, 0, 0, {round(opacity * 255)});"
        )
        self.brightness_overlay.setGeometry(self.centralwidget.rect())
        self.brightness_overlay.setVisible(opacity > 0)
        self.brightness_overlay.raise_()
        return False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "brightness_overlay"):
            self.brightness_overlay.setGeometry(self.centralwidget.rect())

    @staticmethod
    def _network_info():
        if shutil.which("nmcli"):
            result = subprocess.run(
                ["nmcli", "-t", "-f", "TYPE,STATE,CONNECTION", "device"],
                check=False, capture_output=True, text=True, timeout=4,
            )
            for line in result.stdout.splitlines():
                parts = line.split(":", 2)
                if len(parts) == 3 and parts[0] == "wifi" and parts[1] == "connected":
                    return True, parts[2].replace("\\:", ":")
        return False, ""

    def _refresh_network_status(self):
        connected, name = self._network_info()
        self.wifi_status_button.setIcon(self._wifi_icon(connected))
        self.wifi_status_button.setIconSize(QSize(20, 20))
        self.wifi_status_button.setToolTip(
            f"WLAN verbunden · {name}" if connected and name else
            "WLAN verbunden" if connected else "WLAN nicht verbunden"
        )
        self.wifi_status_button.setProperty("connected", connected)
        self.wifi_status_button.style().unpolish(self.wifi_status_button)
        self.wifi_status_button.style().polish(self.wifi_status_button)

    @staticmethod
    def _wifi_icon(connected):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor("#52ead1" if connected else "#ff626f")
        painter.setPen(QPen(color, 2.2, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(3, 3, 18, 15, 35 * 16, 110 * 16)
        painter.drawArc(7, 8, 10, 9, 35 * 16, 110 * 16)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(10, 18, 4, 4)
        if not connected:
            painter.setPen(QPen(color, 2.5, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(4, 4, 20, 20)
        painter.end()
        return QIcon(pixmap)

    def _update_dialog_network_status(self, dialog):
        connected, name = self._network_info()
        dialog.set_network_status(connected, name)

    def _reconnect_wifi(self, dialog):
        if not shutil.which("nmcli"):
            self._show_message(dialog, QMessageBox.Warning, "WLAN", "NetworkManager ist nicht verfügbar.")
            return
        subprocess.run(["nmcli", "radio", "wifi", "on"], check=False, timeout=5)
        subprocess.run(["nmcli", "device", "connect", "wlan0"], check=False, timeout=12)
        self._refresh_network_status()
        self._update_dialog_network_status(dialog)

    def _open_wifi_settings(self, dialog):
        commands = (
            ["gnome-control-center", "wifi"],
            ["nm-connection-editor"],
        )
        for command in commands:
            if shutil.which(command[0]):
                subprocess.Popen(command, start_new_session=True)
                return
        self._show_message(
            dialog, QMessageBox.Information, "WLAN auswählen",
            "Öffne in Ubuntu die Systemeinstellungen und wähle dort „WLAN“.",
        )

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
            self.prayer_times_cache = data
            self.prayer_times_are_current = True
            self.last_successful_update_at = now
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
            self.fallback_horizon.clear()
            self.fallback_horizon.hide()
            self._update_critical_stale_state(now)
        else:
            # Keep the last valid times visible. Avoid nmcli/sudo here:
            # they can trigger desktop authentication or connection dialogs.
            self._activate_cached_date(now.date())
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
            self._update_fallback_horizon(now.date())
            self.fallback_horizon.show()
            if not self.retry_timer.isActive():
                self.retry_timer.start()
            self._update_critical_stale_state(now)

    def _activate_cached_date(self, today):
        selected_data = self.scraper.data_for_date(self.prayer_times_cache, today)
        if selected_data is None:
            self.prayer_times_are_current = False
            return False
        self.prayer_times = selected_data
        self.prayer_times_are_current = True
        self.last_fetch_date = today
        for index in range(6):
            self.current_prayers[index].setText(selected_data["Prayers"][index])
            self.tomorrows_prayers[index].setText(selected_data["nextDayPrayers"]["prayers"][index])
        self._update_midnight()
        return True

    def _load_cached_prayer_times(self):
        try:
            with open(self.cache_path, encoding="utf-8") as cache_file:
                cached = json.load(cache_file)
            data = cached["data"]
            saved_at = datetime.fromisoformat(cached["savedAt"])
            today = datetime.now().date()
            self.prayer_times_cache = data
            self.last_successful_update_at = saved_at
            self.fallback_horizon.clear()
            self.fallback_horizon.hide()
            selected_data = self.scraper.data_for_date(data, today)
            if selected_data is None:
                self.prayer_times_are_current = False
                self._set_update_status("stale")
                self._update_critical_stale_state(datetime.now())
                return
            self.prayer_times = selected_data
            self.prayer_times_are_current = True
            self.last_fetch_date = today
            for index in range(6):
                self.current_prayers[index].setText(selected_data["Prayers"][index])
                self.tomorrows_prayers[index].setText(selected_data["nextDayPrayers"]["prayers"][index])
            self.last_updated_time.setText(saved_at.strftime("%d.%m.%Y · %H:%M"))
            self._set_update_status("cached")
            self.retry_time.setText("Gespeicherte, datumsscharfe Diyanet-Daten")
            self.retry_time.show()
            self._update_midnight()
            self._update_critical_stale_state(datetime.now())
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

    def _update_critical_stale_state(self, now):
        critical = is_critical_stale(
            self.last_successful_update_at,
            now,
            self.prayer_times_are_current,
            self.CRITICAL_STALE_AFTER,
        )
        self.islamic_ornament.set_critical_warning(critical)

    def _update_fallback_horizon(self, today):
        source = self.prayer_times_cache or self.prayer_times
        last_date = self.scraper.last_available_date(source, today)
        self.fallback_horizon.setText(fallback_horizon_after_request(False, last_date, today))

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
            self._select_adhan_profile(path)
            self.audio_player.play()

    def _select_adhan_profile(self, path):
        profile_name = os.path.splitext(os.path.basename(path))[0]
        self.active_adhan_profile = self.adhan_profiles.get(profile_name)

    def _update_adhan_visualizer(self):
        target = (
            self.active_adhan_profile.value_at(self.audio_player.position())
            if self.active_adhan_profile is not None
            else 0.0
        )
        factor = 0.62 if target > self.adhan_visual_level else 0.22
        self.adhan_visual_level += (target - self.adhan_visual_level) * factor
        if self.active_adhan_profile is None and self.adhan_visual_level < 0.005:
            self.adhan_visual_level = 0.0
            self.adhan_visualizer_timer.stop()
        self.islamic_ornament.set_audio_level(self.adhan_visual_level)
        self.clockPanel.set_audio_level(self.adhan_visual_level)
        if self.settings_dialog is not None and self.previewing_adhan:
            self.settings_dialog.effects_preview.set_adhan_level(self.adhan_visual_level)

    @Slot()
    def _on_audio_state_changed(self, state):
        if self.settings_dialog is not None and self.previewing_adhan:
            self.settings_dialog.set_adhan_playing(
                state == QMediaPlayer.PlayingState
            )
        if state != QMediaPlayer.PlayingState:
            self.previewing_adhan = False
        if state == QMediaPlayer.PlayingState:
            self.adhan_visualizer_timer.start()
            self._update_adhan_visualizer()
            self.adhan_blink_visible = True
            self._apply_adhan_blink()
            self.adhan_blink_timer.start()
        else:
            self.active_adhan_profile = None
            if self.adhan_visual_level > 0.0:
                self.adhan_visualizer_timer.start()
            else:
                self.adhan_visualizer_timer.stop()
                self.islamic_ornament.set_audio_level(0.0)
                self.clockPanel.set_audio_level(0.0)
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
            self.islamic_event.setTags(
                special_day_statuses(info["day"], info["month"], value.weekday())
            )
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
            celebration = uses_celebration_palette(info["day"], info["month"])
            self.clockPanel.set_celebration(celebration)
            self.islamic_ornament.set_celebration(celebration)
            self.clockPanel.style().unpolish(self.clockPanel)
            self.clockPanel.style().polish(self.clockPanel)
            arabic, translation, reference = daily_verse(value.date())
            self.quran_arabic.setText(arabic)
            # Keep the complete surah reference together on its own line.
            self.quran_translation.setText(f"„{translation}“\n{reference}")
            self.last_content_date = value.date()
        except (ImportError, ValueError):
            self.hijri_date.setText("Islamisches Datum derzeit nicht verfügbar")
            self.islamic_event.hide()
            self.tomorrow_islamic_notice.hide()
