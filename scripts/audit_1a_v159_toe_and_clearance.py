"""Verify physical toe axes, ankle fit, and blade clearance for V159."""

import json
import math

import bpy
import numpy as np
from mathutils import Vector


scene = bpy.context.scene
if scene.get("prototype_version") != "v159":
    raise RuntimeError(f"Expected V159, got {scene.get('prototype_version')}")
torso = scene.objects["Human · shaped jacket torso"]
ice = scene.objects["V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)"]
ice_top_z = max((ice.matrix_world @ vertex.co).z for vertex in ice.data.vertices)
sides = {
    side: {
        "ankle": scene.objects[f"Human · {side.lower()} ankle joint"],
        "boot": scene.objects[f"{side} skate · website boot v64"],
        "blade": scene.objects[f"{side} skate · website blade v64"],
    }
    for side in ("Left", "Right")
}
torso_forward = Vector((0.0, -1.0, 0.0))
boot_toe = Vector((0.0, 1.0, 0.0))
blade_toe = Vector((0.0, -1.0, 0.0))


def horizontal(v):
    result = Vector((v.x, v.y, 0.0))
    return result.normalized() if result.length > 1e-8 else None


def signed_angle(a, b):
    a, b = horizontal(a), horizontal(b)
    if a is None or b is None:
        raise RuntimeError("Degenerate toe heading")
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


heading_rows = []
for index in range(637):
    frame = scene.frame_start + index * 0.25
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    torso_axis = torso.matrix_world.to_3x3() @ torso_forward
    row = {"frame": frame}
    for side, refs in sides.items():
        boot_axis = refs["boot"].matrix_world.to_3x3() @ boot_toe
        blade_axis = refs["blade"].matrix_world.to_3x3() @ blade_toe
        row[f"{side.lower()}_toe_to_torso_deg"] = signed_angle(torso_axis, boot_axis)
        row[f"{side.lower()}_boot_blade_deg"] = signed_angle(boot_axis, blade_axis)
        anchor = refs["boot"].matrix_world @ (Vector((0.0, 0.045, 0.035)) * 1.8)
        row[f"{side.lower()}_ankle_drift_mm"] = (
            anchor - refs["ankle"].matrix_world.translation).length * 1000.0
    heading_rows.append(row)

step = 1.0 / 16.0
sample_count = round((scene.frame_end - scene.frame_start) / step) + 1
blade_vertices = {
    side: np.asarray([tuple(vertex.co) + (1.0,) for vertex in refs["blade"].data.vertices],
                     dtype=np.float64)
    for side, refs in sides.items()
}
min_clearance = {side: {"meters": float("inf"), "frame": None} for side in sides}
for index in range(sample_count):
    frame = scene.frame_start + index * step
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    for side, refs in sides.items():
        matrix = np.asarray(refs["blade"].matrix_world, dtype=np.float64)
        gap = float((blade_vertices[side] @ matrix.T)[:, 2].min() - ice_top_z)
        if gap < min_clearance[side]["meters"]:
            min_clearance[side] = {"meters": gap, "frame": frame}

report = {
    "version": scene.get("prototype_version"),
    "quarter_frame_heading_samples": len(heading_rows),
    "sixteenth_frame_clearance_samples_per_blade": sample_count,
    "ice_top_z_m": ice_top_z,
    "max_abs_physical_toe_to_torso_yaw_deg": {
        side: round(max(abs(row[f"{side.lower()}_toe_to_torso_deg"])
                        for row in heading_rows), 5)
        for side in sides
    },
    "max_boot_to_blade_toe_yaw_deg": round(max(
        abs(row[f"{side.lower()}_boot_blade_deg"])
        for row in heading_rows for side in sides), 6),
    "max_ankle_anchor_drift_mm": round(max(
        row[f"{side.lower()}_ankle_drift_mm"]
        for row in heading_rows for side in sides), 6),
    "minimum_blade_clearance": min_clearance,
    "key_frames": [row for row in heading_rows
                   if row["frame"] in (48.0, 70.0, 78.0, 79.0, 87.0, 92.0, 120.0, 136.0)],
    "method_limit": "Dense vertex sampling against actual ice top; this does not prove continuous contact or full-body collision freedom.",
}
print("V159_TOE_CLEARANCE_AUDIT " + json.dumps(report, ensure_ascii=False))
if report["max_abs_physical_toe_to_torso_yaw_deg"]["Right"] > 8.05:
    raise RuntimeError("Right physical skate toe still opposes the torso")
if report["max_boot_to_blade_toe_yaw_deg"] > 0.02:
    raise RuntimeError("Visible boot and blade toe axes diverge")
if report["max_ankle_anchor_drift_mm"] > 0.01:
    raise RuntimeError("A boot fit anchor drifted from the ankle")
if min(value["meters"] for value in min_clearance.values()) < -1e-5:
    raise RuntimeError("A blade penetrates the actual ice in the 1/16-frame samples")
