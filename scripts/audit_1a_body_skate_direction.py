"""Read-only audit of visible body, fitted boot/blade, and 22-joint axes."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
JOINTS = json.loads((ASSET / "joint-reference.json").read_text(encoding="utf-8"))
STEP = 0.25
SIDES = {"Left": (7, 10), "Right": (8, 11)}
FORWARD_LOCAL = Vector((0.0, -1.0, 0.0))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def canonical_poses(raw_frames, count):
    poses, previous_forward = [], None
    for raw in raw_frames[:count]:
        points = [Vector(point) for point in raw]
        up = (points[12] - points[0]).normalized()
        across = (points[17] - points[16]).normalized()
        forward = across.cross(up).normalized()
        if previous_forward is not None and forward.dot(previous_forward) < 0.0:
            across.negate()
            forward.negate()
        previous_forward = forward.copy()
        local = [Vector(((point - points[0]).dot(across),
                         (point - points[0]).dot(up),
                         (point - points[0]).dot(forward))) for point in points]
        poses.append([Vector((point.x, -point.z, point.y)) for point in local])
    scale = 1.72 / max(max(point.y for point in pose) - min(point.y for point in pose)
                       for pose in poses) * 0.86
    return [[point * scale for point in pose] for pose in poses]


def horizontal(vector):
    value = Vector((vector.x, vector.y, 0.0))
    return value.normalized() if value.length > 1e-8 else None


def signed_angle(first, second):
    return math.degrees(math.atan2(first.x * second.y - first.y * second.x,
                                   first.dot(second)))


def smooth_directions(vectors):
    weights = tuple(math.comb(40, index) for index in range(41))
    radius = len(weights) // 2
    output = []
    for index in range(len(vectors)):
        value = Vector((0.0, 0.0, 0.0))
        for offset, weight in zip(range(-radius, radius + 1), weights):
            sample = min(len(vectors) - 1, max(0, index + offset))
            value += vectors[sample] * weight
        output.append(value.normalized())
    return output


scene = next((candidate for candidate in bpy.data.scenes
              if candidate.get("prototype_version") in {"v108", "v110", "v111", "v112", "v113"}), None)
require(scene is not None, "Expected a V108, V110, V111, V112, or V113 Single Axel scene")
poses = canonical_poses(JOINTS["frames"], scene.frame_end)
rig = scene.objects["Skater root · simulated travel and 1.5-turn yaw v8"]
head = scene.objects.get("Head · detailed generic human sculpt")
nose = scene.objects.get("Head · nose tip")
require(head is not None and nose is not None, "Expected the detailed head and nose tip")
objects = {}
for side in SIDES:
    objects[side] = {
        "skate": scene.objects[f"{side} skate · exact website fit v64"],
        "boot": scene.objects[f"{side} skate · website boot v64"],
        "blade": scene.objects[f"{side} skate · website blade v64"],
    }

joint_directions = {
    side: smooth_directions([(pose[toe] - pose[ankle]).normalized() for pose in poses])
    for side, (ankle, toe) in SIDES.items()
}

samples = {side: [] for side in SIDES}
frame = scene.frame_start
while frame <= scene.frame_end + 1e-8:
    base = min(int(math.floor(frame)) - scene.frame_start, len(poses) - 1)
    nxt = min(base + 1, len(poses) - 1)
    mix = frame - math.floor(frame)
    scene.frame_set(math.floor(frame), subframe=mix)
    bpy.context.view_layer.update()
    rig_q = rig.matrix_world.to_quaternion()

    # Facial landmarks provide a visible body-facing axis independent of the
    # simulated root object's local coordinate convention.
    face = horizontal(nose.matrix_world.translation - head.matrix_world.translation)
    if face is not None:
        for side, (ankle_index, toe_index) in SIDES.items():
            joint_foot = horizontal(rig_q @ joint_directions[side][base].lerp(
                joint_directions[side][nxt], mix).normalized())

            skate, boot, blade = (objects[side][key] for key in ("skate", "boot", "blade"))
            skate_toe = horizontal(skate.matrix_world.to_3x3() @ FORWARD_LOCAL)
            boot_toe = horizontal(boot.matrix_world.to_3x3() @ FORWARD_LOCAL)
            # The fitted website blade's toe-pick edge is local +Y; V92 aligned
            # that physical edge to the boot toe. Test the actual visible mesh.
            blade_toe = horizontal(blade.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0)))
            require(all(direction is not None for direction in
                        (face, joint_foot, skate_toe, boot_toe, blade_toe)),
                    f"Degenerate horizontal heading at frame {frame:.2f}, {side}")
            samples[side].append({
                "frame": round(frame, 4),
                "face_to_boot_toe_deg": round(signed_angle(face, boot_toe), 4),
                "boot_to_blade_toe_deg": round(signed_angle(boot_toe, blade_toe), 4),
                "joint_to_boot_toe_deg": round(signed_angle(joint_foot, boot_toe), 4),
                "face_to_joint_deg": round(signed_angle(face, joint_foot), 4),
            })
    frame += STEP

summary = {"blend": bpy.data.filepath, "scene": scene.name,
           "frames_sampled_per_side": len(samples["Right"]), "step_frames": STEP,
           "by_side": {}}
key_frames = (60, 76, 82, 85, 87, 89, 90, 93, 95, 100, 110, 120, 130, 140, 150, 160)
for side, values in samples.items():
    exit_values = [value for value in values if value["frame"] >= 100.0]
    summary["by_side"][side] = {
        metric: {
            "max_abs_all_frames_deg": round(max(abs(item[metric]) for item in values), 4),
            "worst_all_frames": max(values, key=lambda item: abs(item[metric])),
            "max_abs_exit_frames_100_160_deg": round(
                max(abs(item[metric]) for item in exit_values), 4),
            "worst_exit": max(exit_values, key=lambda item: abs(item[metric])),
        }
        for metric in ("face_to_boot_toe_deg", "boot_to_blade_toe_deg",
                       "joint_to_boot_toe_deg", "face_to_joint_deg")
    }
    summary["by_side"][side]["key_frames"] = [
        next(item for item in values if item["frame"] == frame) for frame in key_frames]
print("BODY_SKATE_DIRECTION_AUDIT " + json.dumps(summary, ensure_ascii=False))

right = summary["by_side"]["Right"]
require(right["boot_to_blade_toe_deg"]["max_abs_all_frames_deg"] <= 5.0,
        "Right boot toe and blade toe point in materially different directions")
require(right["face_to_boot_toe_deg"]["max_abs_all_frames_deg"] < 120.0,
        "Right boot is near-reversed from the visible face across the sampled sequence")
require(right["joint_to_boot_toe_deg"]["max_abs_all_frames_deg"] <= 50.0,
        "Right boot diverges more than 50 degrees from the generic 22-joint foot heading")
