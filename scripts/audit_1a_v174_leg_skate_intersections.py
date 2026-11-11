"""Compare sampled leg/skate surfaces for V174 candidate."""

import json
import math

import bpy
from mathutils.bvhtree import BVHTree


scene = bpy.context.scene
version = scene.get("prototype_version")
if version != "v174":
    raise RuntimeError(f"Expected V174 candidate, got {version}")

objects = {
    "left_thigh": scene.objects["Human · left leg volume 3"],
    "left_calf": scene.objects["Human · left leg volume 4"],
    "left_boot": scene.objects["Left skate · website boot v64"],
    "right_thigh": scene.objects["Human · right leg volume 3"],
    "right_calf": scene.objects["Human · right leg volume 4"],
    "right_boot": scene.objects["Right skate · website boot v64"],
}
pairs = (
    ("left_boot", "right_boot"),
    ("left_boot", "right_calf"),
    ("left_boot", "right_thigh"),
    ("right_boot", "left_calf"),
    ("right_boot", "left_thigh"),
    ("left_thigh", "right_calf"),
    ("right_thigh", "left_calf"),
)
results = {
    f"{first} ↔ {second}": {
        "samples_with_surface_intersection": 0,
        "max_intersecting_triangle_pairs": 0,
        "worst_frame": None,
    }
    for first, second in pairs
}


def tree_for(obj):
    vertices = [tuple(obj.matrix_world @ vertex.co) for vertex in obj.data.vertices]
    polygons = [tuple(poly.vertices) for poly in obj.data.polygons]
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False, epsilon=1e-6)


step = 0.5
sample_count = round((scene.frame_end - scene.frame_start) / step) + 1
for index in range(sample_count):
    frame = scene.frame_start + index * step
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    trees = {name: tree_for(obj) for name, obj in objects.items()}
    for first, second in pairs:
        overlap_count = len(trees[first].overlap(trees[second]))
        item = results[f"{first} ↔ {second}"]
        if overlap_count:
            item["samples_with_surface_intersection"] += 1
            if overlap_count > item["max_intersecting_triangle_pairs"]:
                item["max_intersecting_triangle_pairs"] = overlap_count
                item["worst_frame"] = frame

print("V174_LEG_SKATE_SURFACE_AUDIT " + json.dumps({
    "version": version, "sample_start_frame": scene.frame_start,
    "sample_end_frame": scene.frame_end, "sample_step_frames": step,
    "sample_count": sample_count, "pairs": results,
    "method_limit": "BVH surface intersections sampled every 0.5 frame; not continuous volumetric collision proof.",
}, ensure_ascii=False))
