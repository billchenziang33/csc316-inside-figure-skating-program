"""Compare leg/skate surface intersections around V150's landing correction."""

import json
import math

import bpy
from mathutils.bvhtree import BVHTree


scene = bpy.context.scene
version = scene.get("prototype_version")
if version not in {"v149", "v150", "v151"}:
    raise RuntimeError(f"Expected V149/V150/V151, got {version}")

objects = {
    "left_thigh": scene.objects["Human · left leg volume 3"],
    "left_calf": scene.objects["Human · left leg volume 4"],
    "left_boot": scene.objects["Left skate · website boot v64"],
    "right_thigh": scene.objects["Human · right leg volume 3"],
    "right_calf": scene.objects["Human · right leg volume 4"],
    "right_boot": scene.objects["Right skate · website boot v64"],
}
pairs = (
    ("left_thigh", "right_thigh"),
    ("left_thigh", "right_calf"),
    ("left_calf", "right_thigh"),
    ("left_calf", "right_calf"),
    ("left_boot", "right_boot"),
    ("left_boot", "right_calf"),
    ("right_boot", "left_calf"),
    ("left_boot", "right_thigh"),
    ("right_boot", "left_thigh"),
)
results = {f"{a} ↔ {b}": {"samples_with_overlap": 0, "max_triangle_pairs": 0,
                           "worst_frame": None} for a, b in pairs}


def tree_for(obj):
    vertices = [tuple(obj.matrix_world @ vertex.co) for vertex in obj.data.vertices]
    polygons = [tuple(poly.vertices) for poly in obj.data.polygons]
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False, epsilon=1e-6)


for index in range(21):
    frame = 80.0 + index * 0.5
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    trees = {name: tree_for(obj) for name, obj in objects.items()}
    for first, second in pairs:
        overlaps = trees[first].overlap(trees[second])
        item = results[f"{first} ↔ {second}"]
        if overlaps:
            item["samples_with_overlap"] += 1
            if len(overlaps) > item["max_triangle_pairs"]:
                item["max_triangle_pairs"] = len(overlaps)
                item["worst_frame"] = frame

print("V151_LEG_SKATE_BVH " + json.dumps({
    "blend": bpy.data.filepath,
    "prototype_version": version,
    "sample_start_frame": 80.0,
    "sample_end_frame": 90.0,
    "sample_step_frames": 0.5,
    "sample_count": 21,
    "pairs": results,
    "method_limit": "Surface triangle intersections sampled every 0.5 frames; not continuous volumetric collision proof.",
}, ensure_ascii=False))

