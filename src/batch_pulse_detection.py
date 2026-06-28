from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal
from scipy.io import wavfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FOLDER = PROJECT_ROOT / "data" / "raw_audio" / "pipistrellus_pipistrellus"

OUTPUT_CSV_FOLDER = PROJECT_ROOT / "data" / "exports" / "pulses"
OUTPUT_IMAGE_FOLDER = PROJECT_ROOT / "data" / "processed" / "pulses"

SUMMARY_CSV = PROJECT_ROOT / "data" / "exports" / "pulses_summary.csv"
ALL_PULSES_CSV = PROJECT_ROOT / "data" / "exports" / "pulses_all.csv"


PULSE_COLUMNS = [
    "filename",
    "pulse_id",
    "start_time",
    "end_time",
    "duration",
    "inter_pulse_interval",
    "peak_frequency_hz",
    "max_energy",
    "mean_energy",
]


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    audio = audio.astype(np.float32)

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    max_value = np.max(np.abs(audio))

    if max_value > 0:
        audio = audio / max_value

    return audio


def smooth_curve(values: np.ndarray, window_size: int = 5) -> np.ndarray:
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


def safe_mean(values: pd.Series) -> float:
    if len(values) == 0:
        return np.nan
    return float(values.mean())


def safe_median(values: pd.Series) -> float:
    if len(values) == 0:
        return np.nan
    return float(values.median())


def analyze_file(audio_path: Path) -> tuple[dict, pd.DataFrame]:
    print(f"Analyzing: {audio_path.name}")

    sr, audio_original = wavfile.read(audio_path)

    if audio_original.ndim == 1:
        channels = 1
    else:
        channels = audio_original.shape[1]

    dtype = str(audio_original.dtype)
    num_samples = audio_original.shape[0]
    duration_seconds = num_samples / sr
    nyquist_hz = sr / 2

    audio = normalize_audio(audio_original)

    peak_amplitude = float(np.max(np.abs(audio)))
    rms_amplitude = float(np.sqrt(np.mean(audio**2)))

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

    # Detection band for this first exploratory version.
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

    energy_smooth = smooth_curve(energy_norm, window_size=5)

    # Exploratory detection parameters.
    threshold = 0.28
    min_pulse_duration = 0.003
    max_gap_between_parts = 0.010

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
    previous_end_time = None

    for start_index, end_index in segments:
        start_time = float(times[start_index])
        end_time = float(times[end_index])
        pulse_duration = end_time - start_time

        if previous_end_time is None:
            inter_pulse_interval = np.nan
        else:
            inter_pulse_interval = start_time - previous_end_time

        pulse_band = band_magnitude[:, start_index:end_index + 1]
        pulse_energy = energy_smooth[start_index:end_index + 1]

        max_frame_local = np.argmax(pulse_band)
        freq_index, _ = np.unravel_index(
            max_frame_local,
            pulse_band.shape,
        )

        peak_frequency = float(band_frequencies[freq_index])

        pulses.append(
            {
                "filename": audio_path.name,
                "pulse_id": len(pulses) + 1,
                "start_time": start_time,
                "end_time": end_time,
                "duration": pulse_duration,
                "inter_pulse_interval": inter_pulse_interval,
                "peak_frequency_hz": peak_frequency,
                "max_energy": float(pulse_energy.max()),
                "mean_energy": float(pulse_energy.mean()),
            }
        )

        previous_end_time = end_time

    pulses_df = pd.DataFrame(pulses, columns=PULSE_COLUMNS)

    OUTPUT_CSV_FOLDER.mkdir(parents=True, exist_ok=True)
    OUTPUT_IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)

    output_csv = OUTPUT_CSV_FOLDER / f"{audio_path.stem}_pulses.csv"
    output_image = OUTPUT_IMAGE_FOLDER / f"{audio_path.stem}_pulses.png"

    pulses_df.to_csv(output_csv, index=False)

    total_active_time = float(pulses_df["duration"].sum()) if len(pulses_df) else 0.0
    activity_ratio = total_active_time / duration_seconds if duration_seconds > 0 else np.nan
    pulse_rate_per_second = len(pulses_df) / duration_seconds if duration_seconds > 0 else np.nan

    summary = {
        "filename": audio_path.name,
        "sample_rate_hz": sr,
        "nyquist_hz": nyquist_hz,
        "duration_seconds": duration_seconds,
        "channels": channels,
        "dtype": dtype,
        "num_samples": num_samples,
        "detected_pulses": len(pulses_df),
        "pulse_rate_per_second": pulse_rate_per_second,
        "mean_pulse_duration": safe_mean(pulses_df["duration"]),
        "median_pulse_duration": safe_median(pulses_df["duration"]),
        "total_active_time": total_active_time,
        "activity_ratio": activity_ratio,
        "mean_inter_pulse_interval": safe_mean(
            pulses_df["inter_pulse_interval"].dropna()
        ),
        "mean_peak_frequency_hz": safe_mean(pulses_df["peak_frequency_hz"]),
        "min_peak_frequency_hz": float(pulses_df["peak_frequency_hz"].min())
        if len(pulses_df)
        else np.nan,
        "max_peak_frequency_hz": float(pulses_df["peak_frequency_hz"].max())
        if len(pulses_df)
        else np.nan,
        "rms_amplitude": rms_amplitude,
        "peak_amplitude": peak_amplitude,
        "detection_min_freq_hz": min_freq,
        "detection_max_freq_hz": max_freq,
        "detection_threshold": threshold,
        "output_csv": str(output_csv),
        "output_image": str(output_image),
    }

    plt.figure(figsize=(14, 4))
    plt.plot(times, energy_norm, alpha=0.35, label="Raw energy")
    plt.plot(times, energy_smooth, label="Smoothed energy")
    plt.axhline(threshold, linestyle="--", label="Threshold")
    plt.xlabel("Time (s)")
    plt.ylabel("Normalized energy")
    plt.title(f"Pulse Detection - {audio_path.name}")
    plt.legend()

    for _, pulse in pulses_df.iterrows():
        plt.axvspan(
            pulse["start_time"],
            pulse["end_time"],
            alpha=0.3,
        )

    plt.tight_layout()
    plt.savefig(output_image, dpi=150)
    plt.close()

    return summary, pulses_df


def main() -> None:
    wav_files = sorted(INPUT_FOLDER.glob("*.wav"))

    if not wav_files:
        raise FileNotFoundError(f"No WAV files found in: {INPUT_FOLDER}")

    summaries = []
    all_pulses = []

    for audio_path in wav_files:
        summary, pulses_df = analyze_file(audio_path)
        summaries.append(summary)

        if len(pulses_df):
            all_pulses.append(pulses_df)

    summary_df = pd.DataFrame(summaries)

    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(SUMMARY_CSV, index=False)

    if all_pulses:
        all_pulses_df = pd.concat(all_pulses, ignore_index=True)
    else:
        all_pulses_df = pd.DataFrame(columns=PULSE_COLUMNS)

    all_pulses_df.to_csv(ALL_PULSES_CSV, index=False)

    print("")
    print("Batch analysis complete.")
    print(
        summary_df[
            [
                "filename",
                "duration_seconds",
                "detected_pulses",
                "pulse_rate_per_second",
                "mean_pulse_duration",
                "mean_peak_frequency_hz",
                "activity_ratio",
            ]
        ]
    )
    print("")
    print(f"Summary CSV saved to: {SUMMARY_CSV}")
    print(f"All pulses CSV saved to: {ALL_PULSES_CSV}")


if __name__ == "__main__":
    main()