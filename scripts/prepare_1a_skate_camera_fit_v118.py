"""Create V118 from V117 with a wider, camera-fit skate inspection lens."""

import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v117.blend"
OUT = ASSET / "single-axel-1a-human-rink-v118.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v118-web.glb"
CAMERA_NAME = "Skate inspection · close view"

if not SOURCE.exists():
	raise RuntimeError(f"Missing V117 source: {SOURCE}")
if OUT.exists() or WEB_OUT.exists():
	raise RuntimeError("Refusing to overwrite an existing V118 artifact")

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = next((item for item in bpy.data.scenes
			  if item.get("prototype_version") == "v117"), None)
if scene is None:
	raise RuntimeError("Expected the V117 Single Axel scene")
default_scene = bpy.data.scenes.get("Scene")
if default_scene is None or sorted(obj.name for obj in default_scene.objects) != ["Camera", "Cube", "Light"]:
	raise RuntimeError("The original default Scene signature changed")

camera = scene.objects.get(CAMERA_NAME)
if camera is None or camera.type != "CAMERA":
	raise RuntimeError(f"Missing skate inspection camera: {CAMERA_NAME}")
old_lens = camera.data.lens
camera.data.lens = 28.0
scene.name = "Single Axel 1A · skate inspection framing v118"
scene["prototype_version"] = scene["version"] = "v118"
scene["v118_revision"] = (
	"Derived from V117 without changing the skater, skate meshes, animation, rink, or trajectory. "
	"The Blender skate-inspection camera uses a wider lens; the web viewer fits the animated boot "
	"and blade bounding sphere into the perspective frustum with a responsive aspect-aware margin. "
	"All motion and measurements remain illustrative/simulated.")
scene["illustrative_simulated"] = True
scene.frame_set(90)
bpy.context.window.scene = scene
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
bpy.ops.export_scene.gltf(
	filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
	export_cameras=True, export_lights=False, export_yup=True,
	use_selection=False, use_active_scene=True, use_visible=True,
	use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
	export_frame_step=1, export_optimize_animation_size=False)

print("V118_CAMERA_FIT_BUILD " + json.dumps({
	"source": str(SOURCE), "blend": str(OUT), "web_glb": str(WEB_OUT),
	"source_camera_lens_mm": old_lens,
	"v118_camera_lens_mm": camera.data.lens,
	"v118_camera_fov_deg": round(math.degrees(camera.data.angle_y), 4),
	"frame_range": [scene.frame_start, scene.frame_end],
	"frame_rate": scene.render.fps / scene.render.fps_base,
	"default_scene_objects": sorted(obj.name for obj in default_scene.objects),
	"animation_action_count": len({obj.animation_data.action for obj in scene.objects
									 if obj.animation_data and obj.animation_data.action}),
	"scene_objects": len(scene.objects),
}, ensure_ascii=False))
