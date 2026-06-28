from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal
from scipy.io import wavfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]

AUDIO_PATH = PROJECT_ROOT / "data" / "raw_audio" / "test.wav"
OUTPUT_CSV = PROJECT_ROOT / "data" / "exports" / "test_pulses.csv"
OUTPUT_IMAGE = PROJECT_ROOT / "data" / "processed" / "test_pulses.png"


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    audio = audio.astype(np.float32)

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    max_value = np.max(np.abs(audio))

    if max_value > 0:
        audio = audio / max_value

    return audio


def smooth_curve(values: np.ndarray, window_size: int = 9) -> np.ndarray:
    if window_size < 2:
        return values

    window = np.ones(window_size) / window_size
    return np.convolve(values, window, mode="same")


def detect_active_segments(
    active: np.ndarray,
    times: np.ndarray,
    min_duration: float,
) -> list[tuple[int, int]]:
    segments = []
    in_segment = False
    start_index = 0

    for i, is_active in enumerate(active):
        if is_active and not in_segment:
            in_segment = True
            start_index = i

        if in_segment and (not is_active or i == len(active) - 1):
            end_index = i

            start_time = times[start_index]
            end_time = times[end_index]
            duration = end_time - start_time

            if duration >= min_duration:
                segments.append((start_index, end_index))

            in_segment = False

    return segments


def merge_close_segments(
    segments: list[tuple[int, int]],
    times: np.ndarray,
    max_gap: float,
) -> list[tuple[int, int]]:
    if not segments:
        return []

    merged = [segments[0]]

    for start_index, end_index in segments[1:]:
        previous_start, previous_end = merged[-1]

        gap = times[start_index] - times[previous_end]

        if gap <= max_gap:
            merged[-1] = (previous_start, end_index)
        else:
            merged.append((start_index, end_index))

    return merged


def detect_pulses(audio_path: Path) -> None:
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    print(f"Loading audio: {audio_path}")

    sr, audio = wavfile.read(audio_path)
    audio = normalize_audio(audio)

    print(f"Sample rate: {sr} Hz")
    print(f"Duration: {len(audio) / sr:.3f} seconds")

    nperseg = 2048
    noverlap = 1536

    frequencies, times, stft = signal.stft(
        audio,
        fs=sr,
        nperseg=nperseg,
        noverlap=noverlap,
        boundary=None,
    )

    magnitude = np.abs(stft)

    # Frequency band used for pulse detection.
    min_freq = 10000
    max_freq = 60000

    freq_mask = (frequencies >= min_freq) & (frequencies <= max_freq)
    band_magnitude = magnitude[freq_mask, :]
    band_frequencies = frequencies[freq_mask]

    energy = band_magnitude.sum(axis=0)

    if energy.max() > 0:
        energy_norm = energy / energy.max()
    else:
        energy_norm = energy

    energy_smooth = smooth_curve(energy_norm, window_size=11)

    # Detection parameters.
    threshold = 0.45
    min_pulse_duration = 0.015
    max_gap_between_parts = 0.020

    active = energy_smooth > threshold

    segments = detect_active_segments(
        active=active,
        times=times,
        min_duration=min_pulse_duration,
    )

    segments = merge_close_segments(
        segments=segments,
        times=times,
        max_gap=max_gap_between_parts,
    )

    pulses = []

    for start_index, end_index in segments:
        start_time = times[start_index]
        end_time = times[end_index]
        duration = end_time - start_time

        pulse_band = band_magnitude[:, start_index:end_index + 1]
        pulse_energy = energy_smooth[start_index:end_index + 1]

        max_frame_local = np.argmax(pulse_band)
        freq_index, time_index = np.unravel_index(
            max_frame_local,
            pulse_band.shape,
        )

        peak_frequency = band_frequencies[freq_index]

        pulses.append(
            {
                "pulse_id": len(pulses) + 1,
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "peak_frequency_hz": peak_frequency,
                "max_energy": pulse_energy.max(),
                "mean_energy": pulse_energy.mean(),
            }
        )

    pulses_df = pd.DataFrame(pulses)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_IMAGE.parent.mkdir(parents=True, exist_ok=True)

    pulses_df.to_csv(OUTPUT_CSV, index=False)

    plt.figure(figsize=(14, 4))
    plt.plot(times, energy_norm, alpha=0.35, label="Raw energy")
    plt.plot(times, energy_smooth, label="Smoothed energy")
    plt.axhline(threshold, linestyle="--", label="Threshold")
    plt.xlabel("Time (s)")
    plt.ylabel("Normalized energy")
    plt.title("Pulse Detection - Bat Spectrum")
    plt.legend()

    for pulse in pulses:
        plt.axvspan(
            pulse["start_time"],
            pulse["end_time"],
            alpha=0.3,
        )

    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=150)
    plt.close()

    print(f"Detected pulses: {len(pulses_df)}")
    print(f"Pulse CSV saved to: {OUTPUT_CSV}")
    print(f"Pulse plot saved to: {OUTPUT_IMAGE}")


if __name__ == "__main__":
    detect_pulses(AUDIO_PATH)