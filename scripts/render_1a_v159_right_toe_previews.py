"""Render V159 right-skate toe-direction review images from saved camera presets."""

import json
from pathlib import Path

import bpy


ASSET = Path(__file__).resolve().parents[1] / "static" / "movement" / "axel-1a-prototype"
EXPECTED = ASSET / "single-axel-1a-human-rink-v159.blend"
scene = bpy.context.scene
if Path(bpy.data.filepath).resolve() != EXPECTED.resolve() or scene.get("prototype_version") != "v159":
    raise RuntimeError(f"Expected saved V159, got {bpy.data.filepath}")

views = {
    "side": scene.objects["Action skater side profile full-body v124"],
    "front": scene.objects["Action front view"],
    "skate-closeup": scene.objects["Skate inspection · close view"],
}
old_camera = scene.camera
old_frame = scene.frame_current
old_engine = scene.render.engine
old_render = (scene.render.resolution_x, scene.render.resolution_y,
              scene.render.resolution_percentage, scene.render.filepath,
              scene.render.image_settings.file_format)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 900, 506
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
outputs = []
for frame, view in ((79, "front"), (79, "skate-closeup"), (92, "side"),
                    (92, "front"), (136, "front")):
    output = ASSET / f"single-axel-1a-human-rink-v159-frame{frame:03d}-{view}.png"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
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
print("V159_RIGHT_TOE_RENDERS " + json.dumps(outputs, ensure_ascii=False))
