"""Render V124 side-profile, front, and skate-detail key-frame previews."""

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SCENE_FILE = ASSET / "single-axel-1a-human-rink-v124.blend"
SCENE = next((item for item in bpy.data.scenes
			  if item.get("prototype_version") == "v124"), None)
if Path(bpy.data.filepath).resolve() != SCENE_FILE.resolve() or SCENE is None:
	 raise RuntimeError(f"Expected V124 scene, got {bpy.data.filepath}")

SIDE_CAMERA = SCENE.camera
FRONT_CAMERA = SCENE.objects.get("Action front view")
SKATE_CAMERA = SCENE.objects.get("Skate inspection · close view")
if SIDE_CAMERA is None or SIDE_CAMERA.type != "CAMERA" or any(
		camera is None or camera.type != "CAMERA" for camera in (FRONT_CAMERA, SKATE_CAMERA)):
	 raise RuntimeError("V124 is missing an inspection camera")

old_camera = SCENE.camera
old_frame = SCENE.frame_current
old_render = (SCENE.render.resolution_x, SCENE.render.resolution_y,
			  SCENE.render.resolution_percentage, SCENE.render.filepath,
			  SCENE.render.image_settings.file_format)
SCENE.render.resolution_x = 1200
SCENE.render.resolution_y = 675
SCENE.render.resolution_percentage = 100
SCENE.render.image_settings.file_format = "PNG"
outputs = []
for frame, camera, view in (
		(60, SIDE_CAMERA, "side"), (76, SIDE_CAMERA, "side"), (90, SIDE_CAMERA, "side"),
		(60, FRONT_CAMERA, "front"), (76, FRONT_CAMERA, "front"), (90, FRONT_CAMERA, "front"),
		(87, SKATE_CAMERA, "skate-closeup"),
	):
	output = ASSET / f"single-axel-1a-human-rink-v124-frame{frame:03d}-{view}.png"
	if output.exists():
		outputs.append(str(output) + " (preserved existing preview)")
		continue
	SCENE.frame_set(frame)
	SCENE.camera = camera
	SCENE.render.filepath = str(output)
	bpy.ops.render.render(write_still=True, scene=SCENE.name)
	outputs.append(str(output))

SCENE.camera = old_camera
SCENE.frame_set(old_frame)
(SCENE.render.resolution_x, SCENE.render.resolution_y,
	SCENE.render.resolution_percentage, SCENE.render.filepath,
	SCENE.render.image_settings.file_format) = old_render
bpy.context.view_layer.update()
print("V124_VIEW_PREVIEWS " + json.dumps(outputs, ensure_ascii=False))
