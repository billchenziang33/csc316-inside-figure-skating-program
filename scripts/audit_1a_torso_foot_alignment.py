"""Audit torso-facing, source foot, boot, and blade headings in v108/v110."""

import json
import math

import bpy
from mathutils import Vector


STEP = 0.25
FORWARD_LOCAL = Vector((0.0, -1.0, 0.0))


def horizontal(value):
    result = Vector((value.x, value.y, 0.0))
    return result.normalized() if result.length > 1e-8 else None


def angle(a, b):
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


scene = bpy.context.scene
version = scene.get("prototype_version")
if version not in {"v108", "v110", "v111", "v112", "v113"}:
    raise RuntimeError(f"Expected v108, v110, v111, v112, or v113, got {version!r}")

body = scene.objects["Body anchor · pelvis-origin poses"]
rig = scene.objects["Skater root · simulated travel and 1.5-turn yaw v8"]
head = scene.objects["Head · detailed generic human sculpt"]
nose = scene.objects["Head · nose tip"]
left_shoulder = scene.objects["Human · left shoulder volume"]
right_shoulder = scene.objects["Human · right shoulder volume"]
pelvis = scene.objects["Human · pelvic/waist volume"]
right_skate = scene.objects["Right skate · exact website fit v64"]
right_boot = scene.objects["Right skate · website boot v64"]
right_blade = scene.objects["Right skate · website blade v64"]

rows = []
frame = float(scene.frame_start)
while frame <= scene.frame_end + 1e-8:
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()

    across = horizontal(right_shoulder.matrix_world.translation -
                        left_shoulder.matrix_world.translation)
    up = (head.matrix_world.translation - pelvis.matrix_world.translation).normalized()
    torso = horizontal(across.cross(up))
    face = horizontal(nose.matrix_world.translation - head.matrix_world.translation)
    joint_root_q = rig.matrix_world.to_quaternion()
    generic_axis = horizontal(joint_root_q @ FORWARD_LOCAL)
    skate_axis = horizontal(right_skate.matrix_world.to_3x3() @ FORWARD_LOCAL)
    boot_axis = horizontal(right_boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
    blade_axis = horizontal(right_blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0)))
    if not all((torso, face, generic_axis, skate_axis, boot_axis, blade_axis)):
        raise RuntimeError(f"Degenerate axis at frame {frame:.2f}")

    # Resolve whether the shoulder-derived perpendicular faces the same way as
    # the mesh's visible nose; flip only the audit vector, never scene data.
    if torso.dot(face) < 0.0:
        torso.negate()
    rows.append({
        "frame": round(frame, 2),
        "torso_to_face_deg": round(angle(torso, face), 4),
        "torso_to_right_boot_deg": round(angle(torso, boot_axis), 4),
        "torso_to_source_axis_deg": round(angle(torso, generic_axis), 4),
        "source_to_boot_deg": round(angle(generic_axis, boot_axis), 4),
        "boot_to_blade_deg": round(angle(boot_axis, blade_axis), 4),
        "torso_heading": [round(x, 5) for x in torso],
        "right_boot_heading": [round(x, 5) for x in boot_axis],
    })
    frame += STEP

frames = (37.0, 60.0, 76.0, 87.0, 89.0, 90.0, 93.0, 120.0, 150.0, 160.0)
selected = [next(row for row in rows if row["frame"] == target) for target in frames]
print("TORSO_FOOT_ALIGNMENT_AUDIT " + json.dumps({
    "file": bpy.data.filepath,
    "prototype_version": version,
    "step_frames": STEP,
    "sample_count": len(rows),
    "max_abs_torso_to_face_deg": max(abs(x["torso_to_face_deg"]) for x in rows),
    "max_abs_torso_to_boot_deg": max(abs(x["torso_to_right_boot_deg"]) for x in rows),
    "max_abs_torso_to_source_axis_deg": max(abs(x["torso_to_source_axis_deg"]) for x in rows),
    "max_abs_source_to_boot_deg": max(abs(x["source_to_boot_deg"]) for x in rows),
    "max_abs_boot_to_blade_deg": max(abs(x["boot_to_blade_deg"]) for x in rows),
    "key_frames": selected,
}, ensure_ascii=False))
