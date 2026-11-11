"""Read-only full-motion heading, fit, continuity and BVH audit for V148/V149."""

import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


scene = bpy.context.scene
version = scene.get("prototype_version")
if version not in {"v148", "v149"}:
    raise RuntimeError(f"Expected V148/V149, got {version}")
torso = scene.objects["Human · shaped jacket torso"]
right_boot = scene.objects["Right skate · website boot v64"]
right_blade = scene.objects["Right skate · website blade v64"]
left_boot = scene.objects["Left skate · website boot v64"]
left_blade = scene.objects["Left skate · website blade v64"]
ice = scene.objects["V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)"]
forward = Vector((0.0, -1.0, 0.0))


def horizontal(vector):
    result = Vector((vector.x, vector.y, 0.0))
    if result.length < 1e-8:
        raise RuntimeError("A direction has no horizontal component")
    return result.normalized()


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


def toe(obj, axis=forward):
    return horizontal(obj.matrix_world.to_3x3() @ axis)


def min_world_z(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    return min((evaluated.matrix_world @ v.co).z for v in evaluated.data.vertices)


def tree_for(obj):
    verts = [tuple(obj.matrix_world @ v.co) for v in obj.data.vertices]
    polys = [tuple(poly.vertices) for poly in obj.data.polygons]
    return BVHTree.FromPolygons(verts, polys, all_triangles=False, epsilon=1e-6)


original_frame = scene.frame_current
heading_rows = []
blade_gap = {"left": float("inf"), "right": float("inf")}
continuity = {"right_boot_max_step_deg": 0.0, "right_boot_max_step_frame": None,
              "right_leg_correction_max_step_deg": 0.0,
              "right_leg_correction_max_step_frame": None}
previous = None
previous_correction = None
overlap = {"right_boot_left_calf": 0, "right_calf_left_thigh": 0,
           "right_thigh_left_calf": 0}
max_pairs = {key: 0 for key in overlap}

try:
    ice_top = max((ice.matrix_world @ vertex.co).z for vertex in ice.data.vertices)
    for index in range(637):
        frame = 1.0 + index * 0.25
        low = math.floor(frame)
        scene.frame_set(low, subframe=frame - low)
        bpy.context.view_layer.update()
        body_axis = toe(torso)
        boot_axis = toe(right_boot)
        right_blade_axis = toe(right_blade, Vector((0.0, 1.0, 0.0)))
        left_boot_axis = toe(left_boot)
        left_blade_axis = toe(left_blade, Vector((0.0, 1.0, 0.0)))
        body_yaw = signed_angle(body_axis, boot_axis)
        boot_blade_yaw = signed_angle(boot_axis, right_blade_axis)
        heading_rows.append({"frame": round(frame, 2),
                             "torso_to_right_boot_deg": body_yaw,
                             "right_boot_to_blade_deg": boot_blade_yaw})
        for side, blade in (("left", left_blade), ("right", right_blade)):
            blade_gap[side] = min(blade_gap[side], min_world_z(blade) - ice_top)

        if previous is not None:
            old_frame, old_boot_axis, old_correction = previous
            step = math.degrees(math.acos(max(-1.0, min(1.0, old_boot_axis.dot(boot_axis)))) )
            if step > continuity["right_boot_max_step_deg"]:
                continuity["right_boot_max_step_deg"] = step
                continuity["right_boot_max_step_frame"] = frame
            correction = body_yaw - max(-20.0, min(20.0, body_yaw))
            correction_step = abs(correction - old_correction)
            if correction_step > continuity["right_leg_correction_max_step_deg"]:
                continuity["right_leg_correction_max_step_deg"] = correction_step
                continuity["right_leg_correction_max_step_frame"] = frame
            previous = (frame, boot_axis, correction)
        else:
            correction = body_yaw - max(-20.0, min(20.0, body_yaw))
            previous = (frame, boot_axis, correction)

        if index % 2 == 0 and frame >= 60.0:
            trees = {
                "left_thigh": tree_for(scene.objects["Human · left leg volume 3"]),
                "left_calf": tree_for(scene.objects["Human · left leg volume 4"]),
                "right_thigh": tree_for(scene.objects["Human · right leg volume 3"]),
                "right_calf": tree_for(scene.objects["Human · right leg volume 4"]),
                "right_boot": tree_for(scene.objects["Right skate · website boot v64"]),
            }
            pairs = (("right_boot_left_calf", "right_boot", "left_calf"),
                     ("right_calf_left_thigh", "right_calf", "left_thigh"),
                     ("right_thigh_left_calf", "right_thigh", "left_calf"))
            for key, first, second in pairs:
                count = len(trees[first].overlap(trees[second]))
                if count:
                    overlap[key] += 1
                    max_pairs[key] = max(max_pairs[key], count)
finally:
    scene.frame_set(original_frame)
    bpy.context.view_layer.update()

worst = max(heading_rows, key=lambda row: abs(row["torso_to_right_boot_deg"]))
max_toe_blade = max(abs(row["right_boot_to_blade_deg"]) for row in heading_rows)
summary = {
    "blend": bpy.data.filepath,
    "prototype_version": scene.get("prototype_version"),
    "sample_step_frames": 0.25,
    "sample_count": len(heading_rows),
    "right_torso_boot_yaw_max_abs_deg": round(abs(worst["torso_to_right_boot_deg"]), 5),
    "right_torso_boot_yaw_worst": worst,
    "right_boot_blade_yaw_max_abs_deg": round(max_toe_blade, 6),
    "blade_min_gap_from_ice_m": {key: round(value, 6) for key, value in blade_gap.items()},
    "ice_top_z_m": round(ice_top, 6),
    "continuity": {key: round(value, 5) if isinstance(value, float) else value
                   for key, value in continuity.items()},
    "bvh_overlap_samples_0_5_frame_from_f60": overlap,
    "bvh_max_triangle_pairs": max_pairs,
    "bvh_method_limit": "Surface triangle intersections at 0.5-frame intervals; not continuous volumetric collision proof.",
}
print(version.upper() + "_RIGHT_LEG_AUDIT " + json.dumps(summary, ensure_ascii=False))
if version == "v149" and summary["right_torso_boot_yaw_max_abs_deg"] > 20.1:
    raise RuntimeError("Right boot exceeds the V149 torso-relative yaw limit")
if summary["right_boot_blade_yaw_max_abs_deg"] > 0.01:
    raise RuntimeError("Right boot and blade toe axes diverged")
if min(blade_gap.values()) < -1e-5:
    raise RuntimeError("A blade crosses below the ice top")
