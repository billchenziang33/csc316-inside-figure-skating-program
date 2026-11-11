"""Read-only comparison of a symmetric 41-pose right-foot-axis filter on V141."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ASSET = Path(__file__).resolve().parents[1] / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "joint-reference.json"
raw = json.loads(SOURCE.read_text(encoding="utf-8"))
scene = next(item for item in bpy.data.scenes if item.get("prototype_version") == "v141")
rig = scene.objects["Skater root · simulated travel and 1.5-turn yaw v8"]
torso = scene.objects["Human · shaped jacket torso"]
boot = scene.objects["Right skate · website boot v64"]


def canonical_poses(raw_frames, count):
    poses, previous_forward = [], None
    for raw_frame in raw_frames[:count]:
        points = [Vector(point) for point in raw_frame]
        up = (points[12] - points[0]).normalized()
        across = (points[17] - points[16]).normalized()
        forward = across.cross(up).normalized()
        if previous_forward is not None and forward.dot(previous_forward) < 0.0:
            across.negate()
            forward.negate()
        previous_forward = forward.copy()
        local = [Vector(((p - points[0]).dot(across),
                         (p - points[0]).dot(up),
                         (p - points[0]).dot(forward))) for p in points]
        poses.append([Vector((p.x, -p.z, p.y)) for p in local])
    height = max(max(p.y for p in pose) - min(p.y for p in pose) for pose in poses)
    scale = 1.72 / height * 0.86
    return [[p * scale for p in pose] for pose in poses]


def flat(vector):
    result = Vector((vector.x, vector.y, 0.0))
    return result.normalized() if result.length > 1e-8 else None


def angle(first, second):
    return math.degrees(math.atan2(first.x * second.y - first.y * second.x,
                                   first.dot(second)))


poses = canonical_poses(raw["frames"], scene.frame_end)
foot_axes = [(pose[11] - pose[8]).normalized() for pose in poses]
weights = [math.comb(40, i) for i in range(41)]
smoothed = []
for index in range(len(foot_axes)):
    value = Vector((0.0, 0.0, 0.0))
    for offset, weight in zip(range(-20, 21), weights):
        value += foot_axes[min(len(foot_axes) - 1, max(0, index + offset))] * weight
    smoothed.append(value.normalized())

rows = []
old_frame, old_subframe = scene.frame_current, scene.frame_subframe
try:
    for frame in (50, 60, 70, 76, 82, 84, 85, 86, 87, 88, 89, 90, 91, 92,
                  93, 94, 95, 96, 100, 110, 121, 150, 160):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        q = rig.matrix_world.to_quaternion()
        source = flat(q @ foot_axes[frame - 1])
        filtered = flat(q @ smoothed[frame - 1])
        body = flat(torso.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0)))
        current_boot = flat(boot.matrix_world.to_3x3() @ Vector((0.0, -1.0, 0.0)))
        rows.append({
            "frame": frame,
            "raw_foot_to_boot_deg": round(angle(source, current_boot), 3),
            "filtered_foot_to_boot_deg": round(angle(filtered, current_boot), 3),
            "filtered_foot_to_torso_deg": round(angle(body, filtered), 3),
            "filtered_world_heading_deg": round(math.degrees(math.atan2(filtered.y, filtered.x)), 3),
        })
finally:
    scene.frame_set(old_frame, subframe=old_subframe)
    bpy.context.view_layer.update()

raw_steps, filtered_steps = [], []
for a, b in zip(foot_axes, foot_axes[1:]):
    raw_steps.append(math.degrees(a.angle(b)))
for a, b in zip(smoothed, smoothed[1:]):
    filtered_steps.append(math.degrees(a.angle(b)))

print("V141_RIGHT_FOOT_FILTER_EVALUATION " + json.dumps({
    "source": bpy.data.filepath,
    "filter": "41-sample binomial direction average in the canonical pose frame",
    "raw_max_pose_step_deg": round(max(raw_steps), 4),
    "filtered_max_pose_step_deg": round(max(filtered_steps), 4),
    "key_frames": rows,
    "status": "illustrative/simulated; filter-only evaluation, no scene edits",
}, ensure_ascii=False))
