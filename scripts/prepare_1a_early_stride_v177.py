"""Ease the two-skate weight transfer that snapped at V176 frames 16–17."""

import argparse
import sys
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_1a_axel_contact_v176 import (
    ICE, SIDES, STEP, TOE, TRACKS, forward_knee, hermite, horizontal, insert_world,
    leg_matrix, linearize, min_height, oriented_about, scene_at, smoothstep,
)
from prepare_1a_leg_hinge_v175 import PARTS


START, END = 11, 20


def spline(frame, before, start, end, after):
    return hermite(frame, START, END, start, end, (start - before) / STEP, (after - end) / STEP)


def report(scene, skates, camera):
    previous = None
    largest_step = dict.fromkeys(SIDES, 0.0)
    at_transition = {}
    narrowest_projection = float("inf")
    for frame in range(START, END + 1):
        scene_at(scene, frame)
        ankles = {s: skates[s]["ankle"].matrix_world.translation.copy() for s in SIDES}
        projections = [world_to_camera_view(scene, camera, ankles[s]).x for s in SIDES]
        narrowest_projection = min(narrowest_projection, abs(projections[0] - projections[1]))
        if previous:
            for side in SIDES:
                step = horizontal(ankles[side] - previous[side]).length
                largest_step[side] = max(largest_step[side], step)
                if frame == 17:
                    at_transition[side] = step
        previous = ankles
    return {
        "largest_horizontal_step_m": {s: round(v, 6) for s, v in largest_step.items()},
        "f16_to_17_horizontal_step_m": {s: round(v, 6) for s, v in at_transition.items()},
        "min_front_projected_ankle_gap": round(narrowest_projection, 6),
    }


def run(scene, blend, glb):
    assert scene.get("prototype_version") == "v176", "Open the preserved V176 scene"
    assert all(not path.exists() for path in (blend, glb) if path), "Output already exists"
    assert sorted(obj.name for obj in bpy.data.scenes["Scene"].objects) == ["Camera", "Cube", "Light"]
    skates = {}
    for side in SIDES:
        skates[side] = dict(zip(
            ("thigh", "shin", "knee", "ankle"),
            (scene.objects[f"Human · {side.lower()} {part}"] for part in PARTS),
        ))
        for part in ("boot", "blade"):
            skates[side][part] = scene.objects[f"{side} skate · website {part} v64"]
    ice = scene.objects[ICE]
    ice_top = max((ice.matrix_world @ v.co).z for v in ice.data.vertices)
    blade_points = {s: np.array([tuple(v.co) for v in skates[s]["blade"].data.vertices]) for s in SIDES}
    camera = scene.objects["Action front view"]
    before = report(scene, skates, camera)
    samples = {}
    for index in range(-1, round((END - START) / STEP) + 2):
        frame = START + index * STEP
        scene_at(scene, frame)
        samples[frame] = {s: {n: obj.matrix_world.copy() for n, obj in skates[s].items()} for s in SIDES}
    last = {}
    for frame, snapshot in samples.items():
        if not START < frame < END:
            continue
        scene_at(scene, frame)
        lateral = horizontal(snapshot["Right"]["thigh"].translation -
                             snapshot["Left"]["thigh"].translation).normalized()
        for side, sign in zip(SIDES, (-1, 1)):
            source = snapshot[side]
            ankle_obj = skates[side]["ankle"]
            hip = spline(frame, *(samples[f][side]["thigh"].translation
                                  for f in (START - STEP, START, END, END + STEP)))
            ankle = spline(frame, *(samples[f][side]["ankle"].translation
                                    for f in (START - STEP, START, END, END + STEP)))
            old_hip = source["thigh"].translation
            old_knee = source["knee"].translation
            old_ankle = source["ankle"].translation
            alpha = smoothstep(START, END, frame)
            old_rotation = source["ankle"].to_quaternion()
            rotation = samples[START][side]["ankle"].to_quaternion().slerp(
                samples[END][side]["ankle"].to_quaternion(), alpha,
            )
            delta = rotation @ old_rotation.inverted()
            blade = oriented_about(source["blade"], delta, old_ankle)
            original_gap = min_height(blade_points[side], source["blade"]) - ice_top
            ankle.z = old_ankle.z + ice_top + original_gap - min_height(blade_points[side], blade)
            forward = horizontal(delta @ (source["boot"].to_3x3() @ TOE)).normalized()
            pole = (forward + lateral * sign * .20).normalized()
            knee, axis = forward_knee(hip, ankle, pole, (old_knee-old_hip).length,
                                      (old_ankle-old_knee).length)
            insert_world(skates[side]["thigh"], leg_matrix(hip, knee, axis), frame, last, TRACKS)
            insert_world(skates[side]["shin"], leg_matrix(knee, ankle, axis), frame, last, TRACKS)
            knee_matrix = source["knee"].copy()
            knee_matrix.translation = knee
            insert_world(skates[side]["knee"], knee_matrix, frame, last, ("location",))
            insert_world(ankle_obj, Matrix.LocRotScale(ankle, rotation, source["ankle"].to_scale()),
                         frame, last, ("location", "rotation_quaternion"))
    for nodes in skates.values():
        for name in ("thigh", "shin", "knee", "ankle"):
            linearize(nodes[name], TRACKS, START, END)
    after = report(scene, skates, camera)
    print("EARLY_STRIDE", before, after)
    assert all(value < .11 for value in after["largest_horizontal_step_m"].values())
    assert after["min_front_projected_ankle_gap"] > .025
    scene["prototype_version"] = "v177"
    scene["source_version"] = "v176"
    scene.name = "Single Axel 1A · continuous stride v177"
    scene_at(scene, 17)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    if glb:
        bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", export_yup=True,
                                  export_animations=True, export_animation_mode="SCENE",
                                  export_frame_range=True, export_optimize_animation_size=False,
                                  export_cameras=True, use_active_scene=True,
                                  use_visible=True, use_renderable=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--glb", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    run(bpy.context.scene, args.blend.resolve(), args.glb.resolve() if args.glb else None)
