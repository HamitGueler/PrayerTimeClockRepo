import json
import tempfile
import unittest
from pathlib import Path

from HelperClasses.AdhanAudioProfile import AdhanAudioProfile, load_adhan_profiles


class AdhanAudioProfileTests(unittest.TestCase):
    def test_profile_interpolates_between_preanalysed_values(self):
        profile = AdhanAudioProfile(100, [0.0, 0.4, 1.0])

        self.assertEqual(profile.value_at(0), 0.0)
        self.assertEqual(profile.value_at(50), 0.2)
        self.assertEqual(profile.value_at(150), 0.7)
        self.assertEqual(profile.value_at(500), 1.0)

    def test_profiles_are_loaded_by_audio_basename(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "adhan.json").write_text(
                json.dumps({"intervalMs": 100, "values": [0.1, 0.5]}),
                encoding="utf-8",
            )

            profiles = load_adhan_profiles(path)

            self.assertEqual(profiles["adhan"].value_at(100), 0.5)

    def test_invalid_profile_falls_back_without_reactivity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "adhan.json").write_text("invalid", encoding="utf-8")

            self.assertEqual(load_adhan_profiles(path), {})


if __name__ == "__main__":
    unittest.main()
