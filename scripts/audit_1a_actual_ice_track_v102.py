"""Read-only, 1/16-frame audit of the current Axel scene against its ice mesh."""

import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
JOINTS = json.loads((ASSET / "joint-reference.json").read_text(encoding="utf-8"))
SIDES = {"Left": (7, 10), "Right": (8, 11)}
STEP = 1.0 / 16.0
AIRBORNE_CLEARANCE = 0.020
SUSTAINED_INTEGER_FRAMES = 3
OFFSET = Vector((0.0, 0.045, 0.035)) * 1.8


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def canonical_poses(raw_frames, count):
    poses, previous_forward = [], None
    for raw in raw_frames[:count]:
        points = [Vector(point) for point in raw]
        up = (points[12] - points[0]).normalized()
        across = (points[17] - points[16]).normalized()
        forward = across.cross(up).normalized()
        if previous_forward is not None and forward.dot(previous_forward) < 0.0:
            across.negate()
            forward.negate()
        previous_forward = forward.copy()
        local = [Vector(((point - points[0]).dot(across),
                         (point - points[0]).dot(up),
                         (point - points[0]).dot(forward))) for point in points]
        poses.append([Vector((point.x, -point.z, point.y)) for point in local])
    scale = 1.72 / max(max(point.y for point in pose) - min(point.y for point in pose)
                       for pose in poses) * 0.86
    return [[point * scale for point in pose] for pose in poses]


def smooth_directions(vectors):
    weights = tuple(math.comb(40, index) for index in range(41))
    radius = len(weights) // 2
    output = []
    for index in range(len(vectors)):
        value = Vector((0.0, 0.0, 0.0))
        for offset, weight in zip(range(-radius, radius + 1), weights):
            sample = min(len(vectors) - 1, max(0, index + offset))
            value += vectors[sample] * weight
        output.append(value.normalized())
    return output


def direction_at(directions, frame, frame_start):
    position = max(0.0, min(len(directions) - 1.0, frame - frame_start))
    low = math.floor(position)
    high = min(low + 1, len(directions) - 1)
    return directions[low].lerp(directions[high], position - low).normalized()


scene = bpy.context.scene
require(scene.get("prototype_version") in {"v101", "v102", "v103", "v104", "v105", "v106", "v107", "v108", "v109", "v110", "v111", "v112", "v113", "v116", "v117", "v118", "v119"},
		f"Expected V101–V113 or V116–V119, got {scene.get('prototype_version')}")
ice = scene.objects.get("V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)")
rig = scene.objects.get("Skater root · simulated travel and 1.5-turn yaw v8")
require(ice and rig, "The ice mesh or animated root is missing")
ice_top_z = max((ice.matrix_world @ vertex.co).z for vertex in ice.data.vertices)
depsgraph = bpy.context.evaluated_depsgraph_get()
poses = canonical_poses(JOINTS["frames"], scene.frame_end)
directions = {
    side: smooth_directions([(pose[pair[1]] - pose[pair[0]]).normalized() for pose in poses])
    for side, pair in SIDES.items()
}
blades, skate_roots, boots, ankles, blade_vertices = {}, {}, {}, {}, {}
for side in SIDES:
    blades[side] = scene.objects[f"{side} skate · website blade v64"]
    skate_roots[side] = scene.objects[f"{side} skate · exact website fit v64"]
    boots[side] = scene.objects[f"{side} skate · website boot v64"]
    ankles[side] = scene.objects[f"Human · {side.lower()} ankle joint"]
    require(skate_roots[side].parent == ankles[side], f"{side} skate is not ankle-parented")
    require(boots[side].parent == skate_roots[side] and blades[side].parent == skate_roots[side],
            f"{side} boot and blade do not share the skate assembly")
    blade_vertices[side] = np.asarray(
        [tuple(vertex.co) + (1.0,) for vertex in blades[side].data.vertices], dtype=np.float64)

samples = []
collision = {
    f"{side} boot ↔ {part}": {
        "samples_with_surface_overlap": 0,
        "max_triangle_pairs": 0,
        "min_boot_relative_intersection_height": 1.0,
        "max_boot_relative_intersection_height": 0.0,
    }
    for side in SIDES for part in ("lower-leg volume 4", "ankle joint")
}


def world_geometry(obj):
    vertices = [tuple(obj.matrix_world @ vertex.co) for vertex in obj.data.vertices]
    polygons = [tuple(polygon.vertices) for polygon in obj.data.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False, epsilon=1e-6)
    return vertices, polygons, tree


for index in range(round((scene.frame_end - scene.frame_start) / STEP) + 1):
    frame = scene.frame_start + index * STEP
    base = math.floor(frame)
    scene.frame_set(base, subframe=frame - base)
    bpy.context.view_layer.update()
    depsgraph.update()
    rig_q = rig.matrix_world.to_quaternion()
    row = {"frame": frame, "root": rig.matrix_world.translation.copy(), "clearance": {},
           "axis_3d_deg": {}, "axis_heading_deg": {}, "boot_blade_deg": {}, "ankle_fit_mm": {}}
    for side, joint_pair in SIDES.items():
        blade = blades[side]
        evaluated = blade.evaluated_get(depsgraph)
        matrix = np.asarray(evaluated.matrix_world, dtype=np.float64)
        vertices = blade_vertices[side]
        row["clearance"][side] = float((vertices @ matrix.T)[:, 2].min() - ice_top_z)
        forward = (rig_q @ direction_at(directions[side], frame, scene.frame_start)).normalized()
        skate_forward = (skate_roots[side].matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0))).normalized()
        row["axis_3d_deg"][side] = math.degrees(forward.angle(skate_forward))
        blade_forward = (blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()
        row["boot_blade_deg"][side] = math.degrees(skate_forward.angle(blade_forward))
        forward_h = Vector((forward.x, forward.y, 0.0))
        skate_h = Vector((skate_forward.x, skate_forward.y, 0.0))
        if forward_h.length > 1e-7 and skate_h.length > 1e-7:
            forward_h.normalize()
            skate_h.normalize()
            row["axis_heading_deg"][side] = math.degrees(forward_h.angle(skate_h))
        offset_world = boots[side].matrix_world @ OFFSET
        row["ankle_fit_mm"][side] = (offset_world - ankles[side].matrix_world.translation).length * 1000.0
        boot_vertices, boot_polygons, boot_tree = world_geometry(boots[side])
        boot_min_z = min(vertex[2] for vertex in boot_vertices)
        boot_height = max(max(vertex[2] for vertex in boot_vertices) - boot_min_z, 1e-9)
        for part_name, part in (("lower-leg volume 4", scene.objects[f"Human · {side.lower()} leg volume 4"]),
                                ("ankle joint", ankles[side])):
            part_tree = world_geometry(part)[2]
            overlap = boot_tree.overlap(part_tree)
            pairs = len(overlap)
            summary = collision[f"{side} boot ↔ {part_name}"]
            summary["samples_with_surface_overlap"] += int(pairs > 0)
            summary["max_triangle_pairs"] = max(summary["max_triangle_pairs"], pairs)
            if overlap:
                ratios = [
                    (sum(boot_vertices[index][2] for index in boot_polygons[face_index]) /
                     len(boot_polygons[face_index]) - boot_min_z) / boot_height
                    for face_index, _ in overlap if face_index < len(boot_polygons)
                ]
                if ratios:
                    summary["min_boot_relative_intersection_height"] = min(
                        summary["min_boot_relative_intersection_height"], min(ratios))
                    summary["max_boot_relative_intersection_height"] = max(
                        summary["max_boot_relative_intersection_height"], max(ratios))
    samples.append(row)

integer = {int(round(row["frame"])): row for row in samples
           if abs(row["frame"] - round(row["frame"])) < 1e-8}
last_frame = max(integer)
takeoff = None
for frame in range(scene.frame_start, last_frame - SUSTAINED_INTEGER_FRAMES + 2):
    if all(min(integer[f]["clearance"].values()) >= AIRBORNE_CLEARANCE
           for f in range(frame, frame + SUSTAINED_INTEGER_FRAMES)):
        takeoff = frame
        break
require(takeoff is not None, "No sustained airborne interval found at the configured threshold")
landing = None
for frame in range(takeoff + 1, last_frame - SUSTAINED_INTEGER_FRAMES + 2):
    if all(min(integer[f]["clearance"].values()) < AIRBORNE_CLEARANCE
           for f in range(frame, frame + SUSTAINED_INTEGER_FRAMES)):
        landing = frame
        break
require(landing is not None, "No sustained return-to-ice interval found")
apex = max(range(takeoff, landing + 1), key=lambda frame: integer[frame]["root"].z)
takeoff_p = integer[takeoff]["root"]
apex_p = integer[apex]["root"]
landing_p = integer[landing]["root"]
horizontal_distance = lambda a, b: math.hypot(b.x - a.x, b.y - a.y)
flight_samples = [row for row in samples if takeoff <= row["frame"] <= landing]
integer_samples = [integer[frame] for frame in range(scene.frame_start, last_frame + 1)]
result = {
    "source": bpy.data.filepath,
    "prototype_version": scene["prototype_version"],
    "blender": bpy.app.version_string,
    "fps": scene.render.fps / scene.render.fps_base,
    "sample_step_frames": STEP,
    "samples_per_skate": len(samples),
    "ice_top_world_z_m": ice_top_z,
    "event_rule": {
        "airborne_clearance_threshold_m": AIRBORNE_CLEARANCE,
        "sustained_integer_frames": SUSTAINED_INTEGER_FRAMES,
        "takeoff_frame": takeoff,
        "apex_frame": apex,
        "landing_frame": landing,
    },
    "flight_seconds_at_scene_fps": (landing - takeoff) / (scene.render.fps / scene.render.fps_base),
    "root_rise_m": apex_p.z - takeoff_p.z,
    "apex_horizontal_from_takeoff_m": horizontal_distance(takeoff_p, apex_p),
    "takeoff_to_landing_horizontal_m": horizontal_distance(takeoff_p, landing_p),
    "minimum_clearance_m": {side: min(row["clearance"][side] for row in samples) for side in SIDES},
    "minimum_flight_clearance_m": {side: min(row["clearance"][side] for row in flight_samples) for side in SIDES},
    "max_ankle_fit_error_mm": {side: max(row["ankle_fit_mm"][side] for row in samples) for side in SIDES},
    "max_boot_blade_heading_error_deg": {
        side: max(row["boot_blade_deg"][side] for row in samples) for side in SIDES
    },
    "max_joint_to_skate_axis_3d_deg": {
        side: max(row["axis_3d_deg"][side] for row in samples) for side in SIDES
    },
    "max_joint_to_skate_heading_deg": {
        side: max(row["axis_heading_deg"][side] for row in samples if side in row["axis_heading_deg"])
        for side in SIDES
    },
    "tested_boot_interfaces": {
        "sample_step_frames": STEP,
        "pairs": collision,
        "interpretation": "Overlapping triangles are localized at the intended boot cuff/ankle junction; other body pairs are not tested by this report.",
    },
    "root_height_min_frame": min(integer_samples, key=lambda row: row["root"].z)["frame"],
    "root_height_max_frame": max(integer_samples, key=lambda row: row["root"].z)["frame"],
    "default_scene_objects": sorted(o.name for o in bpy.data.scenes["Scene"].objects),
}
print("AXEL_ACTUAL_ICE_AUDIT " + json.dumps(result, ensure_ascii=False))
