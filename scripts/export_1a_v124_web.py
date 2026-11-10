"""Export the saved V124 scene to an animated web GLB."""

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "static" / "movement" / "axel-1a-prototype"
EXPECTED = ASSET / "single-axel-1a-human-rink-v124.blend"
OUTPUT = ASSET / "single-axel-1a-human-rink-v124-web.glb"
if Path(bpy.data.filepath).resolve() != EXPECTED.resolve():
	 raise RuntimeError(f"Expected saved V124 scene, got {bpy.data.filepath}")
if OUTPUT.exists():
	 raise RuntimeError(f"Refusing to overwrite web export: {OUTPUT}")
scene = next((item for item in bpy.data.scenes
			  if item.get("prototype_version") == "v124"), None)
if scene is None or scene.camera is None or scene.camera.name != "Action skater side profile full-body v124":
	 raise RuntimeError("Saved V124 scene does not open on the full-body side camera")
default_scene = bpy.data.scenes.get("Scene")
if default_scene is None or sorted(obj.name for obj in default_scene.objects) != ["Camera", "Cube", "Light"]:
	 raise RuntimeError("The original default Scene signature changed")

bpy.ops.export_scene.gltf(
	 filepath=str(OUTPUT), export_format="GLB", export_animations=True,
	 export_cameras=True, export_lights=False, export_yup=True,
	 use_selection=False, use_active_scene=True, use_visible=True,
	 use_renderable=True, export_animation_mode="SCENE", export_frame_range=True,
	 export_frame_step=1, export_optimize_animation_size=False)
print("V124_WEB_EXPORT " + json.dumps({
	"blend": str(EXPECTED), "web_glb": str(OUTPUT),
	"default_scene_objects": sorted(obj.name for obj in default_scene.objects),
	"scene_objects": len(scene.objects),
	"frame_range": [scene.frame_start, scene.frame_end],
	"camera": scene.camera.name,
}, ensure_ascii=False))
