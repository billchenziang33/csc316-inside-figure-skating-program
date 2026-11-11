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

test('V149 is the same right-leg correction in standalone, workspace and public package', () => {
	assert.match(player, /Blender v149/);
	assert.match(player, /blender-player\.js\?v=149/);
	assert.match(runtime, /single-axel-1a-human-rink-v149-web\.glb/);
	assert.match(showcase, /Full 3D skater and capsule arena · V149/);
	assert.match(app, /single-axel-1a-human-rink-v149-frame060-side\.png/);
	assert.match(app, /Play Blender v149 in 3D/);
	assert.match(overlay, /Blender v149 3D reference/);
	for (const asset of [
		'single-axel-1a-human-rink-v149.blend',
		'single-axel-1a-human-rink-v149-web.glb',
		'single-axel-1a-human-rink-v149-frame037-side.png',
		'single-axel-1a-human-rink-v149-frame090-skate-closeup.png'
	]) assert.ok(build.includes(asset), `public build omits ${asset}`);
});
