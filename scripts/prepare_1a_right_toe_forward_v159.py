"""Build V159 by correcting the physical toe axis on the right landing skate."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v156.blend"
OUT = ASSET / "single-axel-1a-human-rink-v159.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v159-web.glb"
TORSO_FORWARD_LOCAL = Vector((0.0, -1.0, 0.0))
BOOT_TOE_LOCAL = Vector((0.0, 1.0, 0.0))
BLADE_TOE_LOCAL = Vector((0.0, -1.0, 0.0))
WORLD_UP = Vector((0.0, 0.0, 1.0))


def horizontal(vector):
    result = Vector((vector.x, vector.y, 0.0))
    return result.normalized() if result.length > 1e-8 else None


def signed_angle(first, second):
    first, second = horizontal(first), horizontal(second)
    if first is None or second is None:
        raise RuntimeError("Degenerate physical skate heading")
    return math.degrees(math.atan2(first.x * second.y - first.y * second.x,
                                   first.dot(second)))


def main():
    if OUT.exists() or WEB_OUT.exists():
        raise FileExistsError("Refusing to overwrite an existing V158 artifact")
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Expected V156 source, got {bpy.data.filepath}")
    scene = bpy.context.scene
    if scene.get("prototype_version") != "v156":
        raise RuntimeError("Expected V156 source scene")
    default_scene = bpy.data.scenes.get("Scene")
    if default_scene is None or sorted(obj.name for obj in default_scene.objects) != [
            "Camera", "Cube", "Light"]:
        raise RuntimeError("The original default Scene signature changed")

    torso = scene.objects["Human · shaped jacket torso"]
    sides = {}
    for side in ("Left", "Right"):
        ankle = scene.objects[f"Human · {side.lower()} ankle joint"]
        skate = scene.objects[f"{side} skate · exact website fit v64"]
        boot = scene.objects[f"{side} skate · website boot v64"]
        blade = scene.objects[f"{side} skate · website blade v64"]
        if skate.parent != ankle or boot.parent != skate or blade.parent != skate:
            raise RuntimeError(f"{side} skate hierarchy changed")
        correction = None
        if side == "Right":
            correction = bpy.data.objects.new(
                f"{side} skate · physical toe-forward correction v159", None)
            scene.collection.objects.link(correction)
            correction.empty_display_type = "ARROWS"
            correction.empty_display_size = 0.08
            correction.parent = ankle
            correction.matrix_parent_inverse = Matrix.Identity(4)
            correction.location = (0.0, 0.0, 0.0)
            correction.rotation_mode = "QUATERNION"
            correction.rotation_quaternion = Quaternion(WORLD_UP, math.pi)
            correction.scale = (1.0, 1.0, 1.0)

            skate_basis = skate.matrix_basis.copy()
            skate.parent = correction
            skate.matrix_parent_inverse = Matrix.Identity(4)
            skate.matrix_basis = skate_basis
        sides[side.lower()] = (ankle, correction, skate, boot, blade)

    rows = []
    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        torso_axis = torso.matrix_world.to_3x3() @ TORSO_FORWARD_LOCAL
        row = {"frame": frame}
        for side, (_, correction, skate, boot, blade) in sides.items():
            boot_toe = boot.matrix_world.to_3x3() @ BOOT_TOE_LOCAL
            blade_toe = blade.matrix_world.to_3x3() @ BLADE_TOE_LOCAL
            row[f"{side}_toe_to_torso_deg"] = signed_angle(torso_axis, boot_toe)
            row[f"{side}_boot_to_blade_deg"] = signed_angle(boot_toe, blade_toe)
            ankle_anchor = (boot.matrix_world @ (Vector((0.0, 0.045, 0.035)) * 1.8))
            row[f"{side}_ankle_anchor_drift_mm"] = (
                ankle_anchor - sides[side][0].matrix_world.translation).length * 1000.0
        rows.append(row)

    right_yaws = [abs(row["right_toe_to_torso_deg"]) for row in rows]
    left_yaws = [abs(row["left_toe_to_torso_deg"]) for row in rows]
    boot_blade = max(abs(row[f"{side}_boot_to_blade_deg"])
                     for row in rows for side in sides)
    anchor_drift = max(row[f"{side}_ankle_anchor_drift_mm"]
                       for row in rows for side in sides)
    key_frames = [row for row in rows if row["frame"] in (48, 70, 78, 79, 87, 92, 120, 136)]
    report = {
        "source": str(SOURCE), "blend": str(OUT), "web_glb": str(WEB_OUT),
        "source_version": scene.get("prototype_version"),
        "visible_boot_toe_axis_local": list(BOOT_TOE_LOCAL),
        "visible_blade_toe_axis_local": list(BLADE_TOE_LOCAL),
        "integer_frame_samples": len(rows),
        "right_max_abs_toe_to_torso_deg": round(max(right_yaws), 5),
        "left_max_abs_toe_to_torso_deg": round(max(left_yaws), 5),
        "max_boot_to_blade_toe_error_deg": round(boot_blade, 6),
        "max_ankle_anchor_drift_mm": round(anchor_drift, 6),
        "key_frames": [{key: (round(value, 4) if isinstance(value, float) else value)
                        for key, value in row.items()} for row in key_frames],
    }
    if max(right_yaws) > 8.05:
        raise RuntimeError("Physical right boot toe is still reversed from torso-forward")
    if boot_blade > 0.02:
        raise RuntimeError("A physical boot toe and blade toe diverged")
    if anchor_drift > 0.01:
        raise RuntimeError("A skate assembly drifted from its ankle pivot")

    scene.name = "Single Axel 1A · right physical skate toe alignment v159"
    scene["prototype_version"] = scene["version"] = "v159"
    scene["skate_toe_forward_v159"] = (
        "Derived from V156. Corrects an axis-reference error: the visible fitted boot mesh's physical "
        "toe is local +Y, while the blade mesh's toe direction is local -Y after its 180-degree child "
        "rotation. The right landing boot/blade assembly is rotated by 180 degrees around its ankle "
        "pivot, preserving the ankle attachment and aligning the physical toe with torso-forward. "
        "The left free-leg skate is unchanged in this candidate after the symmetric experiment created "
        "new boot-to-boot intersections at landing. This is a geometric correction, not a prescribed "
        "Axel body angle.")
    scene["illustrative_simulated"] = True
    scene["technical_reference_limit"] = (
        "Axel references support a forward outside-edge take-off, 1.5 rotations for a single Axel, "
        "opposite-foot backward outside-edge landing, and a checked exit. They do not prescribe a fixed "
        "torso-to-skate angle. Every pose and track in this project is illustrative/simulated.")
    scene.frame_set(92)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
    bpy.ops.export_scene.gltf(
        filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
        export_cameras=True, export_lights=False, export_yup=True,
        use_selection=False, use_active_scene=True, use_visible=True,
        use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
        export_frame_step=1, export_optimize_animation_size=False)
    report.update({
        "version": scene.get("prototype_version"),
        "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
        "status": "illustrative/simulated candidate; awaiting clearance and visual audit",
    })
    print("RIGHT_SKATE_TOE_FORWARD_V159 " + json.dumps(report, ensure_ascii=False))


main()
