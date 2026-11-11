import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const read = (path) => readFile(new URL(path, import.meta.url), 'utf8');
const [player, runtime, showcase, app, overlay, build] = await Promise.all([
	read('../static/movement/axel-1a-prototype/player.html'),
	read('../static/movement/axel-1a-prototype/blender-player.js'),
	read('../static/movement/axel-1a-prototype/index.html'),
	read('../src/App.svelte'),
	read('../src/lib/MotionOverlay.svelte'),
	read('../scripts/build-public-site.mjs')
]);

test('V151 free-skate landing alignment is wired through the standalone and workspace players', () => {
	assert.match(player, /Blender v151/);
	assert.match(player, /blender-player\.js\?v=152/);
	assert.match(runtime, /single-axel-1a-human-rink-v151-web\.glb/);
	assert.match(showcase, /Full 3D skater and capsule arena · V151/);
	assert.match(app, /single-axel-1a-human-rink-v151-frame060-side\.png/);
	assert.match(app, /Play Blender v151 in 3D/);
	assert.match(overlay, /Blender v151 3D reference/);
	for (const asset of [
		'single-axel-1a-human-rink-v151.blend',
		'single-axel-1a-human-rink-v151-web.glb',
		'single-axel-1a-human-rink-v151-frame087-side.png',
		'single-axel-1a-human-rink-v151-frame090-skate-closeup.png',
		'fullscreen-control.js'
	]) assert.ok(build.includes(asset), `public build omits ${asset}`);
});
