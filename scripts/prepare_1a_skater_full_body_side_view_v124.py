"""Center a side-profile camera on the skater's full body; preserve V123 motion."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v123.blend"
OUTPUT = ASSET / "single-axel-1a-human-rink-v124.blend"
WEB_OUTPUT = ASSET / "single-axel-1a-human-rink-v124-web.glb"
SCENE_NAME = "Single Axel 1A · full-body side view v124"
CAMERA_NAME = "Action skater side profile full-body v124"
TARGET_NAME = "Skater pelvis · side-view composition target v124"
TORSO_NAME = "Human · shaped jacket torso"

if not SOURCE.exists():
	 raise RuntimeError(f"Missing source scene: {SOURCE}")
if OUTPUT.exists() or WEB_OUTPUT.exists():
	 raise RuntimeError("Refusing to overwrite an existing V124 artifact")

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = next((item for item in bpy.data.scenes
			  if item.get("prototype_version") == "v123"), None)
if scene is None:
	 raise RuntimeError("Expected the saved V123 Single Axel scene")
torso = scene.objects.get(TORSO_NAME)
source_camera = scene.camera
if torso is None or source_camera is None or source_camera.type != "CAMERA":
	 raise RuntimeError("Missing the V123 torso or side-profile camera")
default_scene = bpy.data.scenes.get("Scene")
if default_scene is None or sorted(obj.name for obj in default_scene.objects) != ["Camera", "Cube", "Light"]:
	 raise RuntimeError("The original default Scene signature changed")

target = bpy.data.objects.new(TARGET_NAME, None)
scene.collection.objects.link(target)
target.empty_display_type = "SPHERE"
target.empty_display_size = 0.07
target.hide_render = True
target.parent = torso
target.location = (0.0, 0.0, -0.35)
target["purpose"] = "Centers a full-body profile framing from skates to head."

data = source_camera.data.copy()
data.name = CAMERA_NAME
camera = bpy.data.objects.new(CAMERA_NAME, data)
scene.collection.objects.link(camera)
camera.parent = target
camera.location = (6.0, 0.0, 1.1)
camera.rotation_euler = (Vector((0.0, 0.0, 0.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera["purpose"] = "Horizontal side profile, centered on the whole skater through body turns."

scene.camera = camera
scene.name = SCENE_NAME
scene["prototype_version"] = "v124"
scene["change_summary"] = "V123 motion unchanged; the side-profile camera now follows a lower full-body target."
scene.frame_set(1)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("V124_FULL_BODY_SIDE " + json.dumps({
	"source": str(SOURCE), "blend": str(OUTPUT),
	"scene": scene.name, "camera": scene.camera.name,
	"target_local_position": list(target.location),
	"camera_local_position": list(camera.location),
	"objects": len(scene.objects),
	"frame_range": [scene.frame_start, scene.frame_end],
	"default_scene_objects": sorted(obj.name for obj in default_scene.objects),
}, ensure_ascii=False))
