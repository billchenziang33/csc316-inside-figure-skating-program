"""Check both corrected blade meshes against the actual rink top at 1/16 frames."""

import json
import math

import bpy
import numpy as np


scene = bpy.context.scene
version = scene.get("prototype_version")
if version != "v137":
    raise RuntimeError(f"Expected V137, got {version}")
ice = scene.objects.get("V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)")
if ice is None:
    raise RuntimeError("The V129 rink ice mesh is missing")
ice_top_z = max((ice.matrix_world @ vertex.co).z for vertex in ice.data.vertices)
blades = {side: scene.objects[f"{side} skate · website blade v64"]
          for side in ("Left", "Right")}
if any(blade.get("toe_pick_mirrored_to_boot_toe") is not True for blade in blades.values()):
    raise RuntimeError("A visible blade is missing its preserved toe orientation marker")
vertices = {side: np.asarray([tuple(vertex.co) + (1.0,) for vertex in blade.data.vertices],
                             dtype=np.float64)
            for side, blade in blades.items()}
old_frame, old_subframe = scene.frame_current, scene.frame_subframe
step = 1.0 / 16.0
sample_count = round((scene.frame_end - scene.frame_start) / step) + 1
minimum = {side: {"clearance_m": float("inf"), "frame": None} for side in blades}
try:
    for index in range(sample_count):
        frame = scene.frame_start + index * step
        base = math.floor(frame)
        scene.frame_set(base, subframe=frame - base)
        bpy.context.view_layer.update()
        for side, blade in blades.items():
            matrix = np.asarray(blade.matrix_world, dtype=np.float64)
            z = float((vertices[side] @ matrix.T)[:, 2].min() - ice_top_z)
            if z < minimum[side]["clearance_m"]:
                minimum[side] = {"clearance_m": z, "frame": round(frame, 4)}
finally:
    scene.frame_set(old_frame, subframe=old_subframe)
    bpy.context.view_layer.update()

report = {
    "blend": bpy.data.filepath, "scene": scene.name,
    "ice_top_z_m": ice_top_z, "step_frames": step,
    "samples_per_blade": sample_count,
    "minimum_blade_clearance": minimum,
    "criteria": "blade mesh must not cross below the actual ice top during sampled playback",
    "method_limit": "Dense sampled geometry-height audit; it does not prove continuous contact or collision-free body motion.",
}
print(version.upper() + "_ACTUAL_ICE_CLEARANCE " + json.dumps(report, ensure_ascii=False))
if min(item["clearance_m"] for item in minimum.values()) < -1e-5:
    raise RuntimeError(f"A {version} blade penetrates the rink ice in the 1/16-frame sample")
