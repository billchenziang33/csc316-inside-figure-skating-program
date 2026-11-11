"""Read-only free-skate/body heading regression audit for V149 and later."""

import json
import math

import bpy
from mathutils import Vector


scene = next((item for item in bpy.data.scenes
              if item.get("prototype_version") in {"v149", "v150", "v151"}), None)
if scene is None:
    raise RuntimeError("Expected a V149/V150/V151 Single Axel scene")

head = scene.objects["Head · detailed generic human sculpt"]
nose = scene.objects["Head · nose tip"]
torso = scene.objects["Human · shaped jacket torso"]
boot = scene.objects["Left skate · website boot v64"]
blade = scene.objects["Left skate · website blade v64"]
ice = scene.objects["V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)"]
FORWARD = Vector((0.0, -1.0, 0.0))


def horizontal(vector):
    value = Vector((vector.x, vector.y, 0.0))
    if value.length < 1e-8:
        raise RuntimeError("Degenerate horizontal heading")
    return value.normalized()


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


def blade_min_z():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = blade.evaluated_get(depsgraph)
    return min((evaluated.matrix_world @ vertex.co).z
               for vertex in evaluated.data.vertices)


ice_top = max((ice.matrix_world @ vertex.co).z for vertex in ice.data.vertices)
rows = []
saved_frame, saved_subframe = scene.frame_current, scene.frame_subframe
try:
    index = 0
    while index <= 640:
        frame = 1.0 + index * 0.25
        if frame > scene.frame_end:
            break
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        face = nose.matrix_world.translation - head.matrix_world.translation
        torso_axis = torso.matrix_world.to_3x3() @ FORWARD
        boot_axis = boot.matrix_world.to_3x3() @ FORWARD
        blade_axis = blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))
        row = {
            "frame": round(frame, 2),
            "face_to_boot_deg": signed_angle(face, boot_axis),
            "torso_to_boot_deg": signed_angle(torso_axis, boot_axis),
            "boot_to_blade_deg": signed_angle(boot_axis, blade_axis),
        }
        if 87.0 <= frame <= 90.0:
            row["blade_gap_m"] = blade_min_z() - ice_top
        rows.append(row)
        index += 1
finally:
    scene.frame_set(saved_frame, subframe=saved_subframe)
    bpy.context.view_layer.update()

landing_window = [row for row in rows if 87.0 <= row["frame"] <= 90.0]
report = {
    "blend": bpy.data.filepath,
    "version": scene.get("prototype_version"),
    "sample_step_frames": 0.25,
    "landing_window_frame_range": [87.0, 90.0],
    "landing_window_max_face_to_boot_abs_deg": round(
        max(abs(row["face_to_boot_deg"]) for row in landing_window), 5),
    "landing_window_max_torso_to_boot_abs_deg": round(
        max(abs(row["torso_to_boot_deg"]) for row in landing_window), 5),
    "full_sequence_max_face_to_boot_abs_deg": round(
        max(abs(row["face_to_boot_deg"]) for row in rows), 5),
    "max_boot_to_blade_abs_deg": round(
        max(abs(row["boot_to_blade_deg"]) for row in rows), 6),
    "minimum_landing_blade_gap_m": round(
        min(row["blade_gap_m"] for row in landing_window), 6),
    "landing_samples": [row for row in landing_window
                        if row["frame"] in {87.0, 88.0, 89.0, 90.0}],
}
print("V151_FREE_SKATE_HEADING_AUDIT " + json.dumps(report, ensure_ascii=False))

if report["landing_window_max_face_to_boot_abs_deg"] > 30.0:
    raise RuntimeError("The visible right-side free skate turns too far from the face during landing")
if report["full_sequence_max_face_to_boot_abs_deg"] >= 90.0:
    raise RuntimeError("The free skate reverses from the visible face")
if report["max_boot_to_blade_abs_deg"] > 0.01:
    raise RuntimeError("The left boot toe and its blade toe point in different directions")
if report["minimum_landing_blade_gap_m"] < -1e-5:
    raise RuntimeError("A blade crosses below the actual ice top")

