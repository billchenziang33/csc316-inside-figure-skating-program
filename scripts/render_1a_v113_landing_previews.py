"""Render phase and skate views from the saved V113 Blender scene."""

from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SCENE_FILE = ASSET / "single-axel-1a-human-rink-v113.blend"
PREVIEWS = (
    (37, "Action side view · horizontal follow composition", "frame037-side"),
    (76, "Action side view · horizontal follow composition", "apex-side"),
    (87, "Action side view · horizontal follow composition", "frame087-side"),
    (90, "Action side view · horizontal follow composition", "frame090-side"),
    (90, "Action front view", "frame090-front"),
    (150, "Action side view · horizontal follow composition", "frame150-side"),
    (150, "Skate inspection · close view", "frame150-skate-closeup"),
)

scene = bpy.context.scene
if Path(bpy.data.filepath).resolve() != SCENE_FILE.resolve():
    raise RuntimeError(f"Expected V113 file, got {bpy.data.filepath}")
if scene.get("prototype_version") != "v113":
    raise RuntimeError(f"Expected V113 scene, got {scene.get('prototype_version')}")

old_render = (scene.render.resolution_x, scene.render.resolution_y,
              scene.render.resolution_percentage, scene.render.filepath, scene.camera)
scene.render.resolution_x, scene.render.resolution_y = 1496, 840
scene.render.resolution_percentage = 100
outputs = []
for frame, camera_name, suffix in PREVIEWS:
    output = ASSET / f"single-axel-1a-human-rink-v113-{suffix}.png"
    if output.exists():
        raise RuntimeError(f"Refusing to overwrite {output}")
    scene.frame_set(frame)
    scene.camera = scene.objects[camera_name]
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    outputs.append(str(output))

(scene.render.resolution_x, scene.render.resolution_y,
 scene.render.resolution_percentage, scene.render.filepath, scene.camera) = old_render
scene.frame_set(90)
bpy.context.view_layer.update()
print("V113_LANDING_PREVIEWS " + repr(outputs))
