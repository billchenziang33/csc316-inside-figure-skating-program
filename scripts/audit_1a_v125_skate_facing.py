"""Read-only face/boot/blade-direction audit on the saved V125 Blender scene."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


EXPECTED = (Path(__file__).resolve().parents[1] / "static" / "movement" /
            "axel-1a-prototype" / "single-axel-1a-human-rink-v125.blend")
scene = bpy.context.scene
if Path(bpy.data.filepath).resolve() != EXPECTED.resolve() or scene.get("prototype_version") != "v125":
    raise RuntimeError(f"Expected saved V125, got {bpy.data.filepath} / {scene.get('prototype_version')}")
head = scene.objects.get("Head · detailed generic human sculpt")
nose = scene.objects.get("Head · nose tip")
if head is None or nose is None:
    raise RuntimeError("V125 is missing its face direction landmarks")


def horizontal(vector):
    value = Vector((vector.x, vector.y, 0.0))
    if value.length < 1e-8:
        raise RuntimeError("A sampled horizontal direction is degenerate")
    return value.normalized()


def signed_degrees(first, second):
    return math.degrees(math.atan2(first.x * second.y - first.y * second.x,
                                   first.dot(second)))


old_frame, old_subframe = scene.frame_current, scene.frame_subframe
values = {side: [] for side in ("Left", "Right")}
try:
    for step in range(637):
        frame = scene.frame_start + step * 0.25
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        face = horizontal(nose.matrix_world.translation - head.matrix_world.translation)
        for side in values:
            anchor = scene.objects[f"{side} skate · exact website fit v64"]
            boot = scene.objects[f"{side} skate · website boot v64"]
            blade = scene.objects[f"{side} skate · website blade v64"]
            if blade.get("toe_pick_mirrored_to_boot_toe") is not True:
                raise RuntimeError(f"{side} runner has not had its asymmetric toe pick reversed")
            boot_toe = horizontal(anchor.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0)))
            blade_toe = horizontal(blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0)))
            values[side].append({
                "frame": round(frame, 2),
                "face_to_boot_deg": signed_degrees(face, boot_toe),
                "boot_to_blade_deg": signed_degrees(boot_toe, blade_toe),
            })
finally:
    scene.frame_set(old_frame, subframe=old_subframe)
    bpy.context.view_layer.update()

by_side = {}
for side, samples in values.items():
    worst = max(samples, key=lambda item: abs(item["face_to_boot_deg"]))
    by_side[side] = {
        "max_abs_face_to_boot_deg": round(abs(worst["face_to_boot_deg"]), 4),
        "worst_face_to_boot": worst,
        "max_abs_boot_to_blade_deg": round(
            max(abs(item["boot_to_blade_deg"]) for item in samples), 6),
        "key_frames": [item for item in samples if item["frame"] in
                       (50.0, 60.0, 72.0, 76.0, 87.0, 90.0, 121.0, 150.0)],
    }
report = {"blend": bpy.data.filepath, "version": "v125",
          "quarter_frame_samples_per_side": len(values["Left"]), "by_side": by_side,
          "interpretation": "Toe pick orientation is checked separately from boot/blade long-axis alignment; torso-face angle is descriptive, not a coaching threshold."}
print("V125_SKATE_FACING " + json.dumps(report, ensure_ascii=False))
if max(by_side[side]["max_abs_face_to_boot_deg"] for side in values) >= 90.0:
    raise RuntimeError("A boot axis points opposite the skater's visible face for a sampled pose")
if max(by_side[side]["max_abs_boot_to_blade_deg"] for side in values) > 1.0:
    raise RuntimeError("A blade long axis no longer follows its boot toe axis")
