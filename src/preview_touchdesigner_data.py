from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_CSV = PROJECT_ROOT / "data" / "exports" / "touchdesigner_pulses.csv"
OUTPUT_IMAGE = PROJECT_ROOT / "data" / "processed" / "touchdesigner_preview.png"


def main() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)

    if df.empty:
        raise ValueError("Input CSV is empty.")

    filenames = sorted(df["filename"].unique())
    file_to_index = {filename: i for i, filename in enumerate(filenames)}

    df["file_index"] = df["filename"].map(file_to_index)

    # Visual mapping:
    # x = pulse time inside each audio
    # y = audio row + frequency offset
    # size = pulse duration
    # brightness = pulse energy
    df["preview_x"] = df["start_time"]
    df["preview_y"] = df["file_index"] + df["freq_norm"] * 0.8
    df["preview_size"] = 20 + df["size"] * 200

    OUTPUT_IMAGE.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(14, 8))

    scatter = plt.scatter(
        df["preview_x"],
        df["preview_y"],
        s=df["preview_size"],
        c=df["brightness"],
        alpha=0.75,
    )

    plt.colorbar(scatter, label="Brightness / energy")
    plt.xlabel("Time inside audio (s)")
    plt.ylabel("Audio file + frequency")
    plt.title("Bat Spectrum — TouchDesigner Data Preview")

    y_ticks = list(file_to_index.values())
    y_labels = list(file_to_index.keys())

    plt.yticks(y_ticks, y_labels)
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=150)
    plt.close()

    print(f"Preview image saved to: {OUTPUT_IMAGE}")
    print(f"Total pulses visualized: {len(df)}")
    print(f"Audio files: {len(filenames)}")


if __name__ == "__main__":
    main()