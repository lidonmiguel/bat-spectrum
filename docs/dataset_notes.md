# Dataset Notes

This document describes how audio files, generated data, cleaned files, and final renders are organised in Bat Spectrum.

## Main principle

The project works with one active audio file at a time:

```text
data/raw_audio/current_audio.wav
```

This file is temporary. It is replaced whenever a new recording is being analysed.

The original source recordings are stored separately by species and should not be modified by the pipeline.

## Source audio

Source recordings are stored in:

```text
data/raw_audio/<species>/
```

Examples:

```text
data/raw_audio/pipistrellus_pipistrellus/
data/raw_audio/nyctalus_noctula/
data/raw_audio/myotis_daubentonii/
```

Example file names:

```text
pip_1.wav
pip_2.wav
noc_1.wav
myd_1.wav
```

The exact naming can evolve, but each file should make clear which species or group it belongs to.

## Current audio

The active working file is:

```text
data/raw_audio/current_audio.wav
```

This file is ignored by Git because it is only used as temporary input.

Typical workflow:

```powershell
Copy-Item "data\raw_audio\pipistrellus_pipistrellus\pip_1.wav" "data\raw_audio\current_audio.wav" -Force
```

Then run the analysis scripts.

## Generated exports

The analysis creates files in:

```text
data/exports/
```

Current generated files:

```text
current_pulses.csv
current_edges.csv
current_metadata.json
blender_scene.json
```

These files describe the active audio only.

They are temporary during analysis, but copies of them are archived together with final renders.

## Cleaned audio

Cleaned audio is generated in:

```text
data/clean/
```

Main output:

```text
data/clean/clean_audio.wav
```

This file is a derived version of the active audio. It is created to reduce non-bat noise and focus on detected pulse regions.

The cleaned audio should not replace the original recording.

## Processed render audio

Render-friendly audio is generated in:

```text
data/processed/current_audio_render.wav
```

This version is converted to a standard sample rate for Blender and video export.

It is a working file and should not be treated as the source recording.

## Final renders

Final outputs are archived in:

```text
visuals/renders/<species>/<number>/
```

Example:

```text
visuals/renders/pipistrellus_pipistrellus/01/
  blender_scene.json
  current_edges.csv
  current_metadata.json
  current_pulses.csv
  render.mp4
```

The render folder stores the exact data used to create the video.

This makes each render reproducible and reviewable.

## Quality notes

Not every audio file should become a final render.

Recordings can be discarded if they contain:

```text
- camera movement
- handling noise
- human movement
- unclear low-frequency events
- too few valid bat pulses
- too much noise for confident interpretation
```

The project favours fewer reliable renders over many uncertain ones.

## Personal path policy

Files committed to the repository should not contain local machine paths such as:

```text
C:\Users\...
```

JSON exports and scripts should use relative paths whenever possible.
