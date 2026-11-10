"""Flip each visible runner's asymmetric toe-pick end forward and refit it."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v124.blend"
OUTPUT = ASSET / "single-axel-1a-human-rink-v125.blend"
WEB_OUTPUT = ASSET / "single-axel-1a-human-rink-v125-web.glb"
SCENE_NAME = "Single Axel 1A · blade toe corrected v125"

if not SOURCE.exists():
    raise RuntimeError(f"Missing source scene: {SOURCE}")
if OUTPUT.exists() or WEB_OUTPUT.exists():
    raise RuntimeError("Refusing to overwrite an existing V125 artifact")

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = next((item for item in bpy.data.scenes
              if item.get("prototype_version") == "v124"), None)
if scene is None or bpy.context.scene != scene:
    raise RuntimeError("Expected the active V124 Single Axel scene")
default_scene = bpy.data.scenes.get("Scene")
if default_scene is None or sorted(obj.name for obj in default_scene.objects) != ["Camera", "Cube", "Light"]:
    raise RuntimeError("The original default Scene signature changed")
if scene.camera is None or scene.camera.name != "Action skater side profile full-body v124":
    raise RuntimeError("V124 did not open on its full-body side camera")

old_frame = scene.frame_current
old_subframe = scene.frame_subframe
changes = {}
for side in ("Left", "Right"):
    blade = scene.objects[f"{side} skate · website blade v64"]
    boot = scene.objects[f"{side} skate · website boot v64"]
    anchor = scene.objects[f"{side} skate · exact website fit v64"]
    if blade.parent != anchor or boot.parent != anchor:
        raise RuntimeError(f"{side} boot and blade no longer share the fitted ankle anchor")
    if blade.animation_data and blade.animation_data.action:
        raise RuntimeError(f"{side} blade already has an object-level action")

    # The source runner's asymmetric pick teeth are at the heel side. Reflect
    # its longitudinal profile about its own midpoint before refitting it.
    blade.data = blade.data.copy()
    source_y = [vertex.co.y for vertex in blade.data.vertices]
    y_mid = (min(source_y) + max(source_y)) * 0.5
    for vertex in blade.data.vertices:
        vertex.co.y = 2.0 * y_mid - vertex.co.y
    blade.data.update()

    scene.frame_set(90)
    bpy.context.view_layer.update()
    anchor_origin = anchor.matrix_world.translation
    toe_axis = (boot.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0))).normalized()

    def quantile_extents(obj, axis):
        values = sorted(((obj.matrix_world @ vertex.co) - anchor_origin).dot(axis)
                        for vertex in obj.data.vertices)
        low = values[math.floor(0.005 * (len(values) - 1))]
        high = values[math.ceil(0.995 * (len(values) - 1))]
        return high, low

    boot_toe, boot_heel = quantile_extents(boot, toe_axis)
    blade_toe, blade_heel = quantile_extents(blade, toe_axis)
    shift_y = ((boot_toe + boot_heel) - (blade_toe + blade_heel)) * 0.5

    # The refit is along the skate's own longitudinal axis. Add a per-frame
    # parent-space translation that cancels only its world-Z component. This
    # preserves the existing blade/ice height while the generic ankle pitches.
    for vertex in blade.data.vertices:
        vertex.co.y += shift_y
    blade.data.update()
    base_location = blade.location.copy()
    blade["prototype_version"] = "v125"
    blade["toe_pick_mirrored_to_boot_toe"] = True
    blade["toe_refit_shift_local_y_m"] = shift_y
    blade["toe_refit_source"] = "v124 visible mesh geometry, reflected and recentered to boot extents"
    blade["vertical_fit_correction"] = "Simulated per-frame support-height compensation; not measured biomechanics"

    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        y_world = blade.matrix_world.to_3x3() @ Vector((0.0, shift_y, 0.0))
        correction_world = Vector((0.0, 0.0, -y_world.z))
        correction_parent = blade.parent.matrix_world.to_3x3().inverted() @ correction_world
        blade.location = base_location + correction_parent
        blade.keyframe_insert(data_path="location", frame=frame, group="V125 blade vertical fit")

    changes[side] = {
        "source_boot_extents_m": [boot_heel, boot_toe],
        "source_reflected_blade_extents_m": [blade_heel, blade_toe],
        "longitudinal_center_shift_m": shift_y,
        "vertices": len(blade.data.vertices),
        "animation_keys_per_axis": scene.frame_end - scene.frame_start + 1,
    }

scene.frame_set(90)
scene.name = SCENE_NAME
scene["prototype_version"] = "v125"
scene["change_summary"] = (
    "Both visible runner meshes now face their sculpted toe-pick ends toward the boot toes "
    "and are longitudinally centered to boot extents. Per-frame simulated vertical fit "
    "compensation preserves the prior blade/ice height over the generic animation."
)
scene["technical_reference_limit"] = (
    "Axel phase references guide illustrative pose review; the 22-joint pose sequence "
    "contains no measured skate orientation, edge, or contact data."
)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

if WEB_OUTPUT.exists():
    raise RuntimeError(f"Refusing to overwrite web export: {WEB_OUTPUT}")
bpy.ops.export_scene.gltf(
    filepath=str(WEB_OUTPUT), export_format="GLB", export_animations=True,
    export_cameras=True, export_lights=False, export_yup=True,
    use_selection=False, use_active_scene=True, use_visible=True,
    use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
    export_frame_step=1, export_optimize_animation_size=False)

report = {
    "source": str(SOURCE), "blend": str(OUTPUT), "web_glb": str(WEB_OUTPUT),
    "scene": scene.name, "version": scene.get("prototype_version"),
    "changes": changes, "frame_range": [scene.frame_start, scene.frame_end],
    "camera": scene.camera.name,
    "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
    "pose_and_fit_status": "illustrative/simulated",
}
print("V125_BLADE_TOE_DIRECTION " + json.dumps(report, ensure_ascii=False))
