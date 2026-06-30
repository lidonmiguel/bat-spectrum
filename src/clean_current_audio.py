from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal
from scipy.io import wavfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_WAV = PROJECT_ROOT / "data" / "raw_audio" / "current_audio.wav"
PULSES_CSV = PROJECT_ROOT / "data" / "exports" / "current_pulses.csv"

OUTPUT_DIR = PROJECT_ROOT / "data" / "clean"
OUTPUT_WAV = OUTPUT_DIR / "clean_audio.wav"


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    audio = audio.astype(np.float32)

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    max_value = np.max(np.abs(audio))

    if max_value > 0:
        audio = audio / max_value

    return audio


def bandpass_bat_audio(audio: np.ndarray, sr: int) -> np.ndarray:
    nyquist = sr / 2

    # General bat-focused range.
    # This removes most human movement, camera handling, wind and low noise.
    low_freq = 18000
    high_freq = min(100000, nyquist * 0.95)

    if high_freq <= low_freq:
        print("Sample rate too low for ultrasonic bandpass. Using high-pass only.")
        sos = signal.butter(
            4,
            low_freq / nyquist,
            btype="highpass",
            output="sos",
        )
    else:
        sos = signal.butter(
            4,
            [low_freq / nyquist, high_freq / nyquist],
            btype="bandpass",
            output="sos",
        )

    return signal.sosfiltfilt(sos, audio)


def build_pulse_mask(audio_length: int, sr: int) -> np.ndarray:
    if not PULSES_CSV.exists():
        print("No current_pulses.csv found. Cleaning only by frequency.")
        return np.ones(audio_length, dtype=np.float32)

    pulses = pd.read_csv(PULSES_CSV)

    if pulses.empty:
        print("current_pulses.csv is empty. Cleaning only by frequency.")
        return np.ones(audio_length, dtype=np.float32)

    mask = np.zeros(audio_length, dtype=np.float32)

    padding_before = 0.020
    padding_after = 0.050
    fade_duration = 0.010

    fade_samples = max(1, int(fade_duration * sr))

    for _, row in pulses.iterrows():
        start_time = float(row["start_time"]) - padding_before
        end_time = float(row["end_time"]) + padding_after

        start_index = max(0, int(start_time * sr))
        end_index = min(audio_length, int(end_time * sr))

        if end_index <= start_index:
            continue

        local_mask = np.ones(end_index - start_index, dtype=np.float32)

        fade_len = min(fade_samples, len(local_mask) // 2)

        if fade_len > 0:
            fade_in = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
            fade_out = np.linspace(1.0, 0.0, fade_len, dtype=np.float32)

            local_mask[:fade_len] = fade_in
            local_mask[-fade_len:] = fade_out

        mask[start_index:end_index] = np.maximum(
            mask[start_index:end_index],
            local_mask,
        )

    return mask


def save_wav(path: Path, sr: int, audio: np.ndarray) -> None:
    max_value = np.max(np.abs(audio))

    if max_value > 0:
        audio = audio / max_value

    audio_int16 = (audio * 32767).astype(np.int16)

    path.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(path, sr, audio_int16)


def main() -> None:
    if not INPUT_WAV.exists():
        raise FileNotFoundError(f"Missing input audio: {INPUT_WAV}")

    print(f"Cleaning audio: {INPUT_WAV}")

    sr, audio_original = wavfile.read(INPUT_WAV)
    audio = normalize_audio(audio_original)

    print(f"Sample rate: {sr} Hz")
    print(f"Duration: {len(audio) / sr:.3f} seconds")

    filtered_audio = bandpass_bat_audio(audio, sr)
    pulse_mask = build_pulse_mask(len(filtered_audio), sr)

    cleaned_audio = filtered_audio * pulse_mask

    save_wav(OUTPUT_WAV, sr, cleaned_audio)

    print("")
    print(f"Clean audio saved to: {OUTPUT_WAV}")
    print("This file keeps the original sample rate.")
    print("Original audio was not modified.")


if __name__ == "__main__":
    main()