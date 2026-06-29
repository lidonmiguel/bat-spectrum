from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy import signal
from scipy.io import wavfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]

AUDIO_PATH = PROJECT_ROOT / "data" / "raw_audio" / "current_audio.wav"

OUTPUT_PULSES_CSV = PROJECT_ROOT / "data" / "exports" / "current_pulses.csv"
OUTPUT_EDGES_CSV = PROJECT_ROOT / "data" / "exports" / "current_edges.csv"
OUTPUT_METADATA_JSON = PROJECT_ROOT / "data" / "exports" / "current_metadata.json"


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


def detect_segments(active: np.ndarray, times: np.ndarray, min_duration: float):
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


def merge_close_segments(segments, times: np.ndarray, max_gap: float):
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


def normalize_column(series: pd.Series) -> pd.Series:
    min_value = series.min()
    max_value = series.max()

    if pd.isna(min_value) or pd.isna(max_value) or max_value == min_value:
        return pd.Series(np.zeros(len(series)), index=series.index)

    return (series - min_value) / (max_value - min_value)


def main() -> None:
    if not AUDIO_PATH.exists():
        raise FileNotFoundError(f"Audio not found: {AUDIO_PATH}")

    print(f"Analyzing: {AUDIO_PATH}")

    sr, audio_original = wavfile.read(AUDIO_PATH)
    audio = normalize_audio(audio_original)

    duration_seconds = len(audio) / sr
    nyquist_hz = sr / 2

    print(f"Sample rate: {sr} Hz")
    print(f"Duration: {duration_seconds:.3f} seconds")
    print(f"Nyquist: {nyquist_hz:.1f} Hz")

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

    # Detection band for Pipistrellus-like ultrasonic calls.
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

    segments = detect_segments(
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
            inter_pulse_interval = 0.0
            previous_pulse_id = 0
        else:
            inter_pulse_interval = start_time - previous_end_time
            previous_pulse_id = len(pulses)

        pulse_band = band_magnitude[:, start_index:end_index + 1]
        pulse_energy = energy_smooth[start_index:end_index + 1]

        max_frame_local = np.argmax(pulse_band)
        freq_index, _ = np.unravel_index(max_frame_local, pulse_band.shape)

        peak_frequency = float(band_frequencies[freq_index])
        mean_energy = float(pulse_energy.mean())
        max_energy = float(pulse_energy.max())

        pulses.append(
            {
                "pulse_id": len(pulses) + 1,
                "previous_pulse_id": previous_pulse_id,
                "start_time": start_time,
                "end_time": end_time,
                "birth_time": start_time,
                "death_time": duration_seconds,
                "duration": pulse_duration,
                "inter_pulse_interval": inter_pulse_interval,
                "peak_frequency_hz": peak_frequency,
                "mean_energy": mean_energy,
                "max_energy": max_energy,
            }
        )

        previous_end_time = end_time

    pulses_df = pd.DataFrame(pulses)

    if pulses_df.empty:
        raise ValueError("No pulses detected. Try lowering the threshold.")

    pulses_df["freq_norm"] = normalize_column(pulses_df["peak_frequency_hz"])
    pulses_df["duration_norm"] = normalize_column(pulses_df["duration"])
    pulses_df["energy_norm"] = normalize_column(pulses_df["mean_energy"])
    pulses_df["interval_norm"] = normalize_column(pulses_df["inter_pulse_interval"])

    # Visual mapping for one audio.
    # X = real time inside the audio
    # Y = frequency height
    # Z = energy / depth
    x_spread = 12.0
    y_spread = 5.0
    z_spread = 3.0

    pulses_df["x_local"] = pulses_df["start_time"] / duration_seconds
    pulses_df["pos_x"] = pulses_df["x_local"] * x_spread
    pulses_df["pos_y"] = pulses_df["freq_norm"] * y_spread
    pulses_df["pos_z"] = pulses_df["energy_norm"] * z_spread

    pulses_df["size"] = 0.08 + pulses_df["duration_norm"] * 0.35
    pulses_df["brightness"] = 0.2 + pulses_df["energy_norm"] * 0.8

    # Simple frequency-based color:
    # lower frequency = warmer, higher frequency = colder.
    pulses_df["color_r"] = 1.0 - pulses_df["freq_norm"]
    pulses_df["color_g"] = pulses_df["energy_norm"]
    pulses_df["color_b"] = pulses_df["freq_norm"]

    # Animation controls.
    pulses_df["visible"] = 1
    pulses_df["fade_in"] = 0.08
    pulses_df["fade_out"] = 0.25

    edge_rows = []

    for i in range(1, len(pulses_df)):
        previous_row = pulses_df.iloc[i - 1]
        current_row = pulses_df.iloc[i]

        edge_rows.append(
            {
                "edge_id": i,
                "from_pulse_id": int(previous_row["pulse_id"]),
                "to_pulse_id": int(current_row["pulse_id"]),
                "birth_time": float(current_row["birth_time"]),
                "from_x": float(previous_row["pos_x"]),
                "from_y": float(previous_row["pos_y"]),
                "from_z": float(previous_row["pos_z"]),
                "to_x": float(current_row["pos_x"]),
                "to_y": float(current_row["pos_y"]),
                "to_z": float(current_row["pos_z"]),
                "energy": float(current_row["energy_norm"]),
                "color_r": float(current_row["color_r"]),
                "color_g": float(current_row["color_g"]),
                "color_b": float(current_row["color_b"]),
            }
        )

    edges_df = pd.DataFrame(edge_rows)

    metadata = {
        "audio_path": str(AUDIO_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "sample_rate_hz": int(sr),
        "duration_seconds": float(duration_seconds),
        "nyquist_hz": float(nyquist_hz),
        "detected_pulses": int(len(pulses_df)),
        "detection_min_freq_hz": min_freq,
        "detection_max_freq_hz": max_freq,
        "detection_threshold": threshold,
        "purpose": "single_audio_realtime_animation",
    }

    OUTPUT_PULSES_CSV.parent.mkdir(parents=True, exist_ok=True)

    pulses_df.to_csv(OUTPUT_PULSES_CSV, index=False)
    edges_df.to_csv(OUTPUT_EDGES_CSV, index=False)

    with open(OUTPUT_METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("")
    print(f"Detected pulses: {len(pulses_df)}")
    print(f"Pulses CSV saved to: {OUTPUT_PULSES_CSV}")
    print(f"Edges CSV saved to: {OUTPUT_EDGES_CSV}")
    print(f"Metadata saved to: {OUTPUT_METADATA_JSON}")
    print("")
    print(pulses_df[["pulse_id", "start_time", "duration", "peak_frequency_hz", "pos_x", "pos_y", "pos_z"]].head(20))


if __name__ == "__main__":
    main()