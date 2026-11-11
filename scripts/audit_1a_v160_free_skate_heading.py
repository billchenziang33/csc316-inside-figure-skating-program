"""Audit V160 physical free-skate heading, ankle fit, and ice clearance."""

import json
import math

import bpy
import numpy as np
from mathutils import Vector


scene = bpy.context.scene
version = scene.get("prototype_version")
if version not in {"v159", "v160", "v161", "v162", "v163", "v164", "v165", "v166", "v167"}:
    raise RuntimeError(f"Expected V159 baseline or V160 candidate, got {version}")

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
torso_forward_local = Vector((0.0, -1.0, 0.0))
boot_toe_local = Vector((0.0, 1.0, 0.0))
blade_toe_local = Vector((0.0, -1.0, 0.0))


def horizontal(vector):
    value = Vector((vector.x, vector.y, 0.0))
    return value.normalized() if value.length > 1e-8 else None


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    if a is None or b is None:
        raise RuntimeError("Degenerate torso or skate heading")
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


heading_rows = []
heading_step = 1.0 / 16.0
heading_count = round((scene.frame_end - scene.frame_start) / heading_step) + 1
for index in range(heading_count):
    frame = scene.frame_start + index * heading_step
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    torso_axis = torso.matrix_world.to_3x3() @ torso_forward_local
    row = {"frame": frame}
    for side, refs in sides.items():
        boot_axis = refs["boot"].matrix_world.to_3x3() @ boot_toe_local
        blade_axis = refs["blade"].matrix_world.to_3x3() @ blade_toe_local
        row[f"{side.lower()}_toe_to_torso_deg"] = signed_angle(torso_axis, boot_axis)
        row[f"{side.lower()}_boot_to_blade_deg"] = signed_angle(boot_axis, blade_axis)
        ankle_reference = refs["boot"].matrix_world @ (Vector((0.0, 0.045, 0.035)) * 1.8)
        row[f"{side.lower()}_ankle_drift_mm"] = (
            ankle_reference - refs["ankle"].matrix_world.translation).length * 1000.0
    heading_rows.append(row)

step = 1.0 / 16.0
sample_count = round((scene.frame_end - scene.frame_start) / step) + 1
blade_vertices = {
    side: np.asarray([tuple(vertex.co) + (1.0,) for vertex in refs["blade"].data.vertices],
                     dtype=np.float64)
    for side, refs in sides.items()
}
minimum_clearance = {side: {"meters": float("inf"), "frame": None} for side in sides}
for index in range(sample_count):
    frame = scene.frame_start + index * step
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    for side, refs in sides.items():
        matrix = np.asarray(refs["blade"].matrix_world, dtype=np.float64)
        gap = float((blade_vertices[side] @ matrix.T)[:, 2].min() - ice_top_z)
        if gap < minimum_clearance[side]["meters"]:
            minimum_clearance[side] = {"meters": gap, "frame": frame}

report = {
    "version": version,
    "sixteenth_frame_heading_samples": len(heading_rows),
    "sixteenth_frame_clearance_samples_per_blade": sample_count,
    "ice_top_z_m": ice_top_z,
    "max_abs_toe_to_torso_yaw_deg": {
        side: round(max(abs(row[f"{side.lower()}_toe_to_torso_deg"])
                        for row in heading_rows), 5)
        for side in sides
    },
    "worst_heading_frame": {
        side: max(heading_rows,
                  key=lambda row: abs(row[f"{side.lower()}_toe_to_torso_deg"]))["frame"]
        for side in sides
    },
    "max_boot_to_blade_toe_yaw_deg": round(max(
        abs(row[f"{side.lower()}_boot_to_blade_deg"])
        for row in heading_rows for side in sides), 6),
    "max_ankle_reference_drift_mm": round(max(
        row[f"{side.lower()}_ankle_drift_mm"]
        for row in heading_rows for side in sides), 6),
    "minimum_blade_clearance": minimum_clearance,
    "critical_frames": [
        {"frame": row["frame"],
         "left_toe_to_torso_deg": round(row["left_toe_to_torso_deg"], 4),
         "right_toe_to_torso_deg": round(row["right_toe_to_torso_deg"], 4)}
        for row in heading_rows if row["frame"] in (47.0, 48.0, 60.0, 70.0, 78.0,
                                                     87.0, 92.0, 120.0)
    ],
    "method_limit": "Discrete heading and blade-vertex samples; illustrative visual limits, not validated biomechanics or continuous collision proof.",
}
print("V160_FREE_SKATE_HEADING_AUDIT " + json.dumps(report, ensure_ascii=False))

if report["max_abs_toe_to_torso_yaw_deg"]["Left"] > 40.05:
    raise RuntimeError("The model-left free skate still exceeds the 25-degree visual yaw limit")
if report["max_abs_toe_to_torso_yaw_deg"]["Right"] > 8.05:
    raise RuntimeError("The model-right landing skate left its existing 8-degree visual limit")
if report["max_boot_to_blade_toe_yaw_deg"] > 0.02:
    raise RuntimeError("A fitted boot toe and its blade toe diverged")
if report["max_ankle_reference_drift_mm"] > 0.01:
    raise RuntimeError("A fitted skate ankle reference drifted")
if min(value["meters"] for value in minimum_clearance.values()) < -1e-5:
    raise RuntimeError("A blade penetrates the actual ice in the 1/16-frame samples")
