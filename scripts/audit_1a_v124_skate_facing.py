"""Read-only quarter-frame audit of V124 face, skate-toe, and blade directions."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


EXPECTED = (Path(__file__).resolve().parents[1] / "static" / "movement" /
            "axel-1a-prototype" / "single-axel-1a-human-rink-v124.blend")
SCENE = next((item for item in bpy.data.scenes
              if item.get("prototype_version") == "v124"), None)
if Path(bpy.data.filepath).resolve() != EXPECTED.resolve() or SCENE is None:
    raise RuntimeError(f"Expected the saved V124 scene, got {bpy.data.filepath}")

head = SCENE.objects.get("Head · detailed generic human sculpt")
nose = SCENE.objects.get("Head · nose tip")
if head is None or nose is None:
    raise RuntimeError("V124 is missing the visible face landmarks")


def horizontal(vector):
    vector = Vector((vector.x, vector.y, 0.0))
    if vector.length < 1e-8:
        raise RuntimeError("A sampled direction has no horizontal component")
    return vector.normalized()


def signed_degrees(first, second):
    return math.degrees(math.atan2(first.x * second.y - first.y * second.x,
                                   first.dot(second)))


old_frame = SCENE.frame_current
samples = {side: [] for side in ("Left", "Right")}
try:
    for step in range(637):
        frame = SCENE.frame_start + step * 0.25
        whole = math.floor(frame)
        SCENE.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        face = horizontal(nose.matrix_world.translation - head.matrix_world.translation)
        for side in samples:
            skate = SCENE.objects[f"{side} skate · exact website fit v64"]
            blade = SCENE.objects[f"{side} skate · website blade v64"]
            boot_toe = horizontal(skate.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0)))
            blade_toe = horizontal(blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0)))
            samples[side].append({
                "frame": round(frame, 2),
                "face_to_skate_deg": signed_degrees(face, boot_toe),
                "boot_to_blade_deg": signed_degrees(boot_toe, blade_toe),
            })
finally:
    SCENE.frame_set(old_frame)
    bpy.context.view_layer.update()

summary = {"blend": bpy.data.filepath, "scene": SCENE.name,
           "sample_step_frames": 0.25, "sample_count_per_side": 637,
           "by_side": {}}
for side, values in samples.items():
    worst = max(values, key=lambda item: abs(item["face_to_skate_deg"]))
    summary["by_side"][side] = {
        "max_abs_face_to_skate_deg": round(abs(worst["face_to_skate_deg"]), 4),
        "worst_face_to_skate": worst,
        "max_abs_boot_to_blade_deg": round(
            max(abs(item["boot_to_blade_deg"]) for item in values), 6),
        "key_frames": [next(item for item in values if item["frame"] == frame)
                       for frame in (60.0, 72.0, 76.0, 87.0, 90.0, 121.0, 150.0)],
    }

print("V124_SKATE_FACING_AUDIT " + json.dumps(summary, ensure_ascii=False))
if summary["by_side"]["Right"]["max_abs_face_to_skate_deg"] >= 90.0:
    raise RuntimeError("Right skate reverses by 90 degrees or more from the visible face")
if any(value["max_abs_boot_to_blade_deg"] > 1.0
       for value in summary["by_side"].values()):
    raise RuntimeError("A visible blade toe differs from its boot toe by more than one degree")
