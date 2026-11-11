import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const player = await readFile(new URL('../static/movement/axel-1a-prototype/blender-player.js', import.meta.url), 'utf8');

test('orbit centers on the animated skater and fits its full bounds', () => {
  assert.match(player, /orbitFitBounds\.setFromObject\(trajectoryRoot\)/);
  assert.match(player, /fitOrbitCameraDistance\(/);
  assert.doesNotMatch(player, /orbitTarget\.y \+= 0\.82/);
});
