"""Render V125 front, side, and skate fit evidence without replacing V124 previews."""

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
EXPECTED = ASSET / "single-axel-1a-human-rink-v125.blend"
scene = bpy.context.scene
if Path(bpy.data.filepath).resolve() != EXPECTED.resolve() or scene.get("prototype_version") != "v125":
    raise RuntimeError(f"Expected the saved V125 scene, got {bpy.data.filepath}")
views = {
    "side": scene.camera,
    "front": scene.objects.get("Action front view"),
    "skate-closeup": scene.objects.get("Skate inspection · close view"),
}
if any(camera is None or camera.type != "CAMERA" for camera in views.values()):
    raise RuntimeError("A V125 evidence camera is missing")
old_camera = scene.camera
old_frame = scene.frame_current
old_render = (scene.render.resolution_x, scene.render.resolution_y,
              scene.render.resolution_percentage, scene.render.filepath,
              scene.render.image_settings.file_format)
scene.render.resolution_x = 1200
scene.render.resolution_y = 675
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
outputs = []
for frame, view in ((60, "side"), (76, "side"), (90, "side"),
                    (60, "front"), (76, "front"), (90, "front"),
                    (87, "skate-closeup")):
    output = ASSET / f"single-axel-1a-human-rink-v125-frame{frame:03d}-{view}.png"
    if output.exists():
        outputs.append(str(output) + " (preserved)")
        continue
    scene.frame_set(frame)
    scene.camera = views[view]
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True, scene=scene.name)
    outputs.append(str(output))
scene.camera = old_camera
scene.frame_set(old_frame)
(scene.render.resolution_x, scene.render.resolution_y,
 scene.render.resolution_percentage, scene.render.filepath,
 scene.render.image_settings.file_format) = old_render
bpy.context.view_layer.update()
print("V125_VIEW_PREVIEWS " + json.dumps(outputs, ensure_ascii=False))
