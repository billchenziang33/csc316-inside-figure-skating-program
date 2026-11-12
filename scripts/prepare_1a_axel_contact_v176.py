"""Build an illustrative Axel with a left take-off and a right landing from V175."""

import argparse
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_1a_leg_hinge_v175 import (
    PARTS, SIDES, TOE, UP, curves_of, forward_knee, horizontal, leg_matrix,
    min_height, scene_at,
)


START, TAKEOFF, LANDING, FINISH = 42, 60, 92, 111
STEP = 0.25
ROOT = "Skater root · simulated travel and 1.5-turn yaw v8"
ICE = "V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)"
TRACKS = ("location", "rotation_quaternion", "scale")


def smoothstep(first, last, value):
    t = max(0, min(1, (value - first) / (last - first)))
    return t * t * (3 - 2 * t)


def ramp(frame, first, full, taper, last):
    return smoothstep(first, full, frame) * (1 - smoothstep(taper, last, frame))


def mix(a, b, t):
    return a + (b - a) * t


def angle(vector):
    return math.atan2(vector.y, vector.x)


def wrapped(value):
    return math.atan2(math.sin(value), math.cos(value))


def hermite(frame, start, end, value0, value1, slope0, slope1):
    span = end - start
    t = (frame - start) / span
    t2, t3 = t*t, t*t*t
    return ((2*t3 - 3*t2 + 1)*value0 + (t3 - 2*t2 + t)*span*slope0
            + (-2*t3 + 3*t2)*value1 + (t3 - t2)*span*slope1)


def insert_world(obj, matrix, frame, last, channels):
    obj.matrix_world = matrix
    if "rotation_quaternion" in channels:
        q = obj.rotation_quaternion.copy().normalized()
        if obj.name in last and q.dot(last[obj.name]) < 0:
            q.negate()
        obj.rotation_quaternion = q
        last[obj.name] = q.copy()
    for channel in channels:
        obj.keyframe_insert(data_path=channel, frame=frame, group="Axel contact and rotation v176")


def linearize(obj, channels, start=1, end=160):
    for curve in curves_of(obj):
        if curve.data_path in channels:
            for point in curve.keyframe_points:
                if start <= point.co.x <= end:
                    point.interpolation = "LINEAR"
            curve.update()


def roll_on_outside(toe, outward, degrees):
    sign = -1 if toe.cross(outward).z > 0 else 1
    return Quaternion(toe, math.radians(degrees * sign))


def oriented_about(matrix, rotation, point):
    pivot = Matrix.Translation(point)
    return pivot @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-point) @ matrix


def leg_snapshot(scene, parts, skate):
    h, shin, knee, ankle = [scene.objects[name].matrix_world.copy() for name in parts]
    boot, blade = skate
    return {
        "hip": h, "shin": shin, "knee": knee, "ankle": ankle,
        "boot": boot.matrix_world.copy(), "blade": blade.matrix_world.copy(),
    }


def skate_material(name, rgb, metallic, roughness):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*rgb, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = material.diffuse_color
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return material


def finish_skates(skates):
    sole = skate_material("V176 · graphite outsole", (.048, .071, .086), 0, .64)
    support = skate_material("V176 · dark blade mounts", (.065, .103, .131), .18, .41)
    steel = skate_material("V176 · satin steel runner", (.27, .34, .41), .48, .32)
    edge = skate_material("V176 · ground steel and toe picks", (.58, .65, .72), .55, .25)
    for boot, blade in skates.values():
        boot.data = boot.data.copy()
        blade.data = blade.data.copy()
        boot.data.materials.append(sole)
        vertices = np.array([tuple(vertex.co) for vertex in boot.data.vertices])
        sections = np.linspace(vertices[:, 1].min(), vertices[:, 1].max(), 64)
        bottom = [vertices[np.abs(vertices[:, 1] - y) < .009, 2].min() for y in sections]
        for face in boot.data.polygons:
            if face.center.z < np.interp(face.center.y, sections, bottom) + .009:
                face.material_index = 1
        blade.data.materials.clear()
        for material in (steel, support, edge):
            blade.data.materials.append(material)
        for face in blade.data.polygons:
            _, y, z = face.center
            if z > -.152 and y < .183:
                face.material_index = 1
            elif z < -.178 or (y > .189 and z < -.151):
                face.material_index = 2
            else:
                face.material_index = 0


def build(scene, blend, glb):
    assert scene.get("prototype_version") == "v175", "Open the preserved V175 scene"
    assert all(not path.exists() for path in (blend, glb) if path), "Output already exists"
    assert sorted(obj.name for obj in bpy.data.scenes["Scene"].objects) == ["Camera", "Cube", "Light"]
    root = scene.objects[ROOT]
    assert not root.parent and root.rotation_mode == "QUATERNION", "Expected world-space root quaternion"
    torso = scene.objects["Human · shaped jacket torso"]
    ice = scene.objects[ICE]
    ice_top = max((ice.matrix_world @ v.co).z for v in ice.data.vertices)
    parts = {s: [f"Human · {s.lower()} {part}" for part in PARTS] for s in SIDES}
    skates = {s: tuple(scene.objects[f"{s} skate · website {part} v64"] for part in ("boot", "blade"))
              for s in SIDES}
    blade_points = {s: np.array([tuple(v.co) for v in skates[s][1].data.vertices]) for s in SIDES}
    frames = [1 + i * STEP for i in range(637)]
    snapshots, yaw = {}, {}
    for frame in frames:
        scene_at(scene, frame)
        rotation = root.matrix_world.to_quaternion()
        heading = angle(horizontal(rotation @ Vector((1, 0, 0))))
        if yaw:
            previous = yaw[frame - STEP]
            heading = previous + wrapped(heading - previous)
        yaw[frame] = heading
        snapshots[frame] = {
            "root_q": rotation,
            "root_p": root.matrix_world.translation.copy(),
            "torso_forward": horizontal(torso.matrix_world.to_3x3() @ TOE).normalized(),
            "legs": {s: leg_snapshot(scene, parts[s], skates[s]) for s in SIDES},
        }

    travel = horizontal(snapshots[LANDING]["root_p"] - snapshots[TAKEOFF]["root_p"]).normalized()
    takeoff_boot = snapshots[TAKEOFF]["legs"]["Left"]["boot"]
    toe_before = horizontal(takeoff_boot.to_3x3() @ TOE)
    start_yaw = yaw[TAKEOFF] + wrapped(angle(travel) - angle(toe_before))
    spin_direction = 1 if yaw[LANDING] > yaw[TAKEOFF] else -1
    land_yaw = start_yaw + spin_direction * 3 * math.pi
    landing_boot = snapshots[LANDING]["legs"]["Right"]["boot"]
    landing_toe = horizontal(landing_boot.to_3x3() @ TOE)
    landing_delta = wrapped(angle(-travel) - angle(landing_toe) - (land_yaw - yaw[LANDING]))
    finish_yaw = land_yaw + wrapped(yaw[FINISH] - land_yaw)
    start_slope = (yaw[START + STEP] - yaw[START - STEP]) / (2 * STEP)
    finish_slope = (yaw[FINISH + STEP] - yaw[FINISH - STEP]) / (2 * STEP)
    takeoff_slope = spin_direction * math.radians(5)
    land_slope = spin_direction * math.radians(4)

    last = {}
    for frame in frames:
        if frame < 43 or frame > 110:
            continue
        snap = snapshots[frame]
        legs = snap["legs"]
        scene_at(scene, frame)
        source_gaps = {s: min_height(blade_points[s], legs[s]["blade"]) - ice_top for s in SIDES}
        swap = ramp(frame, 47, 53, 62, 73)
        support = ramp(frame, 46, 53, 60, 63)
        gather = ramp(frame, 63, 72, 80, 89)
        check = ramp(frame, 84, 92, 94, 103)
        edge = {"Left": 8 * ramp(frame, 47, 54, 60, 64),
                "Right": 8 * ramp(frame, 85, 91, 104, 110)}
        body_forward = snap["torso_forward"]
        lateral = horizontal(legs["Right"]["hip"].translation - legs["Left"]["hip"].translation).normalized()
        for side, sign in (("Left", -1), ("Right", 1)):
            if max(swap, support, gather, edge[side], check if side == "Right" else 0) == 0:
                continue
            data = legs[side]
            opposite = "Right" if side == "Left" else "Left"
            hip = data["hip"].translation
            old_knee = data["knee"].translation
            old_ankle = data["ankle"].translation
            boot_toe = (data["boot"].to_3x3() @ TOE).normalized()
            outward = sign * lateral
            check_yaw = Quaternion(UP, landing_delta * check if side == "Right" else 0)
            delta = roll_on_outside(check_yaw @ boot_toe, outward, edge[side]) @ check_yaw
            rolled_blade = oriented_about(data["blade"], delta, old_ankle)
            gap = mix(source_gaps[side], source_gaps[opposite], swap)
            if side == "Left":
                gap = mix(gap, .004, support)
            gap = max(.004, gap)
            ankle = old_ankle.copy()
            ankle.z += ice_top + gap - min_height(blade_points[side], rolled_blade)

            forward_offset = (old_ankle - hip).dot(body_forward)
            if side == "Left":
                # The support skate finishes just behind the body's rise.
                stride_target = mix(.025, -.10, smoothstep(52, 60, frame))
                ankle += body_forward * (stride_target - forward_offset) * swap
            else:
                # The free foot swings from behind the body through the take-off.
                stride_target = mix(-.24, .20, smoothstep(51, 61, frame))
                ankle += body_forward * (stride_target - forward_offset) * swap

            if gather:
                midpoint = (legs["Left"]["hip"].translation + legs["Right"]["hip"].translation) / 2
                compact = (midpoint + outward * .111 + body_forward * (sign * .04)
                           - UP * (.56 if side == "Right" else .52))
                ankle = ankle.lerp(compact, gather)
                ankle.z = max(ankle.z, old_ankle.z + ice_top + .004 - min_height(blade_points[side], rolled_blade))

            pole = (horizontal(delta @ boot_toe).normalized() + outward * .20).normalized()
            knee, hinge = forward_knee(hip, ankle, pole, (old_knee-hip).length,
                                      (old_ankle-old_knee).length)
            weight = max(swap, support, gather, min(1, edge[side] / 3), check if side == "Right" else 0)
            # Use the source knee as the edit tapers out.
            knee = old_knee.lerp(knee, weight)
            thigh_axis = (knee - hip).normalized()
            hinge = (ankle - hip).cross(knee - hip).normalized()
            hinge = -hinge
            if abs(thigh_axis.dot(hinge)) > 1e-4 or hinge.length < .99:
                raise RuntimeError(f"Degenerate hinge on {side} frame {frame}")

            thigh_obj, shin_obj, knee_obj, ankle_obj = [scene.objects[name] for name in parts[side]]
            insert_world(thigh_obj, leg_matrix(hip, knee, hinge), frame, last, TRACKS)
            insert_world(shin_obj, leg_matrix(knee, ankle, hinge), frame, last, TRACKS)
            knee_matrix = data["knee"].copy()
            knee_matrix.translation = knee
            insert_world(knee_obj, knee_matrix, frame, last, ("location",))
            ankle_matrix = Matrix.LocRotScale(ankle, delta @ data["ankle"].to_quaternion(),
                                              data["ankle"].to_scale())
            insert_world(ankle_obj, ankle_matrix, frame, last, ("location", "rotation_quaternion"))

    for side in SIDES:
        thigh, shin, knee, ankle = [scene.objects[name] for name in parts[side]]
        for obj, channels in ((thigh, TRACKS), (shin, TRACKS), (knee, ("location",)),
                              (ankle, ("location", "rotation_quaternion"))):
            linearize(obj, channels, 43, 110)

    for frame in frames:
        if frame < START or frame > FINISH:
            continue
        scene_at(scene, frame)
        if frame <= TAKEOFF:
            revised = hermite(frame, START, TAKEOFF, yaw[START], start_yaw, start_slope, takeoff_slope)
        elif frame <= LANDING:
            revised = hermite(frame, TAKEOFF, LANDING, start_yaw, land_yaw, takeoff_slope, land_slope)
        else:
            revised = hermite(frame, LANDING, FINISH, land_yaw, finish_yaw, land_slope, finish_slope)
        new_rotation = Quaternion(UP, revised - yaw[frame]) @ snapshots[frame]["root_q"]
        if root.name in last and new_rotation.dot(last[root.name]) < 0:
            new_rotation.negate()
        last[root.name] = new_rotation.copy()
        root.rotation_quaternion = new_rotation
        root.keyframe_insert(data_path="rotation_quaternion", frame=frame, group="Axel yaw v176")
    linearize(root, ("rotation_quaternion",), START, FINISH)

    scene["prototype_version"] = "v176"
    scene["source_version"] = "v175"
    scene["axel_contact"] = "Illustrative left forward outside take-off, 1.5-turn root yaw, and right backward outside landing."
    scene.name = "Single Axel 1A · take-off and landing v176"
    finish_skates(skates)
    scene_at(scene, LANDING)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    if glb:
        bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", export_yup=True,
                                  export_animations=True, export_animation_mode="SCENE",
                                  export_frame_range=True, export_optimize_animation_size=False,
                                  export_cameras=True, use_active_scene=True,
                                  use_visible=True, use_renderable=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--glb", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    build(bpy.context.scene, args.blend.resolve(), args.glb.resolve() if args.glb else None)
