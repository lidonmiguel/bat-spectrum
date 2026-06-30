# Visual System

This document describes how Bat Spectrum converts bat audio analysis into a 3D animated visual system.

## Concept

Each detected bat pulse becomes a visual node.

Connections are created between consecutive pulses.

The result is an acoustic constellation: a spatial map built from frequency, energy, duration, and timing.

```text
pulse
↓
features
↓
node
↓
animation
↓
render
```

## Nodes

Each node represents one detected pulse.

Main acoustic features used:

```text
peak frequency
duration
energy
inter-pulse interval
birth time
```

These values are normalised and exported from:

```text
data/exports/current_pulses.csv
```

## Position

The current visual system does not place nodes directly on a timeline.

Instead, spatial position is based on acoustic behaviour.

Time controls animation, not location.

The node position is built from:

```text
frequency
duration
energy
inter-pulse interval
small deterministic jitter
```

This makes the render feel more like an acoustic map than a simple waveform.

## Time

Each node has a `birth_time`.

This controls when the node appears in the animation.

The audio timeline and the visual animation remain synchronised, but the visual space itself is not a left-to-right timeline.

## Edges

Edges connect consecutive detected pulses.

They are exported from:

```text
data/exports/current_edges.csv
```

Each edge appears when the target pulse is born.

This creates a growing structure over time.

## Colour

Colour is based mainly on frequency and energy.

Lower and higher frequencies can occupy different colour regions, while energy influences brightness.

The colour system is artistic rather than strictly scientific.

## Size and brightness

Node size is influenced by pulse duration.

Node brightness is influenced by energy.

This means stronger or longer calls can become more visually dominant.

## Blender

Blender is used to generate the final 3D render.

Main files:

```text
blender/animate_bat_spectrum.py
blender/bat_spectrum_template.blend
```

The script reads:

```text
data/exports/blender_scene.json
```

and generates:

```text
blender/bat_spectrum_generated.blend
```

The generated `.blend` file is ignored by Git because it can be recreated.

## Camera

The camera is positioned to frame the acoustic constellation.

If nodes are cut off, the camera can be moved back or the lens widened.

Example values:

```text
camera location: (0, -13, 8.0)
lens: 28–40
```

A lower lens value gives a wider view.

## Audio

The render should use:

```text
data/processed/current_audio_render.wav
```

This file is converted to a standard render-friendly sample rate.

The original ultrasonic recording is preserved separately.

## Clean audio option

The cleaned audio output:

```text
data/clean/clean_audio.wav
```

can be used for review or future render experiments.

It is created from the current audio using frequency filtering and pulse masking.

It should be treated as a derived interpretation, not as the original recording.

## Artistic direction

Bat Spectrum is not only a technical detector.

The visual system is designed to explore how bat calls can become:

```text
spatial
animated
archival
musical
interpretable
```

The final image should feel like a sound structure emerging over time.
