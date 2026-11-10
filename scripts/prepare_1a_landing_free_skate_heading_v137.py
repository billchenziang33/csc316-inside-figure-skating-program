"""Refine free-skate heading only through landing and the exit glide."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v128.blend"
OUT = ASSET / "single-axel-1a-human-rink-v137.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v137-web.glb"
FORWARD_LOCAL = Vector((0.0, -1.0, 0.0))
WORLD_UP = Vector((0.0, 0.0, 1.0))
RAMP_START, RAMP_END = 60.0, 76.0
APEX_YAW_LIMIT = 45.0
LANDING_YAW_LIMIT = 30.0
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
            f"Expected V128 source, got {bpy.data.filepath}")
    require(not OUT.exists() and not WEB_OUT.exists(),
            "Refusing to overwrite an existing candidate")
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    require(scene.get("prototype_version") == "v128",
            f"Expected V128 scene, got {scene.get('prototype_version')}")
    default_scene = bpy.data.scenes.get("Scene")
    require(default_scene is not None and
            sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
            "The original default Scene signature changed")

    parts = [scene.objects[name] for name in LEG_PARTS]
    body_anchor = scene.objects["Body anchor · pelvis-origin poses"]
    require(all(obj.parent == body_anchor for obj in parts[:-1]),
            "The left-leg meshes/joints no longer share the body anchor")
    skate, ankle = parts[-1], scene.objects["Human · left ankle joint"]
    boot = scene.objects["Left skate · website boot v64"]
    blade = scene.objects["Left skate · website blade v64"]
    torso = scene.objects["Human · shaped jacket torso"]
    require(skate.parent == ankle and boot.parent == skate and blade.parent == skate,
            "The ankle-parented left boot/blade hierarchy changed")
    require(scene.frame_start == 1 and scene.frame_end == 160,
            "Unexpected source frame range")

    pivot_obj = scene.objects["Human · left leg volume 3"]
    reference_frames = [76.0, 82.0, 86.0, 87.0, 88.0, 89.0, 90.0, 110.0, 150.0]
    samples = []
    count = (scene.frame_end - scene.frame_start) * 4
    for index in range(count + 1):
        frame = scene.frame_start + index * 0.25
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        body = horizontal(torso.matrix_world.to_3x3() @ FORWARD_LOCAL)
        heading = horizontal(boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
        require(body is not None and heading is not None,
                f"Degenerate body or free-skate heading at frame {frame:.2f}")
        transforms = []
        for obj in parts:
            world = obj.matrix_world.copy()
            transforms.append({
                "object": obj,
                "location": world.translation.copy(),
                "rotation": world.to_quaternion().normalized(),
                "scale": world.to_scale(),
            })
        samples.append({
            "frame": frame,
            "pivot": pivot_obj.matrix_world.translation.copy(),
            "body": body,
            "before_yaw": signed_angle(body, heading),
            "transforms": transforms,
        })

    for obj in parts:
        isolate_action(obj)

    previous_quaternions = {obj.name: None for obj in parts}
    max_abs_after = max_apex = max_landing = max_correction = max_anchor_error_mm = 0.0
    report_rows = []
    for sample in samples:
        frame = sample["frame"]
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        before = sample["before_yaw"]
        cap_blend = smoothstep((frame - 86.0) / 4.0)
        yaw_limit = APEX_YAW_LIMIT + (LANDING_YAW_LIMIT - APEX_YAW_LIMIT) * cap_blend
        target = max(-yaw_limit, min(yaw_limit, before))
        if frame <= RAMP_END:
            weight = smoothstep((frame - RAMP_START) / (RAMP_END - RAMP_START))
        elif frame <= 80.0:
            weight = 1.0 - smoothstep((frame - RAMP_END) / 4.0)
        elif frame < 86.0:
            weight = 0.0
        else:
            weight = cap_blend
        correction = (target - before) * weight
        pivot = sample["pivot"]
        hip_fraction = 1.0 - (2.0 / 3.0) * cap_blend
        hip_correction = correction * hip_fraction
        ankle_correction = correction - hip_correction
        hip_yaw = Quaternion(WORLD_UP, math.radians(hip_correction))
        ankle_yaw = Quaternion(WORLD_UP, math.radians(ankle_correction))
        ankle_source = next(item for item in sample["transforms"]
                            if item["object"].name == "Human · left ankle joint")
        ankle_pivot = pivot + hip_yaw @ (ankle_source["location"] - pivot)

        for item in sample["transforms"]:
            obj = item["object"]
            location = pivot + hip_yaw @ (item["location"] - pivot)
            rotation = (hip_yaw @ item["rotation"]).normalized()
            if obj == skate and abs(ankle_correction) > 1e-8:
                location = ankle_pivot + ankle_yaw @ (location - ankle_pivot)
                rotation = (ankle_yaw @ rotation).normalized()
            obj.matrix_world = Matrix.LocRotScale(location, rotation, item["scale"])
            bpy.context.view_layer.update()
            obj.keyframe_insert(data_path="location", frame=frame,
                                group="V137 landing free-skate alignment")
            rotation_path = ("rotation_quaternion" if obj.rotation_mode == "QUATERNION"
                             else "rotation_euler")
            current = (obj.rotation_quaternion.copy().normalized()
                       if rotation_path == "rotation_quaternion"
                       else obj.rotation_euler.to_quaternion().normalized())
            previous = previous_quaternions[obj.name]
            if previous is not None and current.dot(previous) < 0.0:
                if rotation_path == "rotation_quaternion":
                    current.negate()
                    obj.rotation_quaternion = current
            obj.keyframe_insert(data_path=rotation_path, frame=frame,
                                group="V137 landing free-skate alignment")
            previous_quaternions[obj.name] = current.copy()

        bpy.context.view_layer.update()
        after_axis = horizontal(boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
        after = signed_angle(sample["body"], after_axis)
        fit_error = (boot.matrix_world @ (Vector((0.0, 0.045, 0.035)) * 1.8) -
                     ankle.matrix_world.translation).length * 1000.0
        max_anchor_error_mm = max(max_anchor_error_mm, fit_error)
        max_abs_after = max(max_abs_after, abs(after))
        if frame == RAMP_END:
            max_apex = abs(after)
        if frame >= 90.0:
            max_landing = max(max_landing, abs(after))
        max_correction = max(max_correction, abs(correction))
        if frame in reference_frames:
            report_rows.append({
                "frame": frame,
                "before_body_to_free_skate_deg": round(before, 4),
                "after_body_to_free_skate_deg": round(after, 4),
                "yaw_limit_deg": round(yaw_limit, 4),
                "hip_yaw_change_deg": round(hip_correction, 4),
                "ankle_yaw_change_deg": round(ankle_correction, 4),
            })

    for obj in parts:
        bag = channelbag(obj)
        for curve in bag.fcurves:
            if curve.data_path in {"location", "rotation_quaternion", "rotation_euler"}:
                for point in curve.keyframe_points:
                    point.interpolation = "LINEAR"
                curve.update()

    scene.name = "Single Axel 1A · landing free-skate direction refined v137"
    scene["prototype_version"] = scene["version"] = "v137"
    scene["v137_revision"] = (
        "Derived from V128. Retains V133's 45-degree visual cap at the apex and descent, "
        "then smoothly tightens the model-left free-leg and ankle-fitted skate to a 30-degree "
        "torso-relative cap from frames 86–90 for landing and exit glide. Landing correction is "
        "split between a one-third hip/leg turn and a two-thirds skate turn about the ankle, "
        "preserving leg clearance while keeping boot/blade assembly rigid. This limits the visible rearward "
        "toe direction from side/three-quarter views while avoiding the flight crossing window. "
        "The 20-degree value is an illustrative visual target, not a coaching rule or athlete measurement."
    )
    scene["illustrative_simulated"] = True
    scene["technical_reference_limit"] = (
        "Public slow-motion Axel footage informed phase order only: entry curve, free-leg swing, "
        "compact flight, opposite-foot backward landing, and recovery glide. It does not establish "
        "a universal torso-to-free-skate yaw angle. V137's landing cap is a visual review target only."
    )
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
        "version": scene["prototype_version"],
        "retargeted_objects": [obj.name for obj in parts],
        "sample_count": len(samples), "apex_yaw_limit_deg": APEX_YAW_LIMIT,
        "landing_yaw_limit_deg": LANDING_YAW_LIMIT,
        "maximum_abs_body_to_free_skate_yaw_all_frames_deg": round(max_abs_after, 4),
        "maximum_abs_body_to_free_skate_yaw_at_apex_deg": round(max_apex, 4),
        "maximum_abs_body_to_free_skate_yaw_landing_glide_deg": round(max_landing, 4),
        "maximum_hip_yaw_correction_deg": round(max_correction, 4),
        "maximum_left_ankle_fit_error_mm": round(max_anchor_error_mm, 6),
        "key_frames": report_rows,
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
        "pose_status": "illustrative/simulated",
    }
    print("AXEL_LANDING_FREE_SKATE_ALIGNMENT_V137_BUILD " + json.dumps(report, ensure_ascii=False))
    require(max_apex <= APEX_YAW_LIMIT + 0.01,
            "The free skate exceeds the V137 apex visual yaw cap")
    require(max_landing <= LANDING_YAW_LIMIT + 0.01,
            "The free skate exceeds the V137 landing/glide visual yaw cap")
    require(max_anchor_error_mm <= 0.01,
            "The retarget moved the free skate away from its ankle")
    require(scene.frame_current == 90,
            "V137 should open on the landing inspection frame")


main()
