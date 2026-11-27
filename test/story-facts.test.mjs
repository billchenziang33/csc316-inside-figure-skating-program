import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { CHARACTERS, storyFacts } from '../src/lib/data/story-facts.mjs';

const data = JSON.parse(readFileSync(new URL('../static/data/competition.json', import.meta.url), 'utf8'));
const byId = new Map(data.elements.map((element) => [element.id, element]));

test('the opening story follows the official rows it names', () => {
	const pick = (id) => {
		const { skater, element_code_raw, base_value, goe, panel_element_score } = byId.get(id);
		return { skater, code: element_code_raw, base_value, goe, panel_element_score };
	};
	assert.deepEqual(pick(CHARACTERS.unoShort), { skater: 'Shoma Uno', code: '4F', base_value: 11, goe: 3.77, panel_element_score: 14.77 });
	assert.deepEqual(pick(CHARACTERS.unoFree), { skater: 'Shoma Uno', code: '4F', base_value: 11, goe: -5.34, panel_element_score: 5.66 });
	assert.deepEqual(pick(CHARACTERS.brownFree), { skater: 'Jason Brown', code: '3F', base_value: 5.3, goe: 2.35, panel_element_score: 7.65 });
	assert.deepEqual(pick(CHARACTERS.hanyuFree), { skater: 'Yuzuru Hanyu', code: '4A<', base_value: 10, goe: -5, panel_element_score: 5 });
	// "Jason Brown did not try a single quad."
	assert.ok(data.elements.filter((element) => element.skater === 'Jason Brown').every((element) => !/(^|\+)4/.test(element.element_code_raw)));
});

test('the counts quoted in the story come from the 190 protocol rows', () => {
	const facts = storyFacts(data.elements, data.segments);
	assert.equal(facts.elements, 190);
	assert.equal(facts.programs, 20);
	assert.equal(facts.skaters, 10);
	assert.deepEqual(facts.groups, { jump: 100, spin: 60, step_sequence: 20, choreographic_sequence: 10 });
	assert.deepEqual([facts.gained, facts.lost, facts.level], [174, 15, 1]);
	assert.deepEqual([facts.quads, facts.quadsLost, facts.otherJumps, facts.otherJumpsLost], [47, 11, 53, 4]);
	assert.deepEqual([facts.pairs, facts.upsets], [4750, 778]);
	assert.equal(Math.round(facts.tesShare * 100), 53);
});
