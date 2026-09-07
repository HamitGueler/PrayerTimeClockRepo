import subprocess
from types import SimpleNamespace

from HelperClasses.NetworkRecovery import NetworkRecovery, split_fields


class FakeNetwork:
    def __init__(self):
        self.state = 'disconnected'
        self.radio = 'enabled'
        self.connectivity = 'full'
        self.failure = None
        self.calls = []
        self.now = 1000

    def run(self, command, **kwargs):
        assert kwargs['timeout'] <= 17
        assert kwargs['env']['LC_ALL'] == 'C'
        self.calls.append(command)
        args = command[3:]
        output = ''
        if args[-2:] == ['device', 'status']:
            output = f'wlp2s0:wifi:{self.state}:Test\\: WLAN\n'
        elif args == ['radio', 'wifi']:
            output = self.radio
        elif args == ['networking', 'connectivity', 'check']:
            output = self.connectivity
        elif args[:2] == ['connection', 'up']:
            assert args == ['connection', 'up', 'ifname', 'wlp2s0']
            if self.failure == 'timeout':
                raise subprocess.TimeoutExpired(command, kwargs['timeout'])
            if self.failure == 'permission':
                return SimpleNamespace(returncode=4, stdout='', stderr='permission denied')
            self.state = 'connected'
        return SimpleNamespace(returncode=0, stdout=output, stderr='')

    def monitor(self):
        return NetworkRecovery(run=self.run, clock=lambda: self.now, which=lambda _: '/usr/bin/nmcli')

    def attempts(self):
        return sum('up' in call for call in self.calls)


def test_recovers_detected_interface_and_verifies_connection():
    fake = FakeNetwork()
    status = fake.monitor().check()
    assert status.connected and status.name == 'Test: WLAN'
    assert fake.attempts() == 1


def test_retries_after_timeout_without_stopping_monitor():
    fake = FakeNetwork()
    fake.failure = 'timeout'
    monitor = fake.monitor()
    assert not monitor.check().connected
    assert not monitor.check().connected
    assert fake.attempts() == 1
    fake.now = monitor.next_attempt
    fake.failure = None
    assert monitor.check().connected
    assert monitor.retry_delay == 60


def test_long_outage_retries_indefinitely_but_caps_frequency():
    fake = FakeNetwork()
    fake.failure = 'permission'
    monitor = fake.monitor()
    for _ in range(15):
        status = monitor.check()
        assert 'Berechtigungen' in status.message
        assert 0 < monitor.next_attempt - fake.now <= 600
        fake.now = monitor.next_attempt
    assert fake.attempts() == 15


def test_router_internet_outage_does_not_disconnect_working_wifi():
    fake = FakeNetwork()
    fake.state, fake.connectivity = 'connected', 'limited'
    status = fake.monitor().check()
    assert status.connected and status.connectivity == 'limited'
    assert fake.attempts() == 0


def test_respects_disabled_radio_and_in_progress_connection():
    for state, radio in [('disconnected', 'disabled'), ('connecting (getting IP configuration)', 'enabled')]:
        fake = FakeNetwork()
        fake.state, fake.radio = state, radio
        assert not fake.monitor().check().connected
        assert fake.attempts() == 0


def test_manual_request_bypasses_backoff():
    fake = FakeNetwork()
    fake.failure = 'permission'
    monitor = fake.monitor()
    monitor.check()
    fake.failure = None
    assert monitor.check(manual=True).connected


def test_missing_networkmanager_is_reported():
    assert 'nicht verfügbar' in NetworkRecovery(which=lambda _: None).check().message


def test_escaped_network_names():
    assert split_fields(r'wlan0:wifi:connected:Home\: A\\B') == ['wlan0', 'wifi', 'connected', 'Home: A\\B']
