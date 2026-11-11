"""Audit knee flexion, visible cross-leg surfaces, skate attitude and ice clearance."""

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


TOE = Vector((0, -1, 0))
BLADE_TOE = Vector((0, 1, 0))
UP = Vector((0, 0, 1))
SIDES = ("left", "right")
PARTS = ("thigh", "calf", "knee", "ankle", "boot", "blade", "laces", "tongue")


def flat(vector):
    return Vector((vector.x, vector.y, 0)).normalized()


def q_step(a, b):
    return math.degrees(2 * math.acos(min(1, abs(a.dot(b)))))


def aabb(obj):
    bounds = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
    return [(min(p[axis] for p in bounds), max(p[axis] for p in bounds)) for axis in range(3)]


def intersects(bounds_a, bounds_b):
    return all(low_a <= high_b and low_b <= high_a
               for (low_a, high_a), (low_b, high_b) in zip(bounds_a, bounds_b))


def mesh_tree(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        return BVHTree.FromPolygons([evaluated.matrix_world @ v.co for v in mesh.vertices],
                                    [tuple(p.vertices) for p in mesh.polygons], epsilon=1e-6)
    finally:
        evaluated.to_mesh_clear()


def audit(path, collision_stride):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    if (scene.frame_start, scene.frame_end) != (1, 160):
        raise RuntimeError("Expected 160 frame prototype")
    assert sorted(obj.name for obj in bpy.data.scenes["Scene"].objects) == ["Camera", "Cube", "Light"]
    legs = {side: dict(zip(PARTS, [scene.objects[f"Human · {side} {part}"] for part in
                                  ("leg volume 3", "leg volume 4", "knee joint", "ankle joint")]
                      + [scene.objects[f"{side.title()} skate · website {part} v64"] for part in PARTS[4:]]))
            for side in SIDES}
    torso = scene.objects["Human · shaped jacket torso"]
    ice = scene.objects["V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)"]
    ice_z = max((ice.matrix_world @ v.co).z for v in ice.data.vertices)
    blade_xyz = {s:np.array([tuple(v.co) for v in legs[s]["blade"].data.vertices]) for s in SIDES}
    rows = {s:{"reverse_bend_samples": 0, "min_forward_mm": [float("inf"), 0],
               "minimum_blade_gap_mm": [float("inf"), 0], "toe_torso_max_deg": [0, 0],
               "boot_blade_yaw_max_deg": [0, 0], "ankle_fit_max_mm": [0, 0],
               "max_joint_step_deg": {}, "frame_steps_deg": {}, "blade_gap_mm_at_events": {}}
            for s in SIDES}
    prior, collisions = {}, {}
    for i in range(2545):
        frame = 1 + i/16
        scene.frame_set(int(frame), subframe=frame%1)
        for side, parts in legs.items():
            row = rows[side]
            h, k, a = [parts[p].matrix_world.translation for p in ("thigh", "knee", "ankle")]
            axis = (a - h).normalized()
            forward = flat(parts["boot"].matrix_world.to_3x3() @ TOE)
            pole = (forward - axis * forward.dot(axis)).normalized()
            bend = (k - h).dot(pole) * 1000
            row["min_forward_mm"] = min(row["min_forward_mm"], [round(bend, 4), frame])
            if bend < -5:
                row["reverse_bend_samples"] += 1
            x, y, z, t = parts["blade"].matrix_world[2]
            xyz = blade_xyz[side]
            gap = (float(np.min(x*xyz[:,0] + y*xyz[:,1] + z*xyz[:,2])) + t - ice_z) * 1000
            row["minimum_blade_gap_mm"] = min(row["minimum_blade_gap_mm"], [round(gap, 4), frame])
            if frame in (60, 76, 87, 90, 92, 100, 136):
                row["blade_gap_mm_at_events"][str(int(frame))] = round(gap, 4)
            toe_axis = flat(torso.matrix_world.to_3x3() @ TOE)
            blade_axis = flat(parts["blade"].matrix_world.to_3x3() @ BLADE_TOE)
            row["toe_torso_max_deg"] = max(row["toe_torso_max_deg"],
                                           [round(math.degrees(toe_axis.angle(forward)), 4), frame])
            row["boot_blade_yaw_max_deg"] = max(row["boot_blade_yaw_max_deg"],
                                                [round(math.degrees(blade_axis.angle(forward)), 4), frame])
            anchor = parts["boot"].matrix_world @ (Vector((0, .045, .035)) * 1.8)
            row["ankle_fit_max_mm"] = max(row["ankle_fit_max_mm"], [round((anchor-a).length*1000, 5), frame])
            if i % 16 == 0:
                for name in ("thigh", "calf", "boot"):
                    q = parts[name].matrix_world.to_quaternion().normalized()
                    key = (side, name)
                    if key in prior:
                        step = round(q_step(prior[key], q), 3)
                        row["max_joint_step_deg"][name] = max(row["max_joint_step_deg"].get(name, [0, 0]),
                                                               [step, int(frame)])
                        if frame in (17, 35, 40, 51, 77, 80, 87, 92):
                            row["frame_steps_deg"].setdefault(str(int(frame)), {})[name] = step
                    prior[key] = q
        if i % collision_stride:
            continue
        left, right = legs["left"], legs["right"]
        bounds = {obj.name:aabb(obj) for obj in (*left.values(), *right.values())}
        cache = {}
        for (ln, a), (rn, b) in itertools.product(left.items(), right.items()):
            if not intersects(bounds[a.name], bounds[b.name]):
                continue
            for obj in (a, b):
                if obj.name not in cache:
                    cache[obj.name] = mesh_tree(obj)
            n = len(cache[a.name].overlap(cache[b.name]))
            if n:
                result = collisions.setdefault(f"L {ln}/R {rn}", {"poses": 0, "peak": [0, 0]})
                result["poses"] += 1
                result["peak"] = max(result["peak"], [n, frame])
    return {"path": str(path), "version": scene.get("prototype_version"), "motion_poses": 2545,
            "collision_poses": 2544//collision_stride + 1, "legs": rows, "intersections": collisions,
            "scope": "Discrete evaluated-mesh surface intersection samples; same-leg cuff fit and screen-space occlusion are separate."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--collision-step", type=int, default=8, choices=(2,4,8),
                        help="number of sixteenths of a frame between collision samples")
    parser.add_argument("--require-corrected", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    result = audit(args.file.resolve(), args.collision_step)
    print("AXEL_LEG_AUDIT " + json.dumps(result, ensure_ascii=False))
    if args.require_corrected:
        assert not result["intersections"], "Visible surfaces of opposite legs intersect"
        for row in result["legs"].values():
            assert row["reverse_bend_samples"] == 0, "A knee folds opposite the skate toe"
            assert row["minimum_blade_gap_mm"][0] >= 0, "A skate blade penetrates the modeled ice"
            assert row["boot_blade_yaw_max_deg"][0] < .02, "Boot and blade headings diverge"
            assert row["ankle_fit_max_mm"][0] < .01, "Boot moved off its ankle anchor"
            assert max(record[0] for record in row["max_joint_step_deg"].values()) < 30, "Abrupt leg/skate rotation"
