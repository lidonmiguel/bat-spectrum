from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PULSES_CSV = PROJECT_ROOT / "data" / "exports" / "pulses_all.csv"
INPUT_SUMMARY_CSV = PROJECT_ROOT / "data" / "exports" / "pulses_summary.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "exports" / "touchdesigner_pulses.csv"


def normalize_column(series: pd.Series) -> pd.Series:
    min_value = series.min()
    max_value = series.max()

    if pd.isna(min_value) or pd.isna(max_value):
        return pd.Series(np.zeros(len(series)), index=series.index)

    if max_value == min_value:
        return pd.Series(np.zeros(len(series)), index=series.index)

    return (series - min_value) / (max_value - min_value)


def main() -> None:
    if not INPUT_PULSES_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_PULSES_CSV}")

    if not INPUT_SUMMARY_CSV.exists():
        raise FileNotFoundError(f"Summary CSV not found: {INPUT_SUMMARY_CSV}")

    pulses = pd.read_csv(INPUT_PULSES_CSV)
    summary = pd.read_csv(INPUT_SUMMARY_CSV)

    if pulses.empty:
        raise ValueError("Input pulses CSV is empty. No pulses detected.")

    # Keep only the duration information from the summary file.
    summary_small = summary[["filename", "duration_seconds"]].copy()
    summary_small = summary_small.rename(
        columns={"duration_seconds": "audio_duration_seconds"}
    )

    df = pulses.merge(summary_small, on="filename", how="left")

    # Stable order for files.
    filenames = sorted(df["filename"].unique())
    file_to_index = {filename: i for i, filename in enumerate(filenames)}

    df["global_pulse_id"] = np.arange(1, len(df) + 1)
    df["file_index"] = df["filename"].map(file_to_index)

    if len(filenames) > 1:
        df["file_index_norm"] = df["file_index"] / (len(filenames) - 1)
    else:
        df["file_index_norm"] = 0.0

    # Replace missing intervals.
    df["inter_pulse_interval"] = df["inter_pulse_interval"].fillna(0)

    # Normalized acoustic features.
    df["freq_norm"] = normalize_column(df["peak_frequency_hz"])
    df["duration_norm"] = normalize_column(df["duration"])
    df["energy_norm"] = normalize_column(df["mean_energy"])
    df["interval_norm"] = normalize_column(df["inter_pulse_interval"])

    # Time normalized inside each audio file.
    df["x_local"] = df["start_time"] / df["audio_duration_seconds"]
    df["x_local"] = df["x_local"].clip(0, 1)

    # Dataset-wide time normalization, useful for alternative layouts.
    df["x_dataset"] = normalize_column(df["start_time"])

    # TouchDesigner-ready spatial mapping.
    #
    # pos_x: horizontal position inside the audio duration.
    # pos_y: row per audio file.
    # pos_z: frequency height/depth.
    #
    # These are scaled values, not just 0-1 normalized values.
    x_spread = 10.0
    y_spacing = 0.6
    z_spread = 4.0

    df["pos_x"] = df["x_local"] * x_spread
    df["pos_y"] = df["file_index"] * y_spacing
    df["pos_z"] = df["freq_norm"] * z_spread

    # Visual attributes.
    df["size"] = 0.05 + df["duration_norm"] * 0.95
    df["brightness"] = 0.15 + df["energy_norm"] * 0.85
    df["line_length"] = 0.05 + df["duration_norm"] * 2.0

    # Optional color channels.
    # Simple frequency-based gradient:
    # low frequency = more red, high frequency = more blue.
    df["color_r"] = 1.0 - df["freq_norm"]
    df["color_g"] = df["energy_norm"]
    df["color_b"] = df["freq_norm"]

    output_columns = [
        "global_pulse_id",
        "filename",
        "file_index",
        "file_index_norm",
        "pulse_id",
        "start_time",
        "end_time",
        "audio_duration_seconds",
        "duration",
        "inter_pulse_interval",
        "peak_frequency_hz",
        "mean_energy",
        "max_energy",
        "freq_norm",
        "duration_norm",
        "energy_norm",
        "interval_norm",
        "x_local",
        "x_dataset",
        "pos_x",
        "pos_y",
        "pos_z",
        "size",
        "brightness",
        "line_length",
        "color_r",
        "color_g",
        "color_b",
    ]

    output_df = df[output_columns]

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(OUTPUT_CSV, index=False)

    print(f"TouchDesigner CSV saved to: {OUTPUT_CSV}")
    print("")
    print(f"Total visual points: {len(output_df)}")
    print(f"Audio files: {len(filenames)}")
    print("")
    print(output_df.head(20))


if __name__ == "__main__":
    main()