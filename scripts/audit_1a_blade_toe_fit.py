"""Audit the animated website blade's longitudinal fit to the boot toe and heel."""

import json
import math

import bpy
from mathutils import Vector


scene = next((item for item in bpy.data.scenes
              if item.get("prototype_version") == "v125"), None)
if scene is None:
    raise RuntimeError("Expected the V125 Single Axel scene")


def percentile(values, fraction):
    ordered = sorted(values)
    index = math.ceil(fraction * (len(ordered) - 1))
    return ordered[index]


def projected_extents(obj, origin, axis):
    values = [((obj.matrix_world @ vertex.co) - origin).dot(axis)
              for vertex in obj.data.vertices]
    return percentile(values, 0.995), percentile(values, 0.005)


old_frame, old_subframe = scene.frame_current, scene.frame_subframe
rows = []
try:
    for frame in (50.0, 51.0, 60.0, 76.0, 86.0, 87.0, 90.0, 121.0, 150.0):
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        for side in ("Left", "Right"):
            boot = scene.objects[f"{side} skate · website boot v64"]
            blade = scene.objects[f"{side} skate · website blade v64"]
            if blade.get("prototype_version") != "v125" or blade.get("toe_pick_mirrored_to_boot_toe") is not True:
                raise RuntimeError(f"{side} visible blade is missing the V125 forward-toe geometry fix")
            anchor = scene.objects[f"{side} skate · exact website fit v64"].matrix_world.translation
            toe_axis = (boot.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0))).normalized()
            boot_toe, boot_heel = projected_extents(boot, anchor, toe_axis)
            blade_toe, blade_heel = projected_extents(blade, anchor, toe_axis)
            rows.append({
                "frame": frame,
                "side": side,
                "boot_toe_m": boot_toe,
                "blade_toe_m": blade_toe,
                "toe_gap_m": boot_toe - blade_toe,
                "boot_heel_m": boot_heel,
                "blade_heel_m": blade_heel,
                "heel_overhang_m": boot_heel - blade_heel,
            })
finally:
    scene.frame_set(old_frame, subframe=old_subframe)
    bpy.context.view_layer.update()

worst_toe = max(rows, key=lambda row: abs(row["toe_gap_m"]))
worst_heel = max(rows, key=lambda row: max(-0.020 - row["heel_overhang_m"],
                                           row["heel_overhang_m"] - 0.010, 0.0))
report = {
    "blend": bpy.data.filepath,
    "version": scene.get("prototype_version"),
    "sample_count": len(rows),
    "toe_gap_tolerance_m": [-0.015, 0.010],
    "heel_overhang_tolerance_m": [-0.020, 0.010],
    "worst_toe": worst_toe,
    "worst_heel": worst_heel,
    "samples": rows,
    "method_limit": "99.5/0.5-percentile mesh extents projected along each boot's animated local -Y toe axis; this is a fit audit, not continuous collision proof.",
}
print("AXEL_BLADE_TOE_FIT " + json.dumps(report, ensure_ascii=False))

if any(row["toe_gap_m"] < -0.015 or row["toe_gap_m"] > 0.010 for row in rows):
    raise RuntimeError("Blade toe endpoint is more than 15 mm beyond or 10 mm behind the boot toe")
if any(row["heel_overhang_m"] < -0.020 or row["heel_overhang_m"] > 0.010 for row in rows):
    raise RuntimeError("Blade heel endpoint is more than 20 mm beyond or 10 mm short of the boot heel")
