"""Audit V168 face, skate, blade and ice-facing geometry across the animation."""

import json
import math

import bpy
import numpy as np
from mathutils import Vector


scene = bpy.context.scene
if scene.get("prototype_version") != "v168":
    raise RuntimeError(f"Expected V168, got {scene.get('prototype_version')}")

torso = scene.objects["Human · shaped jacket torso"]
left_eye = scene.objects["Head · left eye white"]
right_eye = scene.objects["Head · right eye white"]
nose = scene.objects["Head · nose tip"]
ice = scene.objects["V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)"]
ice_top_z = max((ice.matrix_world @ vertex.co).z for vertex in ice.data.vertices)
skates = {
    side: {
        "ankle": scene.objects[f"Human · {side.lower()} ankle joint"],
        "boot": scene.objects[f"{side} skate · website boot v64"],
        "blade": scene.objects[f"{side} skate · website blade v64"],
    }
    for side in ("Left", "Right")
}
torso_forward_local = Vector((0.0, -1.0, 0.0))
boot_toe_local = Vector((0.0, 1.0, 0.0))
blade_toe_local = Vector((0.0, -1.0, 0.0))


def horizontal(vector):
    value = Vector((vector.x, vector.y, 0.0))
    return value.normalized() if value.length > 1e-8 else None


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    if a is None or b is None:
        raise RuntimeError("Degenerate face, torso or skate heading")
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


step = 1.0 / 16.0
sample_count = round((scene.frame_end - scene.frame_start) / step) + 1
blade_vertices = {
    side: np.asarray([tuple(vertex.co) + (1.0,)
                      for vertex in refs["blade"].data.vertices], dtype=np.float64)
    for side, refs in skates.items()
}
minimum_clearance = {side: {"meters": float("inf"), "frame": None} for side in skates}
max_heading = {side: 0.0 for side in skates}
max_boot_blade_yaw = 0.0
max_ankle_drift_mm = 0.0
max_face_torso_yaw = 0.0
face_rows = []

for index in range(sample_count):
    frame = scene.frame_start + index * step
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    eyes = (left_eye.matrix_world.translation + right_eye.matrix_world.translation) * 0.5
    face_axis = nose.matrix_world.translation - eyes
    torso_axis = torso.matrix_world.to_3x3() @ torso_forward_local
    face_yaw = signed_angle(torso_axis, face_axis)
    max_face_torso_yaw = max(max_face_torso_yaw, abs(face_yaw))
    face_rows.append({"frame": frame, "face_to_torso_deg": face_yaw})
    for side, refs in skates.items():
        boot_axis = refs["boot"].matrix_world.to_3x3() @ boot_toe_local
        blade_axis = refs["blade"].matrix_world.to_3x3() @ blade_toe_local
        heading = signed_angle(torso_axis, boot_axis)
        blade_yaw = signed_angle(boot_axis, blade_axis)
        max_heading[side] = max(max_heading[side], abs(heading))
        max_boot_blade_yaw = max(max_boot_blade_yaw, abs(blade_yaw))
        ankle_reference = refs["boot"].matrix_world @ (Vector((0.0, 0.045, 0.035)) * 1.8)
        max_ankle_drift_mm = max(
            max_ankle_drift_mm,
            (ankle_reference - refs["ankle"].matrix_world.translation).length * 1000.0)
        matrix = np.asarray(refs["blade"].matrix_world, dtype=np.float64)
        gap = float((blade_vertices[side] @ matrix.T)[:, 2].min() - ice_top_z)
        if gap < minimum_clearance[side]["meters"]:
            minimum_clearance[side] = {"meters": gap, "frame": frame}

key_frames = (47.0, 50.0, 70.0, 78.0, 83.0, 87.0, 92.0, 120.0, 136.0)
report = {
    "version": scene.get("prototype_version"),
    "sixteenth_frame_samples": sample_count,
    "max_abs_face_to_torso_yaw_deg": round(max_face_torso_yaw, 5),
    "max_abs_toe_to_torso_yaw_deg": {key: round(value, 5)
                                     for key, value in max_heading.items()},
    "max_abs_boot_to_blade_yaw_deg": round(max_boot_blade_yaw, 6),
    "max_ankle_reference_drift_mm": round(max_ankle_drift_mm, 6),
    "minimum_blade_clearance": minimum_clearance,
    "key_face_yaws_deg": [
        {"frame": row["frame"], "face_to_torso": round(row["face_to_torso_deg"], 4)}
        for row in face_rows if row["frame"] in key_frames],
    "method_limit": "Discrete geometric samples; visual limits only, not biomechanics or continuous collision proof.",
}
print("V168_FACING_ALIGNMENT_AUDIT " + json.dumps(report, ensure_ascii=False))

if max_face_torso_yaw > 18.1:
    raise RuntimeError("Visible face exceeds V168 visual yaw target")
if max_heading["Left"] > 25.1 or max_heading["Right"] > 8.1:
    raise RuntimeError("A physical skate toe exceeds its visual heading target")
if max_boot_blade_yaw > 0.02:
    raise RuntimeError("A fitted boot toe and blade toe diverged")
if max_ankle_drift_mm > 0.01:
    raise RuntimeError("A fitted skate ankle reference drifted")
if min(item["meters"] for item in minimum_clearance.values()) < -1e-5:
    raise RuntimeError("A blade penetrates the actual ice in the samples")
