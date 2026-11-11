"""Derive V149 with a smooth, ankle-connected right-leg heading correction."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v148.blend"
OUT = ASSET / "single-axel-1a-human-rink-v149.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v149-web.glb"
FORWARD_LOCAL = Vector((0.0, -1.0, 0.0))
WORLD_UP = Vector((0.0, 0.0, 1.0))
YAW_LIMIT_DEGREES = 20.0
SAMPLE_STEP = 0.25
PART_NAMES = (
    "Human · right leg volume 3",
    "Human · right leg volume 4",
    "Human · right knee joint",
    "Human · right ankle joint",
    "Right skate · exact website fit v64",
)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def horizontal(vector):
    value = Vector((vector.x, vector.y, 0.0))
    return value.normalized() if value.length > 1e-8 else None


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    require(a is not None and b is not None, "Degenerate torso/boot heading")
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


def isolate_action(obj):
    animation = obj.animation_data
    if animation is None or animation.action is None or animation.action.users <= 1:
        return
    action = animation.action.copy()
    slot_id = animation.action_slot.identifier
    animation.action = action
    slot = next((item for item in action.slots if item.identifier == slot_id), None)
    require(slot is not None, f"Copied action lost slot {slot_id!r}")
    animation.action_slot = slot


def main():
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(),
            f"Expected V148 source, got {bpy.data.filepath}")
    require(not OUT.exists() and not WEB_OUT.exists(),
            "Refusing to overwrite an existing V149 artifact")
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    require(scene.get("prototype_version") == "v148", "Expected V148 source scene")
    default_scene = bpy.data.scenes.get("Scene")
    require(default_scene is not None and
            sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
            "The original default Scene signature changed")
    require((scene.frame_start, scene.frame_end) == (1, 160), "Unexpected frame range")

    parts = [scene.objects[name] for name in PART_NAMES]
    torso = scene.objects["Human · shaped jacket torso"]
    hip = scene.objects["Human · right leg volume 3"]
    ankle = scene.objects["Human · right ankle joint"]
    skate, boot, blade = (scene.objects[name] for name in (
        "Right skate · exact website fit v64",
        "Right skate · website boot v64",
        "Right skate · website blade v64",
    ))
    require(all(obj.parent == scene.objects["Body anchor · pelvis-origin poses"]
                for obj in parts[:-1]), "Right leg pose hierarchy changed")
    require(skate.parent == ankle and boot.parent == skate and blade.parent == skate,
            "Right ankle/skate/boot/blade hierarchy changed")

    samples = []
    total = round((scene.frame_end - scene.frame_start) / SAMPLE_STEP)
    for index in range(total + 1):
        frame = scene.frame_start + index * SAMPLE_STEP
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        face = horizontal(torso.matrix_world.to_3x3() @ FORWARD_LOCAL)
        toe = horizontal(boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
        require(face is not None and toe is not None,
                f"Degenerate torso/boot heading at frame {frame:.2f}")
        yaw = signed_angle(face, toe)
        target = max(-YAW_LIMIT_DEGREES, min(YAW_LIMIT_DEGREES, yaw))
        correction = target - yaw
        hip_pivot = hip.matrix_world.translation.copy()
        ankle_source = ankle.matrix_world.translation.copy()
        transforms = []
        for obj in parts:
            world = obj.matrix_world.copy()
            transforms.append((obj, world.translation.copy(),
                               world.to_quaternion().normalized(), world.to_scale()))
        samples.append((frame, hip_pivot, ankle_source, yaw, correction, transforms))

    for obj in parts:
        isolate_action(obj)

    previous = {obj.name: None for obj in parts}
    max_after = max_correction = max_ankle_drift_mm = 0.0
    key_rows = []
    for frame, hip_pivot, ankle_source, before, correction, transforms in samples:
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        delta = Quaternion(WORLD_UP, math.radians(correction))

        for obj, location, rotation, scale in transforms:
            corrected_location = hip_pivot + delta @ (location - hip_pivot)
            corrected_rotation = (delta @ rotation).normalized()
            obj.matrix_world = Matrix.LocRotScale(corrected_location, corrected_rotation, scale)
            bpy.context.view_layer.update()
            obj.keyframe_insert(data_path="location", frame=frame,
                                group="Right leg chain heading alignment v149")
            path = "rotation_quaternion" if obj.rotation_mode == "QUATERNION" else "rotation_euler"
            value = (obj.rotation_quaternion.copy().normalized()
                     if path == "rotation_quaternion" else
                     obj.rotation_euler.to_quaternion().normalized())
            old = previous[obj.name]
            if old is not None and value.dot(old) < 0.0 and path == "rotation_quaternion":
                value.negate()
                obj.rotation_quaternion = value
            obj.keyframe_insert(data_path=path, frame=frame,
                                group="Right leg chain heading alignment v149")
            previous[obj.name] = value.copy()

        bpy.context.view_layer.update()
        after = signed_angle(torso.matrix_world.to_3x3() @ FORWARD_LOCAL,
                             boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
        ankle_drift = (ankle.matrix_world.translation -
                       (hip_pivot + delta @ (ankle_source - hip_pivot))).length * 1000.0
        max_after = max(max_after, abs(after))
        max_correction = max(max_correction, abs(correction))
        max_ankle_drift_mm = max(max_ankle_drift_mm, ankle_drift)
        if frame in (1.0, 20.0, 37.0, 50.0, 60.0, 70.0, 76.0, 82.0,
                     87.0, 90.0, 100.0, 121.0, 150.0, 160.0):
            key_rows.append({"frame": frame,
                             "before_torso_to_right_boot_deg": round(before, 3),
                             "after_torso_to_right_boot_deg": round(after, 3),
                             "correction_deg": round(correction, 3)})

    for obj in parts:
        action = obj.animation_data.action
        slot = obj.animation_data.action_slot
        for layer in action.layers:
            for strip in layer.strips:
                if strip.type == "KEYFRAME":
                    bag = strip.channelbag(slot)
                    if bag is not None:
                        for curve in bag.fcurves:
                            if curve.data_path in {"location", "rotation_quaternion", "rotation_euler"}:
                                for point in curve.keyframe_points:
                                    point.interpolation = "LINEAR"
                                curve.update()

    scene.name = "Single Axel 1A · right leg and skate heading alignment v149"
    scene["prototype_version"] = scene["version"] = "v149"
    scene["right_leg_alignment_v149"] = (
        "Derived from V148. The model-right leg, ankle, boot and blade assembly is rotated as one "
        "rigid pose chain around the upper-leg pivot when torso-relative boot yaw exceeds 20 degrees. "
        "The attached boot/blade and ankle-relative geometry remain unchanged. This is an illustrative "
        "visual limit, not a technical rule or athlete measurement.")
    scene["illustrative_simulated"] = True
    scene["technical_reference_limit"] = (
        "Public slow-motion and coaching references informed the phase order and opposite-foot "
        "backward landing. They do not define a fixed torso-to-skate yaw. V149 limits a visual heading "
        "difference and does not claim validated biomechanics or athlete capture.")

    scene.frame_set(90)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
    bpy.ops.export_scene.gltf(
        filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
        export_cameras=True, export_lights=False, export_yup=True,
        use_selection=False, use_active_scene=True, use_visible=True,
        use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
        export_frame_step=1, export_optimize_animation_size=False)

    report = {
        "source": str(SOURCE), "blend": str(OUT), "web_glb": str(WEB_OUT),
        "prototype_version": scene["prototype_version"],
        "sample_step_frames": SAMPLE_STEP, "sample_count": len(samples),
        "max_abs_torso_to_right_boot_after_deg": round(max_after, 5),
        "max_right_leg_chain_correction_deg": round(max_correction, 5),
        "max_boot_to_blade_yaw_error_deg": round(abs(signed_angle(
            boot.matrix_world.to_3x3() @ FORWARD_LOCAL,
            blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0)))), 6),
        "max_ankle_drift_mm": round(max_ankle_drift_mm, 6),
        "key_frames": key_rows,
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
        "status": "illustrative/simulated candidate; not yet published",
    }
    print("RIGHT_LEG_ALIGNMENT_V149 " + json.dumps(report, ensure_ascii=False))
    require(max_after <= YAW_LIMIT_DEGREES + 0.1,
            "The right foot exceeded the V149 torso-relative heading limit")
    require(max_ankle_drift_mm < 0.01,
            "Rigid-chain rotation did not preserve the right ankle relationship")


main()
