"""Render V121 at takeoff, apex, right-skate alignment, landing and exit."""

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SCENE_FILE = ASSET / "single-axel-1a-human-rink-v121.blend"
SCENE = next((item for item in bpy.data.scenes
			  if item.get("prototype_version") == "v121"), None)
if Path(bpy.data.filepath).resolve() != SCENE_FILE.resolve() or SCENE is None:
	 raise RuntimeError(f"Expected V121 scene, got {bpy.data.filepath}")

FOLLOW_CAMERA = SCENE.objects.get("Action skater-facing follow view v121")
FRONT_CAMERA = SCENE.objects.get("Action front view")
if FOLLOW_CAMERA is None or FOLLOW_CAMERA.type != "CAMERA":
	 raise RuntimeError("The V121 skater-follow camera is missing")
if FRONT_CAMERA is None or FRONT_CAMERA.type != "CAMERA":
	 raise RuntimeError("The preserved V118 front camera is missing")

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
for frame, camera, suffix in (
		(60, FOLLOW_CAMERA, "takeoff"),
		(76, FOLLOW_CAMERA, "apex"),
		(87, FOLLOW_CAMERA, "right-skate-check"),
		(90, FOLLOW_CAMERA, "landing"),
		(121, FOLLOW_CAMERA, "exit"),
		(60, FRONT_CAMERA, "front"),
		(76, FRONT_CAMERA, "front"),
		(90, FRONT_CAMERA, "front"),
	):
	 output = ASSET / f"single-axel-1a-human-rink-v121-frame{frame:03d}-{suffix}.png"
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
print("V121_SKATER_FOLLOW_PREVIEWS " + json.dumps(outputs, ensure_ascii=False))
