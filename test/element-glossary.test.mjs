import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { describeElement, JUMP_TYPES } from '../src/lib/data/element-glossary.mjs';

const { elements } = JSON.parse(await readFile(new URL('../static/data/competition.json', import.meta.url), 'utf8'));

test('every protocol code in the data gets a plain-English name', () => {
  for (const { element_code_raw: code, info_flag } of elements) {
    const { name } = describeElement(code, info_flag);
    assert.notEqual(name, code, `${code} was not decoded`);
    assert.doesNotMatch(name, /undefined/, code);
  }
});

test('jump, spin and mark readings', () => {
  assert.equal(describeElement('4Lz+3T').name, 'Quad Lutz + Triple Toe loop');
  assert.ok(describeElement('3A').notes.includes('3.5 rotations in the air'));
  assert.equal(describeElement('FCSp4').name, 'Flying camel spin');
  assert.equal(describeElement('FCSSp4').name, 'Flying change-foot sit spin');
  assert.equal(describeElement('CCoSp4V').name, 'Change-foot combination spin');
  assert.ok(describeElement('CCoSp4V').notes.some((n) => n.includes('75%')));
  assert.ok(describeElement('4A<', '<').notes.some((n) => n.startsWith('Under-rotated (<)')));
  assert.ok(describeElement('3A', 'x').notes.some((n) => n.startsWith('Second-half bonus')));
});

test('quad base values match clean solo quads in the official protocols', () => {
  for (const jump of JUMP_TYPES.filter((j) => j.quadBase)) {
    const clean = elements.find((e) => e.element_code_raw === `4${jump.code}` && !e.info_flag);
    if (clean) assert.equal(clean.base_value, jump.quadBase, jump.name);
  }
  // The only 4A was under-rotated, which pays 80% of the full value.
  assert.equal(elements.find((e) => e.element_code_raw === '4A<').base_value, 12.5 * 0.8);
});
