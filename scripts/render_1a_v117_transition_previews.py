"""Render V117 transition frames for visual review and the project site."""

from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SCENE_FILE = ASSET / "single-axel-1a-human-rink-v117.blend"
PREVIEWS = (
    (76, "Action side view · horizontal follow composition", "frame076-side"),
    (82, "Action side view · horizontal follow composition", "frame082-side"),
    (84, "Action side view · horizontal follow composition", "frame084-side"),
    (90, "Action side view · horizontal follow composition", "frame090-side"),
    (82, "Action front view", "frame082-front"),
    (90, "Action front view", "frame090-front"),
)

scene = bpy.context.scene
if Path(bpy.data.filepath).resolve() != SCENE_FILE.resolve():
    raise RuntimeError(f"Expected V117 file, got {bpy.data.filepath}")
if scene.get("prototype_version") != "v117":
    raise RuntimeError(f"Expected V117 scene, got {scene.get('prototype_version')}")

old_render = (scene.render.resolution_x, scene.render.resolution_y,
              scene.render.resolution_percentage, scene.render.filepath, scene.camera)
scene.render.resolution_x, scene.render.resolution_y = 1200, 675
scene.render.resolution_percentage = 100
outputs = []
for frame, camera_name, suffix in PREVIEWS:
    output = ASSET / f"single-axel-1a-human-rink-v117-{suffix}.png"
    if output.exists():
        outputs.append(str(output) + " (preserved existing preview)")
        continue
    scene.frame_set(frame)
    scene.camera = scene.objects[camera_name]
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    outputs.append(str(output))

(scene.render.resolution_x, scene.render.resolution_y,
 scene.render.resolution_percentage, scene.render.filepath, scene.camera) = old_render
scene.frame_set(90)
bpy.context.view_layer.update()
print("V117_TRANSITION_PREVIEWS " + repr(outputs))
