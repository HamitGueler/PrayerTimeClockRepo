#!/bin/bash

cd ~/Desktop/PrayerTimeClockRepo

export DISPLAY=:0
export XAUTHORITY=/home/hamitgueler/.Xauthority
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export SDL_AUDIODRIVER=pulse  # Erzwinge PulseAudio statt ALSA

until pactl info >/dev/null 2>&1; do
  echo "Warte auf PulseAudio..."
  sleep 0.5
done

# Prüfe die Internetverbindung (max. 60s). Die App startet anschließend
# in jedem Fall, damit der lokale Tages-Cache auch offline genutzt wird.
online=false
for i in {1..60}; do
    echo Warte auf Internetverbindung...
    if ping -c 1 8.8.8.8 &> /dev/null; then
        echo "Internetverbindung erkannt"
        online=true
        break
    fi
    sleep 1
done

if ! "$online"; then
    echo "Keine Internetverbindung – starte mit lokalem Tages-Cache"
fi

source venv/bin/activate

# Install dependencies only when requirements.txt has changed. In-app updates
# already do this before switching versions; this also protects manual pulls.
requirements_hash=$(sha256sum requirements.txt | cut -d' ' -f1)
requirements_marker="venv/.requirements.sha256"
installed_hash=$(cat "$requirements_marker" 2>/dev/null || true)
if [ "$requirements_hash" != "$installed_hash" ]; then
    echo "Prüfe neue Python-Abhängigkeiten..."
    if python -m pip install --disable-pip-version-check -r requirements.txt; then
        printf '%s\n' "$requirements_hash" > "$requirements_marker"
    else
        echo "Abhängigkeiten konnten nicht vollständig installiert werden."
    fi
fi

# Keep the launcher alive so an in-app restart can be handled after the Qt
# process has shut down completely.  Exit code 75 is reserved for a requested
# application restart; a normal exit still leaves the clock closed.
export PRAYERCLOCK_SUPERVISED=1
restart_exit_code=75
while true; do
    python src/PrayerTimeClock.py
    app_exit_code=$?
    if [ "$app_exit_code" -ne "$restart_exit_code" ]; then
        exit "$app_exit_code"
    fi
    echo "PrayerTimeClock wird neu gestartet ..."
    sleep 1
done
