from pathlib import Path
from math import gcd

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_WAV = PROJECT_ROOT / "data" / "raw_audio" / "current_audio.wav"
OUTPUT_WAV = PROJECT_ROOT / "data" / "processed" / "current_audio_render.wav"

OUT_SR = 48000


def main() -> None:
    sr, audio = wavfile.read(INPUT_WAV)

    print(f"Input sample rate: {sr}")
    print(f"Input shape: {audio.shape}")

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0
    else:
        audio = audio.astype(np.float32)

    common = gcd(sr, OUT_SR)
    up = OUT_SR // common
    down = sr // common

    audio_out = resample_poly(audio, up, down)

    max_value = np.max(np.abs(audio_out))
    if max_value > 0:
        audio_out = audio_out / max_value * 0.85

    audio_int16 = (audio_out * 32767).astype(np.int16)

    OUTPUT_WAV.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(OUTPUT_WAV, OUT_SR, audio_int16)

    duration = len(audio_int16) / OUT_SR

    print(f"Saved render audio to: {OUTPUT_WAV}")
    print(f"Output sample rate: {OUT_SR}")
    print(f"Duration: {duration:.3f} seconds")


if __name__ == "__main__":
    main()