import json
import os


class AdhanAudioProfile:
    """Pre-analysed, smoothed loudness values for one Adhān recording."""

    def __init__(self, interval_ms, values):
        self.interval_ms = max(1, int(interval_ms))
        self.values = tuple(max(0.0, min(1.0, float(value))) for value in values)

    @classmethod
    def from_file(cls, path):
        try:
            with open(path, encoding="utf-8") as profile_file:
                data = json.load(profile_file)
            return cls(data["intervalMs"], data["values"])
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    def value_at(self, position_ms):
        if not self.values or position_ms < 0:
            return 0.0
        position = position_ms / self.interval_ms
        left = min(int(position), len(self.values) - 1)
        right = min(left + 1, len(self.values) - 1)
        fraction = position - int(position)
        return self.values[left] + (self.values[right] - self.values[left]) * fraction


def load_adhan_profiles(profile_directory):
    profiles = {}
    try:
        filenames = os.listdir(profile_directory)
    except OSError:
        return profiles
    for filename in filenames:
        if not filename.endswith(".json"):
            continue
        profile = AdhanAudioProfile.from_file(os.path.join(profile_directory, filename))
        if profile is not None:
            profiles[os.path.splitext(filename)[0]] = profile
    return profiles
