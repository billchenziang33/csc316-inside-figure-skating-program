"""Regression audit for the V156 model-right landing skate heading."""

import json
import math

import bpy
from mathutils import Vector


scene = bpy.context.scene
torso = scene.objects["Human · shaped jacket torso"]
boot = scene.objects["Right skate · website boot v64"]
blade = scene.objects["Right skate · website blade v64"]
forward = Vector((0.0, -1.0, 0.0))


def horizontal(vector):
    vector = Vector((vector.x, vector.y, 0.0))
    if vector.length < 1e-8:
        raise RuntimeError("A heading has no horizontal component")
    return vector.normalized()


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


rows = []
for index in range(637):
    frame = 1.0 + index * 0.25
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    torso_axis = torso.matrix_world.to_3x3() @ forward
    boot_axis = boot.matrix_world.to_3x3() @ forward
    blade_axis = blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))
    rows.append({
        "frame": frame,
        "torso_to_boot_deg": signed_angle(torso_axis, boot_axis),
        "boot_to_blade_deg": signed_angle(boot_axis, blade_axis),
    })

worst = max(rows, key=lambda row: abs(row["torso_to_boot_deg"]))
report = {
    "version": scene.get("prototype_version"),
    "samples": len(rows),
    "sample_step_frames": 0.25,
    "max_abs_torso_to_right_boot_deg": round(abs(worst["torso_to_boot_deg"]), 5),
    "worst_frame": worst["frame"],
    "max_abs_boot_to_blade_deg": round(max(abs(row["boot_to_blade_deg"]) for row in rows), 6),
    "status": "illustrative/simulated heading audit; 8-degree cap is a visual constraint, not a coaching rule",
}
print("V156_RIGHT_LANDING_HEADING " + json.dumps(report, ensure_ascii=False))

if scene.get("prototype_version") not in {"v155", "v156"}:
    raise RuntimeError("Expected a V155 baseline or V156 candidate")
if report["max_abs_torso_to_right_boot_deg"] > 8.05:
    raise RuntimeError("The right landing boot exceeds the illustrative 8-degree heading cap")
if report["max_abs_boot_to_blade_deg"] > 0.01:
    raise RuntimeError("The right boot and blade toe directions diverged")
