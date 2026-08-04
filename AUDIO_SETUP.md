# Adhān-Audiodateien

Lege die beiden Aufnahmen desselben Muʾadhdhins in `AudioFiles`:

- `adhan.mp3` – normaler Adhān für Dhuhr, ʿAṣr, Maghrib und ʿIschāʾ
- `fajr_adhan.mp3` – Fajr-Adhān mit „aṣ-ṣalātu ḫayrun mina n-naum“

Zu beiden Dateien gehören vorab berechnete Lautstärkeprofile unter
`src/AudioProfiles/`. Während der Wiedergabe steuern diese Profile das
Ornament synchron zur jeweiligen Aufnahme. Sie werden nicht zufällig erzeugt
und benötigen auf dem Raspberry Pi keine Live-Audioanalyse.
Dasselbe Profil steuert die Partikel im Hauptbereich: Lautere Passagen
verstärken ihr Glühen und blenden einige zusätzliche Lichtpunkte weich ein,
während ruhige Passagen die Standardbewegung beibehalten.

Wenn eine Adhān-Datei ersetzt wird, müssen die Profile einmalig auf einem
System mit `ffmpeg` neu erzeugt werden:

```bash
python3 scripts/generate_adhan_profiles.py
```

Fehlt ein Profil oder ist es beschädigt, bleiben Ornament und Partikel
automatisch bei ihrer normalen ruhigen Animation; die Audiowiedergabe ist
davon unabhängig.

Der Adhān wird ausschließlich beim Eintritt einer Gebetszeit abgespielt.
Schurūq löst kein Audio aus.

## Lautstärkeverstärkung für leise Displays

Der Regler in den Touch-Einstellungen reicht von 0 bis 150 %. Bis 100 % wird
die normale Qt-Lautstärke verwendet. Zwischen 101 und 150 % bleibt Qt auf
voller Lautstärke und der Standardausgang von PulseAudio beziehungsweise
PipeWire wird zusätzlich über `pactl` verstärkt. Dadurch können besonders
leise HDMI- oder Displaylautsprecher merklich lauter werden.

Hohe Verstärkung kann abhängig vom Lautsprecher zu Verzerrungen führen.
Empfohlen ist, zunächst 115–125 % mit „Adhān abspielen“ zu testen. Sobald der
Klang kratzt oder scheppert, sollte der Wert wieder reduziert werden. Beim
Zurückregeln auf höchstens 100 % normalisiert die Anwendung den Systemausgang
wieder auf 100 %.
