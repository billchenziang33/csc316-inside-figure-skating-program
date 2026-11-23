
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { resolveMotion } from '../src/lib/data/motion-reference.mjs';
import { protocolMarks } from '../src/lib/data/derived.mjs';
import { cumulativeTurns, formatTurns, smoothTrack, turnsAt } from '../static/movement/beijing-2022/trajectory-hud.mjs';

const root = new URL('../static/movement/beijing-2022/', import.meta.url);
const read = (name) => readFileSync(new URL(name, root), 'utf8');
const catalog = JSON.parse(read('catalog.json'));
const publicFiles = new Set(JSON.parse(read('public-files.json')));
const competition = JSON.parse(readFileSync(new URL('../static/data/competition.json', import.meta.url), 'utf8'));
const publisher = 'https://billchenziang33.github.io';

test('the 50 standard movements have versioned media and course-origin player routes', () => {
  const base = Object.values(catalog.assets);
  assert.equal(base.length, 50);
  assert.equal(catalog.plannedBaseActions, base.length);
  for (const asset of base) {
    assert.equal(asset.file, `${asset.id}-r4-smooth-web.glb`);
    assert.equal(asset.player, `/movement/beijing-2022/player.html?id=${encodeURIComponent(asset.id)}`);
    const glb = new URL(asset.model);
    assert.equal(glb.origin, publisher);
    assert.equal(decodeURIComponent(glb.pathname), `/figure-skate-database-3d/${asset.file}`);
    assert.match(asset.sha256, /^[a-f0-9]{64}$/);
    assert.equal(glb.searchParams.get('v'), asset.sha256.slice(0, 12));
    assert.ok(Number.isInteger(asset.frames) && asset.frames > 1);
    assert.equal(new URL(asset.poster).origin, publisher);
  }
  assert.equal(catalog.assets['2A'].air_turns_available, false);
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
    assert.equal(resolveMotion(catalog, row)?.asset, catalog.assets[occurrence.asset], row.id);
    assert.equal(occurrence.variant, undefined, row.id);
  }
});

test('Hanyu’s official 4A< score opens the standard 4A technique', () => {
  const row = competition.elements.find(({ id }) => id === 'FS:4:1');
  assert.equal(row.skater, 'Yuzuru Hanyu');
  assert.equal(row.element_code_raw, '4A<');
  assert.equal(row.base_value, 10);
  assert.equal(row.goe, -5);
  assert.equal(row.panel_element_score, 5);
  const motion = resolveMotion(catalog, row);
  assert.equal(motion.flags, '<');
  assert.equal(motion.asset, catalog.assets['4A']);
  assert.equal(motion.asset.id, '4A');
  assert.equal(motion.asset.player, '/movement/beijing-2022/player.html?id=4A');
  assert.equal(motion.asset.event_frames.FALL, undefined);
  assert.ok(!Object.hasOwn(catalog.assets, '4A-HANYU'));
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
  assert.match(read('index.html'), /href="\/#workspace\/FS:4:1" target="_top"/);
  assert.ok([...publicFiles].every((name) => !name.endsWith('.glb')));
});

test('the flight readout counts air turns across the ±π wrap without losing a revolution', () => {
  const yaws = Array.from({ length: 41 }, (_, i) => ((i * Math.PI * 2 * 4) / 40 + Math.PI) % (2 * Math.PI) - Math.PI);
  const turns = cumulativeTurns(yaws);
  assert.ok(Math.abs(turns.at(-1) - 4) < 1e-9);
  const segment = { takeoff: 166, apex: 186, landing: 206 };
  assert.equal(turnsAt(160, segment, turns), 0);
  assert.ok(Math.abs(turnsAt(185, segment, turns) - 2) < 1e-9);
  assert.equal(turnsAt(300, segment, turns), turns.at(-1));
  assert.equal(formatTurns(2, 4), '2.0 / 4.0');
});

test('the camera path is smoothed without lag and never across a camera cut', () => {
  // A skater travelling at constant speed while circling a spin axis every 36 frames.
  const circling = Array.from({ length: 200 }, (_, i) => ({
    x: 0.01 * i + 0.3 * Math.cos((i * 2 * Math.PI) / 36),
    y: 1,
    z: 0.3 * Math.sin((i * 2 * Math.PI) / 36),
  }));
  const smooth = smoothTrack(circling, 18);
  assert.equal(smooth.length, circling.length);
  for (let i = 30; i < 170; i++) {
    assert.ok(Math.abs(smooth[i].x - 0.01 * i) < 0.02, `x follows the travel at frame ${i}`);
    assert.ok(Math.abs(smooth[i].z) < 0.02, `the circle is averaged out at frame ${i}`);
  }
  // Height uses its own, shorter window.
  const hop = Array.from({ length: 60 }, (_, i) => ({ x: 0, y: i === 30 ? 1 : 0, z: 0 }));
  assert.ok(Math.abs(smoothTrack(hop, 18, 2)[30].y - 0.2) < 1e-12);
  // A 5 m jump between two frames is a cut: both sides keep their own position.
  const cut = [...Array.from({ length: 20 }, () => ({ x: 0, y: 0, z: 0 })), ...Array.from({ length: 20 }, () => ({ x: 5, y: 0, z: 0 }))];
  const kept = smoothTrack(cut, 18);
  assert.equal(kept[19].x, 0);
  assert.equal(kept[20].x, 5);
});
