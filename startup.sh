#!/bin/bash

cd ~/prayertimeclock

export DISPLAY=:0
export XAUTHORITY=/home/hamitgueler/.Xauthority
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export SDL_AUDIODRIVER=pulse  # Erzwinge PulseAudio statt ALSA

until pactl info >/dev/null 2>&1; do
  echo "Warte auf PulseAudio..."
  sleep 0.5
done

# Warte auf Internetverbindung (max. 60s)
for i in {1..60}; do
    echo Warte auf Internetverbindung...
    if ping -c 1 8.8.8.8 &> /dev/null; then
        echo "Internetverbindung erkannt"

        # Git Pull ausführen
        if git pull | grep -q -v "Already up to date."; then
            echo "Git Pull erfolgreich mit Änderungen"
        else
            echo "Git Pull erfolgreich, aber keine Änderungen"
        fi

        # Aktiviere virtuelle Umgebung
        source venv/bin/activate

        # Starte die App  
        python src/PrayerTimeClock.py  >> python_output.log 2>&1
        exit 0
    fi
    sleep 1
done

echo "Keine Internetverbindung – App wird NICHT gestartet"
exit 1