"""Bounded NetworkManager recovery; invoked outside the Qt GUI thread."""
import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass

log = logging.getLogger(__name__)


def split_fields(line):
    """Decode nmcli's escaped colons/backslashes (including in SSIDs)."""
    fields, value, escaped = [], [], False
    for char in line:
        if escaped:
            value.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append("".join(value))
            value = []
        else:
            value.append(char)
    fields.append("".join(value))
    return fields


@dataclass(frozen=True)
class NetworkStatus:
    connected: bool = False
    name: str = ""
    message: str = "WLAN-Status wird geprüft …"
    connectivity: str = "unknown"


class NetworkRecovery:
    def __init__(self, run=subprocess.run, clock=time.monotonic, which=shutil.which):
        self.run, self.clock, self.which = run, clock, which
        self.next_attempt = 0.0
        self.retry_delay = 60

    def _nmcli(self, *args, wait=4):
        result = self.run(
            ["nmcli", "--wait", str(wait), *args],
            capture_output=True, text=True, check=False, timeout=wait + 2,
            stdin=subprocess.DEVNULL, env={**os.environ, "LC_ALL": "C"},
        )
        if result.returncode:
            # Do not log SSIDs, connection profiles or credentials.
            log.warning("NetworkManager command failed (exit %s)", result.returncode)
            raise RuntimeError("WLAN-Aktion fehlgeschlagen – NetworkManager/Berechtigungen prüfen")
        return result.stdout.strip()

    def check(self, manual=False):
        if not self.which("nmcli"):
            return NetworkStatus(message="NetworkManager ist nicht verfügbar")
        try:
            return self._check(manual)
        except (OSError, subprocess.TimeoutExpired, RuntimeError) as error:
            log.warning("Network check/recovery failed: %s", type(error).__name__)
            if self.clock() >= self.next_attempt:
                self._backoff()
            message = (str(error) if isinstance(error, RuntimeError)
                       else "WLAN-Prüfung fehlgeschlagen – erneuter Versuch folgt")
            return NetworkStatus(message=message)

    def _backoff(self):
        self.next_attempt = self.clock() + self.retry_delay
        self.retry_delay = min(self.retry_delay * 2, 600)

    def _check(self, manual):
        rows = [split_fields(line) for line in self._nmcli(
            "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"
        ).splitlines()]
        wifi = [row for row in rows if len(row) == 4 and row[1] == "wifi"]
        connected = next((row for row in wifi if row[2].startswith("connected")), None)
        if connected:
            self.retry_delay, self.next_attempt = 60, 0.0
            try:
                connectivity = self._nmcli("networking", "connectivity", "check")
            except (OSError, subprocess.TimeoutExpired, RuntimeError):
                connectivity = "unknown"
            suffix = {"full": "Internet erreichbar", "limited": "Internet eingeschränkt",
                      "portal": "WLAN-Anmeldung erforderlich", "none": "Internet nicht erreichbar"}
            return NetworkStatus(True, connected[3],
                                 "WLAN verbunden · " + suffix.get(connectivity, "Internetstatus unbekannt"),
                                 connectivity)
        if not wifi:
            return NetworkStatus(message="Kein WLAN-Adapter gefunden")
        if any(row[1] == "ethernet" and row[2].startswith("connected") for row in rows if len(row) == 4) and not manual:
            return NetworkStatus(message="LAN verbunden · WLAN nicht verbunden")
        if not manual and self.clock() < self.next_attempt:
            remaining = max(1, int(self.next_attempt - self.clock()))
            return NetworkStatus(message=f"WLAN getrennt · neuer Versuch in {remaining} s")
        radio = self._nmcli("radio", "wifi")
        if radio != "enabled":
            if not manual:
                return NetworkStatus(message="WLAN ausgeschaltet · über Neu verbinden einschalten")
            self._nmcli("radio", "wifi", "on")
        # Do not interrupt NetworkManager while it is already activating.
        device = next((row for row in wifi if row[2] == "disconnected"), None)
        if device is None:
            return NetworkStatus(message="WLAN verbindet oder Adapter ist nicht verfügbar")
        self._backoff()
        log.info("Attempting Wi-Fi recovery")
        # Unlike 'device connect', 'connection up' only activates an existing
        # profile. NetworkManager selects the best one for the detected device.
        self._nmcli("connection", "up", "ifname", device[0], wait=15)
        return self._check(False)
