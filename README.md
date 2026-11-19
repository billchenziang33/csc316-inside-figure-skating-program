# Inside a Figure-Skating Program

A CSC316 project built with Vite, Svelte 5, and D3. Its workbench links official Beijing 2022 men's singles top-ten scoring protocols to 50 illustrative 3D references.

## Live site

Open the [CSC316 course site](https://csc316-inside-figure-skating-progra.vercel.app/). The [3D library](https://csc316-inside-figure-skating-progra.vercel.app/movement/beijing-2022/) and [Hanyu's first free-skating element](https://csc316-inside-figure-skating-progra.vercel.app/#workspace/FS:4:1) are on the course domain. The models and preview images are served on demand from the motion archive.

The left column selects a scored occurrence, the middle column keeps the official score, and the right column opens the corresponding standard technique reference on demand. Hanyu's first free-skating element retains its official `4A<` call and 5.00 points. Its 3D reference shows a standard quadruple Axel. Measured trajectories belong to the simulation. [ISU protocol](https://results.isu.org/results/season2122/owg2022/FSKMSINGLES-----------FNL-000100--_JudgesDetailsperSkater.pdf#page=2) · [ISU jump guide](https://www.isu-skating.com/en/figure-skating/news/figure-skating-jumps-explained/)

## Movement Reference

[Step 6 · Movement Reference](https://csc316-inside-figure-skating-progra.vercel.app/#movement) embeds the complete 50-entry 3D Movement Library. Search or filter the competition movement models, then open a model's interactive Blender player on the same page. The standalone library remains at `/movement/beijing-2022/`.

The shared player has three camera controls: a 45° angle, **Auto fit** from above the rink for a full-body frame, and **Bullet Time**, which pauses at the selected frame and makes one slow camera orbit around the skater from a lower 35°-above-rink view. A compact flight capsule sits over the rink; open it to read the simulated phase, height, horizontal travel, peak rise and jump distance without reducing the player layout. A soft projected shadow helps show the skater's clearance above the ice. Bullet Time is a camera move; the pose stays at the selected instant. All 50 entries use the same player.

The workbench also links to the standalone V178 Single Axel study. It shows a left-foot forward take-off, a one-and-a-half-turn airborne phase, and a right-foot backward landing. The animation is illustrative/simulated and uses no Beijing 2022 athlete capture. [Single Axel assets and measurements](static/movement/axel-1a-prototype/README.md)

## Milestone 7 package

The current Prototype 1 package is `submission/CSC316_Milestone7_Final_Submission_2026-11-07-r3.zip`. It includes the current source, the 81-page M1-M7 process book, and the active Blender v62 `.blend` scene and web GLB with side/front stills. The 80-page base preserves the November 6 Google Docs export; the final page records the current v62 player and verification. The player includes local Three.js r160 and `GLTFLoader` files. Each team member must complete their own self/peer evaluation. Quercus's assignment body requests a ZIP, while its file-type label and upload control accept PDF; confirm the required upload format with course staff before submission.

## Run locally

```sh
npm install
npm run data:prepare
npm run test
npm run dev
```

The source is [`data/source/Beijing_2022_Mens_Singles_Top10_Data_Brief.md`](data/source/Beijing_2022_Mens_Singles_Top10_Data_Brief.md), based on the [official ISU event results](https://results.isu.org/results/season2122/owg2022/) and [results book](https://www.isuresults.com/results/season2122/owg2022/owg2022_protocol.pdf). The linked 3D demo is an illustrative reference, not a recording or reconstruction of an Olympic skater.

The project intentionally keeps official scoring records separate from motion references. Protocol element order is not a timestamp or rink location. The cohort contains the final top ten only.

## Guided navigation

Six steps cover the finding, program selection, three-column workbench, S11 protocol matrix, evidence gallery, and movement reference. Back/Next and the progress navigation preserve the shared athlete/program/element selection. Hash links support browser history and direct links, including `#chart-detail/S15`.

The gallery shows S12/S01/S02/S06/S15 one at a time, with an expanded chart stage and underlying-value tables. Below 1040 CSS pixels, the workspace uses Sequence/Score/Movement tabs.

In column C, select **Play** to open the viewport-sized interactive 3D dialog. The upper-right **Return to the main page** button or Escape closes it and restores the selected athlete, program and element. The same-origin player lives at `/movement/beijing-2022/player.html`.

This reuses the user's existing generated Single Axel example, preserving its generic-motion caveats and asset credits. The MotionExpert repository's Apache-2.0 license and Three.js MIT license are included under `static/movement/`; CC BY mesh/skate credits are preserved in `THIRD_PARTY_NOTICES.md` and the demo's expandable credits. Existing external frames remained blank during diagnostics; the local integrated demo was verified interactively in Edge.
