# Bat Spectrum

Bat Spectrum is an experimental bioacoustic visualization project focused on transforming bat sounds and other animal vocalizations into measurable and generative visual systems.

The project combines audio analysis, spectrograms, acoustic feature extraction, Python, TouchDesigner and generative art.

## Goals

- Analyze bat audio recordings.
- Generate spectrograms and acoustic features.
- Detect pulses and call structures.
- Export CSV/JSON data for TouchDesigner.
- Create visual systems that are both aesthetic and measurable.

## First prototype

Audio → Spectrogram → Pulse detection → CSV export → Generative visualization

## Acoustic features

Initial features to extract:

- Peak frequency
- Energy
- Pulse duration
- Inter-pulse interval
- Frequency sweep
- Call density

## Visual mapping ideas

- Frequency controls height or color.
- Energy controls size or brightness.
- Pulse duration controls line length.
- Inter-pulse interval controls spacing.
- Frequency sweeps create curves or trajectories.

## Project structure

```text
bat-spectrum/
├── data/
│   ├── raw_audio/
│   ├── processed/
│   └── exports/
├── notebooks/
├── src/
├── touchdesigner/
├── visuals/
├── docs/
├── requirements.txt
└── README.md