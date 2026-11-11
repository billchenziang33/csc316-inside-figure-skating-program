"""Derive V152 from V151 and align the Landing event to sampled blade contact."""

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v151.blend"
OUT = ASSET / "single-axel-1a-human-rink-v152.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v152-web.glb"
LANDING_FRAME = 93


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(),
            f"Expected V151 source, got {bpy.data.filepath}")
    require(not OUT.exists() and not WEB_OUT.exists(),
            "Refusing to overwrite an existing V152 artifact")
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    require(scene.get("prototype_version") == "v151",
            "Expected V151 source scene")
    default_scene = bpy.data.scenes.get("Scene")
    require(default_scene is not None and
            sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
            "The original default Scene signature changed")

    marker = scene.objects.get("V102_EVENT_LANDING_FRAME_90")
    guide = scene.objects.get("V102 · vertical guide · landing")
    root = scene.objects.get("Skater root · simulated travel and 1.5-turn yaw v8")
    require(marker and guide and root, "Landing marker, guide, or skater root is missing")
    require(scene.objects.get("V102_EVENT_LANDING_FRAME_93") is None,
            "The V152 landing marker name is already in use")

    scene.frame_set(LANDING_FRAME)
    bpy.context.view_layer.update()
    touchdown_x = root.matrix_world.translation.x
    for obj in (marker, guide):
        world = obj.matrix_world.copy()
        world.translation.x = touchdown_x
        obj.matrix_world = world
    marker.name = "V102_EVENT_LANDING_FRAME_93"

    scene.name = "Single Axel 1A · touchdown-aligned landing v152"
    scene["prototype_version"] = scene["version"] = "v152"
    scene["landing_event_frame_v152"] = LANDING_FRAME
    scene["landing_event_alignment_v152"] = (
        "Derived from V151 without changing body pose or root animation. The simulated landing "
        "event and its rink guide are moved from frame 90 to frame 93, where the model-right "
        "support blade first reaches 1.96 mm above the measured ice top in the 1/16-frame audit. "
        "The left free-leg skate remains airborne. Event timing and all motion are illustrative/simulated.")
    scene["illustrative_simulated"] = True

    scene.frame_set(LANDING_FRAME)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
    bpy.ops.export_scene.gltf(
        filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
        export_cameras=True, export_lights=False, export_yup=True,
        use_selection=False, use_active_scene=True, use_visible=True,
        use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
        export_frame_step=1, export_optimize_animation_size=False)

    print("LANDING_EVENT_V152 " + json.dumps({
        "source": str(SOURCE), "blend": str(OUT), "web_glb": str(WEB_OUT),
        "prototype_version": scene.get("prototype_version"),
        "landing_frame": LANDING_FRAME,
        "landing_marker": marker.name,
        "guide_x_m": round(touchdown_x, 6),
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
        "status": "illustrative/simulated candidate; awaiting touchdown audit",
    }, ensure_ascii=False))


main()
