"""Retarget the free-leg hip earlier so its toe stays oriented with the torso (V117)."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v113.blend"
OUT = ASSET / "single-axel-1a-human-rink-v117.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v117-web.glb"
FORWARD_LOCAL = Vector((0.0, -1.0, 0.0))
WORLD_UP = Vector((0.0, 0.0, 1.0))
RAMP_START, RAMP_END = 60.0, 82.0
MAX_FREE_LEG_HEADING = 60.0
LEG_PARTS = (
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
            f"Expected V113 source, got {bpy.data.filepath}")
    require(not OUT.exists() and not WEB_OUT.exists(),
            "Refusing to overwrite an existing V117 artifact")
    scene = bpy.context.scene
    require(scene.get("prototype_version") == "v113",
            f"Expected V113 scene, got {scene.get('prototype_version')}")
    default_scene = bpy.data.scenes.get("Scene")
    require(default_scene is not None and
            sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
            "The original default Scene signature changed")

    parts = [scene.objects[name] for name in LEG_PARTS]
    body_anchor = scene.objects["Body anchor · pelvis-origin poses"]
    require(all(obj.parent == body_anchor for obj in parts[:-1]),
            "The left-leg meshes/joints no longer share the body anchor")
    skate = parts[-1]
    ankle = scene.objects["Human · left ankle joint"]
    boot = scene.objects["Left skate · website boot v64"]
    blade = scene.objects["Left skate · website blade v64"]
    torso = scene.objects["Human · shaped jacket torso"]
    require(skate.parent == ankle and boot.parent == skate and blade.parent == skate,
            "Left boot/blade hierarchy or ankle attachment changed")

    pivot_obj = scene.objects["Human · left leg volume 3"]
    anchor_local = Vector((0.0, 0.045, 0.035)) * 1.8
    samples = []
    count = round((scene.frame_end - scene.frame_start) * 4)
    for index in range(count + 1):
        frame = scene.frame_start + index * 0.25
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        body = horizontal(torso.matrix_world.to_3x3() @ FORWARD_LOCAL)
        require(body is not None, f"Degenerate torso heading at frame {frame:.2f}")
        transforms = []
        for obj in parts:
            world = obj.matrix_world.copy()
            transforms.append({
                "object": obj,
                "location": world.translation.copy(),
                "rotation": world.to_quaternion().normalized(),
                "scale": world.to_scale(),
            })
        boot_heading = horizontal(boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
        fit_point = boot.matrix_world @ anchor_local
        require((fit_point - ankle.matrix_world.translation).length < 1e-5,
                f"V113 left boot reference differs from ankle at frame {frame:.2f}")
        samples.append({
            "frame": frame,
            "pivot": pivot_obj.matrix_world.translation.copy(),
            "body": body,
            "heading": boot_heading,
            "transforms": transforms,
        })

    for obj in parts:
        isolate_action(obj)

    previous_rotations = {obj.name: None for obj in parts}
    max_heading_after = max_correction = max_anchor_error_mm = 0.0
    rows = []
    for sample in samples:
        frame = sample["frame"]
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        before = signed_angle(sample["body"], sample["heading"])
        target = max(-MAX_FREE_LEG_HEADING,
                     min(MAX_FREE_LEG_HEADING, before))
        weight = smoothstep((frame - RAMP_START) / (RAMP_END - RAMP_START))
        correction = (target - before) * weight
        yaw = Quaternion(WORLD_UP, math.radians(correction))
        pivot = sample["pivot"]

        for item in sample["transforms"]:
            obj = item["object"]
            location = pivot + yaw @ (item["location"] - pivot)
            rotation = (yaw @ item["rotation"]).normalized()
            obj.matrix_world = Matrix.LocRotScale(location, rotation, item["scale"])
            bpy.context.view_layer.update()
            obj.keyframe_insert(data_path="location", frame=frame,
                                group="V117 left free-leg hip yaw")
            rotation_path = ("rotation_quaternion" if obj.rotation_mode == "QUATERNION"
                             else "rotation_euler")
            current_rotation = (obj.rotation_quaternion.copy().normalized()
                                if rotation_path == "rotation_quaternion"
                                else obj.rotation_euler.to_quaternion().normalized())
            previous = previous_rotations[obj.name]
            if previous is not None and current_rotation.dot(previous) < 0.0:
                if rotation_path == "rotation_quaternion":
                    current_rotation.negate()
                    obj.rotation_quaternion = current_rotation
            obj.keyframe_insert(data_path=rotation_path, frame=frame,
                                group="V117 left free-leg hip yaw")
            previous_rotations[obj.name] = current_rotation.copy()

        bpy.context.view_layer.update()
        after_heading = horizontal(boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
        after = signed_angle(sample["body"], after_heading)
        fit = (boot.matrix_world @ anchor_local -
               ankle.matrix_world.translation).length * 1000.0
        max_anchor_error_mm = max(max_anchor_error_mm, fit)
        max_heading_after = max(max_heading_after, abs(after))
        max_correction = max(max_correction, abs(correction))
        if frame in {60.0, 68.0, 72.0, 76.0, 78.0, 80.0, 82.0, 84.0,
                     86.0, 88.0, 90.0, 100.0, 130.0, 150.0, 160.0}:
            rows.append({"frame": frame, "body_to_free_boot_before_deg": round(before, 4),
                         "body_to_free_boot_after_deg": round(after, 4),
                         "fade_weight": round(weight, 4),
                         "hip_yaw_correction_deg": round(correction, 4)})

    for obj in parts:
        bag = channelbag(obj)
        for curve in bag.fcurves:
            if curve.data_path in {"location", "rotation_quaternion", "rotation_euler"}:
                for point in curve.keyframe_points:
                    point.interpolation = "LINEAR"
                curve.update()

    scene.name = "Single Axel 1A · early connected free-leg retarget v117"
    scene["prototype_version"] = scene["version"] = "v117"
    scene["v117_revision"] = (
        "Derived from preserved V113. The left free-leg thigh, calf, knee, ankle, and fitted "
        "skate are yaw-retargeted together about the hip from frame 60, with a smooth ramp to "
        "the 60-degree torso-relative cap by frame 82. This closes the V116 near-reversal "
        "window before landing; it is a visual retarget of generic 22-joint motion, not athlete "
        "capture, a coaching angle, or an ISU rule.")
    scene["illustrative_simulated"] = True
    scene.frame_set(90)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
    bpy.ops.export_scene.gltf(
        filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
        export_cameras=True, export_lights=False, export_yup=True,
        use_selection=False, use_active_scene=True, use_visible=True,
        use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
        export_frame_step=1, export_optimize_animation_size=False)
    print("V117_CONNECTED_FREE_LEG_REPORT " + json.dumps({
        "source": str(SOURCE), "blend": str(OUT), "web_glb": str(WEB_OUT),
        "samples": len(samples),
        "ramp_start_frame": RAMP_START, "ramp_end_frame": RAMP_END,
        "max_abs_torso_to_left_boot_after_deg": round(max_heading_after, 4),
        "max_abs_hip_yaw_correction_deg": round(max_correction, 4),
        "max_left_ankle_anchor_error_mm": round(max_anchor_error_mm, 6),
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
        "key_frames": rows,
    }, ensure_ascii=False))


main()
