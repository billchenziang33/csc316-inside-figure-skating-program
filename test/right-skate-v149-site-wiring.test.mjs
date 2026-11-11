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

test('V155 ankle-alignment action is wired through the standalone and workspace players', () => {
	assert.match(player, /Blender v155/);
	assert.match(player, /blender-player\.js\?v=155/);
	assert.match(runtime, /single-axel-1a-human-rink-v155-web\.glb/);
	assert.match(showcase, /Full 3D skater and capsule arena · V155/);
	assert.match(app, /single-axel-1a-human-rink-v155-frame081-side\.png/);
	assert.match(app, /Play Blender v155 in 3D/);
	assert.match(overlay, /Blender v155 3D reference/);
	for (const asset of [
		'single-axel-1a-human-rink-v155.blend',
		'single-axel-1a-human-rink-v155-web.glb',
		'single-axel-1a-human-rink-v155-frame081-side.png',
		'single-axel-1a-human-rink-v155-frame081-front.png',
		'single-axel-1a-human-rink-v155-frame092-skate-closeup.png',
		'fullscreen-control.js'
	]) assert.ok(build.includes(asset), `public build omits ${asset}`);
});
