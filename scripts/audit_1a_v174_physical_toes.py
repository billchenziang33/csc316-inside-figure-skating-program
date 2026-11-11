"""Dense physical toe-axis, ankle-fit, and orientation-continuity audit for V174."""

import json
import math

import bpy
from mathutils import Vector


scene = bpy.context.scene
if scene.get("prototype_version") != "v174":
    raise RuntimeError(f"Expected V174, got {scene.get('prototype_version')}")

torso = scene.objects["Human · shaped jacket torso"]
boots = {side: scene.objects[f"{side} skate · website boot v64"] for side in ("Left", "Right")}
blades = {side: scene.objects[f"{side} skate · website blade v64"] for side in ("Left", "Right")}
ankles = {side: scene.objects[f"Human · {side.lower()} ankle joint"] for side in ("Left", "Right")}


def horizontal(vector):
    value = Vector((vector.x, vector.y, 0.0))
    if value.length <= 1e-8:
        raise RuntimeError("Physical direction axis became degenerate")
    return value.normalized()


def signed_yaw(first, second):
    a, b = horizontal(first), horizontal(second)
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


max_yaw = {side: 0.0 for side in boots}
max_blade_error = 0.0
max_anchor_error_mm = 0.0
max_quarter_heading_step = {side: 0.0 for side in boots}
max_flight_heading_step = {side: 0.0 for side in boots}
max_heading_step_detail = {side: None for side in boots}
previous_axes = {side: None for side in boots}
previous_frames = {side: None for side in boots}
rows = []
sample_count = round((scene.frame_end - scene.frame_start) * 16) + 1
for index in range(sample_count):
    frame = scene.frame_start + index / 16.0
    scene.frame_set(math.floor(frame), subframe=frame - math.floor(frame))
    bpy.context.view_layer.update()
    torso_forward = torso.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0))
    for side in boots:
        boot_toe = boots[side].matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0))
        blade_toe = blades[side].matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))
        yaw = signed_yaw(torso_forward, boot_toe)
        blade_error = abs(signed_yaw(boot_toe, blade_toe))
        anchor = boots[side].matrix_world @ (Vector((0.0, 0.045, 0.035)) * 1.8)
        anchor_error = (anchor - ankles[side].matrix_world.translation).length * 1000.0
        max_yaw[side] = max(max_yaw[side], abs(yaw))
        max_blade_error = max(max_blade_error, blade_error)
        max_anchor_error_mm = max(max_anchor_error_mm, anchor_error)
        axis = horizontal(boot_toe)
        previous = previous_axes[side]
        if previous is not None:
            step = math.degrees(math.acos(max(-1.0, min(1.0, previous.dot(axis)))))
            if step > max_quarter_heading_step[side]:
                max_quarter_heading_step[side] = step
                max_heading_step_detail[side] = {
                    "from_frame": previous_frames[side], "to_frame": frame,
                    "step_deg": round(step, 5), "from_torso_yaw_deg": round(previous_yaws[side], 5),
                    "to_torso_yaw_deg": round(yaw, 5),
                }
            if 60.0 <= frame <= 100.0:
                max_flight_heading_step[side] = max(max_flight_heading_step[side], step)
        previous_axes[side] = axis
        previous_frames[side] = frame
        if "previous_yaws" not in locals():
            previous_yaws = {}
        previous_yaws[side] = yaw
        if frame in {1.0, 47.0, 60.0, 74.0, 87.0, 92.0, 100.0, 136.0, 156.0}:
            rows.append({"frame": frame, "side": side, "boot_toe_to_torso_yaw_deg": round(yaw, 5),
                         "boot_to_blade_yaw_deg": round(blade_error, 7),
                         "ankle_anchor_error_mm": round(anchor_error, 6)})

report = {
    "version": "v174",
    "samples": sample_count,
    "sample_step_frames": 1 / 16,
    "physical_axes": {"boot toe": "local -Y mesh toe end", "blade toe": "local +Y tooth/front end",
                      "torso forward": "torso local -Y"},
    "max_abs_toe_to_torso_yaw_deg": {key: round(value, 5) for key, value in max_yaw.items()},
    "max_boot_to_blade_yaw_deg": round(max_blade_error, 7),
    "max_ankle_anchor_error_mm": round(max_anchor_error_mm, 6),
    "max_adjacent_toe_heading_step_deg": {key: round(value, 5) for key, value in max_quarter_heading_step.items()},
    "max_adjacent_toe_heading_step_deg_frames_60_to_100": {
        key: round(value, 5) for key, value in max_flight_heading_step.items()},
    "max_heading_step_detail": max_heading_step_detail,
    "selected_frames": rows,
    "default_scene_objects": sorted(obj.name for obj in bpy.data.scenes["Scene"].objects),
}
print("V174_PHYSICAL_TOE_DENSE_AUDIT " + json.dumps(report, ensure_ascii=False))
if max(max_yaw.values()) > 12.1 or max_blade_error > 0.02 or max_anchor_error_mm > 0.01:
    raise RuntimeError("V174 physical toe direction, boot/blade agreement, or ankle fit exceeds limit")
if max(max_flight_heading_step.values()) > 5.0:
    raise RuntimeError("V174 has a >5 degree adjacent 1/16-frame physical-toe heading step during take-off, flight, or landing")
