# PrayerTimeClock

Eine touchoptimierte Gebetszeituhr für den Raspberry Pi. Die Anwendung zeigt die
Gebetszeiten für Berlin im Vollbild, lädt die Daten von Diyanet, spielt zum
Gebetseintritt den passenden Adhān und arbeitet bei Netz- oder
Diyanet-Ausfällen mit einem datumsscharfen 7-Tage-Fallback weiter.

![Aktuelle normale Hauptansicht der PrayerTimeClock](prayerclock-preview-v25-monday-thursday-fasting-dedup.svg)

## Funktionsumfang

### Hauptansicht

- Aktuelle Uhrzeit, deutsches Datum und Standort Berlin
- Gebetszeiten für heute und morgen
- Countdown bis zum nächsten Gebet
- Hervorhebung des aktuell eingetretenen Gebets
- Berechnung und Anzeige der islamischen Mitternacht
- Hijri-Datum mit Hinweisen auf besondere islamische Tage und Monate
- Hinweise auf empfohlene Fastentage, unter anderem montags, donnerstags und
  an den weißen Tagen
- Zusammenführung überschneidender Hinweise: „Fasten empfohlen“ erscheint
  nicht doppelt
- Jumuʿah wird freitags im Heute-Bereich und bereits donnerstags im
  Morgen-Bereich angekündigt
- Ruhige Türkis-/Gold-Partikel bewegen sich ausschließlich im linken
  Hauptbereich hinter den Texten
- Animiertes islamisches Ornament
- Datum und Uhrzeit der letzten erfolgreichen Datenaktualisierung
- WLAN-Symbol in der Hauptansicht: grün verbunden, rot und durchgestrichen
  getrennt

### Adhān

- Automatische Wiedergabe ausschließlich beim Eintritt einer tatsächlichen
  Gebetszeit
- Eigene Fajr-Aufnahme mit „aṣ-ṣalātu ḫayrun mina n-naum“
- Normaler Adhān für Dhuhr, ʿAṣr, Maghrib und ʿIschāʾ
- Keine Audioausgabe für Schurūq
- Blinkende Markierung des Gebets während der Wiedergabe
- Das Ornament reagiert synchron auf den tatsächlichen Lautstärkeverlauf der
  jeweiligen Adhān-Aufnahme: ruhige Passagen bewegen die Ringe sanft,
  kräftige Passagen vergrößern und erhellen sie stärker
- Die Partikelbahnen, ihre Größe und ihre Geschwindigkeit bleiben während des
  Adhāns unverändert flüssig. Das Profil beeinflusst nur das Leuchten und
  blendet zusätzliche Lichtpunkte weich ein oder aus.
- Vorab geglättete 100-ms-Profile für normalen und Fajr-Adhān verhindern
  willkürliche oder hektische Ausschläge und entlasten den Raspberry Pi
- Fehlt ein Analyseprofil, läuft sicher die normale Ornamentanimation weiter
- Einstellbare Lautstärke bis 150 % mit sofort hörbarer Änderung. Oberhalb von
  100 % verstärkt PulseAudio beziehungsweise PipeWire den Displayausgang.
- Testfunktion „Adhān abspielen“, die während der Wiedergabe zu
  „Adhān stoppen“ wechselt

Weitere Hinweise zu den Audiodateien stehen in [AUDIO_SETUP.md](AUDIO_SETUP.md).

### Touch-Einstellungen

![Vorschau der Touch-Einstellungen](prayerclock-settings-preview.svg)

- Große Touch-Schaltflächen für die Displayprofile 7, 10 und 14 Zoll
- Live-Regler für Adhān-Lautstärke einschließlich optionaler Verstärkung bis
  150 % und für die Bildschirmhelligkeit
- Kompaktes Zwei-Spalten-Layout ohne notwendiges Scrollen auf dem
  1024×600-Display
- Mini-Live-Vorschau aus exakt demselben Ornament und derselben
  Partikelkomponente wie in der Hauptansicht
- Getrennte Regler für Ornamenttempo, Partikeltempo und Partikelanzahl
- Getrennte Regler für die sichtbare Adhān-Reaktionsstärke von Ornament und
  Partikeln; der geglättete, aufnahmesynchrone Verlauf bleibt erhalten
- Tempo- und Reaktionsregler besitzen einen klar sichtbaren Bereich bis 300 %;
  die Partikeldichte ist von 40–200 % einstellbar
- Die Mini-Vorschau zeigt im Ruhezustand ausschließlich das normale Tempo.
  Die Reaktionsregler werden beim Test-Adhān mit dessen echtem Profil sichtbar.
- Hijri-Korrektur von −2 bis +2 Tagen über separate `−`- und `+`-Tasten
- WLAN-Status einschließlich Name des verbundenen Netzes
- „Neu verbinden“ und „WLAN auswählen / anmelden“
- Updateprüfung, Installation, App-Neustart und App-Beenden
- Eigene umbruchfähige Hinweis- und Bestätigungsdialoge, deren Texte auch auf
  dem Touchdisplay vollständig innerhalb des Fensters bleiben

Die Helligkeitssteuerung verwendet zuerst `brightnessctl`, danach ein
vorhandenes Linux-Backlight-Gerät. Unterstützt ein HDMI-Display keine
Hardwaresteuerung, dimmt die Anwendung die Oberfläche softwareseitig ab.

## Visuelle Zustände

Für jeden relevanten Anwendungszustand gibt es eine eigene SVG-Vorschau. Die
Grafiken sind Beispiele; Datum, Uhrzeit, Gebetszeiten und Hinweise werden in
der Anwendung dynamisch erzeugt.

| Zustand | Darstellung | Vorschau |
| --- | --- | --- |
| Aktuelle Online-Daten | `AKTUELL`, Türkis-/Gold-Partikel und Standardornament | [SVG öffnen](prayerclock-preview-v25-monday-thursday-fasting-dedup.svg) |
| Exakt datierter Cache | `GESPEICHERT` und tatsächlich verbleibende Fallback-Reichweite | [SVG öffnen](prayerclock-cached-state-preview.svg) |
| Kein gültiger Fallback | `VERALTET`, rote Statusfarben und echtes rotes Ornament | [SVG öffnen](prayerclock-fallback-warning-preview.svg) |
| Besonderer islamischer Höhepunkt | deutlich kräftigere Gold-/Weiß-Partikel und Festtagspalette | [SVG öffnen](prayerclock-celebration-state-preview.svg) |
| Laufender Adhān | aufnahme-synchrone Ringausdehnung wie in der SVG: Außenring bleibt formstabil, Mittel- und Innenring pulsieren; transparenter Halo ausschließlich nach außen | [SVG öffnen](prayerclock-adhan-state-preview.svg) |
| Touch-Einstellungen | Display-, Audio-, Helligkeits-, WLAN- und Updateoptionen | [SVG öffnen](prayerclock-settings-preview.svg) |

### Partikel und besondere islamische Tage

Die Standardpartikel verwenden die ruhige Türkis-/Gold-Palette des Designs.
An seltenen, besonders hervorgehobenen Tagen und Nächten wird automatisch eine
hellere Gold-/Weiß-Palette mit mehr und stärker leuchtenden Partikeln
verwendet. Aktuell gilt dies für:

- ʿĪd al-Fiṭr und ʿĪd al-Aḍḥā
- ʿArafah und ʿĀschūrāʾ
- den Beginn Ramaḍāns
- die ungeraden Nächte der letzten zehn Ramaḍān-Nächte
- die ersten zehn Tage von Dhū l-Ḥiddscha

Jumuʿah und andere wichtige Hinweise werden sichtbar gekennzeichnet, lösen
aber nicht automatisch den seltenen Festtagslook aus. Ein kritischer
Fallback-Zustand hat immer Vorrang: Das rote Ornament wird auch an einem
Festtag niemals durch Gold und Weiß überdeckt.

## Datenstatus und 7-Tage-Fallback

Bei jeder erfolgreichen Aktualisierung liest die Anwendung Diyanet-Daten für
heute und die nächsten sieben Tage ein und speichert sie lokal. Jeder Eintrag
ist an ein vollständiges Datum gebunden. Ein alter Montag kann deshalb niemals
als Fallback für einen späteren Montag verwendet werden.

| Anzeige | Bedeutung |
| --- | --- |
| `AKTUELL` | Die heutigen Daten wurden erfolgreich von Diyanet geladen. |
| `GESPEICHERT` | Die Zeiten stammen aus dem lokalen, exakt datierten Fallback. |
| `VERALTET` | Für das benötigte Datum liegen keine gültigen Zeiten vor. |
| `Fallback noch X Tage verfügbar` | So viele lückenlos gespeicherte Tage sind tatsächlich noch nutzbar. |
| `Fallback endet heute` | Nur der heutige Tag ist noch vollständig verfügbar. |
| `Kein Fallback verfügbar` | Es gibt keinen passenden Cache-Eintrag mehr. |

Die Restreichweite wird aus den wirklich vorhandenen Tagen berechnet. Eine
Lücke im Cache wird nicht übersprungen. Nach einem Datumswechsel schaltet die
Uhr nur auf den Eintrag des exakten neuen Datums um; fehlt dieser, werden keine
alten Zeiten als gültig ausgegeben.

Die Fallback-Reichweite ist ausschließlich eine Fehleranzeige: Sie erscheint
erst, nachdem ein Aktualisierungsversuch fehlgeschlagen ist. Nach jedem
erfolgreichen Request verschwindet sie sofort wieder. Scheitern weitere
Versuche an späteren Tagen, wird weiterhin vom Datum des letzten erfolgreichen
Abrufs aus gerechnet und die tatsächlich verbleibende Reichweite entsprechend
kleiner.

Nach sieben vollständigen Tagen ohne erfolgreiche Aktualisierung und ohne
gültige heutige Zeiten wechselt das Ornament auf eine eigene rote Farbpalette.
Es handelt sich nicht um einen transparenten Rotfilter: Konturen, Flächen,
Gürtel und Mittelpunkt werden im Warnzustand neu gerendert. Die
Fallback-Reichweite bleibt kompakt in der oberen Aktualisierungsleiste.
Statusbezeichnung, Fallback-Zeile und Warnbereich reservieren
in jedem Zustand denselben Platz. Der Wechsel von Türkis/Gold zu Rot ändert
nur die Ornamentfarben, nicht die Positionen oder Größen der Oberfläche.

![Aktuelle Hauptansicht ohne verfügbaren Fallback](prayerclock-fallback-warning-preview.svg)

### Verhalten bei Fehlern

- Die Anwendung startet auch ohne Internet mit lokal gespeicherten Daten.
- Beim Start wartet `startup.sh` höchstens 60 Sekunden auf Internet.
- Nach einem fehlgeschlagenen Abruf erfolgt alle fünf Minuten ein neuer
  Datenversuch.
- WLAN-Status und Verbindungswiederherstellung laufen beim Start und alle
  60 Sekunden im Hintergrund. Die Einstellungen zeigen den letzten Prüfstand.
- Bei getrennter WLAN-Verbindung erkennt die App den tatsächlichen Adapter
  (kein festes `wlan0`) und aktiviert über NetworkManager ein vorhandenes
  Verbindungsprofil. Fehlversuche werden nach 60, 120, 240, 480 und danach
  jeweils 600 Sekunden wiederholt; die 60-Sekunden-Prüfung kann den Termin
  auf den nächsten Tick verschieben. Es gibt keine endgültige Versuchsgrenze.
- Ausgeschaltetes WLAN, laufende Verbindungsversuche und eine aktive
  LAN-Verbindung werden automatisch respektiert. „Neu verbinden“ kann WLAN
  ausdrücklich einschalten und die Wartezeit überspringen.
- Ein verbundenes WLAN wird wegen einer Internet-/Diyanet-Störung nicht
  getrennt. Der von NetworkManager gemeldete Internetstatus (erreichbar,
  eingeschränkt, Anmeldung nötig oder unbekannt) erscheint in den Einstellungen
  und im Tooltip. `unknown` ist kein Nachweis für eine funktionierende Verbindung.
- Nach wiederhergestellter Verbindung wird der Datenabruf sofort angestoßen.
  Auch der HTTP-Abruf läuft außerhalb des GUI-Threads: Uhr, Touchbedienung und
  Animationen bleiben während Netzwerktimeouts bedienbar.
- Befehle besitzen Zeitlimits; fehlender NetworkManager, Timeouts und
  Berechtigungsfehler beenden den Monitor nicht. Die App verwendet kein `sudo`
  und erzeugt keine neuen WLAN-Profile. Für das gespeicherte WLAN müssen die
  nötigen Zugangsdaten und die üblichen NetworkManager-Rechte vorhanden sein.
- Ein Wechsel zu einem anderen, in Raspberry Pi OS gespeicherten WLAN erfordert
  keine Änderung an `startup.sh`.

### WLAN bricht erst nach mehreren Tagen ab

Die App kann eine getrennte Verbindung erneut aufbauen. Ob der ursprüngliche
Abbruch durch Router, Funkempfang, Treiber, Stromversorgung oder Energiesparen
entsteht, lässt sich ohne die Raspberry-Pi-Protokolle nicht bestimmen.
Bei einem erneuten Ausfall vor einem Neustart lokal prüfen:

```bash
nmcli device status
nmcli networking connectivity check
journalctl -u NetworkManager --since "2 hours ago" --no-pager
journalctl -k --since "2 hours ago" --no-pager
```

Vor dem Teilen Netzwerknamen, MAC-/IP-Adressen und andere private Angaben
entfernen. Keine Passwörter oder Ausgabe von `--show-secrets` teilen.
Die Änderung wurde mit simulierten Ausfällen geprüft; ein mehrtägiger Test
auf dem tatsächlichen Raspberry Pi steht noch aus.

Referenz: [NetworkManager / nmcli](https://networkmanager.dev/docs/api/latest/nmcli.html).

## Sichere Anwendungsupdates

Updates werden innerhalb der Einstellungsseite installiert:

1. Die Anwendung prüft den Branch `NewClockVersion`.
2. Ein neuer Stand wird zunächst in einem temporären Verzeichnis vorbereitet.
3. Neue Einträge aus `requirements.txt` werden mit der aktiven virtuellen
   Python-Umgebung installiert.
4. Der Python-Code wird kompiliert und der neue Stand getestet.
5. Erst bei erfolgreicher Prüfung wird das Fast-Forward-Update übernommen.
6. Die laufende Anwendung bleibt geöffnet und zeigt
   `Update installiert · Neustart erforderlich`.
7. Der Nutzer startet die App bewusst über „App neu starten“ neu.

`startup.sh` bleibt nach dem Start als unsichtbarer Supervisor aktiv. Ein über
die Einstellungen angeforderter Neustart beendet zuerst die bisherige
Qt-Instanz vollständig und startet sie anschließend anhand des reservierten
Rückgabecodes `75` neu. Ein sichtbares Terminal ist dafür nicht erforderlich;
„App beenden“ bleibt dagegen ein echtes Beenden ohne automatischen Neustart.

Auch nach einem manuellen `git pull` vergleicht `startup.sh` den Hash der
`requirements.txt` und installiert geänderte Python-Abhängigkeiten vor dem
Start einmalig.

## Empfohlene Hardware

- Raspberry Pi 4 Model B oder neuer
- 7-, 10- oder 14-Zoll-Touchdisplay mit HDMI-Eingang
- USB-Verbindung für Touch
- Separate stabile Stromversorgung für das Display
- Lautsprecher über HDMI oder einen vom Betriebssystem bereitgestellten
  Audioausgang

Ein 10,1-Zoll-Display mit 1920 × 1200 Pixeln funktioniert mit dem
10-Zoll-Profil. Beim Raspberry Pi 4 wird für das Bild ein
Micro-HDMI-auf-HDMI-Kabel benötigt.

## Installation

Voraussetzungen: Raspberry Pi OS beziehungsweise eine Debian-/Ubuntu-basierte
Desktop-Umgebung, Python 3, Git und NetworkManager.

```bash
git clone --branch NewClockVersion https://github.com/HamitGueler/PrayerTimeClockRepo.git
cd PrayerTimeClockRepo
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python src/PrayerTimeClock.py
```

Für den automatischen Vollbildstart auf dem Raspberry Pi kann `startup.sh`
verwendet werden. Das Skript erwartet das Repository unter
`~/Desktop/PrayerTimeClockRepo`. Hinweise zum störungsfreien Kiosk-Betrieb
stehen in [KIOSK_SETUP.md](KIOSK_SETUP.md).

## Konfiguration

Die persönlichen Einstellungen werden über `QSettings` gespeichert und beim
nächsten Start wieder geladen:

- Adhān-Lautstärke von 0–150 %; der Bereich oberhalb von 100 % ist eine
  optionale Systemverstärkung für leise Displaylautsprecher
- Helligkeit
- Displayprofil
- Hijri-Korrektur
- Ornamentgeschwindigkeit
- Partikelgeschwindigkeit
- Partikelanzahl
- Adhān-Reaktionsstärke des Ornaments
- Adhān-Reaktionsstärke der Partikel

Die fünf Animationswerte wirken nicht nur in der Vorschau: Nach „Speichern“
werden sie unmittelbar an Ornament und Partikel der Hauptansicht übergeben und
beim nächsten Start wieder aus `QSettings` geladen. Der Bereich bis 300 % dient
bewusst auch der Kontrolle auf dem echten Display; 100 % bleibt die ruhige
Standardabstimmung.

Für bessere Ablesbarkeit bei Tageslicht verwendet die Hauptansicht höhere
Flächenkontraste sowie kräftigere Türkis-, Gold- und Weißtöne. Die Partikel
atmen bereits im Normalbetrieb sichtbar über Kerngröße und zwei getrennte
Leuchthöfe. Während des Adhāns steuert das Analyseprofil nur Deckkraft und Glow
der Partikel sowie das weiche Einblenden bereits vorhandener zusätzlicher
Lichtpunkte. Bahn, Geschwindigkeit und Größe werden nicht vom Ton beeinflusst,
damit die Animation nicht ruckelt. Am Ornament steuert das Profil Ausdehnung
und Leuchten der drei Ringe. Die normale Ornamentgröße bleibt dabei unverändert:
Der äußere Ring reagiert nur dezent, während der Impuls in Mittel- und Innenring
deutlicher sichtbar wird. Der vergrößerte äußere Halo bleibt in der
Zeichenfläche sichtbar und wird auch in der Mini-Vorschau nicht abgeschnitten.
Eine geometrische Maske begrenzt den Ornament-Halo vollständig
auf den Bereich außerhalb des unveränderten Außenrings. Dadurch kann trotz der
leicht transparenten Ornamentbasis kein Licht in die inneren Ringe
durchscheinen; Abstand und Größe bleiben unverändert. Der äußere Partikel-Halo
ist gegenüber der kräftigeren Tageslichtabstimmung leicht reduziert.

Bei mehr als 100 % Adhān-Lautstärke setzt die Anwendung den Standardausgang
über `pactl` entsprechend höher. Beim Zurückregeln auf 100 % oder weniger wird
der Systemausgang wieder auf 100 % normalisiert. Je nach Qualität der im
Display eingebauten Lautsprecher kann hohe Verstärkung verzerren; deshalb
sollte zunächst etwa 115–125 % getestet und nur bei sauberem Klang weiter
erhöht werden.

Die Diyanet-Quelle ist derzeit fest auf Berlin eingestellt:

```text
https://namazvakitleri.diyanet.gov.tr/de-DE/11002/gebetszeit-fur-berlin
```

Der lokale Gebetszeiten-Cache wird beim ersten erfolgreichen Abruf automatisch
erzeugt und atomar ersetzt, damit ein abgebrochener Schreibvorgang keinen
gültigen Cache zerstört.

## Tests

```bash
source venv/bin/activate
python -m unittest discover -s tests -v
```

Die Tests sichern unter anderem ab:

- Parsing und Validierung der Diyanet-Zeiten
- Auswahl des Fallbacks ausschließlich nach exaktem Datum
- Abbruch der Fallback-Reichweite bei einer Datumslücke
- Grenzfall des roten Warnzustands nach sieben Tagen
- Hijri-Korrektur und islamische Tageshinweise
- Deduplizierung überschneidender Fastenempfehlungen
- Unterdrückung freiwilliger Fastenhinweise an ʿĪd- und Taschrīq-Tagen
- Jumuʿah-Hinweise für heute und morgen
- Auswahl der Gold-/Weiß-Festtagspalette

## Projektstruktur

```text
src/
├── AudioFiles/                     # Fajr- und regulärer Adhān
├── HelperClasses/
│   ├── ApplicationUpdateService.py
│   ├── PrayerTimeFreshness.py
│   └── WebScraperClass.py
├── PyViews/                        # PySide6-Oberfläche und Anwendungslogik
├── UIViews/                        # Qt-Designer-Datei
└── PrayerTimeClock.py              # Einstiegspunkt
tests/                              # Logik- und Fallback-Tests
startup.sh                          # Raspberry-Pi-/Kiosk-Start
style.css                           # Oberflächen-Styling
```

## Ältere Ansicht

Das folgende Bild zeigt eine frühere Version und dient nur als historischer
Vergleich:

<img src="Preview.jpeg" alt="Frühere Version der PrayerTimeClock" width="600">

### Sichere Einstellungsaktionen

Die Einstellungsseite öffnet ohne blockierende Git-/Systembefehle im GUI-Thread.
Updateprüfung und Installation laufen als einzelne Hintergrundaufträge. Qt-
Widgets, Dialoge, Audioausgabe und Displayprofilwechsel bleiben im GUI-Thread.
Die Ergebniszustellung erfolgt über Qt-Signale an GUI-eigene Empfänger.

- Erneutes Antippen startet keinen zweiten Updateauftrag. Nach einem Fehler
  wird der Button wieder freigegeben. Während der eigentlichen Installation
  sind App-Neustart und App-Beenden gesperrt; die Einstellungen können weiter
  bedient oder geschlossen werden. Der Auftrag läuft dann weiter.
- Speichern, Abbrechen und App schließen bleiben in einer festen Fußzeile
  sichtbar, auch wenn der Einstellungsinhalt gescrollt wird.
- Geschlossene Dialoge werden nicht mehr von späten Ergebnissen angesprochen.
  Ein erneut geöffneter Dialog übernimmt den aktuellen Auftragsstatus.
- Helligkeit und System-Audioverstärkung werden mit kurzer Verzögerung und
  höchstens einem Hardwareauftrag gleichzeitig geschrieben. Von schnellen
  Reglerbewegungen wird nur der neueste noch ausstehende Wert übernommen.
  „Abbrechen“ stellt Helligkeit und Lautstärke wieder her.
- Die externe WLAN-Auswahl startet über `QProcess`; fehlendes Programm,
  Startfehler und Prozessende werden behandelt. Der Kiosk-Vordergrundmodus und
  die Dialogmodalität werden während der externen Auswahl aufgehoben, damit
  das Systemfenster Touch-Eingaben erhalten kann. Mit dem Schließen/Speichern
  der Einstellungen wird der Vordergrundmodus der Uhr wiederhergestellt.
- Displayprofile werden vollständig zurückgesetzt, wenn zwischen 10, 7 und
  14 Zoll gewechselt wird. Für reine Layoutänderungen wird kein Thread benutzt.
- Updatebefehle erhalten kein interaktives Terminal. Ein Update wird auf die
  konkret vorbereitete Git-Version festgelegt und bei lokalen Änderungen
  abgebrochen. Netzwerk-, Installations- und Hardwarebefehle haben Zeitlimits.

Der Bildschirm-/Treiberzustand und die Desktop-Fokusregeln auf dem konkreten
Raspberry Pi müssen nach Veröffentlichung zusätzlich dort geprüft werden.

### Koran-Zitate: vollständiger Offline-Bestand

Bisher gab es fünf Einträge, die nach dem Tagesdatum in einem Fünf-Tage-Zyklus
wechselten. Nun enthält die App den vollständigen arabischen Koran mit
Bubenheim/Elyas-Bedeutungsübersetzung: **114 Suren, 6.236 Verse**.

In den Einstellungen unter „Tägliches Koran-Zitat“ stehen zwei Sammlungen:

- **Ausgewählte Verse (406)**: eine redaktionelle Referenzliste mit vielen
  bekannten Stellen zu Gebet, Dankbarkeit, Geduld, Barmherzigkeit und Verhalten.
- **Gesamter Koran (6.236 Verse)**: alle Verse des Offline-Bestands.

Ein stabil gemischter Tageszyklus wechselt zwischen Suren. Am selben Tag bleibt
es derselbe Vers, auch nach einem Neustart. Erst nach dem vollständigen
Durchlauf der gewählten Sammlung wiederholt sich ein Eintrag. Dies ist keine
Bewertung der religiösen Bedeutung einzelner Verse.

Die Originaltexte bleiben vollständig. Lange arabische Texte und Übersetzungen
stehen innerhalb eines festen Bereichs: nach zwölf Sekunden beginnt sanftes
Scrollen; am Anfang und Ende wird pausiert. Berührung/Scrollen pausiert die
Automatik für 30 Sekunden. Surenname, Versnummer und Übersetzungsquelle bleiben
sichtbar; die übrige Oberfläche wird durch lange Verse nicht verschoben.
Die mitgelieferte Schrift **Amiri Quran** unterstützt die koranischen
Schriftzeichen, ohne separate Schriftinstallation auf dem Raspberry Pi.

Die Daten stammen aus dokumentierten Quran-JSON-/Quran-API-Datensätzen:
Arabischer Text aus QuranEnc über `risan/quran-json`; deutsche Übersetzung aus
Tanzil über `fawazahmed0/quran-api`. Es wird kein täglicher API-Aufruf und keine
zusätzliche Python-Bibliothek benötigt. Der direkte QuranEnc-Export war in der
Entwicklungsumgebung nicht abrufbar; die gebündelte deutsche Ausgabe ist die
Tanzil-Ausgabe, nicht die Behauptung einer aktuelleren QuranEnc-Revision.

Quellen, Nutzungsbedingungen und Prüfsummen:
[QURAN-SOURCES.md](src/Data/QURAN-SOURCES.md),
[quran-sources.json](src/Data/quran-sources.json),
[Schriftlizenz](src/Fonts/AMIRI-OFL.txt).
Die deutsche Übersetzung ist für nichtkommerzielle Nutzung vorgesehen;
kommerzielle Nutzung erfordert die Erlaubnis des Rechteinhabers.
`scripts/import_quran.py` ermöglicht einen ausdrücklich gestarteten Datenimport;
neue Quellenstände sollten vor einer Veröffentlichung geprüft werden.

### Reproduzierbare Qt-Vorschau

`scripts/render_qt_preview.py` rendert die tatsächlichen Qt-Widgets bei
1920×1200 mit isolierten Einstellungen und festen **Beispielzeiten**.
Es führt keine Netzwerk-, Audio- oder Cache-Schreibaktionen aus. Die PNGs
sind keine Gebetszeitenquelle. Das Skript vergleicht Normal-/Warnzustand
auf identische Geometrie und prüft Ornamentabstand und 64-px-Zeiten.

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python scripts/render_qt_preview.py --output /tmp/prayerclock-preview
# Zusätzlicher Layout-Stresstest mit beispielhaften Tags:
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python scripts/render_qt_preview.py --tags --output /tmp/prayerclock-tags
PYTHONPATH=src python -m pytest -q
```

Das 10-Zoll-Profil behält die 198-px-Hauptuhr und das 370-px-Ornament.
Sekundärtexte und der Morgenbereich sind kompakter, damit auch mit Tags
und Warnzeile ausreichend Platz bleibt. Heutige und morgige Zeiten haben
64 px; ein zuvor stärkerer CSS-Selektor hatte die heutigen Zeiten verkleinert.
Das WLAN-Symbol nutzt 40 px innerhalb seines 58-px-Buttons.
