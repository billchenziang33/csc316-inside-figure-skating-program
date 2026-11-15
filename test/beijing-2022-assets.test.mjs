import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { resolveMotion } from '../src/lib/data/motion-reference.mjs';

const root = new URL('../static/movement/beijing-2022/', import.meta.url);
const catalog = JSON.parse(readFileSync(new URL('catalog.json', root), 'utf8'));
const publicFiles = new Set(JSON.parse(readFileSync(new URL('public-files.json', root), 'utf8')));
const competition = JSON.parse(readFileSync(new URL('../static/data/competition.json', import.meta.url), 'utf8'));
const homepage = readFileSync(new URL('index.html', root), 'utf8');
const expected = ['1S', '2A', '2S', '2T', '3A', '3S', '3T', '4S', '4T'];

test('the 190 ordered program occurrences include every currently modeled action', () => {
  assert.equal(Object.keys(catalog.occurrences).length, 190);
  for (const code of expected) {
    const asset = catalog.assets[code];
    assert.ok(asset, `missing ${code} asset mapping`);
    assert.match(asset.player, new RegExp(`/movement/beijing-2022/player\\.html\\?id=${code}$`));
    assert.ok(publicFiles.has(asset.file), `public build omits ${asset.file}`);
    const poster = asset.poster.split('/').at(-1);
    assert.ok(publicFiles.has(poster), `public build omits ${poster}`);

    const modelPath = new URL(asset.file, root);
    const sha256 = createHash('sha256').update(readFileSync(modelPath)).digest('hex');
    assert.equal(sha256, asset.sha256, `${code} model digest does not match its catalog`);
  }
});

test('every completed jump occurrence resolves to its modeled element code', () => {
  const rows = competition.elements.filter(row => expected.includes(catalog.occurrences[row.id]?.asset));
  const expectedInPrograms = expected.filter(code =>
    Object.values(catalog.occurrences).some(occurrence => occurrence.asset === code));
  const resolvedCodes = new Set();
  for (const row of rows) {
    const motion = resolveMotion(catalog, row);
    assert.ok(motion?.asset, `program element ${row.id} has no playable model`);
    const code = catalog.occurrences[row.id].asset;
    assert.equal(motion.asset.player, `/movement/beijing-2022/player.html?id=${code}`);
    resolvedCodes.add(code);
  }
  for (const code of expectedInPrograms) {
    assert.ok(resolvedCodes.has(code), `${code} has no mapped program occurrence`);
  }
});

test('the public library marks visual reviews that are still pending', () => {
  assert.match(homepage, /Blender 几何与技术检查通过 · 公开侧视待复核/);
});

test('every Beijing player module import resolves to a file in the curated public build', () => {
  const playerSource = readFileSync(new URL('blender-player.js', root), 'utf8');
  const buildSource = readFileSync(new URL('../scripts/build-public-site.mjs', import.meta.url), 'utf8');
  const imports = [...playerSource.matchAll(/from\s+['"]([^'"]+)['"]/g)].map((match) => match[1]);

  for (const specifier of imports) {
    const publicPath = new URL(specifier, 'https://example.test/movement/beijing-2022/blender-player.js').pathname.slice(1);
    assert.doesNotThrow(() => readFileSync(new URL(`../static/${publicPath}`, import.meta.url)), `${specifier} is missing from static sources`);
    assert.ok(buildSource.includes(`'${publicPath}'`), `curated build omits ${publicPath}`);
  }
});
