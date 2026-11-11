"""Render V153 take-off and apex for the prototype showcase."""

from pathlib import Path

import bpy


ASSET = Path(__file__).resolve().parents[1] / "static" / "movement" / "axel-1a-prototype"
EXPECTED = ASSET / "single-axel-1a-human-rink-v153.blend"
scene = bpy.context.scene
if Path(bpy.data.filepath).resolve() != EXPECTED.resolve() or scene.get("prototype_version") != "v153":
    raise RuntimeError(f"Expected saved V153, got {bpy.data.filepath}")
views = {
    "side": scene.objects["Action skater side profile full-body v124"],
    "front": scene.objects["Action front view"],
}
old_camera = scene.camera
old_frame = scene.frame_current
old_render = (scene.render.resolution_x, scene.render.resolution_y,
              scene.render.resolution_percentage, scene.render.filepath,
              scene.render.image_settings.file_format)
scene.render.resolution_x, scene.render.resolution_y = 1200, 675
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
for frame, view in ((60, "side"), (60, "front"), (76, "side"), (76, "front")):
    output = ASSET / f"single-axel-1a-human-rink-v153-frame{frame:03d}-{view}.png"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    scene.frame_set(frame)
    scene.camera = views[view]
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True, scene=scene.name)
scene.camera = old_camera
scene.frame_set(old_frame)
(scene.render.resolution_x, scene.render.resolution_y,
 scene.render.resolution_percentage, scene.render.filepath,
 scene.render.image_settings.file_format) = old_render
bpy.context.view_layer.update()
