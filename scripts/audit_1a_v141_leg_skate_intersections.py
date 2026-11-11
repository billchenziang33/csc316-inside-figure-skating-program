"""Sample V126 leg/skate surface intersections during flight and glide-out."""

import json
import math

import bpy
from mathutils.bvhtree import BVHTree


scene = bpy.context.scene
if scene.get("prototype_version") not in {"v141", "v144", "v145"}:
    raise RuntimeError(f"Expected V141, got {scene.get('prototype_version')}")
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
start, end, step = 60.0, float(scene.frame_end), 0.5
results = {f"{a} ↔ {b}": {"samples_with_overlap": 0, "max_triangle_pairs": 0,
                           "worst_frame": None} for a, b in pairs}


def tree_for(obj):
    vertices = [tuple(obj.matrix_world @ vertex.co) for vertex in obj.data.vertices]
    polygons = [tuple(poly.vertices) for poly in obj.data.polygons]
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False, epsilon=1e-6)


for index in range(round((end - start) / step) + 1):
    frame = start + index * step
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

print(scene.get("prototype_version").upper() + "_LEG_SKATE_BVH " + json.dumps({
    "blend": bpy.data.filepath,
    "sample_start_frame": start,
    "sample_end_frame": end,
    "sample_step_frames": step,
    "sample_count": round((end - start) / step) + 1,
    "pairs": results,
    "method_limit": "BVH surface triangle intersections at 0.5-frame samples; not continuous volumetric collision proof.",
}, ensure_ascii=False))
