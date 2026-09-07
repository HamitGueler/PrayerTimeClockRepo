"""Blocking hardware operations. No Qt objects belong in this module."""
import os
import shutil
import subprocess


def set_audio_gain(value):
    if not shutil.which('pactl'):
        return False
    result = subprocess.run(
        ['pactl', 'set-sink-volume', '@DEFAULT_SINK@', f'{max(100, value)}%'],
        stdin=subprocess.DEVNULL, capture_output=True, timeout=3, check=False,
    )
    return result.returncode == 0


def set_brightness(value):
    if shutil.which('brightnessctl'):
        try:
            result = subprocess.run(
                ['brightnessctl', 'set', f'{value}%'], stdin=subprocess.DEVNULL,
                check=False, capture_output=True, timeout=3,
            )
            if result.returncode == 0:
                return True
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        for device in os.listdir('/sys/class/backlight'):
            root = os.path.join('/sys/class/backlight', device)
            try:
                with open(os.path.join(root, 'max_brightness'), encoding='utf-8') as file:
                    maximum = int(file.read().strip())
                with open(os.path.join(root, 'brightness'), 'w', encoding='utf-8') as file:
                    file.write(str(max(1, round(maximum * value / 100))))
                return True
            except (OSError, ValueError):
                continue
    except OSError:
        pass
    return False
