"""Audit the screen-right free skate against the visible face across descent."""

import json
import math

import bpy
from mathutils import Vector


scene = bpy.context.scene
version = scene.get("prototype_version")
if version not in {"v153", "v155"}:
    raise RuntimeError(f"Expected V153/V155 candidate, got {version}")

head = scene.objects["Head · detailed generic human sculpt"]
nose = scene.objects["Head · nose tip"]
boot = scene.objects["Left skate · website boot v64"]
blade = scene.objects["Left skate · website blade v64"]
right_boot = scene.objects["Right skate · website boot v64"]
right_blade = scene.objects["Right skate · website blade v64"]


def horizontal(vector):
    value = Vector((vector.x, vector.y, 0.0))
    return value.normalized() if value.length > 1e-8 else None


def yaw(first, second):
    a, b = horizontal(first), horizontal(second)
    if a is None or b is None:
        raise RuntimeError("Degenerate horizontal facing axis")
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


rows = []
for frame in (76.0, 78.0, 80.0, 81.0, 82.0, 83.0, 84.0, 85.0, 86.0, 87.0, 90.0, 92.0):
    scene.frame_set(math.floor(frame), subframe=frame - math.floor(frame))
    bpy.context.view_layer.update()
    face = horizontal(nose.matrix_world.translation - head.matrix_world.translation)
    left_toe = horizontal(boot.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0)))
    left_blade_toe = horizontal(blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0)))
    right_toe = horizontal(right_boot.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0)))
    right_blade_toe = horizontal(right_blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0)))
    rows.append({
        "frame": frame,
        "face_to_screen_right_boot_deg": yaw(face, left_toe),
        "screen_right_boot_to_blade_deg": yaw(left_toe, left_blade_toe),
        "face_to_landing_boot_deg": yaw(face, right_toe),
        "landing_boot_to_blade_deg": yaw(right_toe, right_blade_toe),
    })

window = [row for row in rows if 80.0 <= row["frame"] <= 85.0]
report = {
    "blend": bpy.data.filepath,
    "prototype_version": version,
    "screen_right_free_skate_max_face_yaw_deg_f80_f85": round(
        max(abs(row["face_to_screen_right_boot_deg"]) for row in window), 4),
    "max_boot_to_blade_axis_error_deg": round(max(
        abs(row[key]) for row in rows
        for key in ("screen_right_boot_to_blade_deg", "landing_boot_to_blade_deg")), 6),
    "key_frames": rows,
    "method_limit": "Illustrative yaw review metric; not an ISU or coaching angle prescription.",
}
print("SCREEN_RIGHT_SKATE_AUDIT_V155 " + json.dumps(report, ensure_ascii=False))

if report["screen_right_free_skate_max_face_yaw_deg_f80_f85"] > 55.0:
    raise RuntimeError("Screen-right free skate visibly turns too far away from the face during descent")
if report["max_boot_to_blade_axis_error_deg"] > 0.01:
    raise RuntimeError("A boot toe and its attached blade toe are no longer aligned")
