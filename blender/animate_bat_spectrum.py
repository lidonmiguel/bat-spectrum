from __future__ import annotations

from pathlib import Path
import json
import math

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCENE_JSON = PROJECT_ROOT / "data" / "exports" / "blender_scene.json"
OUTPUT_BLEND = PROJECT_ROOT / "blender" / "bat_spectrum_generated.blend"
OUTPUT_VIDEO = PROJECT_ROOT / "data" / "processed" / "bat_spectrum_render.mp4"


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)

    for curve in list(bpy.data.curves):
        bpy.data.curves.remove(curve)

    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)


def make_emission_material(name: str, color: list[float], strength: float = 1.5):
    material = bpy.data.materials.new(name)
    material.use_nodes = True

    nodes = material.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    output = nodes.new(type="ShaderNodeOutputMaterial")
    emission = nodes.new(type="ShaderNodeEmission")

    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = strength

    material.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])

    return material


def look_at(obj, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def frame_from_time(seconds: float, fps: int) -> int:
    return max(1, int(round(seconds * fps)) + 1)


def create_node(node: dict, fps: int):
    position = node["position"]
    radius = float(node["radius"])
    radius = min(radius, 0.13)
    birth_frame = frame_from_time(float(node["birth_time"]), fps)
    fade_frames = max(2, int(round(float(node.get("fade_in", 0.08)) * fps)))

    color = node["color"]
    brightness = float(node.get("brightness", 1.0))

    material = make_emission_material(
        name=f"node_mat_{node['id']}",
        color=color,
        strength=1.2 + brightness * 2.0,
    )

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=32,
        ring_count=16,
        radius=1.0,
        location=position,
    )

    obj = bpy.context.object
    obj.name = f"pulse_{node['id']:03d}"
    obj.data.materials.append(material)

    # Invisible before birth.
    obj.scale = (0.0, 0.0, 0.0)
    obj.keyframe_insert(data_path="scale", frame=max(1, birth_frame - 1))

    # Pop / grow in.
    obj.scale = (radius, radius, radius)
    obj.keyframe_insert(data_path="scale", frame=birth_frame + fade_frames)

    # Small overshoot for organic pulse.
    obj.scale = (radius * 1.25, radius * 1.25, radius * 1.25)
    obj.keyframe_insert(data_path="scale", frame=birth_frame + fade_frames + 3)

    obj.scale = (radius, radius, radius)
    obj.keyframe_insert(data_path="scale", frame=birth_frame + fade_frames + 8)

    return obj


def create_edge(edge: dict, fps: int):
    from_position = edge["from_position"]
    to_position = edge["to_position"]

    birth_frame = frame_from_time(float(edge["birth_time"]), fps)
    fade_frames = 5

    color = edge["color"]
    energy = float(edge.get("energy", 0.5))

    material = make_emission_material(
        name=f"edge_mat_{edge['id']}",
        color=color,
        strength=0.5 + energy * 1.8,
    )

    curve = bpy.data.curves.new(f"edge_curve_{edge['id']:03d}", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = 0.0025 + energy * 0.0035
    curve.bevel_resolution = 3
    curve.bevel_factor_start = 0.0
    curve.bevel_factor_end = 0.0

    spline = curve.splines.new(type="POLY")
    spline.points.add(1)

    spline.points[0].co = (
        from_position[0],
        from_position[1],
        from_position[2],
        1.0,
    )
    spline.points[1].co = (
        to_position[0],
        to_position[1],
        to_position[2],
        1.0,
    )

    obj = bpy.data.objects.new(f"edge_{edge['id']:03d}", curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)

    # Hidden / undrawn before birth.
    curve.bevel_factor_end = 0.0
    curve.keyframe_insert(data_path="bevel_factor_end", frame=max(1, birth_frame - 1))

    # Draws from previous node to new node.
    curve.bevel_factor_end = 1.0
    curve.keyframe_insert(data_path="bevel_factor_end", frame=birth_frame + fade_frames)

    return obj


def add_audio_to_sequence_editor(audio_path: str) -> None:
    scene = bpy.context.scene
    sequence_editor = scene.sequence_editor_create()

    try:
        sequence_editor.sequences.new_sound(
            name="current_audio",
            filepath=audio_path,
            channel=1,
            frame_start=1,
        )
        print(f"Audio added to sequencer: {audio_path}")
    except Exception as exc:
        print(f"Could not add audio through sequence_editor.sequences.new_sound: {exc}")
        print("You can add the WAV manually in Blender if needed.")


def setup_camera_and_light(scene_data: dict) -> None:
    nodes = scene_data["nodes"]

    if nodes:
        positions = [Vector(node["position"]) for node in nodes]
        center = sum(positions, Vector()) / len(positions)
    else:
        center = Vector((0, 0, 0))

    bpy.ops.object.light_add(type="AREA", location=(0, -5, 7))
    light = bpy.context.object
    light.name = "main_soft_light"
    light.data.energy = 350
    light.data.size = 6

    bpy.ops.object.camera_add(location=(0, -9, 6.5))
    camera = bpy.context.object
    camera.name = "camera_main"
    look_at(camera, center)

    camera.data.lens = 45
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = 12
    camera.data.dof.aperture_fstop = 5.6

    bpy.context.scene.camera = camera


def setup_scene(scene_data: dict) -> None:
    scene = bpy.context.scene
    fps = int(scene_data["animation"]["fps"])

    scene.frame_start = int(scene_data["animation"]["frame_start"])
    scene.frame_end = int(scene_data["animation"]["frame_end"])
    scene.frame_set(scene.frame_start)

    scene.render.fps = fps
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100

    scene.world = bpy.data.worlds.new("Bat Spectrum World") if not scene.world else scene.world
    scene.world.color = (0, 0, 0)

    # Eevee is fast and good enough for the first preview.
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"

    scene.render.filepath = str(OUTPUT_VIDEO)

    # Blender 5.1 no acepta FFMPEG directamente aquí.
    # De momento generamos la escena .blend y luego configuramos el render manualmente.
    try:
        scene.render.image_settings.file_format = "PNG"
    except Exception:
        pass


def main() -> None:
    if not SCENE_JSON.exists():
        raise FileNotFoundError(f"Missing scene JSON: {SCENE_JSON}")

    scene_data = json.loads(SCENE_JSON.read_text(encoding="utf-8"))

    clear_scene()
    setup_scene(scene_data)

    fps = int(scene_data["animation"]["fps"])

    node_objects = []
    edge_objects = []

    for node in scene_data["nodes"]:
        node_objects.append(create_node(node, fps))

    for edge in scene_data["edges"]:
        edge_objects.append(create_edge(edge, fps))

        setup_camera_and_light(scene_data)

    audio_path = Path(scene_data["audio"]["path"])

    if not audio_path.is_absolute():
        audio_path = PROJECT_ROOT / audio_path

    add_audio_to_sequence_editor(str(audio_path))

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))

    print("")
    print("Bat Spectrum Blender scene created.")
    print(f"Nodes: {len(node_objects)}")
    print(f"Edges: {len(edge_objects)}")
    print(f"Saved blend: {OUTPUT_BLEND}")
    print(f"Configured video output: {OUTPUT_VIDEO}")
    print("")
    print("Open the .blend, press Play, and the nodes/lines should appear in sync with the audio timeline.")


if __name__ == "__main__":
    main()