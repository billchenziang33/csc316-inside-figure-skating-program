"""Sample cross-leg and boot intersections after the V116 free-leg retarget."""

import json
import math

import bpy
from mathutils.bvhtree import BVHTree


scene = next(s for s in bpy.data.scenes if s.get("prototype_version") == "v116")
if scene is None:
    raise RuntimeError("Expected a V116 Single Axel scene")

OBJECTS = {
    "left_thigh": scene.objects["Human · left leg volume 3"],
    "left_calf": scene.objects["Human · left leg volume 4"],
    "left_boot": scene.objects["Left skate · website boot v64"],
    "right_thigh": scene.objects["Human · right leg volume 3"],
    "right_calf": scene.objects["Human · right leg volume 4"],
    "right_boot": scene.objects["Right skate · website boot v64"],
}
PAIRS = (
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
STEP = 0.5
results = {f"{a} ↔ {b}": {"samples_with_overlap": 0, "max_triangle_pairs": 0,
                           "worst_frame": None} for a, b in PAIRS}


def tree_for(obj):
    vertices = [tuple(obj.matrix_world @ vertex.co) for vertex in obj.data.vertices]
    polygons = [tuple(poly.vertices) for poly in obj.data.polygons]
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False, epsilon=1e-6)


for sample_index in range(round((160.0 - 82.0) / STEP) + 1):
    frame = 82.0 + sample_index * STEP
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    trees = {name: tree_for(obj) for name, obj in OBJECTS.items()}
    for first, second in PAIRS:
        pairs = trees[first].overlap(trees[second])
        entry = results[f"{first} ↔ {second}"]
        if pairs:
            entry["samples_with_overlap"] += 1
            if len(pairs) > entry["max_triangle_pairs"]:
                entry["max_triangle_pairs"] = len(pairs)
                entry["worst_frame"] = frame

print("V116_CROSS_LEG_BVH " + json.dumps({
    "blend": bpy.data.filepath,
    "sample_step_frames": STEP,
    "sample_count": round((160.0 - 82.0) / STEP) + 1,
    "pairs": results,
    "method_limit": "BVH surface triangle intersections at 0.5-frame samples; not continuous volumetric collision proof.",
}, ensure_ascii=False))
