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

    OUTPUT_IMAGE.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(14, 8))

    scatter = plt.scatter(
        df["pos_x"],
        df["pos_y"] + df["pos_z"] * 0.15,
        s=df["size"] * 250,
        c=df["brightness"],
        alpha=0.75,
    )

    plt.colorbar(scatter, label="Brightness / energy")
    plt.xlabel("pos_x — normalized time inside audio")
    plt.ylabel("pos_y + frequency offset")
    plt.title("Bat Spectrum — TouchDesigner Layout Preview")

    filenames = (
        df[["filename", "file_index", "pos_y"]]
        .drop_duplicates()
        .sort_values("file_index")
    )

    plt.yticks(
        filenames["pos_y"],
        filenames["filename"],
    )

    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=150)
    plt.close()

    print(f"Preview image saved to: {OUTPUT_IMAGE}")
    print(f"Total points visualized: {len(df)}")
    print(f"Audio files: {df['filename'].nunique()}")


if __name__ == "__main__":
    main()