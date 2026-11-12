"""Correct V177 anatomical handedness without reversing the airborne yaw or ice track."""
import argparse
import math
import sys
from pathlib import Path

import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_1a_anatomical_handedness import LANDING, ROOT, TAKEOFF, flat, run as audit


def prepare(scene, blend, glb):
    assert scene.get("prototype_version") == "v177"
    root = scene.objects[ROOT]
    scene.frame_set(LANDING)
    land = root.matrix_world.translation.copy()
    scene.frame_set(TAKEOFF)
    travel = flat(land - root.matrix_world.translation)
    local_travel = root.matrix_world.to_3x3().inverted() @ travel
    angle = math.atan2(local_travel.y, local_travel.x)
    children = tuple(root.children)
    cameras = tuple(obj for obj in root.children_recursive if obj.type == "CAMERA")

    # Reflect poses in the moving root frame, with the plane aligned to the
    # take-off blade. The root yaw, travel, timing and all runner heights stay intact.
    mirror = bpy.data.objects.new("Skater pose · anatomical handedness v178", None)
    scene.collection.objects.link(mirror)
    mirror.parent = root
    mirror.rotation_euler.z = 2 * angle
    mirror.scale.y = -1
    for child in children:
        child.parent = mirror
    # Keep the reflected follow cameras upright and right-handed. The fixed
    # arena, front and close-up cameras stay outside the reflected hierarchy.
    for camera in cameras:
        assert not camera.animation_data and not camera.constraints
        camera.scale.x *= -1

    scene["prototype_version"] = "v178"
    scene["source_version"] = "v177"
    scene["axel_contact"] = "Illustrative anatomical left forward outside take-off, 1.5 CCW turns, anatomical right backward outside landing."
    scene.name = "Single Axel 1A · anatomical handedness v178"
    audit(scene)
    scene.frame_set(TAKEOFF)
    for camera in cameras:
        assert camera.matrix_world.to_3x3().determinant() > 0
    assert {obj.name for obj in bpy.data.scenes["Scene"].objects} == {"Camera", "Cube", "Light"}

    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", export_yup=True,
                              export_animations=True, export_animation_mode="SCENE",
                              export_frame_range=True, export_optimize_animation_size=False,
                              export_cameras=True, use_active_scene=True,
                              use_visible=True, use_renderable=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--glb", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])

    prepare(bpy.context.scene, args.blend.resolve(), args.glb.resolve())
