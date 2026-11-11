"""Render V169 key poses for visual review before any website wiring."""

import json
from pathlib import Path

import bpy


ASSET = Path(__file__).resolve().parents[1] / "static" / "movement" / "axel-1a-prototype"
EXPECTED = ASSET / "single-axel-1a-human-rink-v169.blend"
scene = bpy.context.scene
if Path(bpy.data.filepath).resolve() != EXPECTED.resolve() or scene.get("prototype_version") != "v169":
    raise RuntimeError(f"Expected saved V169, got {bpy.data.filepath}")

views = {
    "side": scene.objects["Action skater side profile full-body v124"],
    "front": scene.objects["Action front view"],
}
old_camera = scene.camera
old_frame = scene.frame_current
old_engine = scene.render.engine
old_render = (scene.render.resolution_x, scene.render.resolution_y,
              scene.render.resolution_percentage, scene.render.filepath,
              scene.render.image_settings.file_format)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
outputs = []
for frame, view in ((47, "side"), (70, "side"), (87, "side"),
                    (92, "side"), (156, "side"), (156, "front")):
    output = ASSET / f"single-axel-1a-human-rink-v169-frame{frame:03d}-{view}.png"
    if output.exists():
        continue
    scene.frame_set(frame)
    scene.camera = views[view]
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True, scene=scene.name)
    outputs.append(str(output))

scene.camera = old_camera
scene.frame_set(old_frame)
scene.render.engine = old_engine
(scene.render.resolution_x, scene.render.resolution_y,
 scene.render.resolution_percentage, scene.render.filepath,
 scene.render.image_settings.file_format) = old_render
bpy.context.view_layer.update()
print("V169_ALIGNMENT_RENDERS " + json.dumps(outputs, ensure_ascii=False))
