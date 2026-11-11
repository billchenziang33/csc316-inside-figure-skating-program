# Inside a Figure-Skating Program

A CSC316 prototype built with Vite, Svelte 5, and D3. It explores the official Beijing 2022 men's singles top-ten scoring protocols and presents a separate generic 3D jump reference.

## Live site

Open the public prototype at [inside-figure-skating-program.eagercoast2.chatgpt.site](https://inside-figure-skating-program.eagercoast2.chatgpt.site/). No local server is needed.

## Current Blender reference

The interactive Movement panel uses the V175 Blender/GLB scene with draggable 3D orbit, front/side/skate views, playback, frame scrubbing, and a live simulated trajectory. V175 reconstructs both knees to bend forward and separates the legs and skates. The matching assets, previews, measured changes, sources and limits are documented in [the Single Axel README](static/movement/axel-1a-prototype/README.md). The animation is illustrative/simulated and uses no Beijing 2022 athlete capture.

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

In column C, activate **Expand 3D example** to open the viewport-sized interactive 3D dialog. Moving the pointer over the panel does not launch it. The upper-right **Return to the main page** button or Escape closes it without changing the selected athlete/program/element. The demo is served from `/movement/index.html` on the same origin, with canvas, statistics and playback controls laid out separately; on phones the camera follows the mirrored skater horizontally.

This reuses the user's existing generated Single Axel example, preserving its generic-motion caveats and asset credits. The MotionExpert repository's Apache-2.0 license and Three.js MIT license are included under `static/movement/`; CC BY mesh/skate credits are preserved in `THIRD_PARTY_NOTICES.md` and the demo's expandable credits. Existing external frames remained blank during diagnostics; the local integrated demo was verified interactively in Edge.
