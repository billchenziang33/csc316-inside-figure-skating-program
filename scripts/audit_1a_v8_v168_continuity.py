"""Compare important adjacent-frame pose changes in the preserved V8 and V168 scenes.

Run with Blender 5.2.3:
  blender --background --python scripts/audit_1a_v8_v168_continuity.py -- V8.blend V168.blend

This audit only reads scene transforms. It does not save either blend file.
"""

import json
import math
import sys

import bpy


OBJECTS = (
    "Human · left leg volume 3",
    "Human · left leg volume 4",
    "Human · right leg volume 3",
    "Human · right leg volume 4",
    "Left skate · fitted ankle anchor v4",
    "Right skate · fitted ankle anchor v4",
)


def shortest_rotation_degrees(first, second):
    degrees = math.degrees(first.rotation_difference(second).angle)
    return min(degrees, 360.0 - degrees)


def transition(rows, start_frame, end_frame):
    target = next(
        (row for row in rows if row["from"] == start_frame and row["to"] == end_frame),
        None,
    )
    return None if target is None else round(target["degrees"], 4)


def summarize_scene(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    objects = {name: scene.objects.get(name) for name in OBJECTS}
    missing = [name for name, obj in objects.items() if obj is None]
    if missing:
        raise RuntimeError(f"{path} is missing required objects: {missing}")

    previous = {}
    steps = {name: [] for name in OBJECTS}
    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for name, obj in objects.items():
            current = obj.matrix_world.to_quaternion().normalized()
            if name in previous:
                steps[name].append({
                    "from": frame - 1,
                    "to": frame,
                    "degrees": shortest_rotation_degrees(previous[name], current),
                })
            previous[name] = current.copy()

    report = {}
    for name, rows in steps.items():
        near_takeoff = [row for row in rows if 45 <= row["from"] and row["to"] <= 55]
        peak_takeoff = max(near_takeoff, key=lambda row: row["degrees"], default=None)
        peak_all = max(rows, key=lambda row: row["degrees"], default=None)

        def peak_record(row):
            if row is None:
                return None
            return {"frames": [row["from"], row["to"]], "degrees": round(row["degrees"], 4)}

        report[name] = {
            "50_to_51_deg": transition(rows, 50, 51),
            "86_to_87_deg": transition(rows, 86, 87),
            "largest_step_f45_to_55": peak_record(peak_takeoff),
            "largest_step_entire_scene": peak_record(peak_all),
            "steps_over_30_deg": sum(row["degrees"] > 30.0 for row in rows),
        }

    return {
        "blend": bpy.data.filepath,
        "scene": scene.name,
        "prototype_version": scene.get("prototype_version"),
        "frame_range": [scene.frame_start, scene.frame_end],
        "poses": report,
    }


arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(arguments) != 2:
    raise SystemExit("Pass exactly two blend files after --: V8.blend V168.blend")

results = [summarize_scene(path) for path in arguments]
print("AXEL_CONTINUITY_COMPARISON " + json.dumps(results, ensure_ascii=False))
