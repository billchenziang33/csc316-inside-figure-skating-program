"""Render V108 phase previews from its saved Blender scene."""

from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SCENE_FILE = ASSET / "single-axel-1a-human-rink-v108.blend"

PREVIEWS = (
    (60, "Action side view · horizontal follow composition", "takeoff-side"),
    (76, "Action side view · horizontal follow composition", "apex-side"),
    (90, "Action side view · horizontal follow composition", "landing-side"),
    (60, "Action front view", "takeoff-front"),
    (76, "Action front view", "apex-front"),
    (90, "Action front view", "landing-front"),
    (86, "Skate inspection · close view", "skate-closeup"),
)

scene = bpy.context.scene
if Path(bpy.data.filepath).resolve() != SCENE_FILE.resolve():
    raise RuntimeError(f"Expected V108 file, got {bpy.data.filepath}")
if scene.get("prototype_version") != "v108":
    raise RuntimeError(f"Expected V108 scene, got {scene.get('prototype_version')}")

old_render = (scene.render.resolution_x, scene.render.resolution_y,
              scene.render.resolution_percentage, scene.render.filepath, scene.camera)
scene.render.resolution_x, scene.render.resolution_y = 1496, 840
scene.render.resolution_percentage = 100
outputs = []
for frame, camera_name, suffix in PREVIEWS:
    output = ASSET / f"single-axel-1a-human-rink-v108-{suffix}.png"
    if output.exists():
        raise RuntimeError(f"Refusing to overwrite {output}")
    scene.frame_set(frame)
    scene.camera = scene.objects[camera_name]
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    outputs.append(str(output))

(scene.render.resolution_x, scene.render.resolution_y,
 scene.render.resolution_percentage, scene.render.filepath, scene.camera) = old_render
scene.frame_set(76)
bpy.context.view_layer.update()
print("V108_SHOWCASE_PREVIEWS " + repr(outputs))
