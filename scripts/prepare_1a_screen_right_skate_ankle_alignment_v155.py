"""Derive V155 using a small ankle articulation instead of rotating the full free leg."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v153.blend"
OUT = ASSET / "single-axel-1a-human-rink-v155.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v155-web.glb"
FORWARD_LOCAL = Vector((0.0, -1.0, 0.0))
WORLD_UP = Vector((0.0, 0.0, 1.0))
SAMPLE_STEP = 0.25
SKATE_NAME = "Left skate · exact website fit v64"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def horizontal(vector):
    value = Vector((vector.x, vector.y, 0.0))
    return value.normalized() if value.length > 1e-8 else None


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    require(a is not None and b is not None, "Degenerate horizontal facing axis")
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def heading_limit(frame):
    if frame <= 76.0:
        return 60.0
    if frame <= 80.0:
        return 60.0 - 16.0 * smoothstep((frame - 76.0) / 4.0)
    if frame <= 85.0:
        return 44.0
    if frame <= 87.0:
        return 44.0 - 28.0 * smoothstep((frame - 85.0) / 2.0)
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
            f"Expected V153 source, got {bpy.data.filepath}")
    require(not OUT.exists() and not WEB_OUT.exists(),
            "Refusing to overwrite an existing V155 artifact")
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    require(scene.get("prototype_version") == "v153", "Expected V153 source scene")
    default_scene = bpy.data.scenes.get("Scene")
    require(default_scene is not None and
            sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
            "The original default Scene signature changed")
    require(scene.objects.get("V102_EVENT_LANDING_FRAME_92") is not None,
            "V153 landing event frame 92 is missing")
    require((scene.frame_start, scene.frame_end) == (1, 160), "Unexpected frame range")

    torso = scene.objects["Human · shaped jacket torso"]
    head = scene.objects["Head · detailed generic human sculpt"]
    nose = scene.objects["Head · nose tip"]
    ankle = scene.objects["Human · left ankle joint"]
    skate = scene.objects[SKATE_NAME]
    boot = scene.objects["Left skate · website boot v64"]
    blade = scene.objects["Left skate · website blade v64"]
    require(skate.parent == ankle and boot.parent == skate and blade.parent == skate,
            "The ankle-parented boot/blade hierarchy changed")

    samples = []
    count = round((90.0 - 76.0) / SAMPLE_STEP)
    for index in range(count + 1):
        frame = 76.0 + index * SAMPLE_STEP
        scene.frame_set(math.floor(frame), subframe=frame - math.floor(frame))
        bpy.context.view_layer.update()
        body_axis = horizontal(torso.matrix_world.to_3x3() @ FORWARD_LOCAL)
        boot_axis = horizontal(boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
        require(body_axis is not None and boot_axis is not None,
                f"Degenerate direction at frame {frame:.2f}")
        world = skate.matrix_world.copy()
        yaw = signed_angle(body_axis, boot_axis)
        limit = heading_limit(frame)
        target = max(-limit, min(limit, yaw))
        samples.append((frame, ankle.matrix_world.translation.copy(), yaw, target,
                        world.translation.copy(), world.to_quaternion().normalized(), world.to_scale()))

    isolate_action(skate)
    previous_quaternion = None
    max_face_yaw = max_anchor_drift_mm = 0.0
    key_rows = []
    for frame, ankle_pivot, before, target, original_location, original_rotation, scale in samples:
        scene.frame_set(math.floor(frame), subframe=frame - math.floor(frame))
        bpy.context.view_layer.update()
        correction = target - before
        delta = Quaternion(WORLD_UP, math.radians(correction))
        location = ankle_pivot + delta @ (original_location - ankle_pivot)
        rotation = (delta @ original_rotation).normalized()
        skate.matrix_world = Matrix.LocRotScale(location, rotation, scale)
        bpy.context.view_layer.update()
        skate.keyframe_insert(data_path="location", frame=frame,
                              group="Screen-right skate ankle alignment v155")
        path = "rotation_quaternion" if skate.rotation_mode == "QUATERNION" else "rotation_euler"
        value = (skate.rotation_quaternion.copy().normalized()
                 if path == "rotation_quaternion" else skate.rotation_euler.to_quaternion().normalized())
        if previous_quaternion is not None and value.dot(previous_quaternion) < 0.0 and path == "rotation_quaternion":
            value.negate()
            skate.rotation_quaternion = value
        skate.keyframe_insert(data_path=path, frame=frame,
                              group="Screen-right skate ankle alignment v155")
        previous_quaternion = value.copy()

        bpy.context.view_layer.update()
        face_axis = horizontal(nose.matrix_world.translation - head.matrix_world.translation)
        boot_axis = horizontal(boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
        face_yaw = abs(signed_angle(face_axis, boot_axis))
        max_face_yaw = max(max_face_yaw, face_yaw)
        fit_anchor = boot.matrix_world @ (Vector((0.0, 0.045, 0.035)) * 1.8)
        anchor_drift_mm = (fit_anchor - ankle.matrix_world.translation).length * 1000.0
        max_anchor_drift_mm = max(max_anchor_drift_mm, anchor_drift_mm)
        if frame in (76.0, 78.0, 80.0, 81.0, 82.0, 83.0, 84.0, 85.0,
                     86.0, 87.0, 90.0):
            key_rows.append({
                "frame": frame,
                "face_to_boot_after_deg": round(face_yaw, 4),
                "heading_limit_deg": round(heading_limit(frame), 4),
                "correction_deg": round(correction, 4),
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

    scene.name = "Single Axel 1A · screen-right skate ankle alignment v155"
    scene["prototype_version"] = scene["version"] = "v155"
    scene["free_skate_alignment_v155"] = (
        "Derived from V153. The model-left free skate, which appears on the viewer's right in side view, "
        "eases toward the torso heading through frames 76-90 by articulating the entire boot/blade "
        "assembly around the ankle. The leg mesh and knee path remain unchanged, and the ankle anchor "
        "is preserved. The 44-degree visual limit is illustrative, not a coaching rule or athlete measurement.")
    scene["illustrative_simulated"] = True
    scene["technical_reference_limit"] = (
        "Public coaching/video sources inform Axel phase order and free-leg timing, but do not specify "
        "a universal torso-to-free-skate angle. V155 is a visual ankle articulation only; poses, trajectory "
        "and all measurements remain illustrative/simulated, not athlete capture or validated biomechanics.")

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
        "max_face_yaw_deg_f76_f90": round(max_face_yaw, 5),
        "max_boot_ankle_anchor_drift_mm": round(max_anchor_drift_mm, 6),
        "key_frames": key_rows,
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
        "status": "illustrative/simulated candidate; awaiting direction, collision and touchdown audits",
    }
    print("SCREEN_RIGHT_SKATE_ANKLE_ALIGNMENT_V155 " + json.dumps(report, ensure_ascii=False))
    require(max_anchor_drift_mm < 0.01,
            "The boot no longer fits its ankle anchor")


main()
