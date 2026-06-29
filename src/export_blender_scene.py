from pathlib import Path
import json
import math

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PULSES_CSV = PROJECT_ROOT / "data" / "exports" / "current_pulses.csv"
EDGES_CSV = PROJECT_ROOT / "data" / "exports" / "current_edges.csv"
METADATA_JSON = PROJECT_ROOT / "data" / "exports" / "current_metadata.json"
AUDIO_PATH = PROJECT_ROOT / "data" / "raw_audio" / "current_audio.wav"

OUTPUT_JSON = PROJECT_ROOT / "data" / "exports" / "blender_scene.json"


def safe_float(value, default=0.0) -> float:
    if pd.isna(value):
        return default
    return float(value)


def safe_int(value, default=0) -> int:
    if pd.isna(value):
        return default
    return int(value)


def main() -> None:
    if not PULSES_CSV.exists():
        raise FileNotFoundError(f"Missing pulses CSV: {PULSES_CSV}")

    if not EDGES_CSV.exists():
        raise FileNotFoundError(f"Missing edges CSV: {EDGES_CSV}")

    if not AUDIO_PATH.exists():
        raise FileNotFoundError(f"Missing audio file: {AUDIO_PATH}")

    pulses = pd.read_csv(PULSES_CSV)
    edges = pd.read_csv(EDGES_CSV)

    if pulses.empty:
        raise ValueError("No pulses found in current_pulses.csv")

    metadata = {}

    if METADATA_JSON.exists():
        metadata = json.loads(METADATA_JSON.read_text(encoding="utf-8"))

    duration_seconds = float(
        metadata.get("duration_seconds", pulses["death_time"].max())
    )

    # Blender uses Z as vertical.
    # We map:
    # X = time position
    # Y = depth / energy
    # Z = frequency height
    center_x = pulses["pos_x"].mean()
    center_y = pulses["pos_y"].mean()
    center_z = pulses["pos_z"].mean()

    nodes = []

    for _, row in pulses.iterrows():
        pulse_id = safe_int(row["pulse_id"])

              # Acoustic map position.
        # Important: time is NOT used for position anymore.
        # Time only controls animation through birth_time.
        freq_norm = safe_float(row.get("freq_norm", 0.5), 0.5)
        duration_norm = safe_float(row.get("duration_norm", 0.5), 0.5)
        energy_norm = safe_float(row.get("energy_norm", 0.5), 0.5)
        interval_norm = safe_float(row.get("interval_norm", 0.5), 0.5)

               # Acoustic constellation map.
        # Time is NOT used for position.
        # Frequency defines a region, duration/interval spread the node,
        # and energy gives height/depth.
        pulse_seed = pulse_id * 12.9898

        jitter_x = math.sin(pulse_seed) * 0.45
        jitter_y = math.cos(pulse_seed * 1.37) * 0.45
        jitter_z = math.sin(pulse_seed * 0.73) * 0.30

        angle = 2.0 * math.pi * (
            freq_norm * 0.70
            + duration_norm * 0.18
            + interval_norm * 0.12
        )

        # Compressed radius: avoids very long arms/outliers.
        radius_map = 1.4 + 2.1 * (
            duration_norm * 0.45
            + interval_norm * 0.25
            + energy_norm * 0.30
        )

        x = math.cos(angle) * radius_map + jitter_x
        y = math.sin(angle) * radius_map + jitter_y
        z = (energy_norm - 0.5) * 3.8 + (duration_norm - 0.5) * 1.1 + jitter_z

        size = safe_float(row["size"], 0.1)
        brightness = safe_float(row["brightness"], 1.0)

        color = [
            safe_float(row["color_r"], 1.0),
            safe_float(row["color_g"], 1.0),
            safe_float(row["color_b"], 1.0),
            1.0,
        ]

        nodes.append(
            {
                "id": pulse_id,
                "previous_pulse_id": safe_int(row.get("previous_pulse_id", 0)),
                "start_time": safe_float(row["start_time"]),
                "end_time": safe_float(row["end_time"]),
                "birth_time": safe_float(row["birth_time"]),
                "death_time": safe_float(row["death_time"], duration_seconds),
                "duration": safe_float(row["duration"]),
                "peak_frequency_hz": safe_float(row["peak_frequency_hz"]),
                "energy": safe_float(row.get("energy_norm", row.get("mean_energy", 0.0))),
                "position": [x, y, z],
                "radius": max(size * 0.45, 0.03),
                "brightness": brightness,
                "color": color,
                "fade_in": safe_float(row.get("fade_in", 0.08), 0.08),
                "fade_out": safe_float(row.get("fade_out", 0.25), 0.25),
            }
        )

    node_lookup = {node["id"]: node for node in nodes}

    edge_items = []

    for _, row in edges.iterrows():
        from_id = safe_int(row["from_pulse_id"])
        to_id = safe_int(row["to_pulse_id"])

        if from_id not in node_lookup or to_id not in node_lookup:
            continue

        from_node = node_lookup[from_id]
        to_node = node_lookup[to_id]

        edge_items.append(
            {
                "id": safe_int(row["edge_id"]),
                "from": from_id,
                "to": to_id,
                "birth_time": safe_float(row["birth_time"]),
                "from_position": from_node["position"],
                "to_position": to_node["position"],
                "color": [
                    safe_float(row.get("color_r", to_node["color"][0])),
                    safe_float(row.get("color_g", to_node["color"][1])),
                    safe_float(row.get("color_b", to_node["color"][2])),
                    1.0,
                ],
                "energy": safe_float(row.get("energy", to_node["energy"])),
            }
        )

    scene = {
        "project": "Bat Spectrum",
        "mode": "single_audio_realtime_map",
        "audio": {
            "path": str(AUDIO_PATH.resolve()),
            "duration_seconds": duration_seconds,
        },
        "animation": {
            "fps": 30,
            "frame_start": 1,
            "frame_end": int(duration_seconds * 30) + 30,
        },
        "nodes": nodes,
        "edges": edge_items,
        "metadata": metadata,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(scene, indent=2), encoding="utf-8")

    print(f"Blender scene exported to: {OUTPUT_JSON}")
    print(f"Audio duration: {duration_seconds:.3f} s")
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edge_items)}")


if __name__ == "__main__":
    main()