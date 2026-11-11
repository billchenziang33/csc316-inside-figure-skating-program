"""Correct the V169 boot/blade axis using the physical toe ends of their meshes."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v169.blend"
OUT = ASSET / "single-axel-1a-human-rink-v174.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v174-web.glb"
ICE_TOP_OBJECT = "V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)"
TOE_CORRECTION_PIVOTS = {
    "Left": "Left skate · exact website fit v64",
    "Right": "Right skate · physical toe-forward correction v159",
}
BOOT_PHYSICAL_TOE_LOCAL = Vector((0.0, -1.0, 0.0))
BLADE_PHYSICAL_TOE_LOCAL = Vector((0.0, 1.0, 0.0))
TORSO_FORWARD_LOCAL = Vector((0.0, -1.0, 0.0))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def horizontal(vector):
    value = Vector((vector.x, vector.y, 0.0))
    return value.normalized() if value.length > 1e-8 else None


def signed_angle(first, second):
    a, b = horizontal(first), horizontal(second)
    require(a is not None and b is not None, "Degenerate body or physical skate toe axis")
    return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))


def mesh_end_profile(obj, end):
    ys = [vertex.co.y for vertex in obj.data.vertices]
    bound = min(ys) if end == "min" else max(ys)
    band = 0.015
    vertices = [vertex.co for vertex in obj.data.vertices
                if (vertex.co.y <= bound + band if end == "min" else vertex.co.y >= bound - band)]
    require(vertices, f"No vertices at the {end}-Y end of {obj.name}")
    return {"y": round(bound, 6), "z_min": round(min(v.z for v in vertices), 6),
            "z_max": round(max(v.z for v in vertices), 6), "sample_vertices": len(vertices)}


def blade_min_world_z(blade):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = blade.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return min((evaluated.matrix_world @ vertex.co).z for vertex in mesh.vertices)
    finally:
        evaluated.to_mesh_clear()


def isolate_action(obj):
    animation = obj.animation_data
    require(animation is not None and animation.action is not None,
            f"Missing transform action on {obj.name}")
    if animation.action.users <= 1:
        return
    slot_id = animation.action_slot.identifier
    action = animation.action.copy()
    animation.action = action
    slot = next((item for item in action.slots if item.identifier == slot_id), None)
    require(slot is not None, f"Copied action lost slot {slot_id!r} on {obj.name}")
    animation.action_slot = slot


def make_linear(obj):
    for layer in obj.animation_data.action.layers:
        for strip in layer.strips:
            if strip.type != "KEYFRAME":
                continue
            bag = strip.channelbag(obj.animation_data.action_slot)
            if bag is None:
                continue
            for curve in bag.fcurves:
                if curve.data_path == "rotation_quaternion":
                    for point in curve.keyframe_points:
                        point.interpolation = "LINEAR"
                    curve.update()


def main():
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(),
            f"Expected V169 source, got {bpy.data.filepath}")
    require(not OUT.exists() and not WEB_OUT.exists(),
            "Refusing to overwrite an existing V174 artifact")
    scene = bpy.context.scene
    require(scene.get("prototype_version") == "v169", "Expected V169 source scene")
    default_scene = bpy.data.scenes.get("Scene")
    require(default_scene is not None and
            sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
            "The original default Blender Scene signature changed")

    torso = scene.objects["Human · shaped jacket torso"]
    ice = scene.objects[ICE_TOP_OBJECT]
    ice_top_z = max((ice.matrix_world @ vertex.co).z for vertex in ice.data.vertices)
    skates = {}
    for side, pivot_name in TOE_CORRECTION_PIVOTS.items():
        ankle = scene.objects[f"Human · {side.lower()} ankle joint"]
        pivot = scene.objects[pivot_name]
        fit = scene.objects[f"{side} skate · exact website fit v64"]
        boot = scene.objects[f"{side} skate · website boot v64"]
        blade = scene.objects[f"{side} skate · website blade v64"]
        require(pivot.parent == ankle, f"{side} skate correction pivot is not ankle-parented")
        require((fit == pivot or fit.parent == pivot) and
                boot.parent == fit and blade.parent == fit,
                f"{side} fitted boot/blade hierarchy changed")
        boot_profile = mesh_end_profile(boot, "min")
        require(boot_profile["z_max"] < mesh_end_profile(boot, "max")["z_max"],
                f"The -Y end is not the lower physical toe region for {side} boot")
        skates[side] = {"ankle": ankle, "pivot": pivot, "fit": fit,
                        "boot": boot, "blade": blade,
                        "boot_toe_profile": boot_profile,
                        "blade_toe_axis_error_deg": None}

    # Both pivots sit at the ankle. The left fitted group is animated, so apply the
    # same constant parent-space half-turn to each saved quarter-frame quaternion.
    for side, refs in skates.items():
        require((refs["pivot"].matrix_world.translation -
                 refs["ankle"].matrix_world.translation).length < 1e-5,
                f"{side} skate pivot is not at its ankle")

    left_pivot = skates["Left"]["pivot"]
    require(left_pivot.rotation_mode == "QUATERNION",
            "Expected the animated left fitted group to use quaternion rotation")
    isolate_action(left_pivot)
    delta = Quaternion(Vector((0.0, 0.0, 1.0)), math.pi)
    left_samples = []
    for index in range(637):
        frame = 1.0 + index * 0.25
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        left_samples.append((frame, left_pivot.rotation_quaternion.copy().normalized()))

    previous_quaternion = None
    for frame, quaternion in left_samples:
        scene.frame_set(math.floor(frame), subframe=frame - math.floor(frame))
        bpy.context.view_layer.update()
        corrected = (delta @ quaternion).normalized()
        if previous_quaternion is not None and corrected.dot(previous_quaternion) < 0.0:
            corrected.negate()
        left_pivot.rotation_quaternion = corrected
        left_pivot.keyframe_insert(data_path="rotation_quaternion", frame=frame,
                                   group="Physical skate toe-axis correction v174")
        previous_quaternion = corrected.copy()
    make_linear(left_pivot)

    right_pivot = skates["Right"]["pivot"]
    require(right_pivot.animation_data is None or right_pivot.animation_data.action is None,
            f"Refusing static rotation edit on animated {right_pivot.name}")
    right_pivot.rotation_mode = "QUATERNION"
    right_pivot.rotation_quaternion = Quaternion()

    # Audit all quarter frames for physical toe alignment, blade alignment, and fit.
    max_toe_torso_yaw = {side: 0.0 for side in skates}
    max_boot_blade_yaw = 0.0
    max_anchor_error_mm = 0.0
    toe_heading_rows = []
    for index in range(637):
        frame = 1.0 + index * 0.25
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        torso_axis = torso.matrix_world.to_3x3() @ TORSO_FORWARD_LOCAL
        row = {"frame": frame}
        for side, refs in skates.items():
            boot_axis = refs["boot"].matrix_world.to_3x3() @ BOOT_PHYSICAL_TOE_LOCAL
            blade_axis = refs["blade"].matrix_world.to_3x3() @ BLADE_PHYSICAL_TOE_LOCAL
            torso_yaw = signed_angle(torso_axis, boot_axis)
            blade_yaw = signed_angle(boot_axis, blade_axis)
            max_toe_torso_yaw[side] = max(max_toe_torso_yaw[side], abs(torso_yaw))
            max_boot_blade_yaw = max(max_boot_blade_yaw, abs(blade_yaw))
            anchor = refs["boot"].matrix_world @ (Vector((0.0, 0.045, 0.035)) * 1.8)
            anchor_error = (anchor - refs["ankle"].matrix_world.translation).length * 1000.0
            max_anchor_error_mm = max(max_anchor_error_mm, anchor_error)
            row[f"{side.lower()}_toe_to_torso_deg"] = round(torso_yaw, 4)
            row[f"{side.lower()}_boot_blade_deg"] = round(blade_yaw, 6)
        if frame in (1.0, 47.0, 60.0, 74.0, 87.0, 92.0, 100.0, 136.0, 156.0):
            toe_heading_rows.append(row)

    minimum_clearance = {side: {"meters": float("inf"), "frame": None} for side in skates}
    blade_local_vertices = {
        side: [tuple(vertex.co) + (1.0,) for vertex in refs["blade"].data.vertices]
        for side, refs in skates.items()
    }
    for index in range(2545):
        frame = 1.0 + index / 16.0
        whole = math.floor(frame)
        scene.frame_set(whole, subframe=frame - whole)
        bpy.context.view_layer.update()
        for side, refs in skates.items():
            matrix = refs["blade"].matrix_world
            vertices_z = [(matrix @ Vector(vertex[:3])).z for vertex in blade_local_vertices[side]]
            gap = min(vertices_z) - ice_top_z
            if gap < minimum_clearance[side]["meters"]:
                minimum_clearance[side] = {"meters": gap, "frame": frame}

    report = {
        "version": "v174",
        "source": "v169",
        "physical_axis_basis": {
            "boot_toe_local": list(BOOT_PHYSICAL_TOE_LOCAL),
            "blade_toe_local": list(BLADE_PHYSICAL_TOE_LOCAL),
            "left_boot_mesh_toe_end": skates["Left"]["boot_toe_profile"],
            "right_boot_mesh_toe_end": skates["Right"]["boot_toe_profile"],
        },
        "correction": "Rotate each fitted skate assembly 180 degrees about its ankle-origin pivot; do not alter leg or root tracks.",
        "quarter_frame_samples": 637,
        "max_abs_physical_toe_to_torso_yaw_deg": {
            side: round(value, 5) for side, value in max_toe_torso_yaw.items()},
        "max_abs_boot_to_blade_toe_yaw_deg": round(max_boot_blade_yaw, 6),
        "max_ankle_attachment_error_mm": round(max_anchor_error_mm, 6),
        "sixteenth_frame_blade_clearance_samples": 2545,
        "minimum_blade_clearance": minimum_clearance,
        "key_frames": toe_heading_rows,
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
    }
    require(max(max_toe_torso_yaw.values()) < 12.1,
            "Physical boot toe remains misaligned with the torso")
    require(max_boot_blade_yaw < 0.02, "Physical boot and blade toe axes diverged")
    require(max_anchor_error_mm < 0.01, "Ankle attachment moved")
    require(min(item["meters"] for item in minimum_clearance.values()) >= -1e-5,
            "A blade penetrates the modeled ice")

    scene.name = "Single Axel 1A · physical skate toe axes v174"
    scene["prototype_version"] = scene["version"] = "v174"
    scene["physical_skate_toe_axis_v174"] = (
        "Derived from V169. Mesh inspection establishes the website boot toe at local -Y and the "
        "matching blade toe at local +Y. V169's prior +Y/-Y audit used both heel directions and "
        "therefore reported a false alignment. Each fitted skate assembly is rotated 180 degrees "
        "around its ankle-origin pivot; leg and root animation tracks are unchanged.")
    scene["illustrative_simulated"] = True
    scene["technical_reference_limit"] = (
        "ISU and coaching sources inform phase order and opposite-foot backward landing, not a numeric "
        "torso-to-toe heading target. V174 corrects the local mesh-axis interpretation and remains an "
        "illustrative/simulated animation, not athlete capture or validated biomechanics.")
    scene.frame_set(92)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
    bpy.ops.export_scene.gltf(
        filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
        export_cameras=True, export_lights=False, export_yup=True,
        use_selection=False, use_active_scene=True, use_visible=True,
        use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
        export_frame_step=1, export_optimize_animation_size=False,
    )
    report["blend"] = str(OUT)
    report["web_glb"] = str(WEB_OUT)
    report["status"] = "Built; half-frame surface and visual audits pending"
    print("PHYSICAL_SKATE_TOE_AXIS_V174 " + json.dumps(report, ensure_ascii=False))


main()
