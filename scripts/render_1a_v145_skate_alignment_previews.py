"""Render new V145 review frames without replacing any existing image."""

import json
from pathlib import Path

import bpy


ASSET = Path(__file__).resolve().parents[1] / "static" / "movement" / "axel-1a-prototype"
EXPECTED = ASSET / "single-axel-1a-human-rink-v145.blend"
scene = bpy.context.scene
if Path(bpy.data.filepath).resolve() != EXPECTED.resolve() or scene.get("prototype_version") != "v145":
    raise RuntimeError(f"Expected the saved V145 scene, got {bpy.data.filepath}")
views = {
    "side": scene.objects.get("Action skater side profile full-body v124"),
    "front": scene.objects.get("Action front view"),
    "skate-closeup": scene.objects.get("Skate inspection · close view"),
}
if any(camera is None or camera.type != "CAMERA" for camera in views.values()):
    raise RuntimeError("A V141 review camera is missing")
old_camera = scene.camera
old_frame = scene.frame_current
old_render = (scene.render.resolution_x, scene.render.resolution_y,
              scene.render.resolution_percentage, scene.render.filepath,
              scene.render.image_settings.file_format)
scene.render.resolution_x, scene.render.resolution_y = 1200, 675
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
outputs = []
for frame, view in ((87, "side"), (90, "side"), (90, "front"), (90, "skate-closeup")):
    output = ASSET / f"single-axel-1a-human-rink-v145-frame{frame:03d}-{view}.png"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
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
print("V145_REVIEW_RENDERS " + json.dumps(outputs, ensure_ascii=False))
