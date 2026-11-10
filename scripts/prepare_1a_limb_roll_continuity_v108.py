"""Derive V108 by parallel-transporting the two calf mesh roll tracks."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v107.blend"
OUT = ASSET / "single-axel-1a-human-rink-v108.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v108-web.glb"
LOCAL_AXIS = Vector((0.0, 0.0, 1.0))
CALVES = ("Human · left leg volume 4", "Human · right leg volume 4")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


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


def copy_action_if_shared(obj):
    animation = obj.animation_data
    action = animation.action
    if action.users <= 1:
        return
    slot_identifier = animation.action_slot.identifier
    copied = action.copy()
    animation.action = copied
    slot = next((slot for slot in copied.slots
                 if slot.identifier == slot_identifier), None)
    require(slot is not None, f"Copied action lost slot {slot_identifier!r}")
    animation.action_slot = slot


def sampled_axis_track(scene, obj, frames):
    directions = []
    rotations = []
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        rotation = obj.rotation_quaternion.copy().normalized()
        directions.append((rotation @ LOCAL_AXIS).normalized())
        rotations.append(rotation)
    return directions, rotations


def transported_track(directions, initial_rotation):
    rotations = [initial_rotation.copy().normalized()]
    previous_direction = directions[0]
    for direction in directions[1:]:
        # Carry the previous local frame by the shortest rotation between
        # adjacent joint-defined segment axes; this changes roll only.
        rotation = previous_direction.rotation_difference(direction) @ rotations[-1]
        rotation.normalize()
        if rotation.dot(rotations[-1]) < 0.0:
            rotation.negate()
        rotations.append(rotation)
        previous_direction = direction
    return rotations


def rewrite_rotation_keys(obj, frames, rotations):
    bag = channelbag(obj)
    curves = {curve.array_index: curve for curve in bag.fcurves
              if curve.data_path == "rotation_quaternion"}
    require(set(curves) == {0, 1, 2, 3},
            f"Expected four quaternion curves for {obj.name}: {sorted(curves)}")
    points = {
        index: {round(float(point.co.x)): point for point in curve.keyframe_points}
        for index, curve in curves.items()
    }
    for frame, rotation in zip(frames, rotations):
        for axis in range(4):
            point = points[axis].get(frame)
            require(point is not None, f"Missing {obj.name} quaternion key at frame {frame}")
            point.co.y = rotation[axis]
            point.interpolation = "LINEAR"
    for curve in curves.values():
        curve.update()


def angular_step_degrees(first, second):
    relative = first.inverted() @ second
    xyz = math.sqrt(relative.x**2 + relative.y**2 + relative.z**2)
    return math.degrees(2.0 * math.atan2(xyz, abs(relative.w)))


def main():
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(),
            f"Expected V107 source, got {bpy.data.filepath}")
    require(not OUT.exists() and not WEB_OUT.exists(),
            "Refusing to overwrite an existing V108 artifact")
    scene = bpy.context.scene
    require(scene.get("prototype_version") == "v107",
            f"Expected V107 scene, got {scene.get('prototype_version')}")
    default_scene = bpy.data.scenes.get("Scene")
    require(default_scene is not None and
            sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
            "The original default Scene changed")

    frames = list(range(scene.frame_start, scene.frame_end + 1))
    require(len(frames) == 160 and scene.render.fps == 12,
            f"Unexpected V107 frame range or fps: {frames[0]}–{frames[-1]}, {scene.render.fps}")
    report = {}
    for name in CALVES:
        obj = scene.objects.get(name)
        require(obj is not None, f"Missing calf mesh {name}")
        copy_action_if_shared(obj)
        directions, original = sampled_axis_track(scene, obj, frames)
        transported = transported_track(directions, original[0])
        require(all(a.dot(b) >= -1e-6 for a, b in zip(transported, transported[1:])),
                f"Quaternion sign discontinuity in transported track: {name}")
        max_axis_error = max(
            math.degrees(math.acos(max(-1.0, min(1.0,
                (rotation @ LOCAL_AXIS).normalized().dot(direction)))))
            for rotation, direction in zip(transported, directions)
        )
        before = max(angular_step_degrees(a, b) for a, b in zip(original, original[1:]))
        after = max(angular_step_degrees(a, b) for a, b in zip(transported, transported[1:]))
        rewrite_rotation_keys(obj, frames, transported)
        report[name] = {
            "max_integer_step_before_deg": round(before, 4),
            "max_integer_step_after_deg": round(after, 4),
            "max_axis_alignment_error_deg": round(max_axis_error, 6),
        }

    scene.name = "Single Axel 1A · calf roll continuity v108"
    scene["prototype_version"] = "v108"
    scene["version"] = "v108"
    scene["v108_revision"] = (
        "Derived from preserved V107. Left and right calf segment quaternion frames are "
        "parallel-transported along their unchanged 22-joint long-axis directions. This removes "
        "arbitrary axial roll near anti-parallel poses while retaining the sampled segment axes, "
        "positions, skates, rink, cameras, and the original default Scene. All motion remains "
        "illustrative/simulated."
    )
    scene["illustrative_simulated"] = True
    scene.frame_set(76)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
    bpy.ops.export_scene.gltf(
        filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
        export_cameras=True, export_lights=False, export_yup=True,
        use_selection=False, use_active_scene=True, use_visible=True,
        use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
        export_frame_step=1, export_optimize_animation_size=False,
    )

    old_render = (scene.render.resolution_x, scene.render.resolution_y,
                  scene.render.resolution_percentage, scene.render.filepath, scene.camera)
    scene.render.resolution_x, scene.render.resolution_y = 960, 720
    scene.render.resolution_percentage = 75
    previews = []
    for frame, camera_name, view in (
            (63, "Action side view · horizontal follow composition", "side"),
            (64, "Action side view · horizontal follow composition", "side"),
            (63, "Action front view", "front"),
            (64, "Action front view", "front")):
        path = ASSET / f"single-axel-1a-human-rink-v108-frame{frame:03d}-{view}.png"
        require(not path.exists(), f"Refusing to overwrite {path.name}")
        scene.frame_set(frame)
        scene.camera = scene.objects[camera_name]
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        previews.append(str(path))

    (scene.render.resolution_x, scene.render.resolution_y,
     scene.render.resolution_percentage, scene.render.filepath, scene.camera) = old_render
    scene.frame_set(76)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
    bpy.ops.export_scene.gltf(
        filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
        export_cameras=True, export_lights=False, export_yup=True,
        use_selection=False, use_active_scene=True, use_visible=True,
        use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
        export_frame_step=1, export_optimize_animation_size=False,
    )
    print("V108_LIMB_ROLL_REPORT " + json.dumps({
        "source": str(SOURCE), "blend": str(OUT), "web_glb": str(WEB_OUT),
        "segments": report, "previews": previews,
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
    }, ensure_ascii=False))


main()
