"""Audit skate heading through the Single Axel landing transition."""

import json
import math

import bpy
from mathutils import Vector


scene = next((item for item in bpy.data.scenes
              if item.get("prototype_version") in {"v116", "v117"}), None)
if scene is None:
    raise RuntimeError("Expected a V116 or V117 Single Axel scene")


def horizontal(vector):
    value = Vector((vector.x, vector.y, 0.0))
    return value.normalized() if value.length > 1e-8 else None


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    if a is None or b is None:
        raise RuntimeError("Degenerate horizontal heading")
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


torso = scene.objects["Human · shaped jacket torso"]
left_boot = scene.objects["Left skate · website boot v64"]
left_blade = scene.objects["Left skate · website blade v64"]
right_boot = scene.objects["Right skate · website boot v64"]
right_blade = scene.objects["Right skate · website blade v64"]
left_ankle = scene.objects["Human · left ankle joint"]
left_anchor = Vector((0.0, 0.045, 0.035)) * 1.8

samples = []
frame = 76.0
while frame <= 92.0 + 1e-8:
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    body_forward = torso.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0))
    left_toe = left_boot.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0))
    left_pick = left_blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))
    right_toe = right_boot.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0))
    right_pick = right_blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))
    ankle_error_mm = (left_boot.matrix_world @ left_anchor -
                      left_ankle.matrix_world.translation).length * 1000.0
    samples.append({
        "frame": round(frame, 2),
        "left_body_to_toe_deg": signed_angle(body_forward, left_toe),
        "left_boot_to_blade_deg": signed_angle(left_toe, left_pick),
        "left_ankle_fit_mm": ankle_error_mm,
        "right_body_to_toe_deg": signed_angle(body_forward, right_toe),
        "right_boot_to_blade_deg": signed_angle(right_toe, right_pick),
    })
    frame += 0.25

summary = {
    "blend": bpy.data.filepath,
    "scene": scene.name,
    "version": scene.get("prototype_version"),
    "sample_count": len(samples),
    "transition": {
        "left_max_abs_body_to_toe_deg": max(
            samples, key=lambda item: abs(item["left_body_to_toe_deg"]))
            ["left_body_to_toe_deg"],
        "left_max_abs_boot_to_blade_deg": max(
            abs(item["left_boot_to_blade_deg"]) for item in samples),
        "left_max_ankle_fit_mm": max(item["left_ankle_fit_mm"] for item in samples),
        "right_max_abs_body_to_toe_deg": max(
            abs(item["right_body_to_toe_deg"]) for item in samples),
        "right_max_abs_boot_to_blade_deg": max(
            abs(item["right_boot_to_blade_deg"]) for item in samples),
        "left_near_reversals_over_90_deg": sum(
            abs(item["left_body_to_toe_deg"]) > 90.0 for item in samples),
        "key_frames": [item for item in samples
                       if item["frame"] in {76.0, 80.0, 82.0, 84.0, 86.0, 88.0, 90.0}],
    },
}
print("AXEL_FREE_LEG_TRANSITION_AUDIT " + json.dumps(summary, ensure_ascii=False))

if summary["transition"]["left_near_reversals_over_90_deg"]:
    raise RuntimeError("Left free skate reverses beyond 90 degrees from the torso")
if summary["transition"]["left_max_abs_boot_to_blade_deg"] > 1.0:
    raise RuntimeError("Left boot toe and visible blade toe do not agree")
if summary["transition"]["right_max_abs_boot_to_blade_deg"] > 1.0:
    raise RuntimeError("Right boot toe and visible blade toe do not agree")
if summary["transition"]["left_max_ankle_fit_mm"] > 0.01:
    raise RuntimeError("Left boot no longer fits the ankle anchor")
