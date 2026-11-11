"""Report V169 leg landmarks and boot bounds at the two overlap hotspots."""

import json

import bpy
from mathutils import Vector


scene = bpy.context.scene
if scene.get("prototype_version") != "v169":
    raise RuntimeError(f"Expected V169, got {scene.get('prototype_version')}")
items = {
    "left_hip": scene.objects["Human · left leg volume 3"],
    "left_knee": scene.objects["Human · left knee joint"],
    "left_ankle": scene.objects["Human · left ankle joint"],
    "left_boot": scene.objects["Left skate · website boot v64"],
    "right_hip": scene.objects["Human · right leg volume 3"],
    "right_knee": scene.objects["Human · right knee joint"],
    "right_ankle": scene.objects["Human · right ankle joint"],
    "right_boot": scene.objects["Right skate · website boot v64"],
    "pelvis": next(obj for obj in scene.objects if "pelvis" in obj.name.lower()),
    "torso": scene.objects["Human · shaped jacket torso"],
}
rows = []
for frame in (12.0, 34.0):
    scene.frame_set(int(frame))
    bpy.context.view_layer.update()
    points = {}
    for name, obj in items.items():
        points[name] = [round(value, 5) for value in obj.matrix_world.translation]
    lateral_axis = items["torso"].matrix_world.to_3x3() @ Vector((1.0, 0.0, 0.0))
    forward_axis = items["torso"].matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0))
    points["torso_lateral_world"] = [round(value, 5) for value in lateral_axis]
    points["torso_forward_world"] = [round(value, 5) for value in forward_axis]
    points["lateral_pitch_effect_on_left_ankle"] = [
        round(value, 5) for value in lateral_axis.cross(
            items["left_ankle"].matrix_world.translation -
            items["left_hip"].matrix_world.translation)]
    for name in ("left_boot", "right_boot"):
        obj = items[name]
        bounds = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        points[name + "_bounds"] = {
            axis: [round(min(point[i] for point in bounds), 5),
                   round(max(point[i] for point in bounds), 5)]
            for i, axis in enumerate("xyz")
        }
    left = items["left_boot"].matrix_world.translation
    right = items["right_boot"].matrix_world.translation
    points["boot_center_distance_m"] = round((left - right).length, 5)
    points["boot_x_center_delta_m"] = round(left.x - right.x, 5)
    rows.append({"frame": frame, "points": points})
print("V169_APPROACH_LANDMARKS " + json.dumps(rows, ensure_ascii=False))
