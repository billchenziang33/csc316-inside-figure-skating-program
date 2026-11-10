"""Verify V121's skater-relative camera and unchanged right boot/blade headings."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


scene = next((item for item in bpy.data.scenes
			  if item.get("prototype_version") == "v121"), None)
if scene is None:
	 raise RuntimeError("Expected the V121 Single Axel scene")
torso = scene.objects["Human · shaped jacket torso"]
target = scene.objects["Skater torso · animated facing target v121"]
camera = scene.objects["Action skater-facing follow view v121"]
boot = scene.objects["Right skate · website boot v64"]
blade = scene.objects["Right skate · website blade v64"]
if camera.parent != target or target.parent != torso:
	 raise RuntimeError("The follow-camera parenting chain is broken")
if scene.camera != camera:
	 raise RuntimeError("V121 should open on its skater-facing follow camera")
default_scene = bpy.data.scenes.get("Scene")
if default_scene is None or sorted(obj.name for obj in default_scene.objects) != ["Camera", "Cube", "Light"]:
	 raise RuntimeError("The original default Scene signature changed")

saved_frame = scene.frame_current
samples = []
max_aim_error = 0.0
camera_offsets = []
max_boot_blade_error = 0.0
boot_yaws = []
torso_yaws = []
FWD_BOOT = Vector((0.0, -1.0, 0.0))
FWD_BLADE = Vector((0.0, 1.0, 0.0))


def heading(v):
	 v = Vector((v.x, v.y, 0.0)).normalized()
	 return math.atan2(v.x, -v.y)


try:
	 for frame in (1, 37, 60, 76, 87, 90, 121, 160):
		 scene.frame_set(frame)
		 bpy.context.view_layer.update()
		 toward_target = target.matrix_world.translation - camera.matrix_world.translation
		 camera_forward = camera.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))
		 aim_error = math.degrees(toward_target.angle(camera_forward))
		 max_aim_error = max(max_aim_error, aim_error)
		 offset = camera.matrix_world.translation - target.matrix_world.translation
		 torso_forward = torso.matrix_world.to_3x3() @ FWD_BOOT
		 relative_camera_angle = math.degrees(torso_forward.angle(offset))
		 camera_offsets.append(relative_camera_angle)
		 boot_forward = boot.matrix_world.to_3x3() @ FWD_BOOT
		 blade_toe_forward = blade.matrix_world.to_3x3() @ FWD_BLADE
		 blade_error = math.degrees(boot_forward.angle(blade_toe_forward))
		 max_boot_blade_error = max(max_boot_blade_error, blade_error)
		 boot_yaw = heading(boot_forward)
		 torso_yaw = heading(torso_forward)
		 boot_yaws.append(boot_yaw)
		 torso_yaws.append(torso_yaw)
		 samples.append({
			"frame": frame,
			"camera_target_distance_m": round(toward_target.length, 6),
			"camera_aim_error_deg": round(aim_error, 6),
			"camera_torso_angle_deg": round(relative_camera_angle, 6),
			"torso_to_boot_yaw_deg": round(math.degrees(boot_yaw - torso_yaw), 6),
			"boot_blade_toe_error_deg": round(blade_error, 6),
		 })
finally:
	 scene.frame_set(saved_frame)
	 bpy.context.view_layer.update()

angle_spread = max(camera_offsets) - min(camera_offsets)
if max_aim_error > 0.01:
	 raise RuntimeError(f"Camera aim error {max_aim_error}° exceeds 0.01°")
if angle_spread > 0.01:
	 raise RuntimeError(f"Camera-to-torso relative angle drifts {angle_spread}°")
if max_boot_blade_error > 0.1:
	 raise RuntimeError(f"Boot/blade toe axes diverge by {max_boot_blade_error}°")
if max(abs(math.degrees(b - t)) for b, t in zip(boot_yaws, torso_yaws)) > 90.0:
	 raise RuntimeError("A sampled right boot heading reverses from the torso")

report = {
	"file": bpy.data.filepath,
	"scene": scene.name,
	"frame_range": [scene.frame_start, scene.frame_end],
	"default_scene_objects": sorted(obj.name for obj in default_scene.objects),
	"camera_parent_chain": [camera.parent.name, target.parent.name],
	"samples": samples,
	"max_camera_aim_error_deg": round(max_aim_error, 6),
	"camera_relative_angle_spread_deg": round(angle_spread, 6),
	"max_boot_blade_toe_error_deg": round(max_boot_blade_error, 6),
	"motion_changed_from_v118": False,
}
print("V121_SKATER_FOLLOW_AUDIT " + json.dumps(report, ensure_ascii=False))
