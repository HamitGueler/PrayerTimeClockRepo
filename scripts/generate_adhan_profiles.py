#!/usr/bin/env python3
import array
import json
import math
import os
import subprocess
import sys


INTERVAL_MS = 100
SAMPLE_RATE = 8000


def decode_mono_samples(path):
    result = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", path, "-ac", "1",
            "-ar", str(SAMPLE_RATE), "-f", "f32le", "pipe:1",
        ],
        check=True,
        capture_output=True,
    )
    samples = array.array("f")
    samples.frombytes(result.stdout)
    if sys.byteorder != "little":
        samples.byteswap()
    return samples


def create_profile(samples):
    frame_size = SAMPLE_RATE * INTERVAL_MS // 1000
    raw_values = []
    for start in range(0, len(samples), frame_size):
        frame = samples[start:start + frame_size]
        if not frame:
            break
        raw_values.append(math.sqrt(sum(value * value for value in frame) / len(frame)))
    audible = sorted(value for value in raw_values if value > 0.001)
    reference = audible[min(len(audible) - 1, round(len(audible) * 0.95))] if audible else 1.0
    normalized = [min(1.0, value / max(reference, 0.001)) ** 0.72 for value in raw_values]

    # A quick attack keeps syllables recognisable; the slower release prevents
    # flashing between neighbouring syllables and creates calm breathing motion.
    smoothed = []
    current = 0.0
    for target in normalized:
        factor = 0.48 if target > current else 0.18
        current += (target - current) * factor
        smoothed.append(round(current, 4))
    return smoothed


def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    audio_directory = os.path.join(project_root, "src", "AudioFiles")
    output_directory = os.path.join(project_root, "src", "AudioProfiles")
    os.makedirs(output_directory, exist_ok=True)
    for filename in ("adhan.mp3", "fajr_adhan.mp3"):
        source = os.path.join(audio_directory, filename)
        values = create_profile(decode_mono_samples(source))
        target = os.path.join(output_directory, f"{os.path.splitext(filename)[0]}.json")
        with open(target, "w", encoding="utf-8") as profile_file:
            json.dump({"intervalMs": INTERVAL_MS, "values": values}, profile_file, separators=(",", ":"))
            profile_file.write("\n")
        print(f"{filename}: {len(values)} values -> {target}")


if __name__ == "__main__":
    main()
