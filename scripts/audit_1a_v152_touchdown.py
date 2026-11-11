"""Check that the V152 landing event coincides with support-blade contact."""

import json
import math
from pathlib import Path

import bpy


ICE_TOP_Z = 0.012
FRAME_STEP = 1.0 / 16.0
LANDING_FRAME = 93
scene = bpy.context.scene


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


require(scene.get("prototype_version") == "v152", "Expected V152 scene")
landing_markers = [obj for obj in scene.objects if "EVENT_LANDING_FRAME" in obj.name]
require(len(landing_markers) == 1 and landing_markers[0].name.endswith("_93"),
        "Expected a single landing event marker at frame 93")
root = scene.objects["Skater root · simulated travel and 1.5-turn yaw v8"]
support_blade = scene.objects["Right skate · website blade v64"]
free_blade = scene.objects["Left skate · website blade v64"]
guide = scene.objects["V102 · vertical guide · landing"]

samples = []
count = round((110.0 - 90.0) / FRAME_STEP)
for index in range(count + 1):
    frame = 90.0 + index * FRAME_STEP
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    support = support_blade.evaluated_get(depsgraph)
    free = free_blade.evaluated_get(depsgraph)
    support_min = min((support.matrix_world @ vertex.co).z for vertex in support.data.vertices)
    free_min = min((free.matrix_world @ vertex.co).z for vertex in free.data.vertices)
    samples.append({
        "frame": frame,
        "support_gap_m": support_min - ICE_TOP_Z,
        "free_skate_gap_m": free_min - ICE_TOP_Z,
    })

first_contact = next((row for row in samples if row["support_gap_m"] <= 0.003), None)
landing_sample = min(samples, key=lambda row: abs(row["frame"] - LANDING_FRAME))
frame90 = next(row for row in samples if row["frame"] == 90.0)
scene.frame_set(LANDING_FRAME)
bpy.context.view_layer.update()
expected_x = root.matrix_world.translation.x
guide_error = abs(guide.matrix_world.translation.x - expected_x)
report = {
    "blend": bpy.data.filepath,
    "landing_marker": landing_markers[0].name,
    "sample_step_frames": FRAME_STEP,
    "first_support_gap_under_3mm": {
        "frame": first_contact["frame"] if first_contact else None,
        "gap_m": round(first_contact["support_gap_m"], 6) if first_contact else None,
    },
    "frame90_support_gap_mm": round(frame90["support_gap_m"] * 1000.0, 3),
    "frame93_support_gap_mm": round(landing_sample["support_gap_m"] * 1000.0, 3),
    "frame93_free_skate_gap_mm": round(landing_sample["free_skate_gap_m"] * 1000.0, 3),
    "landing_guide_to_root_x_error_mm": round(guide_error * 1000.0, 3),
    "post_touchdown_min_support_gap_mm": round(
        min(row["support_gap_m"] for row in samples if row["frame"] >= LANDING_FRAME) * 1000.0, 3),
}
print("TOUCHDOWN_AUDIT_V152 " + json.dumps(report, ensure_ascii=False))

require(first_contact is not None and abs(first_contact["frame"] - LANDING_FRAME) <= FRAME_STEP,
        "The landing marker does not align with first support-blade contact")
require(0.001 <= landing_sample["support_gap_m"] <= 0.003,
        "The support blade is not within the 1–3 mm contact tolerance at the landing event")
require(landing_sample["free_skate_gap_m"] > 0.02,
        "The free-leg skate unexpectedly intersects or contacts the ice at landing")
require(guide_error < 1e-5, "The landing guide is not at the touchdown root position")
require(min(row["support_gap_m"] for row in samples) >= -1e-5,
        "The support blade intersects the ice in the sampled landing interval")
