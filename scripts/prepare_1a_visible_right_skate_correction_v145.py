"""Derive a conservative viewer-right free-skate alignment candidate from V141."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v141.blend"
OUT = ASSET / "single-axel-1a-human-rink-v145.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v145-web.glb"
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
    if frame <= 90.0:
        return 10.0
    if frame <= 100.0:
        return 10.0 + 5.0 * smoothstep((frame - 90.0) / 10.0)
    if frame <= 110.0:
        return 15.0 + 15.0 * smoothstep((frame - 100.0) / 10.0)
    return 30.0


def isolate_action(obj):
    animation = obj.animation_data
    action = animation.action
    if action.users <= 1:
        return
    slot_id = animation.action_slot.identifier
    action = action.copy()
    animation.action = action
    slot = next((item for item in action.slots if item.identifier == slot_id), None)
    require(slot is not None, f"Copied action lost slot {slot_id!r}")
    animation.action_slot = slot


def channelbag(obj):
    action = obj.animation_data.action
    slot = obj.animation_data.action_slot
    require(action is not None and slot is not None, f"{obj.name} has no action slot")
    for layer in action.layers:
        for strip in layer.strips:
            if strip.type == "KEYFRAME":
                bag = strip.channelbag(slot)
                if bag is not None:
                    return bag
    raise RuntimeError(f"No keyframe channel bag for {obj.name}")


def main():
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(),
            f"Expected V141 source, got {bpy.data.filepath}")
    require(not OUT.exists() and not WEB_OUT.exists(),
            "Refusing to overwrite an existing V145 artifact")
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    require(scene.get("prototype_version") == "v141", "Expected V141 scene")
    default_scene = bpy.data.scenes.get("Scene")
    require(default_scene is not None and
            sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
            "The original default Scene signature changed")
    require((scene.frame_start, scene.frame_end) == (1, 160), "Unexpected frame range")

    parts = [scene.objects[name] for name in PART_NAMES]
    torso = scene.objects["Human · shaped jacket torso"]
    ankle = scene.objects["Human · left ankle joint"]
    skate, boot, blade = (scene.objects[name] for name in (
        "Left skate · exact website fit v64",
        "Left skate · website boot v64",
        "Left skate · website blade v64",
    ))
    hip = scene.objects["Human · left leg volume 3"]
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
        body = horizontal(torso.matrix_world.to_3x3() @ FORWARD_LOCAL)
        foot = horizontal(boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
        require(body is not None and foot is not None,
                f"Degenerate direction at frame {frame:.2f}")
        transforms = []
        for obj in parts:
            world = obj.matrix_world.copy()
            transforms.append((obj, world.translation.copy(),
                               world.to_quaternion().normalized(), world.to_scale()))
        samples.append((frame, hip.matrix_world.translation.copy(),
                        ankle.matrix_world.translation.copy(),
                        signed_angle(body, foot), transforms))

    for obj in parts:
        isolate_action(obj)

    previous = {obj.name: None for obj in parts}
    rows = []
    max_anchor_error_mm = 0.0
    for frame, hip_pivot, ankle_source, before, transforms in samples:
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        allowed = heading_limit(frame)
        target = max(-allowed, min(allowed, before))
        correction = (target - before) * smoothstep((frame - 86.0) / 4.0)
        hip_yaw = Quaternion(WORLD_UP, math.radians(correction / 3.0))
        ankle_yaw = Quaternion(WORLD_UP, math.radians(correction * 2.0 / 3.0))
        corrected_ankle = hip_pivot + hip_yaw @ (ankle_source - hip_pivot)

        for obj, location, rotation, scale in transforms:
            corrected_location = hip_pivot + hip_yaw @ (location - hip_pivot)
            corrected_rotation = (hip_yaw @ rotation).normalized()
            if obj == skate:
                corrected_location = corrected_ankle + ankle_yaw @ (corrected_location - corrected_ankle)
                corrected_rotation = (ankle_yaw @ corrected_rotation).normalized()
            obj.matrix_world = Matrix.LocRotScale(corrected_location, corrected_rotation, scale)
            bpy.context.view_layer.update()
            obj.keyframe_insert(data_path="location", frame=frame,
                                group="Viewer-right late-free-skate heading v145")
            path = "rotation_quaternion" if obj.rotation_mode == "QUATERNION" else "rotation_euler"
            value = (obj.rotation_quaternion.copy().normalized() if path == "rotation_quaternion"
                     else obj.rotation_euler.to_quaternion().normalized())
            old = previous[obj.name]
            if old is not None and value.dot(old) < 0.0 and path == "rotation_quaternion":
                value.negate()
                obj.rotation_quaternion = value
            obj.keyframe_insert(data_path=path, frame=frame,
                                group="Viewer-right late-free-skate heading v145")
            previous[obj.name] = value.copy()

        bpy.context.view_layer.update()
        after = signed_angle(torso.matrix_world.to_3x3() @ FORWARD_LOCAL,
                             boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
        anchor_error = ((boot.matrix_world @ (Vector((0.0, 0.045, 0.035)) * 1.8) -
                         ankle.matrix_world.translation).length * 1000.0)
        max_anchor_error_mm = max(max_anchor_error_mm, anchor_error)
        if frame in (84.0, 86.0, 87.0, 88.0, 89.0, 90.0, 92.0,
                     96.0, 100.0, 105.0, 110.0, 121.0, 150.0):
            rows.append({"frame": frame,
                         "before_body_to_viewer_right_skate_deg": round(before, 3),
                         "after_body_to_viewer_right_skate_deg": round(after, 3),
                         "limit_deg": round(allowed, 3),
                         "correction_deg": round(correction, 3)})

    for obj in parts:
        bag = channelbag(obj)
        for curve in bag.fcurves:
            if curve.data_path in {"location", "rotation_quaternion", "rotation_euler"}:
                for point in curve.keyframe_points:
                    point.interpolation = "LINEAR"
                curve.update()

    scene.name = "Single Axel 1A · viewer-right late free skate alignment v145"
    scene["prototype_version"] = scene["version"] = "v145"
    scene["right_skate_revision_v145"] = (
        "Derived from V141 without changing the original default Scene. The side-view viewer-right "
        "skate is the model-left free skate. Its leg chain eases after frame 86 to within 10 degrees "
        "of torso-forward at simulated landing, then opens smoothly to 15 degrees by frame 100 and "
        "30 degrees by frame 110 for the illustrative exit glide. Hip/leg and ankle-centered rigid "
        "boot/blade turns preserve the ankle attachment. Values are visual targets only.")
    scene["illustrative_simulated"] = True
    scene["technical_reference_limit"] = (
        "Public Axel analyses informed only the phase order (entry edge, free-leg swing, compact "
        "flight, opposite-foot backward landing, and checked glide-out). They do not define a fixed "
        "torso-to-free-skate yaw. V145 is an illustrative visual correction, not athlete capture "
        "or certified technique.")
    scene.frame_set(90)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
    bpy.ops.export_scene.gltf(
        filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
        export_cameras=True, export_lights=False, export_yup=True,
        use_selection=False, use_active_scene=True, use_visible=True,
        use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
        export_frame_step=1, export_optimize_animation_size=False)
    print("V145_FREE_SKATE_BUILD " + json.dumps({
        "source": str(SOURCE), "blend": str(OUT), "web_glb": str(WEB_OUT),
        "sample_step_frames": SAMPLE_STEP, "sample_count": len(samples),
        "max_boot_anchor_error_mm": round(max_anchor_error_mm, 6),
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
        "key_frames": rows, "status": "illustrative/simulated candidate; not yet published",
    }, ensure_ascii=False))
    require(max_anchor_error_mm < 0.01, "Boot shifted away from its ankle")


main()
