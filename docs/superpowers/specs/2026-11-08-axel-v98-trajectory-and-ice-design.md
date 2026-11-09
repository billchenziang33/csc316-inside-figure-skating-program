# V98 Single Axel trajectory, foot alignment, and ice design

**Status:** Proposed for review
**Scope:** Derive V98 from the existing V97 Blender scene and publish a matching web player asset. Keep every pose, measurement, and path explicitly labeled *illustrative/simulated*.

## Evidence and problem statement

V97 is the current local prototype. Its animation uses the existing 22-joint pose reference and a skater root transform. The attached older Blender screenshot is not evidence of the V97 scene: its timeline is at frame 167, while V97 runs frames 1–160.

The V97 ice object (`V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)`) has its upper surface at world Z=+0.012 m. The V97 blade audit measured the lowest blade point at about Z=+0.001 m, but compared it with Z=0. Relative to the actual ice surface, that is approximately 11 mm of penetration. The previous clearance claim therefore used the wrong reference plane and must be withdrawn.

The V97 root track indicates about 0.435 m of rise from takeoff to apex and about 1.788 m of forward displacement from takeoff to landing. These are values derived from the simulated Blender animation, not athlete measurements. The original movement page separately defines a reference preset of 0.60 s flight, 0.44 m peak lift, and 1.92 m travel; retain those only as a clearly identified comparison preset.

V97 boot-to-ankle fit and boot/blade axis audits are numerically close, but the source foot-to-toe residual reaches approximately 88.4° in constrained poses. A good fit between the boot and ankle alone does not prove the anatomical toe, boot, and blade point in the same direction. V98 must evaluate the visible foot/toe axis and skate direction together through the full jump.

## Proposed V98 behavior

1. **Preserve and derive.** Save a new V98 `.blend` and `.glb` from V97. Do not overwrite V97 or any older asset. Keep the default Blender `Scene` objects and collections intact; add the new work under its existing project collections.
2. **Correct the contact plane.** Use the measured top of the ice mesh, Z=+0.012 m, as the blade-clearance reference. Constrain the landing/approach blades to a visible but small clearance target of at least 5 mm where they should be above ice. For intentional contact poses, target contact without penetration within the audit tolerance. Recompute the root's vertical trajectory after this correction rather than applying an unchecked scene-wide offset.
3. **Align toe, boot, and blade.** At every sampled frame, compare the anatomical foot/toe forward direction, boot forward axis, and blade forward axis in world space. Fix the left-foot reversal and the later right-foot angle by correcting pose-local transforms/constraints so all three axes remain consistent while the foot is planted or rotating. Preserve the existing 22-joint pose source and stage timing.
4. **Audit collisions and continuity.** Sample the complete animation at 1/16-frame intervals, including approach, takeoff, flight rotation, landing, and glide-out. Check blade-to-ice clearance and mesh intersections between each skate/boot and its adjacent cuff/shank. Treat intended joint/limb overlap as a separate, documented category; report unexpected intersections rather than claiming a global no-penetration guarantee. Also measure frame-to-frame heading and position changes for discontinuities.
5. **Add actual-track flight markers and HUD.** In the Blender scene and exported GLB, mark takeoff, apex, landing, the apex vertical projection to the ice, and the skater's sampled flight path. In the website player, update a compact HUD during playback and scrubbing with phase/frame, root/pelvis-proxy height above takeoff, horizontal distance from takeoff, and total takeoff-to-landing travel. Derive these values from the actual exported Blender root track and GLB animation time; do not substitute the reference preset values. Label the HUD and markers *Illustrative / simulated*.
6. **Improve ice appearance.** Give the current pale-blue surface restrained tonal variation, roughness variation, subtle skate scratches, and readable reflections while keeping markings low-contrast. Use materials/textures packaged in the Blender file and GLB so the web version does not depend on loose external files. Keep sufficient contrast for the skater, blades, path, and markers.
7. **Match the web presentation.** Provide clear front and side inspection views in the site, use the same V98 GLB for both, and keep playback/scrubbing synchronized with the HUD. Keep the existing arena geometry and seating; do not add audience people.

## Reference values and interpretation

| Quantity | V97 simulated track (pre-correction) | Original page reference preset |
|---|---:|---:|
| Flight time | To be recalculated from V98 takeoff/landing frames and FPS | 0.60 s |
| Peak rise | About 0.435 m | 0.44 m |
| Horizontal travel | About 1.788 m | 1.92 m |

The original page uses a kinematic parabola (`y = 4 × height × u × (1 − u)`) and travel from horizontal speed × flight time. These are pedagogical simulation inputs, not official Single Axel performance measurements. V98's primary HUD uses the actual V98 animation transforms.

## Acceptance checks

- V98 Blender and GLB are new versioned files; V97 and the default Blender scene remain available.
- Ice clearance is measured against the actual ice mesh top. Intended contacts show no penetration beyond the stated numerical tolerance; flight blades have at least 5 mm clearance at the 1/16-frame audit samples.
- Boot-to-ankle alignment error is at most 1 mm; boot-to-blade and visible foot/toe-to-blade heading error are at most 1° in the defined aligned poses. Frames that intentionally articulate the free foot must still avoid a reversed toe/blade direction.
- No unexpected skate/boot-to-shank mesh intersections appear in the sampled animation; any remaining intentional intersections are listed explicitly.
- Takeoff, apex, landing and projection markers agree with the V98 track. HUD height, distance, phase and total travel match sampled transforms and animation time during play and scrub.
- Ice reads as a subtle blue, reflective rink rather than a white plane, with no loss of figure/blade visibility.
- Blender and website front/side views show the same V98 motion. All simulated values and pose data are labeled illustrative/simulated and are not described as Beijing Olympics athlete capture.
- Record measured values, sampling method, known limitations, source/reference links and verification evidence in the project README and `summary.md`.

## Risks and limits

Mesh intersection tests can flag intentional overlaps at joints and can miss thin surface intersections if sampling is too coarse; report the tested object pairs and sampling resolution. The browser may interpolate animation between samples, so inspect transition frames in the actual player in addition to static audits. The scene's root/pelvis proxy is a consistent height reference, not a measured center of mass. No value in this prototype represents real athlete capture or judging data.

## Self-review

- Scope addresses the reported left toe/blade mismatch, ice penetration, readable takeoff/apex/landing and travel, ice appearance, and site parity.
- Preserves versioned history and the existing 22-joint source; does not silently replace the approved reference preset with measured-looking values.
- Acceptance checks are observable and distinguish intended contact/overlap from defects.
- The actual GLB track is the source for the HUD, preventing hand-authored display values from drifting away from the animation.
- Before implementation, confirm exact frame indices, mesh axes, and current website player data flow from code; update this spec if those inspections change any evidence above.
