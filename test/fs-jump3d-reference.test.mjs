import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const read = path => readFile(new URL(path, import.meta.url), 'utf8');
const root = '../static/movement/fs-jump3d/';

test('step six hosts the FS-Jump3D library and the workbench links to that step', async () => {
	const app = await read('../src/App.svelte');
	const stage = app.split("{:else if activeStage === 'movement'}")[1]?.split('    {/if}')[0] ?? '';
	assert.match(stage, /<FsJumpReference\s*\/>/);
	assert.doesNotMatch(stage, /v178-frame|motion-poster/);
	assert.match(app, /onclick=\{\(\) => go\('movement'\)\}>Explore FS-Jump3D Blender library/);

	const library = await read('../src/lib/FsJumpReference.svelte');
	assert.match(library, /fetch\(\x60\$\{base\}records-manifest\.json\x60/);
	assert.match(library, /<iframe\s+src=\{player\}/);
});

test('the published manifest supplies the player and every round offered in the library', async () => {
	const records = JSON.parse(await read(root + 'records-manifest.json'));
	const files = new Set(JSON.parse(await read(root + 'public-files.json')));
	const ready = records.filter(record => record.geometry_status === 'geometry_pass' && record.rounds.includes('r3') && record.available !== false);
	assert.ok(ready.length > 0);
	assert.ok(files.has('player.html'));
	assert.ok(files.has('records-manifest.json'));
	for (const record of ready) {
		for (const round of record.rounds) assert.ok(files.has(record.assets[round].path), `${record.id} ${round}`);
	}
});

test('the old library entry leads to step six and the public reference is in English', async () => {
	const entry = await read(root + 'index.html');
	assert.match(entry, /http-equiv="refresh" content="0; url=\/#movement"/);
	for (const file of [root + 'index.html', root + 'player.html', root + 'README.md', '../src/lib/FsJumpReference.svelte', '../static/movement/beijing-2022/catalog.json']) {
		assert.doesNotMatch(await read(file), /\p{Script=Han}|lang="zh/iu, file);
	}
});
