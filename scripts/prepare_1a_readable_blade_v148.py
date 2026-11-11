"""Derive V148 from V145 with a brighter satin-steel finish on both skate blades."""

import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
SOURCE = ASSET / "single-axel-1a-human-rink-v145.blend"
OUT = ASSET / "single-axel-1a-human-rink-v148.blend"
WEB_OUT = ASSET / "single-axel-1a-human-rink-v148-web.glb"
SOURCE_MATERIAL = "V95 · graphite satin stainless skate blade"
TARGET_MATERIAL = "V148 · satin stainless skate blade"
STEEL_COLOR = (0.60, 0.68, 0.73, 1.0)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(),
        f"Expected saved V145 source, got {bpy.data.filepath}")
require(not OUT.exists() and not WEB_OUT.exists(),
        "Refusing to overwrite an existing V148 artifact")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = next((item for item in bpy.data.scenes
              if item.get("prototype_version") == "v145"), None)
require(scene is not None, "V145 scene is missing")
default_scene = bpy.data.scenes.get("Scene")
require(default_scene is not None and
        sorted(obj.name for obj in default_scene.objects) == ["Camera", "Cube", "Light"],
        "The original default Scene signature changed")

source_material = bpy.data.materials.get(SOURCE_MATERIAL)
require(source_material is not None, f"Missing source material {SOURCE_MATERIAL!r}")
material = source_material.copy()
material.name = TARGET_MATERIAL
material.diffuse_color = STEEL_COLOR
require(material.node_tree is not None, "Source steel material has no shader nodes")
principled = next((node for node in material.node_tree.nodes
                   if node.type == "BSDF_PRINCIPLED"), None)
require(principled is not None, "Source steel material has no Principled BSDF")
principled.inputs["Base Color"].default_value = STEEL_COLOR
principled.inputs["Metallic"].default_value = 0.35
principled.inputs["Roughness"].default_value = 0.28

blades = []
for side in ("Left", "Right"):
    blade = scene.objects.get(f"{side} skate · website blade v64")
    require(blade is not None and blade.type == "MESH",
            f"Missing active website blade mesh for {side.lower()} skate")
    old_slots = [slot.material.name if slot.material else None
                 for slot in blade.material_slots]
    require(SOURCE_MATERIAL in old_slots,
            f"{side} blade does not use expected material: {old_slots}")
    blade.data.materials.clear()
    blade.data.materials.append(material)
    blades.append({"name": blade.name, "vertices": len(blade.data.vertices),
                   "material": material.name, "old_materials": old_slots})

scene.name = "Single Axel 1A · satin-steel skate readability v148"
scene["prototype_version"] = scene["version"] = "v148"
scene["skate_blade_revision_v148"] = (
    "Derived from V145. Preserves website boot/blade meshes, blade transforms, ankle fit, "
    "animation, rink and cameras. Only the material on both active website blade meshes is "
    "copied and brightened for screen-scale steel readability. All action and dimensions "
    "remain illustrative/simulated.")
scene["illustrative_simulated"] = True
scene.frame_set(90)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
bpy.ops.export_scene.gltf(
    filepath=str(WEB_OUT), export_format="GLB", export_animations=True,
    export_cameras=True, export_lights=False, export_yup=True,
    use_selection=False, use_active_scene=True, use_visible=True,
    use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
    export_frame_step=1, export_optimize_animation_size=False)
print("V148_STEEL_BUILD " + json.dumps({
    "source": str(SOURCE), "blend": str(OUT), "web_glb": str(WEB_OUT),
    "material": TARGET_MATERIAL, "base_color_linear_rgba": STEEL_COLOR,
    "metallic": principled.inputs["Metallic"].default_value,
    "roughness": principled.inputs["Roughness"].default_value,
    "blades": blades,
    "default_scene_objects": sorted(obj.name for obj in default_scene.objects),
    "status": "illustrative/simulated candidate; visual review pending",
}, ensure_ascii=False))
