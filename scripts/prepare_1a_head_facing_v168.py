"""Derive V168 by keeping the skater's visible face with the torso heading."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v167.blend"
OUT = ASSET / "single-axel-1a-human-rink-v168.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v168-web.glb"
SAMPLE_STEP = 0.25
FACE_MAX_YAW = 18.0
WORLD_UP = Vector((0.0, 0.0, 1.0))
TORSO_FORWARD_LOCAL = Vector((0.0, -1.0, 0.0))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def horizontal(vector):
    value = Vector((vector.x, vector.y, 0.0))
    return value.normalized() if value.length > 1e-8 else None


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    if a is None or b is None:
        raise RuntimeError("Degenerate face or torso heading")
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
    require(animation is not None and animation.action is not None,
            f"Missing animation for {obj.name}")
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


def face_heading(nose, left_eye, right_eye):
    eyes = (left_eye.matrix_world.translation + right_eye.matrix_world.translation) * 0.5
    return nose.matrix_world.translation - eyes


def main():
    require(not OUT.exists() and not WEB_OUT.exists(),
            "Refusing to overwrite an existing V168 artifact")
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(),
            f"Expected V167 source, got {bpy.data.filepath}")

    scene = bpy.context.scene
    require(scene.get("prototype_version") == "v167", "Expected V167 source scene")
    require((scene.frame_start, scene.frame_end) == (1, 160),
            "Unexpected source animation range")
    default_scene = bpy.data.scenes.get("Scene")
    require(default_scene is not None and
            sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
            "The original default Scene signature changed")

    body_anchor = scene.objects["Body anchor · pelvis-origin poses"]
    head = scene.objects["Head · detailed generic human sculpt"]
    left_eye = scene.objects["Head · left eye white"]
    right_eye = scene.objects["Head · right eye white"]
    nose = scene.objects["Head · nose tip"]
    torso = scene.objects["Human · shaped jacket torso"]
    head_parts = [obj for obj in scene.objects
                  if obj.parent == body_anchor and
                  (obj.name.startswith("Head ·") or obj.name.startswith("Hair ·"))]
    require(len(head_parts) >= 12 and head in head_parts,
            "Expected the complete animated head, face and hair assembly")
    require(all(obj.animation_data and obj.animation_data.action for obj in head_parts),
            "A head/face/hair object is missing its source animation")

    total = round((scene.frame_end - scene.frame_start) / SAMPLE_STEP)
    samples = []
    for index in range(total + 1):
        frame = scene.frame_start + index * SAMPLE_STEP
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        torso_axis = torso.matrix_world.to_3x3() @ TORSO_FORWARD_LOCAL
        yaw = signed_angle(torso_axis, face_heading(nose, left_eye, right_eye))
        target_yaw = max(-FACE_MAX_YAW, min(FACE_MAX_YAW, yaw))
        delta = Quaternion(WORLD_UP, math.radians(target_yaw - yaw))
        pivot = head.matrix_world.translation.copy()
        transforms = []
        for obj in head_parts:
            world = obj.matrix_world.copy()
            transforms.append((obj, world.translation.copy(),
                               world.to_quaternion().normalized(), world.to_scale()))
        samples.append({"frame": frame, "before_yaw": yaw, "target_yaw": target_yaw,
                        "delta": delta, "pivot": pivot, "transforms": transforms})

    for obj in head_parts:
        isolate_action(obj)
        obj.rotation_mode = "QUATERNION"

    previous = {obj.name: None for obj in head_parts}
    rows = []
    for sample in samples:
        frame = sample["frame"]
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        pivot, delta = sample["pivot"], sample["delta"]
        for obj, location, rotation, scale in sample["transforms"]:
            obj.matrix_world = Matrix.LocRotScale(
                pivot + delta @ (location - pivot), (delta @ rotation).normalized(), scale)
            bpy.context.view_layer.update()
            obj.keyframe_insert(data_path="location", frame=frame,
                                group="Head direction correction v168")
            rotation = obj.rotation_quaternion.copy().normalized()
            old = previous[obj.name]
            if old is not None and rotation.dot(old) < 0.0:
                rotation.negate()
                obj.rotation_quaternion = rotation
            obj.keyframe_insert(data_path="rotation_quaternion", frame=frame,
                                group="Head direction correction v168")
            previous[obj.name] = rotation.copy()

        bpy.context.view_layer.update()
        face_yaw = signed_angle(
            torso.matrix_world.to_3x3() @ TORSO_FORWARD_LOCAL,
            face_heading(nose, left_eye, right_eye))
        rows.append({"frame": frame, "before_yaw_deg": sample["before_yaw"],
                     "after_yaw_deg": face_yaw})

    for obj in head_parts:
        set_linear_animation(obj)
    scene.name = "Single Axel 1A · head facing correction v168"
    scene["prototype_version"] = scene["version"] = "v168"
    scene["head_facing_v168"] = (
        "Derived from preserved V167. The visible head/face/hair assembly is rotated together "
        "about the head center so the face remains within 18 degrees of torso-forward. This "
        "visual tolerance is an illustrative readability choice, not a coaching or biomechanics "
        "standard. Body, root path, limbs, skates, event markers and rink are unchanged.")
    scene["illustrative_simulated"] = True
    scene["technical_reference_limit"] = (
        "Public Axel coaching analysis discusses head position at take-off and upper-body "
        "deceleration at landing, but does not prescribe a numeric head-to-torso yaw. The "
        "correction is for visual coherence only; all project motion remains illustrative/simulated.")

    scene.frame_set(92)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
    bpy.ops.export_scene.gltf(
        filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
        export_cameras=True, export_lights=False, export_yup=True,
        use_selection=False, use_active_scene=True, use_visible=True,
        use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
        export_frame_step=1, export_optimize_animation_size=False)

    key_frames = (47.0, 50.0, 70.0, 78.0, 83.0, 87.0, 92.0, 120.0, 136.0)
    report = {
        "source_version": "v167", "version": scene.get("prototype_version"),
        "sample_step_frames": SAMPLE_STEP, "sample_count": len(rows),
        "head_parts": [obj.name for obj in head_parts],
        "max_abs_face_to_torso_deg": round(max(abs(row["after_yaw_deg"])
                                                for row in rows), 5),
        "max_abs_head_correction_deg": round(max(abs(row["after_yaw_deg"] -
                                                      row["before_yaw_deg"])
                                                  for row in rows), 5),
        "key_frames": [row for row in rows if row["frame"] in key_frames],
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
        "blend": str(OUT), "web_glb": str(WEB_OUT),
        "status": "illustrative/simulated candidate; visual and alignment audits pending",
    }
    print("HEAD_FACING_V168 " + json.dumps(report, ensure_ascii=False))


main()
