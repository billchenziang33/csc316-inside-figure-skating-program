"""Measure support-foot identity, skate direction, outside lean and airborne yaw."""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_1a_axel_contact_v176 import (
    ICE, LANDING, ROOT, SIDES, TAKEOFF, TOE, horizontal, min_height, scene_at, wrapped,
)


def run(scene):
    root = scene.objects[ROOT]
    ice = scene.objects[ICE]
    ice_top = max((ice.matrix_world @ v.co).z for v in ice.data.vertices)
    hips = [scene.objects[f"Human · {side.lower()} leg volume 3"] for side in SIDES]
    boots = {s: scene.objects[f"{s} skate · website boot v64"] for s in SIDES}
    blades = {s: scene.objects[f"{s} skate · website blade v64"] for s in SIDES}
    xyz = {s: np.array([tuple(v.co) for v in blades[s].data.vertices]) for s in SIDES}
    scene_at(scene, TAKEOFF)
    start = root.matrix_world.translation.copy()
    scene_at(scene, LANDING)
    finish = root.matrix_world.translation.copy()
    travel = horizontal(finish - start).normalized()
    event_samples, landing_gaps, both_air = {}, [], []
    previous_heading, rotation = None, 0.0
    for step in range(2545):
        frame = 1 + step / 16
        scene_at(scene, frame)
        hip_right = horizontal(hips[1].matrix_world.translation - hips[0].matrix_world.translation).normalized()
        gaps = {s: min_height(xyz[s], blades[s].matrix_world) - ice_top for s in SIDES}
        if TAKEOFF <= frame <= LANDING:
            forward = root.matrix_world.to_3x3() @ Vector((1, 0, 0))
            heading = math.atan2(forward.y, forward.x)
            if previous_heading is not None:
                rotation += wrapped(heading - previous_heading)
            previous_heading = heading
        if min(gaps.values()) > .03:
            both_air.append(frame)
        if LANDING <= frame <= 102:
            landing_gaps.append(gaps["Right"])
        if frame in (TAKEOFF, 61, 76, 90, LANDING, 98, 102):
            event_samples[frame] = {}
            for side, sign in zip(SIDES, (-1, 1)):
                toe = horizontal(boots[side].matrix_world.to_3x3() @ TOE)
                cross = (blades[side].matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
                if cross.dot(sign * hip_right) < 0:
                    cross.negate()
                event_samples[frame][side] = {
                    "gap_mm": round(gaps[side] * 1000, 3),
                    "toe_to_travel_deg": round(math.degrees(toe.angle(travel)), 3),
                    "outside_edge_down_deg": round(math.degrees(math.asin(-cross.z)), 3),
                }
    events = {"takeoff": event_samples[TAKEOFF]["Left"], "landing": event_samples[LANDING]["Right"]}
    turns = rotation / math.tau
    print(json.dumps({
        "event_samples": event_samples, "air_turns": round(turns, 6),
        "right_landing_mm_range": [round(min(landing_gaps)*1000, 3), round(max(landing_gaps)*1000, 3)],
        "left_right_both_more_than_30_mm_before_takeoff_samples": sum(f < TAKEOFF for f in both_air),
    }, indent=2))
    if scene.get("prototype_version") == "v176":
        assert abs(abs(turns) - 1.5) < .005, "Expected 1.5 airborne rotations"
        assert events["takeoff"]["toe_to_travel_deg"] <= 3
        assert events["landing"]["toe_to_travel_deg"] >= 177
        assert all(0 <= e["gap_mm"] <= 6 and e["outside_edge_down_deg"] >= 1 for e in events.values())
        assert event_samples[TAKEOFF]["Right"]["gap_mm"] > 50
        assert event_samples[LANDING]["Left"]["gap_mm"] > 50
        assert 0 < min(landing_gaps) <= max(landing_gaps) < .006


if __name__ == "__main__":
    run(bpy.context.scene)
