"""Create V121 with a skater-facing follow camera; preserve all V118 geometry/motion."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v118.blend"
OUT = ASSET / "single-axel-1a-human-rink-v121.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v121-web.glb"
CAMERA_NAME = "Action skater-facing follow view v121"
TARGET_NAME = "Skater torso · animated facing target v121"

if not SOURCE.exists():
	 raise RuntimeError(f"Missing V118 source: {SOURCE}")
if OUT.exists() or WEB_OUT.exists():
	 raise RuntimeError("Refusing to overwrite an existing V121 artifact")

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = next((item for item in bpy.data.scenes
			  if item.get("prototype_version") == "v118"), None)
if scene is None:
	 raise RuntimeError("Expected the V118 Single Axel scene")
default_scene = bpy.data.scenes.get("Scene")
if default_scene is None or sorted(obj.name for obj in default_scene.objects) != ["Camera", "Cube", "Light"]:
	 raise RuntimeError("The original default Scene signature changed")
torso = scene.objects.get("Human · shaped jacket torso")
if torso is None:
	 raise RuntimeError("Missing animated torso to follow")

target = bpy.data.objects.new(TARGET_NAME, None)
scene.collection.objects.link(target)
target.empty_display_type = "SPHERE"
target.empty_display_size = 0.08
target.hide_render = True
target.parent = torso
target.matrix_parent_inverse = Matrix.Identity(4)
target.location = (0.0, 0.0, 0.22)
target.rotation_euler = (0.0, 0.0, 0.0)
target["purpose"] = "Tracks torso position and facing for a stable 3/4 inspection view."

camera_data = bpy.data.cameras.new(CAMERA_NAME)
camera = bpy.data.objects.new(CAMERA_NAME, camera_data)
scene.collection.objects.link(camera)
camera.parent = target
camera.matrix_parent_inverse = Matrix.Identity(4)
camera.location = (2.5, -6.0, 1.55)
camera_target = Vector((0.0, 0.0, 0.0))
camera.rotation_euler = (camera_target - camera.location).to_track_quat("-Z", "Y").to_euler()
camera_data.lens = 50.0
camera_data.clip_start = 0.05
camera_data.clip_end = 200.0
camera["purpose"] = "Torso-parented 3/4 follow view for checking skater and skate headings."
camera["basis"] = "Illustrative camera aid; does not alter the simulated body or skate transforms."

scene.name = "Single Axel 1A · skater-facing follow view v121"
scene["prototype_version"] = scene["version"] = "v121"
scene["v121_revision"] = (
	"Derived from V118 without changing the skater, skate geometry, animation, rink, or trajectory. "
	"Adds a camera and torso-facing target that follow the animated torso, so a fixed world-side camera "
	"does not show the skater's back during the jump. Motion and measurements remain illustrative/simulated.")
scene["illustrative_simulated"] = True
scene.camera = camera
scene.frame_set(87)
if bpy.context.window is not None:
	bpy.context.window.scene = scene
bpy.context.view_layer.update()

saved_frame = scene.frame_current
camera_samples = []
for frame in (1, 37, 60, 76, 87, 90, 121, 160):
	 scene.frame_set(frame)
	 bpy.context.view_layer.update()
	 toward = target.matrix_world.translation - camera.matrix_world.translation
	 cam_forward = camera.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))
	 camera_samples.append({
		"frame": frame,
		"camera_position": [round(value, 5) for value in camera.matrix_world.translation],
		"target_distance_m": round(toward.length, 5),
	"points_toward_target_deg": round(math.degrees(toward.angle(cam_forward)), 5),
	 })
scene.frame_set(saved_frame)
bpy.context.view_layer.update()
if max(row["points_toward_target_deg"] for row in camera_samples) > 0.01:
	 raise RuntimeError("The follow camera is not aimed at the torso across the sample frames")

bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
bpy.ops.export_scene.gltf(
	 filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
	 export_cameras=True, export_lights=False, export_yup=True,
	 use_selection=False, use_active_scene=True, use_visible=True,
	 use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
	 export_frame_step=1, export_optimize_animation_size=False)

print("V121_SKATER_FOLLOW_CAMERA " + json.dumps({
	"source": str(SOURCE), "blend": str(OUT), "web_glb": str(WEB_OUT),
	"camera": CAMERA_NAME, "target": TARGET_NAME,
	"camera_parent": camera.parent.name,
	"default_scene_objects": sorted(obj.name for obj in default_scene.objects),
	"frame_range": [scene.frame_start, scene.frame_end],
	"camera_samples": camera_samples,
	"motion_changed": False,
}, ensure_ascii=False))
