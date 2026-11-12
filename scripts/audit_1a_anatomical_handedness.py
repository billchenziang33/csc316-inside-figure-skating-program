"""Verify anatomical support feet from the face, torso and evaluated blade mesh."""
import json
import math

import bpy
from mathutils import Vector

UP = Vector((0, 0, 1))
TOE = Vector((0, -1, 0))
ROOT = "Skater root · simulated travel and 1.5-turn yaw v8"
SIDES = ("Left", "Right")
TAKEOFF, LANDING = 60, 92


def flat(v):
    return Vector((v.x, v.y, 0)).normalized()


def run(scene):
    objects = scene.objects
    root = objects[ROOT]
    torso = objects["Human · shaped jacket torso"]
    nose = objects["Head · nose tip"]
    skull = objects["Head · detailed generic human sculpt"]
    hips = [objects[f"Human · {s.lower()} leg volume 3"] for s in SIDES]
    boots = [objects[f"{s} skate · website boot v64"] for s in SIDES]
    blades = [objects[f"{s} skate · website blade v64"] for s in SIDES]
    ice = objects["V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)"]
    ice_z = max((ice.matrix_world @ v.co).z for v in ice.data.vertices)
    headings, points, events = [], {}, {}
    for frame in range(TAKEOFF, LANDING + 1):
        scene.frame_set(frame)
        body_forward = flat(torso.matrix_world.to_3x3() @ TOE)
        headings.append(math.atan2(body_forward.y, body_forward.x))
        if frame not in (TAKEOFF, LANDING):
            continue
        face_forward = flat(nose.matrix_world.translation - skull.matrix_world.translation)
        assert face_forward.dot(body_forward) > .8, "Torso axis does not match the face"
        left = UP.cross(body_forward)
        lateral = hips[0].matrix_world.translation - hips[1].matrix_world.translation
        assert abs(lateral.dot(left)) > .10
        anatomy = SIDES if lateral.dot(left) > 0 else SIDES[::-1]
        points[frame] = root.matrix_world.translation.copy()
        events[frame] = []
        for i, (boot, blade) in enumerate(zip(boots, blades)):
            gap = min((blade.matrix_world @ v.co).z for v in blade.data.vertices) - ice_z
            outside = (blade.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
            outward = left if anatomy[i] == "Left" else -left
            if outside.dot(outward) < 0:
                outside.negate()
            events[frame].append((gap, anatomy[i], flat(boot.matrix_world.to_3x3() @ TOE),
                                  math.degrees(math.asin(-outside.z))))
    travel = flat(points[LANDING] - points[TAKEOFF])
    rotation = sum(math.remainder(b - a, math.tau) for a, b in zip(headings, headings[1:])) / math.tau
    result = {}
    for label, frame in (("takeoff", TAKEOFF), ("landing", LANDING)):
        support, free = sorted(events[frame], key=lambda row: row[0])
        gap, side, toe, bank = support
        result[label] = dict(frame=frame, support=side, gap_mm=round(1000*gap, 3),
                             free_gap_mm=round(1000*free[0], 3), outside_down_deg=round(bank, 3),
                             toe_to_travel_deg=round(math.degrees(toe.angle(travel)), 3))
    print("ANATOMICAL_AXEL", json.dumps(dict(result, signed_turns=round(rotation, 6))), flush=True)
    assert result["takeoff"]["support"] == "Left", "Physical take-off foot is not the skater's left"
    assert result["landing"]["support"] == "Right", "Physical landing foot is not the skater's right"
    assert result["takeoff"]["toe_to_travel_deg"] <= 3
    assert result["landing"]["toe_to_travel_deg"] >= 177
    assert all(0 < e["gap_mm"] < 6 < e["free_gap_mm"] and e["outside_down_deg"] > 1 for e in result.values())
    assert abs(rotation - 1.5) < .005, "Expected 1.5 counterclockwise turns viewed from above"


if __name__ == "__main__":
    run(bpy.context.scene)
