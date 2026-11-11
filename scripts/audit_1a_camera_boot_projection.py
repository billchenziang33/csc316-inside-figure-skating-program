"""Read-only map of each boot toe into the saved side camera at selected frames."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


scene = bpy.context.scene
camera = scene.objects.get("Action skater side profile full-body v124")
if camera is None:
    raise RuntimeError("Saved side-profile camera is missing")
rows = []
for frame in (87, 90):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    cam = camera.matrix_world.to_3x3()
    screen_right = cam.col[0].normalized()
    torso = scene.objects["Human · shaped jacket torso"]
    body_forward = (torso.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0))).normalized()
    row = {"frame": frame,
           "torso_forward_screen_x": round(body_forward.dot(screen_right), 5),
           "boots": {}}
    for side in ("Left", "Right"):
        boot = scene.objects[f"{side} skate · website boot v64"]
        toe = (boot.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0))).normalized()
        point = boot.matrix_world.translation
        camera_point = camera.matrix_world.inverted() @ point
        row["boots"][side] = {
            "camera_space_x": round(camera_point.x, 5),
            "toe_screen_x": round(toe.dot(screen_right), 5),
            "body_to_toe_deg": round(math.degrees(math.atan2(
                body_forward.cross(toe).z, body_forward.dot(toe))), 3),
        }
    rows.append(row)
print("CAMERA_BOOT_PROJECTION " + json.dumps({
    "blend": bpy.data.filepath,
    "camera": camera.name,
    "selected_frame_results": rows,
}, ensure_ascii=False))
