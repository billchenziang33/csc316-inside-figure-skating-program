"""Measure both V169 blade clearances around the simulated landing window."""

import json

import bpy


scene = bpy.context.scene
if scene.get("prototype_version") != "v169":
    raise RuntimeError(f"Expected V169, got {scene.get('prototype_version')}")
ice = scene.objects["V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)"]
ice_top_z = max((ice.matrix_world @ vertex.co).z for vertex in ice.data.vertices)
blades = {
    side: scene.objects[f"{side} skate · website blade v64"]
    for side in ("Left", "Right")
}
samples = []
frame = 86.0
while frame <= 98.0 + 1e-8:
    whole = int(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    clearance = {}
    for side, blade in blades.items():
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = blade.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            lowest = min((evaluated.matrix_world @ vertex.co).z for vertex in mesh.vertices)
        finally:
            evaluated.to_mesh_clear()
        clearance[side] = round((lowest - ice_top_z) * 1000.0, 3)
    samples.append({"frame": frame, "clearance_mm": clearance})
    frame += 0.25

print("V169_LANDING_CLEARANCE " + json.dumps({
    "ice_top_z_m": round(ice_top_z, 6),
    "event_frames": {key: scene.get(key) for key in (
        "takeoff_frame", "apex_frame", "landing_frame", "exit_frame")},
    "samples": samples,
    "limit": "Clearance is geometric separation only; it does not identify the actual supporting blade edge.",
}, ensure_ascii=False))
