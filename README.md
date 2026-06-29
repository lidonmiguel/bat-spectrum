# Bat Spectrum

**Bat Spectrum** is an audiovisual project that transforms bat recordings into animated acoustic maps.

The current pipeline analyzes one selected audio file, detects bat sound events, converts those events into nodes and connections, and renders an animated 3D map in Blender. The original field recording is preserved as the audio source, while the visualization reveals the detected bat activity over time.

## Concept

The project is based on a simple idea:

```text
audio recording
↓
bat sound event detection
↓
acoustic features
↓
3D sound map
↓
animated nodes and connections
↓
Blender render with original audio
```

The visualization is not intended to be a traditional graph. It is a spatial map of sound events. Each node represents a detected bat pulse or call event. The position of the node is based on acoustic characteristics such as frequency, duration, energy and interval between events. Time controls when each node appears.

This means:

```text
node position = acoustic similarity / sound characteristics
node birth = real time in the audio
edges = temporal connections between consecutive events
```

## Current workflow

The final workflow works with one active audio file:

```text
data/raw_audio/current_audio.wav
```

To generate a new visualization, copy the desired `.wav` file into this location and run the analysis pipeline.

Example:

```powershell
Copy-Item "data\raw_audio\pipistrellus_pipistrellus\pip_016.wav" "data\raw_audio\current_audio.wav"
```

Then run:

```powershell
python src/analyze_single_audio.py
python src/export_blender_scene.py
```

If Blender has trouble playing the original high-sample-rate audio correctly, create a render-friendly 48 kHz copy:

```powershell
python src/create_render_audio.py
```

This does not sonify or invent a new sound. It only converts the original recording into a more standard audio format for video rendering.

## Blender rendering

The Blender part of the project is stored in:

```text
blender/
```

Main files:

```text
blender/animate_bat_spectrum.py
blender/bat_spectrum_template.blend
```

The script reads:

```text
data/exports/blender_scene.json
```

and creates the animated node map in Blender.

Typical Blender workflow:

1. Open `blender/bat_spectrum_template.blend`.
2. Open the Scripting workspace.
3. Run `blender/animate_bat_spectrum.py`.
4. Add the audio strip in the Video Sequencer if needed.
5. Render the animation as an MP4 video.

Recommended render settings:

```text
Resolution: 1280 x 720
Frame rate: 30 fps
Frame range: 1–409, or as defined by the current audio duration
Container: MPEG-4
Video Codec: H.264
Audio Codec: AAC
Sample Rate: 48000
```

Final renders should be saved by species and audio ID, for example:

```text
visuals/renders/pipistrellus_pipistrellus/pip_016/
```

## Project structure

```text
bat-spectrum/
├── blender/
│   ├── animate_bat_spectrum.py
│   └── bat_spectrum_template.blend
├── data/
│   ├── exports/
│   ├── processed/
│   └── raw_audio/
│       └── pipistrellus_pipistrellus/
├── docs/
├── src/
│   ├── analyze_single_audio.py
│   ├── audio_analysis.py
│   ├── create_render_audio.py
│   └── export_blender_scene.py
├── visuals/
│   └── renders/
├── README.md
├── requirements.txt
└── .gitignore
```

## Main scripts

### `src/analyze_single_audio.py`

Analyzes:

```text
data/raw_audio/current_audio.wav
```

and exports:

```text
data/exports/current_pulses.csv
data/exports/current_edges.csv
data/exports/current_metadata.json
```

These files contain the detected bat events, their acoustic properties, visual parameters and temporal connections.

### `src/export_blender_scene.py`

Converts the analysis outputs into:

```text
data/exports/blender_scene.json
```

This JSON file is the bridge between Python and Blender.

It contains:

```text
audio path
animation duration
nodes
edges
positions
colors
sizes
birth times
```

### `src/create_render_audio.py`

Creates a 48 kHz version of the current audio for Blender/video rendering:

```text
data/processed/current_audio_render.wav
```

This is useful when the original recorder file uses a high or unusual sample rate.

### `src/audio_analysis.py`

Utility script for generating additional study material from a single audio file, such as spectrograms and acoustic summaries.

## Data philosophy

The repository uses `current_audio.wav` as a working file. This makes the pipeline simple and repeatable.

For each final render, the outputs should be archived separately by species and audio ID:

```text
data/exports/<species>/<audio_id>/
visuals/renders/<species>/<audio_id>/
```

Example:

```text
data/exports/pipistrellus_pipistrellus/pip_016/
visuals/renders/pipistrellus_pipistrellus/pip_016/
```

This keeps the active pipeline clean while preserving final results.

## Installation

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Blender is required for the final visualization and rendering stage.

## Notes

The project originally explored TouchDesigner as a prototyping environment. The current final pipeline is based on Python and Blender.

TouchDesigner files and scripts are no longer part of the main workflow.
