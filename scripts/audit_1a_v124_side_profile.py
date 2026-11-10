"""Audit V124's saved active camera is a stable horizontal side profile."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / "static" / "movement" / "axel-1a-prototype" / "single-axel-1a-human-rink-v124.blend"
CAMERA_NAME = "Action skater side profile full-body v124"
TARGET_NAME = "Skater pelvis · side-view composition target v124"
SCENE = next((item for item in bpy.data.scenes
			  if item.get("prototype_version") == "v124"), None)
if Path(bpy.data.filepath).resolve() != EXPECTED.resolve() or SCENE is None:
	 raise RuntimeError(f"Expected saved V124 scene, got {bpy.data.filepath}")
if SCENE.camera is None or SCENE.camera.name != CAMERA_NAME:
	 raise RuntimeError("V124 does not open with the full-body side-profile camera active")
camera = SCENE.camera
target = SCENE.objects.get(TARGET_NAME)
torso = SCENE.objects.get("Human · shaped jacket torso")
if target is None or torso is None or camera.parent != target or target.parent != torso:
	 raise RuntimeError("The side camera is not parented to its animated torso target")
default_scene = bpy.data.scenes.get("Scene")
if default_scene is None or sorted(obj.name for obj in default_scene.objects) != ["Camera", "Cube", "Light"]:
	 raise RuntimeError("The original default Scene signature changed")

old_frame = SCENE.frame_current
samples = []
for frame in (1, 37, 60, 76, 87, 90, 121, 160):
	SCENE.frame_set(frame)
	bpy.context.view_layer.update()
	depgraph = bpy.context.evaluated_depsgraph_get()
	cam_eval = camera.evaluated_get(depgraph)
	target_eval = target.evaluated_get(depgraph)
	torso_eval = torso.evaluated_get(depgraph)
	to_camera = cam_eval.matrix_world.translation - target_eval.matrix_world.translation
	to_camera.z = 0.0
	to_camera.normalize()
	local_side = torso_eval.matrix_world.to_3x3() @ Vector((1, 0, 0))
	local_side.z = 0.0
	local_side.normalize()
	local_forward = torso_eval.matrix_world.to_3x3() @ Vector((0, 1, 0))
	local_forward.z = 0.0
	local_forward.normalize()
	cam_to_target = (target_eval.matrix_world.translation - cam_eval.matrix_world.translation).normalized()
	view_forward = (cam_eval.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
	angle = math.degrees(math.acos(max(-1.0, min(1.0, cam_to_target.dot(view_forward)))))
	side_alignment = abs(to_camera.dot(local_side))
	forward_leak = abs(to_camera.dot(local_forward))
	samples.append({
		"frame": frame,
		"camera_to_target_m": round((cam_eval.matrix_world.translation - target_eval.matrix_world.translation).length, 5),
		"side_alignment": round(side_alignment, 6),
		"forward_leak": round(forward_leak, 6),
		"camera_elevation_deg": round(math.degrees(math.asin((cam_eval.matrix_world.translation - target_eval.matrix_world.translation).normalized().z)), 6),
		"aim_error_deg": round(angle, 6),
	})
SCENE.frame_set(old_frame)
bpy.context.view_layer.update()
print("V124_SIDE_PROFILE_SAMPLES " + json.dumps(samples, ensure_ascii=False))
if max(item["aim_error_deg"] for item in samples) > 0.1:
	 raise RuntimeError("Camera aim is not stable across the sampled frames")
if min(item["side_alignment"] for item in samples) < 0.999:
	 raise RuntimeError("Camera drifted away from the skater's side axis")
if max(item["forward_leak"] for item in samples) > 0.05:
	 raise RuntimeError("Side camera is no longer perpendicular to torso forward")
print("V124_SIDE_PROFILE_AUDIT " + json.dumps({
	"samples": samples,
	"max_aim_error_deg": max(item["aim_error_deg"] for item in samples),
	"min_side_alignment": min(item["side_alignment"] for item in samples),
	"max_forward_leak": max(item["forward_leak"] for item in samples),
	"default_scene_objects": sorted(obj.name for obj in default_scene.objects),
}, ensure_ascii=False))
