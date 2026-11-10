"""Render V118 side/front action and skate-close-up review images."""

from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SCENE_FILE = ASSET / "single-axel-1a-human-rink-v118.blend"
SCENE = next((item for item in bpy.data.scenes
			  if item.get("prototype_version") == "v118"), None)
if Path(bpy.data.filepath).resolve() != SCENE_FILE.resolve() or SCENE is None:
	raise RuntimeError(f"Expected V118 scene, got {bpy.data.filepath}")

PREVIEWS = (
	(60, "Action side view · horizontal follow composition", "frame060-side"),
	(76, "Action side view · horizontal follow composition", "frame076-side"),
	(82, "Action side view · horizontal follow composition", "frame082-side"),
	(90, "Action side view · horizontal follow composition", "frame090-side"),
	(60, "Action front view", "frame060-front"),
	(76, "Action front view", "frame076-front"),
	(90, "Action front view", "frame090-front"),
	(87, "Skate inspection · close view", "frame087-skate-closeup-web"),
)
old_camera = SCENE.camera
old_render = (SCENE.render.resolution_x, SCENE.render.resolution_y,
			  SCENE.render.resolution_percentage, SCENE.render.filepath,
			  SCENE.render.image_settings.file_format)
SCENE.render.resolution_x = 1200
SCENE.render.resolution_y = 675
SCENE.render.resolution_percentage = 100
SCENE.render.image_settings.file_format = "PNG"

outputs = []
for frame, camera_name, suffix in PREVIEWS:
	output = ASSET / f"single-axel-1a-human-rink-v118-{suffix}.png"
	if output.exists():
		outputs.append(str(output) + " (preserved existing preview)")
		continue
	SCENE.frame_set(frame)
	SCENE.camera = SCENE.objects[camera_name]
	SCENE.render.filepath = str(output)
	hidden = []
	if suffix.endswith("skate-closeup-web"):
		for obj in SCENE.objects:
			if obj.name.startswith("V102"):
				hidden.append((obj, obj.hide_render))
				obj.hide_render = True
	bpy.ops.render.render(write_still=True, scene=SCENE.name)
	for obj, was_hidden in hidden:
		obj.hide_render = was_hidden
	outputs.append(str(output))

SCENE.camera = old_camera
(SCENE.render.resolution_x, SCENE.render.resolution_y,
	SCENE.render.resolution_percentage, SCENE.render.filepath,
	SCENE.render.image_settings.file_format) = old_render
SCENE.frame_set(90)
bpy.context.view_layer.update()
print("V118_SHOWCASE_PREVIEWS " + repr(outputs))
