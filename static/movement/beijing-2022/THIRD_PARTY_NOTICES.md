# Figure-skating 3D demo asset attribution

## Human reference mesh

- Asset: **CesiumMan** from the Khronos glTF Sample Assets collection
- Source: <https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/CesiumMan>
- License: **CC BY 4.0**
- License text: <https://creativecommons.org/licenses/by/4.0/>
- Local file: `human_cesiumman.glb`

The page now deforms the opaque mesh with its original skin weights. Nineteen skin bones are mapped to the MotionExpert joint positions using segment frames. The original integral shoes are masked where the imported skate boots take over. Materials and pose are modified. This is a generic stylized body, not a scan of the recorded athlete. Bone twist and wrist orientation are approximate.

The earlier Blender v2/v3 scenes retained in the versioned `.blend` files use the CesiumMan model embedded in `index.html`; they do not add a separate model copy. They retarget the weighted surface to the generic 22-joint reference. The active v8 scene uses a project-authored volumetric primitive human and does not use the CesiumMan body mesh. The v8 file retains the older scenes as checkpoints, so this attribution remains applicable to those archived scenes. The v8 head and rink are project-authored, not a likeness or capture of an athlete.

## Ice skates

- Asset: **Ice Skates**, by **IsaacTheMaverick**
- Original: https://sketchfab.com/3d-models/623771273fd44848bd3e4e55dc358190
- Public distribution: https://huggingface.co/datasets/allenai/objaverse/resolve/main/glbs/000-051/623771273fd44848bd3e4e55dc358190.glb
- License: Creative Commons Attribution (`by` in the archived Objaverse metadata).
- License information: https://creativecommons.org/licenses/by/4.0/
- Evidence: `metadata-051.json.gz`, entry `623771273fd44848bd3e4e55dc358190`.
- Original local file: `ice_skates_isaac.glb`.
- Modifications: extracted one skate from the posed pair, removed display objects and ice, normalized orientation and size, mirrored for the second foot, recolored materials. Generated geometry: `skate-derived.json`.
- Build conversion: `node prepare_skate.cjs`, then `node build_skater_viewer.cjs` from the workspace root.

The Blender v3, v8, v18, and v22 scenes reuse the skate geometry embedded in `index.html`, including the boot, blade, tongue, and lace meshes. The active v8 scene reuses the fitted skate assemblies and their generic animation from v3. v18 enlarges both assemblies 1.5×; v22 enlarges the v18 assemblies another 1.5× around the fitted ankle anchors. v22 trims a localized heel-side scan patch, welds duplicate vertices for smoother shading, and adds a small project-authored heel repair cover. The source geometry and these modifications remain under the credited CC BY 4.0 terms. This is a visual fit to the generic pose reference. It is not a certified skate-size measurement; the source joint sequence does not measure blade roll or contact edge.

The first candidate by UniverseGames23234 was not imported: its download API required authentication. The IsaacTheMaverick asset is independently available in the public Objaverse collection. The model is artist-created and is not a certified measurement of standard skating equipment.

### Foot attachment correction (2026-09-24)

The estimated boot ankle landmark `(0, .035, -.045)` and forefoot landmark `(0, -.055, .065)` define a downward-sloping local reference vector. That reference, not the horizontal blade axis, is mapped to the recorded ankle-to-foot joint direction. This removes an approximately 39-degree artificial downward pitch in the flat-foot fixture. These are visual registration estimates, not athlete-calibrated anatomical measurements. Foot roll is underdetermined by joint positions: the renderer transports the previous orientation, restores the up reference gradually (at most four degrees of roll correction per source frame), and applies symmetric five-frame quaternion smoothing. The ankle anchor remains exact. Grounding uses actual blade vertices rather than bounding-box corners. The recorded pelvis-centred motion and illustrative trajectory remain unchanged; this does not certify the action as a biomechanically accurate Axel.

## Motion and height limitations

The MotionExpert coordinates are pelvis-centred. The displayed lift is a relative foot-position proxy; the ice clearance is illustrative. Neither gives a calibrated world-space jump height or verified flight phase. The five-frame smoothing and playback interval are presentation choices. The old Python builder creates the previous procedural version; use the Node builder for this version.

## Procedural face details

- No additional third-party head mesh or texture was downloaded. The viewer adds a low-complexity head surface and facial features with the already-bundled Three.js geometry primitives (`SphereGeometry` and `BufferGeometry`) so the page remains self-contained and works offline.
- Three.js geometry references: <https://threejs.org/docs/pages/SphereGeometry.html>, <https://threejs.org/docs/pages/BufferGeometry.html>, and <https://threejs.org/manual/pages/primitives.html>.
- The head is a generic stylized replacement aligned to the recorded neck/head direction, not an athlete scan. Original head-weighted triangles are removed, and the new opaque head is centered above the neck rather than offset in front of the old head. The earlier claim that head masking necessarily removes the torso was incorrect; the corrected filtering preserves the body.

### Blender v8 head

The active v8 Blender scene builds its head from native authored mesh rings and ellipsoid details for ears, eyes, irises, brows, nose, scalp, and hair. No external head model or texture is embedded. A BlendKit “Human Base Mesh (Sculpting)” candidate was reviewed, but retrieval requires its add-on/account; the scene therefore does not depend on that external service. The candidate is listed as Royalty Free at <https://www.blendkit.com/asset-gallery-detail/b881b381-b12a-4057-b018-6506331564df/>; terms are at <https://www.blendkit.com/docs/licenses/>. It is not included in the project.


## MotionExpert
Source: https://github.com/MotionXperts/MotionExpert (Apache-2.0 repository license, verified 2026-11-05). The released dataset is described in its README and stored in its dataset directory. This existing demo uses one Single Axel sequence, cropped to 200 display frames, mirrored, smoothed and combined with illustrative travel. The motion is not Olympic athlete capture. Full repository license: LICENSE.MOTIONEXPERT.txt.

## Three.js and GLTFLoader
Three.js by the Three.js authors, MIT license. Source: https://github.com/mrdoob/three.js. Full license: LICENSE.THREE.txt. The Blender v61 web player bundles Three.js r160 and its matching `GLTFLoader` addon in `axel-1a-prototype/vendor/`; these files were extracted from the project's existing inline runtime in `static/movement/index.html`. The player loads these local copies and does not request Three.js from a CDN. The older generic 22-joint page continues to use its existing bundled/inline implementation.

## Integration changes
The original demo was copied from the user’s existing generated Single Axel page; only presentation CSS was changed to separate its canvas, statistics and controls. The overlay and return navigation are part of the CSC316 application.


## FS-Jump3D Axel sample

Skater_A-Axel-08 Round 3 adapts the FS-Jump3D dataset by Ryota Takeda
and collaborators. Source and adapted motion use CC BY-NC-SA 4.0.
Source https://github.com/ryota-skating/FS-Jump3D
License https://creativecommons.org/licenses/by-nc-sa/4.0/


## Double Axel database rebuild (2A-FS)

The current 2A and the 2A-FS comparison clips derive from FS-Jump3D by Ryota Takeda and collaborators, trial Skater_C/Axel/Axel_7.c3d. The marker-derived poses were retargeted to the generic CSC316 character. Later revisions adjusted the character proportions, arm transitions and free skate position during exit. The adapted motion, GLB and preview are offered under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). See the [source dataset](https://github.com/ryota-skating/FS-Jump3D) and [paper](https://arxiv.org/abs/2408.16638). This was a training capture with a generic model and simulated trajectory display.

## Beijing 2022 free skate 4A< study

The 4A< study is an authored Blender illustration using the existing CSC316 character, ice and standard 4A pose basis. The [Olympic Games broadcast](https://www.youtube.com/watch?v=D35ANhKWsc4&t=65s) was used as a visual reference. The [ISU judges' protocol, page 2](https://results.isu.org/results/season2122/owg2022/FSKMSINGLES-----------FNL-000100--_JudgesDetailsperSkater.pdf#page=2) records the official call and score. The [2021–22 technical panel handbook](https://www.nzifsa.org.nz/rules/TP%20Handbook%20Single%20Skating%202021-22_Final.pdf#page=19) explains the under-rotation notation. All model trajectories and timings are simulated. The release carries no footage or Olympic motion-capture data.
