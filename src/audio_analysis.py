from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy import signal


PROJECT_ROOT = Path(__file__).resolve().parents[1]

AUDIO_PATH = PROJECT_ROOT / "data" / "raw_audio" / "test.wav"
OUTPUT_IMAGE = PROJECT_ROOT / "data" / "processed" / "test_spectrogram.png"
OUTPUT_CSV = PROJECT_ROOT / "data" / "exports" / "test_features.csv"


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    audio = audio.astype(np.float32)

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    max_value = np.max(np.abs(audio))

    if max_value > 0:
        audio = audio / max_value

    return audio


def analyze_audio(audio_path: Path) -> None:
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    print(f"Loading audio: {audio_path}")

    sr, audio = wavfile.read(audio_path)
    audio = normalize_audio(audio)

    duration = len(audio) / sr

    print(f"Sample rate: {sr} Hz")
    print(f"Duration: {duration:.3f} seconds")

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
    magnitude_db = 20 * np.log10(magnitude / np.max(magnitude) + 1e-12)

    peak_frequency = []
    energy = []

    for frame in magnitude.T:
        peak_index = np.argmax(frame)
        peak_frequency.append(frequencies[peak_index])
        energy.append(np.sum(frame))

    features = pd.DataFrame(
        {
            "time_seconds": times,
            "peak_frequency_hz": peak_frequency,
            "energy": energy,
        }
    )

    OUTPUT_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    features.to_csv(OUTPUT_CSV, index=False)

    plt.figure(figsize=(14, 6))
    plt.pcolormesh(
        times,
        frequencies,
        magnitude_db,
        shading="gouraud",
        vmin=-90,
        vmax=0,
    )
    plt.colorbar(label="Amplitude (dB)")
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.title("Spectrogram - Bat Spectrum")
    plt.ylim(0, 80000)
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=150)
    plt.close()

    print(f"Spectrogram saved to: {OUTPUT_IMAGE}")
    print(f"CSV saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    analyze_audio(AUDIO_PATH)