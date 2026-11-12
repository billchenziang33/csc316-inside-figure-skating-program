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

test('V176 skate alignment is wired through the standalone and workspace players', () => {
	assert.match(player, /Blender v176/);
	assert.match(player, /blender-player\.js\?v=176/);
	assert.match(player, /data-mobile-extra/);
	assert.match(player, /\.camera-picks\s+\[data-mobile-extra\]\s*\{\s*display:\s*none/);
	assert.match(runtime, /single-axel-1a-human-rink-v176-web\.glb/);
	assert.match(showcase, /Full 3D skater and capsule arena · V176/);
	assert.match(app, /single-axel-1a-human-rink-v176-frame087-side\.png/);
	assert.match(app, /Play Blender v176 in 3D/);
	assert.match(overlay, /Blender v176 3D reference/);
	for (const asset of [
		'single-axel-1a-human-rink-v155.blend',
		'single-axel-1a-human-rink-v155-web.glb',
		'single-axel-1a-human-rink-v155-frame081-side.png',
		'single-axel-1a-human-rink-v155-frame081-front.png',
		'single-axel-1a-human-rink-v155-frame092-skate-closeup.png',
		'single-axel-1a-human-rink-v176.blend',
		'single-axel-1a-human-rink-v176-web.glb',
		'single-axel-1a-human-rink-v176-frame087-side.png',
		'single-axel-1a-human-rink-v176-frame092-front.png',
		'fullscreen-control.js'
	]) assert.ok(build.includes(asset), `public build omits ${asset}`);
});
