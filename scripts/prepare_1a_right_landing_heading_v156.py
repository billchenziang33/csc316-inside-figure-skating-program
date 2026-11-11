"""Derive V156 with a tighter ankle-pivoted heading for the right landing skate."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v155.blend"
OUT = ASSET / "single-axel-1a-human-rink-v156.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v156-web.glb"
FORWARD_LOCAL = Vector((0.0, -1.0, 0.0))
WORLD_UP = Vector((0.0, 0.0, 1.0))
SAMPLE_STEP = 0.25
YAW_LIMIT_DEGREES = 8.0


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
            f"Expected V155 source, got {bpy.data.filepath}")
    require(not OUT.exists() and not WEB_OUT.exists(),
            "Refusing to overwrite an existing V156 artifact")
    scene = bpy.context.scene
    require(scene.get("prototype_version") == "v155", "Expected V155 source scene")
    default_scene = bpy.data.scenes.get("Scene")
    require(default_scene is not None and
            sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
            "The original default Scene signature changed")
    require(scene.objects.get("V102_EVENT_LANDING_FRAME_92") is not None,
            "V155 landing marker at frame 92 is missing")
    require((scene.frame_start, scene.frame_end) == (1, 160), "Unexpected frame range")

    torso = scene.objects["Human · shaped jacket torso"]
    ankle = scene.objects["Human · right ankle joint"]
    skate = scene.objects["Right skate · exact website fit v64"]
    boot = scene.objects["Right skate · website boot v64"]
    blade = scene.objects["Right skate · website blade v64"]
    require(skate.parent == ankle and boot.parent == skate and blade.parent == skate,
            "The right ankle/skate/boot/blade hierarchy changed")

    samples = []
    count = round((scene.frame_end - scene.frame_start) / SAMPLE_STEP)
    for index in range(count + 1):
        frame = scene.frame_start + index * SAMPLE_STEP
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        body_axis = horizontal(torso.matrix_world.to_3x3() @ FORWARD_LOCAL)
        boot_axis = horizontal(boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
        require(body_axis is not None and boot_axis is not None,
                f"Degenerate heading at frame {frame:.2f}")
        ankle_pivot = ankle.matrix_world.translation.copy()
        world = skate.matrix_world.copy()
        before = signed_angle(body_axis, boot_axis)
        target = max(-YAW_LIMIT_DEGREES, min(YAW_LIMIT_DEGREES, before))
        samples.append((frame, ankle_pivot, before, target,
                        world.translation.copy(), world.to_quaternion().normalized(), world.to_scale()))

    isolate_action(skate)
    previous_quaternion = None
    max_abs_after = max_anchor_drift_mm = max_correction = 0.0
    key_rows = []
    for frame, pivot, before, target, location, rotation, scale in samples:
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        correction = target - before
        delta = Quaternion(WORLD_UP, math.radians(correction))
        corrected_location = pivot + delta @ (location - pivot)
        corrected_rotation = (delta @ rotation).normalized()
        skate.matrix_world = Matrix.LocRotScale(corrected_location, corrected_rotation, scale)
        bpy.context.view_layer.update()
        skate.keyframe_insert(data_path="location", frame=frame,
                              group="Right landing skate ankle heading v156")
        path = "rotation_quaternion" if skate.rotation_mode == "QUATERNION" else "rotation_euler"
        value = (skate.rotation_quaternion.copy().normalized()
                 if path == "rotation_quaternion" else skate.rotation_euler.to_quaternion().normalized())
        if previous_quaternion is not None and value.dot(previous_quaternion) < 0.0 and path == "rotation_quaternion":
            value.negate()
            skate.rotation_quaternion = value
        skate.keyframe_insert(data_path=path, frame=frame,
                              group="Right landing skate ankle heading v156")
        previous_quaternion = value.copy()

        bpy.context.view_layer.update()
        after = signed_angle(torso.matrix_world.to_3x3() @ FORWARD_LOCAL,
                             boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
        anchor = (boot.matrix_world @ (Vector((0.0, 0.045, 0.035)) * 1.8))
        anchor_drift_mm = (anchor - ankle.matrix_world.translation).length * 1000.0
        max_abs_after = max(max_abs_after, abs(after))
        max_anchor_drift_mm = max(max_anchor_drift_mm, anchor_drift_mm)
        max_correction = max(max_correction, abs(correction))
        if frame in (1.0, 20.0, 37.0, 46.0, 48.0, 60.0, 70.0, 80.0,
                     85.0, 87.0, 90.0, 91.0, 92.0, 100.0, 120.0, 150.0, 160.0):
            key_rows.append({
                "frame": frame,
                "before_torso_to_boot_deg": round(before, 3),
                "after_torso_to_boot_deg": round(after, 3),
                "correction_deg": round(correction, 3),
                "ankle_anchor_drift_mm": round(anchor_drift_mm, 6),
            })

    action = skate.animation_data.action
    slot = skate.animation_data.action_slot
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

    scene.name = "Single Axel 1A · right landing skate alignment v156"
    scene["prototype_version"] = scene["version"] = "v156"
    scene["right_landing_skate_alignment_v156"] = (
        "Derived from V155. The model-right landing skate, boot, and blade rotate together about the "
        "right ankle so their heading remains within 8 degrees of the torso-forward axis. The ankle "
        "position, leg pose, root trajectory, 1.5-turn body motion, and frame-92 landing event remain "
        "unchanged. The 8-degree cap is an illustrative visual constraint, not a coaching rule.")
    scene["illustrative_simulated"] = True
    scene["technical_reference_limit"] = (
        "Axel references inform the forward outside-edge take-off, opposite-foot backward landing, "
        "free-leg swing, compact flight, and checked landing. They do not prescribe a fixed torso-to-skate "
        "angle. All poses, trajectory, event times, and angle limits remain illustrative/simulated.")

    scene.frame_set(92)
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
        "prototype_version": scene.get("prototype_version"),
        "sample_step_frames": SAMPLE_STEP, "samples": len(samples),
        "max_abs_torso_to_right_boot_after_deg": round(max_abs_after, 5),
        "max_ankle_anchor_drift_mm": round(max_anchor_drift_mm, 6),
        "max_ankle_pivot_correction_deg": round(max_correction, 5),
        "key_frames": key_rows,
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
        "status": "illustrative/simulated candidate; awaiting collision, boot fit, and ice-clearance audit",
    }
    print("RIGHT_LANDING_HEADING_V156 " + json.dumps(report, ensure_ascii=False))
    require(max_abs_after <= YAW_LIMIT_DEGREES + 0.05,
            "The right landing skate exceeded the illustrative 8-degree heading cap")
    require(max_anchor_drift_mm < 0.01,
            "The ankle fit anchor moved during the yaw correction")


main()
