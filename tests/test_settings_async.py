import threading
from unittest.mock import Mock
import pytest
from PySide6.QtCore import QEventLoop, QSettings, QTimer, Qt
from PySide6.QtWidgets import QDialog
from HelperClasses.AsyncActions import LatestValueAction
from PyViews import PrayerTimeClockWindow_Impl as impl


def wait_until(predicate, timeout=1500):
    loop = QEventLoop()
    poll = QTimer()
    poll.setInterval(5)
    poll.timeout.connect(lambda: loop.quit() if predicate() else None)
    deadline = QTimer()
    deadline.setSingleShot(True)
    deadline.timeout.connect(loop.quit)
    poll.start()
    deadline.start(timeout)
    if not predicate():
        loop.exec()
    poll.stop()
    deadline.stop()
    assert predicate(), 'Asynchronous result did not arrive'


@pytest.fixture
def clock(qapp, monkeypatch, tmp_path):
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    settings.setValue('displayProfile', '10 Zoll')
    monkeypatch.setattr(impl, 'QSettings', lambda *args: settings)
    for name in ('refresh_data', '_refresh_network_status', '_load_cached_prayer_times',
                 '_save_prayer_times_cache', '_apply_brightness', '_apply_system_audio_gain'):
        monkeypatch.setattr(impl.PrayerTimeClockWindow, name, Mock())
    window = impl.PrayerTimeClockWindow()
    for timer in window.findChildren(QTimer):
        timer.stop()
    yield window
    if window.settings_dialog is not None:
        window.settings_dialog.reject()
    window.close()
    window.deleteLater()
    qapp.processEvents()


def test_update_check_does_not_block_profile_buttons_and_closed_dialog_is_safe(clock, monkeypatch):
    release = threading.Event()
    calls = []
    def check():
        calls.append(threading.get_ident())
        release.wait(1)
        return 2
    monkeypatch.setattr(clock.update_service, 'available_commits', check)
    try:
        clock.open_settings()
        dialog = clock.settings_dialog
        assert clock.actions.busy('update')
        dialog.profile_buttons['7 Zoll'].click()
        assert dialog.selected_display_profile() == '7 Zoll'
        clock._handle_update(dialog)
        dialog.reject()
        assert clock.settings_dialog is None
        release.set()
        wait_until(lambda: not clock.actions.busy('update'))
        assert len(calls) == 1
        assert calls[0] != threading.get_ident()
        assert clock.isVisible()
    finally:
        release.set()


def test_install_continues_after_settings_close_and_blocks_app_restart(clock, monkeypatch):
    monkeypatch.setattr(clock.update_service, 'available_commits', lambda: 1)
    monkeypatch.setattr(clock, '_ask_confirmation', lambda *args: True)
    release = threading.Event()
    monkeypatch.setattr(clock.update_service, 'install_and_validate',
                        lambda: (release.wait(1) and True, 'Installed'))
    try:
        clock.open_settings()
        wait_until(lambda: not clock.actions.busy('update'))
        clock._handle_update(clock.settings_dialog)
        wait_until(lambda: clock.update_installing)
        clock._restart_application(clock.settings_dialog, False)
        assert 'abschließen' in clock.settings_dialog.system_feedback.text()
        clock.settings_dialog.reject()
        clock.open_settings()
        assert not clock.settings_dialog.check_update_button.isEnabled()
        release.set()
        wait_until(lambda: not clock.update_installing)
        assert clock.settings_dialog.check_update_button.isEnabled()
        assert 'Neustart' in clock.settings_dialog.update_status.text()
    finally:
        release.set()


def test_external_program_start_failure_keeps_clock_alive(clock, monkeypatch):
    monkeypatch.setattr(clock.update_service, 'available_commits', lambda: 0)
    clock.open_settings()
    wait_until(lambda: not clock.actions.busy('update'))
    # Discovery says installed, actual process spawn fails in this environment.
    monkeypatch.setattr(impl.shutil, 'which', lambda _: '/nonexistent/nm-connection-editor')
    clock._open_wifi_settings(clock.settings_dialog)
    wait_until(lambda: clock.external_settings_process is None)
    assert clock.settings_dialog.wifi_button.isEnabled()
    assert clock.isVisible()
    assert not clock.windowFlags() & Qt.WindowStaysOnTopHint
    clock.settings_dialog.reject()
    assert clock.windowFlags() & Qt.WindowStaysOnTopHint


def test_slider_writes_are_serialized_and_only_latest_pending_value_wins(qapp):
    release = threading.Event()
    started = threading.Event()
    writes, received = [], []
    def write(value):
        writes.append(value)
        started.set()
        if value == 10:
            release.wait(1)
        return True
    action = LatestValueAction(write)
    action.completed.connect(lambda value, result, error: received.append((value, error)))
    action.set_value(10)
    action.timer.stop()
    action._start()
    wait_until(started.is_set)
    action.set_value(20)
    action.set_value(30)
    action.set_value(80)
    release.set()
    wait_until(lambda: bool(received))
    assert writes == [10, 80]
    assert received == [(80, None)]
    action.deleteLater()


def test_cancel_restores_brightness_and_all_profile_switches_reset_layout(clock, monkeypatch):
    monkeypatch.setattr(clock.update_service, 'available_commits', lambda: 0)
    clock.open_settings()
    wait_until(lambda: not clock.actions.busy('update'))
    clock.settings_dialog.brightness_slider.setValue(20)
    clock.settings_dialog.reject()
    clock._apply_brightness.assert_called_with(clock.brightness)
    for profile in ('7 Zoll', '14 Zoll', '10 Zoll'):
        clock._apply_display_profile(profile)
        assert clock.quran_panel.height() > 0
    assert clock.islamic_ornament.width() == 370


def test_hardware_error_delivers_failure_and_accepts_next_request(qapp):
    def write(value):
        if value == 10:
            raise PermissionError('test')
        return True
    action = LatestValueAction(write)
    received = []
    action.completed.connect(lambda value, result, error: received.append((value, result, error)))
    action.set_value(10)
    wait_until(lambda: len(received) == 1)
    assert isinstance(received[0][2], PermissionError)
    action.set_value(60)
    wait_until(lambda: len(received) == 2)
    assert received[1] == (60, True, None)
    action.deleteLater()
