"""Refine the right-skate heading into landing and exit (V113)."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v110.blend"
OUT = ASSET / "single-axel-1a-human-rink-v113.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v113-web.glb"
FORWARD_LOCAL = Vector((0.0, -1.0, 0.0))
WORLD_UP = Vector((0.0, 0.0, 1.0))
ANCHOR_LOCAL = Vector((0.0, 0.045, 0.035)) * 1.8
RAMP_START, RAMP_END = 82.0, 90.0
LANDING_MAX_OFFSET = 15.0


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def horizontal(vector):
    result = Vector((vector.x, vector.y, 0.0))
    return result.normalized() if result.length > 1e-8 else None


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    require(a is not None and b is not None, "Degenerate horizontal heading")
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def channelbag(obj):
    action = obj.animation_data.action
    slot = obj.animation_data.action_slot
    require(action is not None and slot is not None,
            f"{obj.name} has no layered animation action/slot")
    for layer in action.layers:
        for strip in layer.strips:
            if strip.type == "KEYFRAME":
                bag = strip.channelbag(slot)
                if bag is not None:
                    return bag
    raise RuntimeError(f"No keyframe channel bag for {obj.name}")


def isolate_action(obj):
    animation = obj.animation_data
    action = animation.action
    if action.users <= 1:
        return
    identifier = animation.action_slot.identifier
    action = action.copy()
    animation.action = action
    slot = next((item for item in action.slots if item.identifier == identifier), None)
    require(slot is not None, f"Copied action lost slot {identifier!r}")
    animation.action_slot = slot


def main():
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(),
            f"Expected V110 source, got {bpy.data.filepath}")
    require(not OUT.exists() and not WEB_OUT.exists(),
            "Refusing to overwrite an existing V113 artifact")
    scene = bpy.context.scene
    require(scene.get("prototype_version") == "v110",
            f"Expected V110 scene, got {scene.get('prototype_version')}")
    default_scene = bpy.data.scenes.get("Scene")
    require(default_scene is not None and
            sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
            "The original default Scene signature changed")
    require((scene.frame_start, scene.frame_end, scene.render.fps) == (1, 160, 12),
            "Unexpected animation timing")

    skate = scene.objects["Right skate · exact website fit v64"]
    boot = scene.objects["Right skate · website boot v64"]
    blade = scene.objects["Right skate · website blade v64"]
    ankle = scene.objects["Human · right ankle joint"]
    head = scene.objects["Head · detailed generic human sculpt"]
    nose = scene.objects["Head · nose tip"]
    left_shoulder = scene.objects["Human · left shoulder volume"]
    right_shoulder = scene.objects["Human · right shoulder volume"]
    pelvis = scene.objects["Human · pelvic/waist volume"]
    require(skate.parent == ankle and boot.parent == skate and blade.parent == skate,
            "Right boot/blade hierarchy or ankle attachment changed")

    samples = []
    count = round((scene.frame_end - scene.frame_start) * 4)
    for index in range(count + 1):
        frame = scene.frame_start + index * 0.25
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        ankle_world = ankle.matrix_world.translation.copy()
        world_matrix = skate.matrix_world.copy()
        anchor_local = world_matrix.inverted() @ (boot.matrix_world @ ANCHOR_LOCAL)
        require((boot.matrix_world @ ANCHOR_LOCAL - ankle_world).length < 1e-5,
                f"V110 boot reference differs from ankle at frame {frame:.2f}")
        across = horizontal(right_shoulder.matrix_world.translation -
                            left_shoulder.matrix_world.translation)
        up = (head.matrix_world.translation - pelvis.matrix_world.translation).normalized()
        torso = horizontal(across.cross(up)) if across is not None else None
        face = horizontal(nose.matrix_world.translation - head.matrix_world.translation)
        require(torso is not None and face is not None,
                f"Degenerate torso/face heading at frame {frame:.2f}")
        if torso.dot(face) < 0.0:
            torso.negate()
        samples.append({
            "frame": frame, "ankle": ankle_world, "anchor_local": anchor_local,
            "scale": world_matrix.to_scale(),
            "rotation": world_matrix.to_quaternion().normalized(),
            "torso": torso,
            "heading": horizontal(world_matrix.to_3x3() @ FORWARD_LOCAL),
        })

    isolate_action(skate)
    max_before = max_after = max_anchor_error_mm = 0.0
    key_rows = []
    previous_rotation = None
    for sample in samples:
        frame = sample["frame"]
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        before = signed_angle(sample["torso"], sample["heading"])
        progress = smoothstep((frame - RAMP_START) / (RAMP_END - RAMP_START))
        limit = LANDING_MAX_OFFSET
        if frame < RAMP_START:
            correction = 0.0
        else:
            # Fade in a stricter torso-heading constraint after the jump's
            # free-leg swing; retain the V110 foot axis earlier in the action.
            target = max(-limit, min(limit, before))
            correction = (target - before) * progress
        rotation = (Quaternion(WORLD_UP, math.radians(correction)) @
                    sample["rotation"]).normalized()
        origin = sample["ankle"] - rotation @ (sample["anchor_local"] * sample["scale"])
        skate.matrix_world = Matrix.LocRotScale(origin, rotation, sample["scale"])
        bpy.context.view_layer.update()

        fit_error = (boot.matrix_world @ ANCHOR_LOCAL -
                     ankle.matrix_world.translation).length * 1000.0
        max_anchor_error_mm = max(max_anchor_error_mm, fit_error)
        local_rotation = skate.rotation_quaternion.copy().normalized()
        if previous_rotation is not None and local_rotation.dot(previous_rotation) < 0.0:
            local_rotation.negate()
        skate.rotation_quaternion = local_rotation
        skate.keyframe_insert(data_path="location", frame=frame,
                              group="V113 right-skate landing heading")
        skate.keyframe_insert(data_path="rotation_quaternion", frame=frame,
                              group="V113 right-skate landing heading")
        previous_rotation = local_rotation.copy()
        after = signed_angle(sample["torso"], horizontal(skate.matrix_world.to_3x3() @
                                                          FORWARD_LOCAL))
        max_before, max_after = max(max_before, abs(before)), max(max_after, abs(after))
        if frame in {37.0, 60.0, 76.0, 82.0, 84.0, 86.0, 87.0, 89.0, 90.0,
                     93.0, 100.0, 120.0, 150.0, 160.0}:
            key_rows.append({"frame": frame, "offset_before_deg": round(before, 4),
                             "offset_after_deg": round(after, 4),
                             "active_limit_deg": round(limit, 4),
                             "yaw_correction_deg": round(correction, 4)})

    bag = channelbag(skate)
    for curve in bag.fcurves:
        if curve.data_path in {"location", "rotation_quaternion"}:
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"
            curve.update()

    scene.name = "Single Axel 1A · landing right-skate heading refinement v113"
    scene["prototype_version"] = scene["version"] = "v113"
    scene["v113_revision"] = (
        "Derived from preserved V110. The right boot/blade heading is identical to V110 before "
        "frame 82; a smooth correction activates between frames 82 and 90, limiting horizontal "
        "offset from the animated shoulder-derived torso axis to 15 degrees at and after frame 90. "
        "It remains ankle-pivoted and boot/blade-coaxial. The limit is an illustrative visual "
        "constraint, not an ISU technique rule or athlete measurement.")
    scene["illustrative_simulated"] = True
    scene.frame_set(76)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
    bpy.ops.export_scene.gltf(
        filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
        export_cameras=True, export_lights=False, export_yup=True,
        use_selection=False, use_active_scene=True, use_visible=True,
        use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
        export_frame_step=1, export_optimize_animation_size=False)
    print("V113_LANDING_HEADING_REPORT " + json.dumps({
        "source": str(SOURCE), "blend": str(OUT), "web_glb": str(WEB_OUT),
        "samples": len(samples), "max_abs_torso_to_boot_before_deg": round(max_before, 4),
        "max_abs_torso_to_boot_after_deg": round(max_after, 4),
        "max_ankle_anchor_error_mm": round(max_anchor_error_mm, 6),
        "boot_and_blade_share_parent": boot.parent == blade.parent == skate,
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
        "key_frames": key_rows,
    }, ensure_ascii=False))


main()
