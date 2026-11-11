"""Derive V167 by correcting the free-leg chain around its hip pivot."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v159.blend"
OUT = ASSET / "single-axel-1a-human-rink-v167.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v167-web.glb"
TORSO_FORWARD_LOCAL = Vector((0.0, -1.0, 0.0))
BOOT_TOE_LOCAL = Vector((0.0, 1.0, 0.0))
WORLD_UP = Vector((0.0, 0.0, 1.0))
FREE_SKATE_MAX_YAW = 25.0
SAMPLE_STEP = 0.25
PART_NAMES = (
    "Human · left leg volume 3",
    "Human · left leg volume 4",
    "Human · left knee joint",
    "Human · left ankle joint",
    "Left skate · exact website fit v64",
)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def horizontal(vector):
    result = Vector((vector.x, vector.y, 0.0))
    return result.normalized() if result.length > 1e-8 else None


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    if a is None or b is None:
        raise RuntimeError("Degenerate torso or physical skate heading")
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


def isolate_action(obj):
    animation = obj.animation_data
    if animation is None or animation.action is None or animation.action.users <= 1:
        return
    slot_id = animation.action_slot.identifier
    action = animation.action.copy()
    animation.action = action
    slot = next((item for item in action.slots if item.identifier == slot_id), None)
    require(slot is not None, f"Copied action lost slot {slot_id!r} on {obj.name}")
    animation.action_slot = slot


def set_linear_animation(obj):
    animation = obj.animation_data
    if animation is None or animation.action is None:
        raise RuntimeError(f"Missing animation for {obj.name}")
    for layer in animation.action.layers:
        for strip in layer.strips:
            if strip.type != "KEYFRAME":
                continue
            bag = strip.channelbag(animation.action_slot)
            if bag is None:
                continue
            for curve in bag.fcurves:
                if curve.data_path in {"location", "rotation_quaternion", "rotation_euler"}:
                    for point in curve.keyframe_points:
                        point.interpolation = "LINEAR"
                    curve.update()


def main():
    require(not OUT.exists() and not WEB_OUT.exists(),
            "Refusing to overwrite an existing V167 artifact")
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(),
            f"Expected V159 source, got {bpy.data.filepath}")
    scene = bpy.context.scene
    require(scene.get("prototype_version") == "v159", "Expected V159 source scene")
    require((scene.frame_start, scene.frame_end) == (1, 160),
            "Unexpected source animation range")
    default_scene = bpy.data.scenes.get("Scene")
    require(default_scene is not None and
            sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
            "The original default Scene signature changed")

    torso = scene.objects["Human · shaped jacket torso"]
    hip = scene.objects["Human · left leg volume 3"]
    ankle = scene.objects["Human · left ankle joint"]
    skate = scene.objects["Left skate · exact website fit v64"]
    boot = scene.objects["Left skate · website boot v64"]
    blade = scene.objects["Left skate · website blade v64"]
    body_anchor = scene.objects["Body anchor · pelvis-origin poses"]
    parts = [scene.objects[name] for name in PART_NAMES]
    require(all(obj.parent == body_anchor for obj in parts[:-1]),
            "The left thigh/calf/knee/ankle hierarchy changed")
    require(skate.parent == ankle and boot.parent == skate and blade.parent == skate,
            "The left skate hierarchy changed")

    total = round((scene.frame_end - scene.frame_start) / SAMPLE_STEP)
    samples = []
    for index in range(total + 1):
        frame = scene.frame_start + index * SAMPLE_STEP
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        torso_axis = torso.matrix_world.to_3x3() @ TORSO_FORWARD_LOCAL
        boot_axis = boot.matrix_world.to_3x3() @ BOOT_TOE_LOCAL
        yaw = signed_angle(torso_axis, boot_axis)
        target_yaw = max(-FREE_SKATE_MAX_YAW, min(FREE_SKATE_MAX_YAW, yaw))
        delta = Quaternion(WORLD_UP, math.radians(target_yaw - yaw))
        pivot = hip.matrix_world.translation.copy()
        transforms = []
        for obj in parts:
            world = obj.matrix_world.copy()
            transforms.append((obj, world.translation.copy(),
                               world.to_quaternion().normalized(), world.to_scale()))
        samples.append({
            "frame": frame,
            "before_yaw_deg": yaw,
            "target_yaw_deg": target_yaw,
            "delta": delta,
            "pivot": pivot,
            "transforms": transforms,
        })

    for obj in parts:
        isolate_action(obj)
    for obj in parts:
        obj.rotation_mode = "QUATERNION"
    previous = {obj.name: None for obj in parts}
    ankle_reference_drift_mm = 0.0
    corrected_rows = []
    for sample in samples:
        frame = sample["frame"]
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        source_ankle = ankle.matrix_world.translation.copy()
        pivot = sample["pivot"]
        delta = sample["delta"]
        lateral = horizontal(torso.matrix_world.to_3x3() @ Vector((1.0, 0.0, 0.0)))
        clearance_offset = -0.19 * math.exp(-0.5 * ((frame - 50.5) / 1.25) ** 2)
        lateral_clearance = lateral * clearance_offset
        for obj, location, rotation, scale in sample["transforms"]:
            corrected_location = pivot + delta @ (location - pivot) + lateral_clearance
            corrected_rotation = (delta @ rotation).normalized()
            obj.matrix_world = Matrix.LocRotScale(corrected_location,
                                                  corrected_rotation, scale)
            bpy.context.view_layer.update()
            obj.keyframe_insert(data_path="location", frame=frame,
                                group="Free-leg heading correction v167")
            if obj.rotation_mode == "QUATERNION":
                quaternion = obj.rotation_quaternion.copy().normalized()
                old = previous[obj.name]
                if old is not None and quaternion.dot(old) < 0.0:
                    quaternion.negate()
                    obj.rotation_quaternion = quaternion
                obj.keyframe_insert(data_path="rotation_quaternion", frame=frame,
                                    group="Free-leg heading correction v167")
                previous[obj.name] = quaternion.copy()
            else:
                obj.keyframe_insert(data_path="rotation_euler", frame=frame,
                                    group="Free-leg heading correction v167")

        bpy.context.view_layer.update()
        boot_axis = boot.matrix_world.to_3x3() @ BOOT_TOE_LOCAL
        torso_axis = torso.matrix_world.to_3x3() @ TORSO_FORWARD_LOCAL
        ankle_reference = boot.matrix_world @ (Vector((0.0, 0.045, 0.035)) * 1.8)
        ankle_reference_drift_mm = max(
            ankle_reference_drift_mm,
            (ankle_reference - ankle.matrix_world.translation).length * 1000.0,
        )
        corrected_rows.append({
            "frame": frame,
            "before_yaw_deg": sample["before_yaw_deg"],
            "after_yaw_deg": signed_angle(torso_axis, boot_axis),
            "correction_deg": sample["target_yaw_deg"] - sample["before_yaw_deg"],
        })

    for obj in parts:
        set_linear_animation(obj)
    scene.name = "Single Axel 1A · free-leg heading correction v167"
    scene["prototype_version"] = scene["version"] = "v167"
    scene["free_leg_heading_v167"] = (
        "Derived from preserved V159. Every quarter frame, the model-left free-leg chain "
        "(thigh, calf, knee, ankle and attached boot/blade) is rotated as one around the left hip "
        "pivot to keep the physical boot toe within 25 degrees of torso-forward. A smooth, "
        "temporary 0.19 m torso-lateral clearance offset centered at frame 50.5 separates the "
        "take-off feet. This retains the "
        "internal leg/skate fit and changes no torso, root-path or event-marker animation. The angle "
        "limit is an illustrative visual review target, not an ISU or coaching prescription."
    )
    scene["illustrative_simulated"] = True
    scene["technical_reference_limit"] = (
        "The reviewed slow-motion example shows entry, free-leg swing, air-position change, landing "
        "and exit check, but its wide camera view cannot establish numerical 3D toe angles. Axel "
        "references define phase order and take-off/landing edges, not a universal torso-to-free-skate "
        "yaw. Every project pose and track remains illustrative/simulated, not athlete capture."
    )

    scene.frame_set(92)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
    bpy.ops.export_scene.gltf(
        filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
        export_cameras=True, export_lights=False, export_yup=True,
        use_selection=False, use_active_scene=True, use_visible=True,
        use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
        export_frame_step=1, export_optimize_animation_size=False,
    )

    report = {
        "source": str(SOURCE), "blend": str(OUT), "web_glb": str(WEB_OUT),
        "source_version": "v159", "version": scene.get("prototype_version"),
        "sample_step_frames": SAMPLE_STEP, "sample_count": len(corrected_rows),
        "max_abs_left_yaw_deg": round(max(abs(row["after_yaw_deg"])
                                            for row in corrected_rows), 5),
        "max_ankle_reference_drift_mm": round(ankle_reference_drift_mm, 6),
        "key_frames": [row for row in corrected_rows
                       if row["frame"] in (47, 48, 60, 70, 78, 87, 92, 120)],
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
        "status": "illustrative/simulated candidate; audits and visual review pending",
    }
    print("FREE_LEG_HEADING_V167 " + json.dumps(report, ensure_ascii=False))


main()
