"""Rebuild the visible V174 leg chains with forward knee hinges and lateral clearance."""

import argparse
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector


SIDES = ("Left", "Right")
PARTS = ("leg volume 3", "leg volume 4", "knee joint", "ankle joint")
UP = Vector((0, 0, 1))
TOE = Vector((0, -1, 0))
STEP = 0.25
FILTER = (1, 4, 6, 4, 1)
STRIDE = 3  # 3/4 of a source frame between temporal filter taps.


def horizontal(vector):
    return Vector((vector.x, vector.y, 0))


def smooth(values, index):
    indices = [max(0, min(len(values) - 1, index + offset * STRIDE))
               for offset in range(-2, 3)]
    return sum((values[j] * w for j, w in zip(indices, FILTER)), values[0] * 0) / sum(FILTER)


def soft_positive(x, transition):
    # C1 ramp with an exact zero outside the separation band.
    if x <= -transition:
        return 0.0
    if x >= transition:
        return x
    return (x + transition) ** 2 / (4 * transition)


def scene_at(scene, frame):
    scene.frame_set(math.floor(frame), subframe=frame % 1)


def leg_matrix(start, end, lateral):
    delta = end - start
    axis = delta.normalized()
    sagittal = axis.cross(lateral)
    matrix = Matrix((lateral, sagittal, axis * delta.length)).transposed().to_4x4()
    matrix.translation = start
    return matrix


def forward_knee(hip, ankle, forward, l1, l2):
    """Find the forward point on the hip/ankle two-sphere intersection."""
    travel = ankle - hip
    distance = travel.length
    axis = travel / distance
    pole = (forward - axis * forward.dot(axis)).normalized()
    # Preserve nominal reach wherever possible. Blend small length changes
    # when a baked V174 ankle is unusually close to, or far from, the hip.
    max_length = distance / 0.978
    min_length = distance / 0.996
    old_length = l1 + l2
    limit_for_deep_flexion = max_length / 0.72
    length = (old_length + soft_positive(min_length - old_length, 0.018)
              - soft_positive(old_length - limit_for_deep_flexion, 0.018))
    l1, l2 = l1 * length / old_length, l2 * length / old_length
    along = (l1*l1 - l2*l2 + distance*distance) / (2*distance)
    radius = math.sqrt(max(0, l1*l1 - along*along))
    return hip + axis * along + pole * radius, pole.cross(axis).normalized()


def smooth_rotation(values, index):
    reference = values[index]
    aligned = [q if q.dot(reference) >= 0 else -q for q in
               (values[max(0, min(len(values)-1, index + step*STRIDE))] for step in range(-2, 3))]
    return type(reference)([sum(q[j] * w for q, w in zip(aligned, FILTER)) for j in range(4)]).normalized()


def min_height(points, matrix):
    x, y, z, t = matrix[2]
    return float(np.min(x*points[:,0] + y*points[:,1] + z*points[:,2])) + t


def resize_trouser_segment(obj, radii):
    """Shape the existing ring mesh into a tapered garment segment."""
    obj.data = obj.data.copy()
    for v in obj.data.vertices:
        x, y, z = v.co
        radial = math.hypot(x, y)
        if radial < 1e-8:
            continue
        for (z0, r0), (z1, r1) in zip(radii, radii[1:]):
            if z <= z1 + 1e-6:
                target = r0 + (r1-r0) * (z-z0)/(z1-z0)
                v.co.x *= target / radial
                v.co.y *= target / radial
                break
    obj.data.update()


def put_world(obj, matrix, frame, last, channels):
    obj.matrix_world = matrix
    if "rotation_quaternion" in channels:
        q = obj.rotation_quaternion.copy().normalized()
        if obj.name in last and q.dot(last[obj.name]) < 0:
            q.negate()
        obj.rotation_quaternion = q
        last[obj.name] = q.copy()
    for channel in channels:
        obj.keyframe_insert(data_path=channel, frame=frame, group="Forward knee hinge v175")


def curves_of(obj):
    anim = obj.animation_data
    if anim is None or anim.action is None:
        return
    for layer in anim.action.layers:
        for strip in layer.strips:
            if strip.type == "KEYFRAME":
                bag = strip.channelbag(anim.action_slot)
                if bag is not None:
                    yield from bag.fcurves


def run(out, glb):
    scene = bpy.context.scene
    if scene.get("prototype_version") != "v174" or (scene.frame_start, scene.frame_end) != (1, 160):
        raise RuntimeError("Open the preserved V174 1–160 frame file")
    if sorted(o.name for o in bpy.data.scenes["Scene"].objects) != ["Camera", "Cube", "Light"]:
        raise RuntimeError("Default scene signature changed")
    if any(path is not None and path.exists() for path in (out, glb)):
        raise FileExistsError("Refusing to overwrite an existing version")
    legs = {s: [scene.objects[f"Human · {s.lower()} {name}"] for name in PARTS] for s in SIDES}
    boots = {s: scene.objects[f"{s} skate · website boot v64"] for s in SIDES}
    blades = {s: scene.objects[f"{s} skate · website blade v64"] for s in SIDES}
    ice = scene.objects["V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)"]
    ice_z = max((ice.matrix_world @ v.co).z for v in ice.data.vertices)
    blade_points = {s:np.array([tuple(v.co) for v in blades[s].data.vertices]) for s in SIDES}
    frames = [1 + i * STEP for i in range(637)]
    source = []
    for frame in frames:
        scene_at(scene, frame)
        row = {}
        for side in SIDES:
            thigh, calf, knee, ankle = legs[side]
            h, k, a = [o.matrix_world.translation.copy() for o in (thigh,knee,ankle)]
            blade_world = blades[side].matrix_world.copy()
            # Source has long intervals at a few millimetres above modeled ice.
            zmin = min_height(blade_points[side], blade_world)
            row[side] = (h, k, a, knee.matrix_world.copy(), ankle.matrix_world.copy(),
                         boots[side].matrix_world.to_quaternion().normalized(), zmin - ice_z,
                         blade_world, boots[side].matrix_world.copy())
        source.append(row)

    for side, (thigh, calf, knee, ankle) in legs.items():
        resize_trouser_segment(thigh, [(0, .074), (.25, .073), (.66, .062), (1, .055)])
        resize_trouser_segment(calf, [(0, .055), (.26, .059), (.57, .053), (1, .033)])
        knee.data = knee.data.copy()
        for v in knee.data.vertices:
            v.co *= .056 / .078
        for obj in (thigh, calf, knee, ankle):
            if obj.animation_data.action.users != 1:
                raise RuntimeError(f"Shared animation on {obj.name}")
        thigh.rotation_mode = calf.rotation_mode = ankle.rotation_mode = "QUATERNION"

    # Smooth approach jitter; keep the source flight and landing boot attitude.
    # Allocate any lateral clearance to the higher/free foot.
    locs = {s:[row[s][2] for row in source] for s in SIDES}
    attitudes = {s:[row[s][5] for row in source] for s in SIDES}
    boot_points = {s: np.array([tuple(v.co) for v in boots[s].data.vertices]) for s in SIDES}
    lengths = {s:[((row[s][1]-row[s][0]).length, (row[s][2]-row[s][1]).length)
                  for row in source] for s in SIDES}
    for side in SIDES:
        lengths[side] = [list(v) for v in zip(*lengths[side])]
    shifts, rotations = [], []
    for i, row in enumerate(source):
        lateral = horizontal(row["Right"][0] - row["Left"][0]).normalized()
        approach = max(0, min(1, (55 - frames[i])/9))
        approach *= approach*(3 - 2*approach)
        ankles, deltas, boot_inner_edge = {}, {}, {}
        for s in SIDES:
            _, _, a, _, _, boot_q, gap, blade_world, boot_world = row[s]
            target_q = boot_q.slerp(smooth_rotation(attitudes[s], i), approach)
            delta = target_q @ boot_q.inverted()
            candidate = a.lerp(smooth(locs[s], i), approach)
            if approach:
                rotated = Matrix.Translation(a) @ delta.to_matrix().to_4x4() @ Matrix.Translation(-a) @ blade_world
                height_delta = min_height(blade_points[s], rotated) - ice_z - gap
                # Preserve near-ice support; damp isolated vertical excursions
                # when a skate is well clear of the surface.
                contact = 1 - max(0, min(1, (gap - .009)/.035))
                contact *= contact*(3 - 2*contact)
                candidate.z += contact * (a.z - height_delta - candidate.z)
                candidate.z = max(candidate.z, a.z - gap - height_delta + .003)
            ankles[s] = candidate
            deltas[s] = (delta, target_q)
            # Measure the inside of the actual rotated boot rather than
            # assuming a symmetric shape centred on the ankle.
            axis = (delta.inverted() @ lateral)
            local_axis = boot_world.to_3x3().transposed() @ axis
            xyz = boot_points[s]
            projection = local_axis.x*xyz[:,0] + local_axis.y*xyz[:,1] + local_axis.z*xyz[:,2]
            projection += axis.dot(boot_world.translation - a)
            boot_inner_edge[s] = (float(np.max(projection)) if s == "Left"
                                  else float(np.min(projection)))
        spread = (ankles["Right"] - ankles["Left"]).dot(lateral)
        midpoint = (row["Left"][0] + row["Right"][0]) / 2
        boot_width = boot_inner_edge["Left"] - boot_inner_edge["Right"]
        off = soft_positive(max(.175, boot_width + .018) - spread, .025)
        weight = .5 + .5*math.tanh((row["Left"][6]-row["Right"][6])/.080)
        targets = {"Left": ankles["Left"] - lateral * off * weight,
                   "Right": ankles["Right"] + lateral * off * (1-weight)}
        for side, sign in (("Left", -1), ("Right", 1)):
            # A skate may cross in depth, but don't push a calf across the
            # opposite hip's lane when the free skate is passing closely.
            margin = (targets[side] - midpoint).dot(lateral) * sign
            targets[side] += sign * lateral * soft_positive(.065 - margin, .02)
        shifts.append({s: targets[s]-row[s][2] for s in SIDES})
        rotations.append(deltas)

    pose_channels = ("location", "rotation_quaternion", "scale")
    last = {}
    for i, frame in enumerate(frames):
        scene_at(scene, frame)
        row = source[i]
        lateral = horizontal(row["Right"][0] - row["Left"][0]).normalized()
        extra_hip = soft_positive(.173 - (row["Right"][0]-row["Left"][0]).dot(lateral), .015)
        for side, sign in (("Left", -1), ("Right", 1)):
            thigh, calf, knee, ankle = legs[side]
            hip, _, a, knee_world, ankle_world, _, _, _, _ = row[side]
            hip = hip + sign * lateral * extra_hip/2
            delta, foot_rotation = rotations[i][side]
            foot_forward = horizontal(foot_rotation @ TOE).normalized()
            a = a + shifts[i][side]
            # Place the pole just outside the sagittal plane to give the two
            # knees room while keeping their flexion directed towards the toe.
            pole = (foot_forward + sign * lateral * .20).normalized()
            l1, l2 = [smooth(v, i) * .35 + target * .65
                      for v, target in zip(lengths[side], (.335, .355))]
            k, hinge_axis = forward_knee(hip, a, pole, l1, l2)
            put_world(thigh, leg_matrix(hip, k, hinge_axis), frame, last, pose_channels)
            put_world(calf, leg_matrix(k, a, hinge_axis), frame, last, pose_channels)
            knee_world.translation = k
            ankle_world = Matrix.LocRotScale(a, delta @ ankle_world.to_quaternion(), ankle_world.to_scale())
            put_world(knee, knee_world, frame, last, ("location",))
            put_world(ankle, ankle_world, frame, last, ("location", "rotation_quaternion"))
    for thigh, calf, knee, ankle in legs.values():
        for obj in (thigh, calf, knee, ankle):
            for curve in curves_of(obj):
                if (curve.data_path == "location" or
                        obj in (thigh, calf) and curve.data_path in pose_channels or
                        obj == ankle and curve.data_path == "rotation_quaternion"):
                    for point in curve.keyframe_points:
                        point.interpolation = "LINEAR"
                    curve.update()

    scene.name = "Single Axel 1A · forward knee hinges v175"
    scene["prototype_version"] = scene["version"] = "v175"
    scene["leg_hinge_v175"] = (
        "Reconstructs the visible knee centres on the skate-forward side of each hip/ankle line. "
        "Damps approach jitter and introduces horizontal foot clearance "
        "and a tapered trouser shape. Root track, cameras, rink and jump event timing come from V174. "
        "Illustrative/simulated motion; no Beijing 2022 athlete capture.")
    scene["illustrative_simulated"] = True
    scene_at(scene, 34)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), check_existing=False)
    if glb is not None:
        bpy.ops.export_scene.gltf(
            filepath=str(glb), export_format="GLB", export_animations=True,
            export_cameras=True, export_lights=False, export_yup=True,
            use_selection=False, use_active_scene=True, use_visible=True,
            use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
            export_frame_step=1, export_optimize_animation_size=False,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--glb", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    run(args.blend.resolve(), args.glb.resolve() if args.glb is not None else None)
