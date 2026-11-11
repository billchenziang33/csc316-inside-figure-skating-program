import assert from 'node:assert/strict';
import { readFile, stat } from 'node:fs/promises';
import test from 'node:test';

const root = new URL('../static/movement/axel-1a-prototype/', import.meta.url);
const html = await readFile(new URL('player.html', root), 'utf8');
const player = await readFile(new URL('blender-player.js', root), 'utf8');
const prototypePage = await readFile(new URL('index.html', root), 'utf8');
const app = await readFile(new URL('../src/App.svelte', import.meta.url), 'utf8');
const motionOverlay = await readFile(new URL('../src/lib/MotionOverlay.svelte', import.meta.url), 'utf8');
const publicBuild = await readFile(new URL('../scripts/build-public-site.mjs', import.meta.url), 'utf8');
const cameraFit = await readFile(new URL('../static/movement/axel-1a-prototype/camera-fit.mjs', import.meta.url), 'utf8');
const v101Builder = await readFile(new URL('../scripts/prepare_1a_foot_motion_v101.py', import.meta.url), 'utf8');
const v102Builder = await readFile(new URL('../scripts/prepare_1a_actual_ice_track_v102.py', import.meta.url), 'utf8');
const v102Audit = await readFile(new URL('../scripts/audit_1a_actual_ice_track_v102.py', import.meta.url), 'utf8');
const v124Builder = await readFile(new URL('../scripts/prepare_1a_skater_full_body_side_view_v124.py', import.meta.url), 'utf8');
const readme = await readFile(new URL('../static/movement/axel-1a-prototype/README.md', import.meta.url), 'utf8');

test('the standalone player exposes all simulated GLB trajectory measurements', () => {
	for (const id of ['flight-phase', 'flight-height', 'flight-distance', 'flight-peak', 'flight-total']) {
		assert.match(html, new RegExp(`id="${id}"`));
		assert.match(prototypePage, new RegExp(`id="${id}"`));
		assert.match(player, new RegExp(`#${id}`));
	}
	assert.match(player, /trajectoryRoot\.getWorldPosition/);
	assert.match(player, /findExportedNamesByPrefix\(sceneObjects, 'V102'\)/);
	assert.match(player, /readAxelEventFrames\(sceneObjects\)/);
	assert.match(player, /guide\.visible = !followInspection/);
	assert.match(html, /Actual Blender\/GLB root track · illustrative\/simulated/);
});

test('V101 scene, GLB and previews remain as an archived checkpoint', async () => {
	assert.match(v101Builder, /math\.comb\(40, index\) for index in range\(41\)/);
	assert.match(v101Builder, /V101_TRACK_AUDIT/);
	assert.match(readme, /right skate 86→87 heading change falls from 16\.847° \(V100\) to 4\.811°/);
	for (const file of [
		'single-axel-1a-human-rink-v101.blend',
		'single-axel-1a-human-rink-v101-web.glb',
		'single-axel-1a-human-rink-v101-frame039-side.png',
		'single-axel-1a-human-rink-v101-frame093-side.png',
		'single-axel-1a-human-rink-v101-frame050-transition.png',
		'single-axel-1a-human-rink-v101-frame051-transition.png',
		'single-axel-1a-human-rink-v101-frame087-transition.png',
		'single-axel-1a-human-rink-v101-frame039-front-4x3.png',
		'single-axel-1a-human-rink-v101-frame093-front-4x3.png',
		'single-axel-1a-human-rink-v101-frame086-skate-closeup.png',
	]) assert.ok((await stat(new URL(file, root))).size > 10_000, `${file} is missing`);
});

test('showcase includes V168 side previews for approach, flight and exit glide', () => {
	const showcase = prototypePage.match(/<div class="blender-views">([\s\S]*?)<\/div>/)?.[1] ?? '';
	assert.match(showcase, /v168-frame047-side\.png/);
	assert.match(showcase, /v168-frame083-side\.png/);
	assert.match(showcase, /v168-frame136-side\.png/);
	assert.doesNotMatch(showcase, /front-browser/);
	assert.doesNotMatch(publicBuild, /front-browser/);
});

test('public package includes the local Three runtime, camera fit module and V124/V125 evidence', () => {
	assert.match(publicBuild, /vendor\/three\.umd\.js/);
	assert.match(publicBuild, /vendor\/GLTFLoader\.js/);
	assert.match(publicBuild, /camera-fit\.mjs/);
	assert.match(publicBuild, /single-axel-1a-human-rink-v124-frame076-front\.png/);
	assert.match(publicBuild, /single-axel-1a-human-rink-v124-frame060-front\.png/);
	assert.match(publicBuild, /single-axel-1a-human-rink-v124-frame090-front\.png/);
	assert.match(publicBuild, /single-axel-1a-human-rink-v124-frame060-side\.png/);
	assert.match(publicBuild, /single-axel-1a-human-rink-v124-web\.glb/);
	assert.match(publicBuild, /single-axel-1a-human-rink-v125-frame090-side\.png/);
	assert.match(publicBuild, /single-axel-1a-human-rink-v125-web\.glb/);
	assert.match(player, /fitBoundingSphereDistance/);
	assert.match(cameraFit, /halfHorizontal/);
});

test('current player reads inherited event markers and selects the V168 scene', () => {
	assert.match(player, /single-axel-1a-human-rink-v168-web\.glb/);
	assert.match(player, /readAxelEventFrames\(sceneObjects\)/);
	assert.match(player, /phaseAt\(frame, trajectoryEventFrames\)/);
	assert.match(player, /findExportedNamesByPrefix\(sceneObjects, 'V102'\)/);
	assert.match(prototypePage, /Full 3D skater and capsule arena · V168/);
	assert.match(motionOverlay, /Blender v168/);
	assert.match(app, /single-axel-1a-human-rink-v168-frame083-side\.png/);
	assert.match(publicBuild, /single-axel-1a-human-rink-v168-web\.glb/);
	assert.match(v102Builder, /AIRBORNE_CLEARANCE = 0\.020/);
	assert.match(v102Builder, /V102_BUILD_AUDIT/);
	assert.match(v102Audit, /STEP = 1\.0 \/ 16\.0/);
});

test('V102 Blender, GLB and event-frame side/front previews are present', async () => {
	for (const file of [
		'single-axel-1a-human-rink-v102.blend',
		'single-axel-1a-human-rink-v102-web.glb',
		'single-axel-1a-human-rink-v102-takeoff-side.png',
		'single-axel-1a-human-rink-v102-apex-side.png',
		'single-axel-1a-human-rink-v102-landing-side.png',
		'single-axel-1a-human-rink-v102-takeoff-front.png',
		'single-axel-1a-human-rink-v102-apex-front.png',
		'single-axel-1a-human-rink-v102-landing-front.png',
		'single-axel-1a-human-rink-v102-skate-closeup.png',
	]) assert.ok((await stat(new URL(file, root))).size > 10_000, `${file} is missing`);
});

test('the 3D player supports free pointer orbit, wheel zoom and a camera reset', () => {
	assert.match(html, /id="blender-camera-reset"/);
	assert.match(html, /Left-drag: rotate · Shift \+ left-drag or right-drag: pan · scroll: zoom/);
	assert.match(player, /addEventListener\('pointerdown'/);
	assert.match(player, /addEventListener\('pointermove'/);
	assert.match(player, /addEventListener\('wheel'/);
	assert.match(player, /viewerCamera/);
	assert.match(player, /resetView/);
});

test('the V168 player resolves the exported capsule-ice arena target', () => {
	assert.match(player, /V23 capsule ice · 60 m × 30 m \(30 m straights \+ semicircles\)/);
	assert.doesNotMatch(player, /V23 capsule ice polygon/);
	assert.match(html, /blender-player\.js\?v=168/);
});

test('the player defaults to a full-body side profile and keeps rink and follow views', () => {
	assert.match(html, /data-camera="Action skater side profile full-body v124" aria-pressed="true"/);
	assert.match(html, /data-camera="Action skater-facing follow view v121" aria-pressed="false"/);
	assert.match(html, /data-camera="Action side view · horizontal follow composition" aria-pressed="false">Rink side/);
	assert.match(player, /Action skater-facing follow view v121/);
	assert.match(player, /chooseCamera\(CAMERA_NAMES\[5\]\)/);
	assert.match(player, /Action skater side profile full-body v124/);
	assert.match(v124Builder, /Skater pelvis · side-view composition target v124/);
	assert.match(v124Builder, /target\.parent = torso/);
	assert.match(v124Builder, /camera\.parent = target/);
	assert.match(v124Builder, /scene\.camera = camera/);
	for (const file of [
		'single-axel-1a-human-rink-v124.blend',
		'single-axel-1a-human-rink-v124-web.glb',
		'single-axel-1a-human-rink-v124-frame087-skate-closeup.png',
	]) assert.match(publicBuild, new RegExp(file.replaceAll('.', '\\.'), 'u'));
});
