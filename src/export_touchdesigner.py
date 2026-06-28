from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_CSV = PROJECT_ROOT / "data" / "exports" / "pulses_all.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "exports" / "touchdesigner_pulses.csv"


def normalize_column(series: pd.Series) -> pd.Series:
    min_value = series.min()
    max_value = series.max()

    if pd.isna(min_value) or pd.isna(max_value):
        return series

    if max_value == min_value:
        return pd.Series(np.zeros(len(series)), index=series.index)

    return (series - min_value) / (max_value - min_value)


def main() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)

    if df.empty:
        raise ValueError("Input CSV is empty. No pulses detected.")

    df["inter_pulse_interval"] = df["inter_pulse_interval"].fillna(0)

    df["freq_norm"] = normalize_column(df["peak_frequency_hz"])
    df["duration_norm"] = normalize_column(df["duration"])
    df["energy_norm"] = normalize_column(df["mean_energy"])
    df["interval_norm"] = normalize_column(df["inter_pulse_interval"])

    # Basic visual mapping for TouchDesigner.
    df["x"] = normalize_column(df["start_time"])
    df["y"] = df["freq_norm"]
    df["size"] = 0.05 + df["duration_norm"] * 0.95
    df["brightness"] = 0.15 + df["energy_norm"] * 0.85

    output_columns = [
        "filename",
        "pulse_id",
        "start_time",
        "end_time",
        "duration",
        "inter_pulse_interval",
        "peak_frequency_hz",
        "mean_energy",
        "max_energy",
        "freq_norm",
        "duration_norm",
        "energy_norm",
        "interval_norm",
        "x",
        "y",
        "size",
        "brightness",
    ]

    output_df = df[output_columns]

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(OUTPUT_CSV, index=False)

    print(f"TouchDesigner CSV saved to: {OUTPUT_CSV}")
    print("")
    print(output_df.head(20))


if __name__ == "__main__":
    main()