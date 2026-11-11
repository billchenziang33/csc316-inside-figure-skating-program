"""Derive V151 with a gradual landing-direction correction to the free leg."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v149.blend"
OUT = ASSET / "single-axel-1a-human-rink-v151.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v151-web.glb"
FORWARD_LOCAL = Vector((0.0, -1.0, 0.0))
WORLD_UP = Vector((0.0, 0.0, 1.0))
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
    value = Vector((vector.x, vector.y, 0.0))
    return value.normalized() if value.length > 1e-8 else None


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    require(a is not None and b is not None, "Degenerate torso/skate heading")
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def heading_limit(frame):
    if frame <= 85.0:
        return 60.0
    if frame <= 87.0:
        return 60.0 - 44.0 * smoothstep((frame - 85.0) / 2.0)
    if frame <= 90.0:
        return 16.0 - 6.0 * smoothstep((frame - 87.0) / 3.0)
    return 180.0


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
            f"Expected V149 source, got {bpy.data.filepath}")
    require(not OUT.exists() and not WEB_OUT.exists(),
            "Refusing to overwrite an existing V151 artifact")
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    require(scene.get("prototype_version") == "v149", "Expected V149 source scene")
    default_scene = bpy.data.scenes.get("Scene")
    require(default_scene is not None and
            sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
            "The original default Scene signature changed")
    require((scene.frame_start, scene.frame_end) == (1, 160), "Unexpected frame range")

    parts = [scene.objects[name] for name in PART_NAMES]
    torso = scene.objects["Human · shaped jacket torso"]
    hip = scene.objects["Human · left leg volume 3"]
    ankle = scene.objects["Human · left ankle joint"]
    skate = scene.objects["Left skate · exact website fit v64"]
    boot = scene.objects["Left skate · website boot v64"]
    blade = scene.objects["Left skate · website blade v64"]
    require(all(obj.parent == scene.objects["Body anchor · pelvis-origin poses"]
                for obj in parts[:-1]), "Left leg pose hierarchy changed")
    require(skate.parent == ankle and boot.parent == skate and blade.parent == skate,
            "Ankle-parented skate assembly changed")

    samples = []
    total = round((scene.frame_end - scene.frame_start) / SAMPLE_STEP)
    for index in range(total + 1):
        frame = scene.frame_start + index * SAMPLE_STEP
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        body_axis = horizontal(torso.matrix_world.to_3x3() @ FORWARD_LOCAL)
        boot_axis = horizontal(boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
        require(body_axis is not None and boot_axis is not None,
                f"Degenerate direction at frame {frame:.2f}")
        transforms = []
        for obj in parts:
            world = obj.matrix_world.copy()
            transforms.append((obj, world.translation.copy(),
                               world.to_quaternion().normalized(), world.to_scale()))
        yaw = signed_angle(body_axis, boot_axis)
        limit = heading_limit(frame)
        target = max(-limit, min(limit, yaw))
        samples.append((frame, hip.matrix_world.translation.copy(), yaw, target, transforms))

    for obj in parts:
        isolate_action(obj)

    previous = {obj.name: None for obj in parts}
    landing_rows = []
    max_ankle_drift_mm = 0.0
    for frame, hip_pivot, before, target, transforms in samples:
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        correction = target - before
        delta = Quaternion(WORLD_UP, math.radians(correction))
        source_ankle = ankle.matrix_world.translation.copy()
        for obj, location, rotation, scale in transforms:
            corrected_location = hip_pivot + delta @ (location - hip_pivot)
            corrected_rotation = (delta @ rotation).normalized()
            obj.matrix_world = Matrix.LocRotScale(corrected_location, corrected_rotation, scale)
            bpy.context.view_layer.update()
            obj.keyframe_insert(data_path="location", frame=frame,
                                group="Landing free-skate alignment v151")
            path = "rotation_quaternion" if obj.rotation_mode == "QUATERNION" else "rotation_euler"
            value = (obj.rotation_quaternion.copy().normalized()
                     if path == "rotation_quaternion" else
                     obj.rotation_euler.to_quaternion().normalized())
            old = previous[obj.name]
            if old is not None and value.dot(old) < 0.0 and path == "rotation_quaternion":
                value.negate()
                obj.rotation_quaternion = value
            obj.keyframe_insert(data_path=path, frame=frame,
                                group="Landing free-skate alignment v151")
            previous[obj.name] = value.copy()

        bpy.context.view_layer.update()
        torso_axis = torso.matrix_world.to_3x3() @ FORWARD_LOCAL
        corrected_axis = boot.matrix_world.to_3x3() @ FORWARD_LOCAL
        after = signed_angle(torso_axis, corrected_axis)
        expected_ankle = hip_pivot + delta @ (source_ankle - hip_pivot)
        ankle_drift = (ankle.matrix_world.translation - expected_ankle).length * 1000.0
        max_ankle_drift_mm = max(max_ankle_drift_mm, ankle_drift)
        if 80.0 <= frame <= 90.0 and frame in (80.0, 82.0, 84.0, 86.0,
                                                87.0, 88.0, 89.0, 90.0):
            landing_rows.append({"frame": frame,
                                 "before_torso_to_boot_deg": round(before, 3),
                                 "after_torso_to_boot_deg": round(after, 3),
                                 "limit_deg": round(heading_limit(frame), 3),
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

    scene.name = "Single Axel 1A · landing free-skate alignment v151"
    scene["prototype_version"] = scene["version"] = "v151"
    scene["free_skate_alignment_v151"] = (
        "Derived from V149. During the simulated descent, the model-left free leg and its attached "
        "boot/blade gradually turn toward the torso-facing heading: the visual yaw allowance eases "
        "from 60 degrees at frame 80 to 16 degrees at frame 87 and 10 degrees at frame 90. This "
        "illustrative limit is not an ISU or coaching rule. The ankle, boot and blade are transformed "
        "as a connected leg chain around the hip pivot.")
    scene["illustrative_simulated"] = True
    scene["technical_reference_limit"] = (
        "Axel references support the forward outside-edge take-off, free-leg swing, 1.5 airborne "
        "revolutions, opposite-foot backward landing and controlled glide. They do not prescribe a "
        "universal torso-to-free-skate yaw. V151 is a visual correction, not athlete capture or "
        "validated biomechanics.")

    scene.frame_set(90)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
    bpy.ops.export_scene.gltf(
        filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
        export_cameras=True, export_lights=False, export_yup=True,
        use_selection=False, use_active_scene=True, use_visible=True,
        use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
        export_frame_step=1, export_optimize_animation_size=False)

    right_side = [row for row in landing_rows if row["frame"] in (87.0, 88.0, 89.0, 90.0)]
    report = {
        "source": str(SOURCE), "blend": str(OUT), "web_glb": str(WEB_OUT),
        "prototype_version": scene.get("prototype_version"),
        "sample_step_frames": SAMPLE_STEP, "sample_count": len(samples),
        "max_ankle_drift_mm": round(max_ankle_drift_mm, 6),
        "max_torso_to_boot_abs_after_deg_87_90": round(
            max(abs(row["after_torso_to_boot_deg"]) for row in right_side), 5),
        "key_frames": landing_rows,
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
        "status": "illustrative/simulated candidate; not yet published",
    }
    print("FREE_SKATE_ALIGNMENT_V151 " + json.dumps(report, ensure_ascii=False))
    require(max_ankle_drift_mm < 0.01,
            "The free-leg correction did not preserve its ankle path")


main()

