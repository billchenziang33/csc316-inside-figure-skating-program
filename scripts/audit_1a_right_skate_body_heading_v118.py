"""Audit right-boot direction against torso and toe-pick throughout V118."""

import json
import math

import bpy
from mathutils import Vector


scene = next((item for item in bpy.data.scenes
              if item.get("prototype_version") == "v118"), None)
if scene is None:
    raise RuntimeError("Expected the V118 Single Axel scene")

FORWARD = Vector((0.0, -1.0, 0.0))
torso = scene.objects["Human · shaped jacket torso"]
right_skate = scene.objects["Right skate · exact website fit v64"]
right_boot = scene.objects["Right skate · website boot v64"]
right_blade = scene.objects["Right skate · website blade v64"]
nose_bridge = scene.objects["Head · nose bridge"]
nose_tip = scene.objects["Head · nose tip"]


def horizontal(vector):
    result = Vector((vector.x, vector.y, 0.0))
    return result.normalized() if result.length > 1e-8 else None


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    if a is None or b is None:
        raise RuntimeError("Degenerate horizontal heading")
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


rows = []
saved_frame = scene.frame_current
saved_subframe = scene.frame_subframe
frame = float(scene.frame_start)
while frame <= scene.frame_end + 1e-8:
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    body = torso.matrix_world.to_3x3() @ FORWARD
    face = nose_tip.matrix_world.translation - nose_bridge.matrix_world.translation
    boot_toe = right_boot.matrix_world.to_3x3() @ FORWARD
    blade_toe = right_blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))
    rows.append({
        "frame": round(frame, 2),
        "torso_to_right_boot_deg": signed_angle(body, boot_toe),
        "face_to_right_boot_deg": signed_angle(face, boot_toe),
        "face_to_torso_deg": signed_angle(body, face),
        "boot_to_visible_blade_toe_deg": signed_angle(boot_toe, blade_toe),
    })
    frame += 0.25

scene.frame_set(saved_frame, subframe=saved_subframe)
bpy.context.view_layer.update()

phase_ranges = {
    "approach": (1.0, 50.0),
    "takeoff": (51.0, 60.0),
    "flight": (61.0, 89.0),
    "landing": (90.0, 105.0),
    "exit": (106.0, 160.0),
}
phase_maxima = {
    phase: round(max(abs(row["torso_to_right_boot_deg"]) for row in rows
                     if start <= row["frame"] <= end), 4)
    for phase, (start, end) in phase_ranges.items()
}
max_yaw = max(abs(row["torso_to_right_boot_deg"]) for row in rows)
max_face_yaw = max(abs(row["face_to_right_boot_deg"]) for row in rows)
worst_heading_rows = [
    {"frame": row["frame"], "yaw_deg": round(row["torso_to_right_boot_deg"], 4)}
    for row in rows if abs(abs(row["torso_to_right_boot_deg"]) - max_yaw) < 1e-6
]

report = {
    "blend": bpy.data.filepath,
    "prototype_version": scene.get("prototype_version"),
    "sample_range": [float(scene.frame_start), float(scene.frame_end)],
    "sample_step_frames": 0.25,
    "sample_count": len(rows),
    "max_abs_torso_to_right_boot_heading_deg": round(max_yaw, 4),
    "max_abs_torso_to_right_boot_by_phase_deg": phase_maxima,
    "max_abs_face_to_right_boot_heading_deg": round(max_face_yaw, 4),
    "frames_at_max_heading": worst_heading_rows,
    "max_abs_boot_to_visible_blade_toe_heading_deg": round(
        max(abs(row["boot_to_visible_blade_toe_deg"]) for row in rows), 6),
    "key_frames": [row for row in rows if row["frame"] in {37.0, 50.0, 60.0, 70.0,
                                                            76.0, 82.0, 87.0, 90.0,
                                                            100.0, 121.0, 150.0, 160.0}],
    "interpretation": (
        "The toe-pick and boot axes use different intrinsic mesh signs (boot -Y, blade +Y). "
        "This is a geometric orientation audit, not a prescribed skating technique angle."),
}
print("V118_RIGHT_SKATE_BODY_HEADING " + json.dumps(report, ensure_ascii=False))
result = report
if report["max_abs_torso_to_right_boot_heading_deg"] >= 90.0:
    raise RuntimeError("The right boot reverses beyond 90 degrees from the torso")
if report["max_abs_boot_to_visible_blade_toe_heading_deg"] > 0.1:
    raise RuntimeError("The right blade toe-pick points away from the boot toe")
