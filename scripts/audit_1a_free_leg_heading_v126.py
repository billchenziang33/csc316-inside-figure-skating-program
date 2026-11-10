"""Audit the apparent reversed free skate correction in V125/V126."""

import json
import math

import bpy
from mathutils import Vector


scene = bpy.context.scene
version = scene.get("prototype_version")
if version not in {"v125", "v126", "v127", "v128"}:
    raise RuntimeError(f"Expected V125/V126/V127/V128, got {version!r}")

torso = scene.objects["Human · shaped jacket torso"]
left_boot = scene.objects["Left skate · website boot v64"]
left_blade = scene.objects["Left skate · website blade v64"]
right_boot = scene.objects["Right skate · website boot v64"]
right_blade = scene.objects["Right skate · website blade v64"]
left_ankle = scene.objects["Human · left ankle joint"]
left_anchor = Vector((0.0, 0.045, 0.035)) * 1.8
FORWARD = Vector((0.0, -1.0, 0.0))


def horizontal(vector):
    value = Vector((vector.x, vector.y, 0.0))
    return value.normalized() if value.length > 1e-8 else None


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    if a is None or b is None:
        raise RuntimeError("Degenerate horizontal facing vector")
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


old_frame, old_subframe = scene.frame_current, scene.frame_subframe
rows = []
try:
    for index in range((scene.frame_end - scene.frame_start) * 4 + 1):
        frame = scene.frame_start + index * 0.25
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        body = torso.matrix_world.to_3x3() @ FORWARD
        left_toe = left_boot.matrix_world.to_3x3() @ FORWARD
        right_toe = right_boot.matrix_world.to_3x3() @ FORWARD
        left_pick = left_blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))
        right_pick = right_blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))
        fit_error_mm = (left_boot.matrix_world @ left_anchor -
                        left_ankle.matrix_world.translation).length * 1000.0
        rows.append({
            "frame": round(frame, 2),
            "free_leg_body_yaw_deg": signed_angle(body, left_toe),
            "landing_leg_body_yaw_deg": signed_angle(body, right_toe),
            "left_boot_blade_yaw_deg": signed_angle(left_toe, left_pick),
            "right_boot_blade_yaw_deg": signed_angle(right_toe, right_pick),
            "left_ankle_fit_error_mm": fit_error_mm,
        })
finally:
    scene.frame_set(old_frame, subframe=old_subframe)
    bpy.context.view_layer.update()

flight_and_exit = [row for row in rows if row["frame"] >= 76.0]
report = {
    "blend": bpy.data.filepath,
    "version": version,
    "sample_step_frames": 0.25,
    "sample_count": len(rows),
    "maximum_free_leg_yaw_76_160_deg": round(max(
        abs(row["free_leg_body_yaw_deg"]) for row in flight_and_exit), 4),
    "maximum_landing_leg_yaw_all_frames_deg": round(max(
        abs(row["landing_leg_body_yaw_deg"]) for row in rows), 4),
    "maximum_left_boot_blade_yaw_deg": round(max(
        abs(row["left_boot_blade_yaw_deg"]) for row in rows), 6),
    "maximum_right_boot_blade_yaw_deg": round(max(
        abs(row["right_boot_blade_yaw_deg"]) for row in rows), 6),
    "maximum_left_ankle_fit_error_mm": round(max(
        row["left_ankle_fit_error_mm"] for row in rows), 6),
    "key_frames": [row for row in rows if row["frame"] in {
        60.0, 70.0, 72.0, 76.0, 82.0, 87.0, 90.0, 100.0, 150.0,
    }],
    "interpretation": (
        "The model-left leg is the free leg in several camera views. The V126/V127 target "
        "is a visual continuity limit informed by slow-motion reference, not a coaching rule."
    ),
}
print("AXEL_FREE_LEG_HEADING " + json.dumps(report, ensure_ascii=False))

limit = {"v125": 90.0, "v126": 45.5, "v127": 55.5, "v128": 60.5}[version]
if report["maximum_free_leg_yaw_76_160_deg"] > limit:
    raise RuntimeError(f"The model-left free skate exceeds the {version} visual limit")
if report["maximum_landing_leg_yaw_all_frames_deg"] > 52.0:
    raise RuntimeError("The untouched model-right landing skate changed unexpectedly")
if max(report["maximum_left_boot_blade_yaw_deg"],
       report["maximum_right_boot_blade_yaw_deg"]) > 0.1:
    raise RuntimeError("A skate blade toe no longer follows its boot toe")
if report["maximum_left_ankle_fit_error_mm"] > 0.01:
    raise RuntimeError("Retargeting broke the free skate's ankle fit")
