import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { resolveMotion } from '../src/lib/data/motion-reference.mjs';

const data = JSON.parse(readFileSync(new URL('../static/data/competition.json', import.meta.url)));

test('a 3A opens its own clip, a pending spin never opens a different move', () => {
  const catalog = { occurrences: {'SP:1:2': {asset:'3A'}, 'SP:1:3': {asset:'CCSp'}},
    assets: {'3A': {player:'/movement/beijing-2022/player.html?id=3A'}} };
  assert.equal(resolveMotion(catalog, data.elements.find(row => row.id === 'SP:1:2')).asset.player,
    '/movement/beijing-2022/player.html?id=3A');
  assert.equal(resolveMotion(catalog, data.elements.find(row => row.id === 'SP:1:3')).asset, null);
});

test('obsolete occurrence variants cannot override a standard reference', () => {
  const row = data.elements.find(row => row.id === 'FS:4:1');
  const catalog = { occurrences: {[row.id]: {asset:'4A', variant:'4A-hanyu-fs1', flags:'<'}},
    assets: {'4A':{player:'/base'}, '4A-hanyu-fs1':{player:'/variant'}} };
  assert.equal(resolveMotion(catalog,row).asset.player,'/base');
  assert.equal(resolveMotion(catalog,row).flags,'<');
});
