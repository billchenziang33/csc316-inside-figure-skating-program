
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { resolveMotion } from '../src/lib/data/motion-reference.mjs';
import { protocolMarks } from '../src/lib/data/derived.mjs';

const root = new URL('../static/movement/beijing-2022/', import.meta.url);
const read = (name) => readFileSync(new URL(name, root), 'utf8');
const catalog = JSON.parse(read('catalog.json'));
const publicFiles = new Set(JSON.parse(read('public-files.json')));
const competition = JSON.parse(readFileSync(new URL('../static/data/competition.json', import.meta.url), 'utf8'));
const publisher = 'https://billchenziang33.github.io';

test('50 base movements have versioned media and course-origin player routes', () => {
  const base = Object.values(catalog.assets).filter((asset) => !asset.baseAction);
  assert.equal(base.length, 50);
  assert.equal(catalog.plannedBaseActions, base.length);
  for (const asset of base) {
    assert.equal(asset.player, `/movement/beijing-2022/player.html?id=${encodeURIComponent(asset.id)}`);
    const glb = new URL(asset.model);
    assert.equal(glb.origin, publisher);
    assert.equal(decodeURIComponent(glb.pathname), `/figure-skate-database-3d/${asset.file}`);
    assert.match(asset.sha256, /^[a-f0-9]{64}$/);
    assert.equal(glb.searchParams.get('v'), asset.sha256.slice(0, 12));
    assert.ok(Number.isInteger(asset.frames) && asset.frames > 1);
    assert.equal(new URL(asset.poster).origin, publisher);
  }
  assert.equal(catalog.assets['2A'].file, '2A-C07-iteration-3-web.glb');
  assert.equal(new URL(catalog.assets['4T+3T'].player, 'https://example.test').searchParams.get('id'), '4T+3T');
});

test('all 190 scored occurrences keep their original code and resolve to a reference', () => {
  assert.equal(Object.keys(catalog.occurrences).length, 190);
  assert.equal(competition.elements.length, 190);
  for (const row of competition.elements) {
    const occurrence = catalog.occurrences[row.id];
    assert.equal(occurrence.code, row.element_code_raw, row.id);
    // The prepared scores sometimes put the rotation call in the raw code and x in info_flag.
    assert.deepEqual(
      protocolMarks({ element_code_raw: occurrence.code, info_flag: occurrence.official_info }),
      protocolMarks(row),
      row.id,
    );
    assert.equal(occurrence.official_info.includes('x'), (row.info_flag ?? '').includes('x'), row.id);
    assert.ok(catalog.assets[occurrence.asset], row.id);
    assert.ok(resolveMotion(catalog, row)?.asset?.model, row.id);
  }
});

test('Hanyu free skate starts with 4A< and keeps the unmodified score', () => {
  const row = competition.elements.find(({ id }) => id === 'FS:4:1');
  assert.equal(row.skater, 'Yuzuru Hanyu');
  assert.equal(row.element_code_raw, '4A<');
  assert.equal(row.base_value, 10);
  assert.equal(row.goe, -5);
  assert.equal(row.panel_element_score, 5);
  const motion = resolveMotion(catalog, row);
  assert.equal(motion.flags, '<');
  assert.equal(motion.asset.id, catalog.assets['4A-HANYU'] ? '4A-HANYU' : '4A');
  if (catalog.assets['4A-HANYU']) {
    assert.equal(motion.asset.baseAction, '4A');
    assert.equal(motion.usesBase, false);
    assert.notEqual(motion.asset.sha256, catalog.assets['4A'].sha256);
    const variantOccurrences = Object.entries(catalog.occurrences).filter(([, entry]) => entry.variant);
    assert.deepEqual(variantOccurrences.map(([id]) => id), ['FS:4:1']);
  }
});

test('library and player modules resolve in the curated public build', () => {
  const playerSource = read('blender-player.js');
  const buildSource = readFileSync(new URL('../scripts/build-public-site.mjs', import.meta.url), 'utf8');
  const imports = [...playerSource.matchAll(/from\s+['"]([^'"]+)['"]/g)].map((match) => match[1]);
  for (const specifier of imports) {
    const published = new URL(specifier, 'https://example.test/movement/beijing-2022/blender-player.js');
    const publicPath = published.pathname.slice(1);
    assert.doesNotThrow(() => readFileSync(new URL(`../static/${publicPath}`, import.meta.url)), specifier);
    assert.ok(
      buildSource.includes(`'${publicPath}'`) ||
      (publicPath.startsWith('movement/beijing-2022/') && publicFiles.has(publicPath.split('/').at(-1))),
      `curated build omits ${publicPath}`,
    );
  }
  for (const name of ['catalog.json', 'player.html', 'blender-player.js', 'library.js', 'THIRD_PARTY_NOTICES.md']) {
    assert.ok(publicFiles.has(name), name);
  }
  assert.match(read('index.html'), /href="\/#workspace\/FS:4:1"/);
  assert.ok([...publicFiles].every((name) => !name.endsWith('.glb')));
});
