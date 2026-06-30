# Bat Spectrum

**Bat Spectrum** is an audiovisual research project that transforms bat recordings into animated acoustic maps.

The project analyses a selected bat audio file, detects ultrasonic pulse events, extracts acoustic features, and converts them into a 3D visual system rendered in Blender.

The goal is not to create a literal scientific visualization only, but a hybrid between analysis, archive, and audiovisual interpretation.

```text
bat recording
↓
audio analysis
↓
pulse detection
↓
acoustic features
↓
3D node map
↓
animated Blender render
↓
archived visual result
```

## Current status

The project currently works with a **single active audio file** at a time.

The active working file is:

```text
data/raw_audio/current_audio.wav
```

This file is temporary and can be replaced whenever a new recording is being analysed.

Final source recordings are stored by species:

```text
data/raw_audio/pipistrellus_pipistrellus/
data/raw_audio/nyctalus_noctula/
data/raw_audio/myotis_daubentonii/
```

Final renders and their exported data are archived in:

```text
visuals/renders/<species>/<render_number>/
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

## Main workflow

### 1. Select an audio

Copy a source recording into the active working file:

```powershell
Copy-Item "data\raw_audio\pipistrellus_pipistrellus\pip_1.wav" "data\raw_audio\current_audio.wav" -Force
```

### 2. Analyse the audio

```powershell
python src\analyze_single_audio.py
```

This generates:

```text
data/exports/current_pulses.csv
data/exports/current_edges.csv
data/exports/current_metadata.json
```

### 3. Export the Blender scene data

```powershell
python src\export_blender_scene.py
```

This generates:

```text
data/exports/blender_scene.json
```

### 4. Create render-friendly audio

```powershell
python src\create_render_audio.py
```

This generates:

```text
data/processed/current_audio_render.wav
```

### 5. Optional: create a cleaned bat-focused audio

```powershell
python src\clean_current_audio.py
```

This generates:

```text
data/clean/clean_audio.wav
```

The original recording is never modified.

### 6. Render in Blender

Open:

```text
blender/bat_spectrum_template.blend
```

Run:

```text
blender/animate_bat_spectrum.py
```

Then render the animation as an MP4 using H.264 and AAC audio.

## Project structure

```text
bat-spectrum/
  blender/
    animate_bat_spectrum.py
    bat_spectrum_template.blend

  data/
    raw_audio/
      current_audio.wav
      pipistrellus_pipistrellus/
      nyctalus_noctula/
      myotis_daubentonii/

    exports/
      blender_scene.json
      current_edges.csv
      current_metadata.json
      current_pulses.csv

    processed/
      current_audio_render.wav
      bat_spectrum_render.mp4

    clean/
      clean_audio.wav

  docs/
    dataset_notes.md
    research_notes.md
    visual_system.md

  src/
    analyze_single_audio.py
    audio_analysis.py
    clean_current_audio.py
    create_render_audio.py
    export_blender_scene.py

  visuals/
    renders/
      pipistrellus_pipistrellus/
      nyctalus_noctula/
      myotis_daubentonii/
```

## Scripts

### `src/analyze_single_audio.py`

Analyses the current audio file and detects bat-like pulse events.

It exports pulse data, edge data, and metadata used by the rest of the pipeline.

### `src/export_blender_scene.py`

Converts the detected pulse data into a Blender-friendly JSON scene.

The visual position of each node is based on acoustic features such as frequency, energy, duration, and interval. Time is used for animation, not for spatial placement.

### `src/create_render_audio.py`

Converts the current audio into a render-friendly 48 kHz WAV file for Blender and video export.

### `src/clean_current_audio.py`

Creates a bat-focused cleaned version of the current audio.

It combines frequency filtering with pulse-based masking, using the detected pulse regions to reduce non-bat noise.

### `src/audio_analysis.py`

Exploratory helper script for inspecting audio, spectrograms, and acoustic behaviour.

## Data philosophy

The project separates four types of data:

1. **Source audio**
   Original recordings stored by species.

2. **Current working audio**
   Temporary file used by the pipeline.

3. **Generated exports**
   CSV and JSON files created from the current audio.

4. **Archived renders**
   Final visual results stored with the exact data used to create them.

The original source audio is never overwritten by the analysis, cleaning, or rendering scripts.

## Notes on species and detection

The project uses species folders such as:

```text
pipistrellus_pipistrellus
nyctalus_noctula
myotis_daubentonii
```

Detection settings may need to change depending on the species, the recording device, and the amount of noise in the file.

Noisy recordings are not automatically treated as valid bat material. If a recording appears to contain camera handling, movement, human noise, or uncertain events, it can be discarded instead of archived as a final render.

## Blender

Blender is used as the final visual rendering environment.

The generated `.blend` file is not committed to the repository. The reusable template is:

```text
blender/bat_spectrum_template.blend
```

The generated file:

```text
blender/bat_spectrum_generated.blend
```

is ignored because it is recreated by the script.

## License and sources

Audio files should only be added when their source and license are clear.

When using public datasets or external recordings, the source, species name, and license should be documented before archiving the render.
