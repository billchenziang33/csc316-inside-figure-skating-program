import test from 'node:test';
import assert from 'node:assert/strict';
import { readRoute, routeHash, stages, chartIds, libraryHref } from '../src/lib/navigation.mjs';
test('unknown and malformed links fall back to the finding', () => {
  for (const hash of ['', '#not-a-stage', '#%zz']) assert.equal(readRoute(hash).stage, 'story');
  assert.equal(readRoute('#charts/unknown').chart, 'S12');
});
test('all stages and expanded charts survive direct-link round trips', () => {
  for (const stage of stages) assert.equal(readRoute(routeHash(stage.id)).stage, stage.id);
  for (const chart of chartIds) assert.deepEqual(readRoute(routeHash('chart-detail', chart)), { stage: 'chart-detail', chart });
});

test('the workbench and library retain the exact scored occurrence', () => {
  assert.equal(routeHash('workspace', 'S12', 'FS:4:1'), '#workspace/FS:4:1');
  assert.deepEqual(readRoute('#workspace/FS:4:1'), { stage: 'workspace', chart: 'S12', elementId: 'FS:4:1' });
  assert.equal(readRoute('#workspace/invalid').elementId, undefined);
  assert.equal(libraryHref('FS:4:1'), '/movement/beijing-2022/?from=FS%3A4%3A1');
  assert.equal(libraryHref(null), '/movement/beijing-2022/');
});
