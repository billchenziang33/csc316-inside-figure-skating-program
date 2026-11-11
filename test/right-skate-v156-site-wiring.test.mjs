import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { test } from 'node:test';

const read = (path) => readFileSync(new URL(path, import.meta.url), 'utf8');

test('V167 corrected skates are the site playback and download asset', () => {
	const player = read('../static/movement/axel-1a-prototype/player.html');
	const runtime = read('../static/movement/axel-1a-prototype/blender-player.js');
	const showcase = read('../static/movement/axel-1a-prototype/index.html');
	const overlay = read('../src/lib/MotionOverlay.svelte');

	assert.match(player, /Blender v167/);
	assert.match(runtime, /single-axel-1a-human-rink-v167-web\.glb/);
	assert.match(showcase, /V167/);
	assert.match(overlay, /Blender v167 3D reference/);
	assert.ok(existsSync(new URL('../static/movement/axel-1a-prototype/single-axel-1a-human-rink-v167.blend', import.meta.url)));
	assert.ok(existsSync(new URL('../static/movement/axel-1a-prototype/single-axel-1a-human-rink-v167-web.glb', import.meta.url)));
});
