# Raspberry Pi kiosk setup

The application itself uses a frameless always-on-top full-screen window and
brings it back to the foreground every two seconds. It never clicks or confirms
dialogs automatically.

For a dedicated prayer-clock device, also disable desktop notifications and
automatic update prompts in Raspberry Pi OS. With LXDE, add these lines to the
user's autostart file:

```text
@xset s off
@xset -dpms
@xset s noblank
@sh -c 'sleep 3; python3 /path/to/PrayerTimeClock.py'
```

If update notifications are still shown, disable the graphical update notifier
in the desktop session's autostart settings. Keep unattended security updates
enabled where possible; disabling the notification UI is preferable to
disabling updates themselves.

Do not use an image-change detector that clicks automatically. It could confirm
an update, authentication, shutdown, or another security-sensitive dialog.
