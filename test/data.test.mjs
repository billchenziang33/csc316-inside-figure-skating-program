import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { parseBrief } from '../src/lib/data/parse-brief.mjs';
import { countJumpElements, elementLevel, jumpRotations, protocolMarks, summarizeJumpShare } from '../src/lib/data/derived.mjs';

const markdown = await readFile(new URL('../data/source/Beijing_2022_Mens_Singles_Top10_Data_Brief.md', import.meta.url), 'utf8');
const data = parseBrief(markdown);

test('parses the complete top-ten tables and preserves numeric values', () => {
	assert.equal(data.elements.length, 190);
	assert.equal(data.segments.length, 20);
	assert.equal(data.components.length, 100);
	assert.equal(new Set(data.elements.map((d) => d.skater)).size, 10);
	assert.equal(data.elements[0].element_order, 1);
	assert.equal(data.elements[0].panel_element_score, 19.6);
	assert.equal(data.elements[0].info_flag, null);
});

test('each segment element sum agrees with TES and total score arithmetic', () => {
	for (const segment of data.segments) {
		const rows = data.elements.filter((d) => d.skater === segment.skater && d.segment === segment.segment);
		const elementSum = rows.reduce((sum, row) => sum + row.panel_element_score, 0);
		assert.equal(rows.length, segment.element_count);
	assert.ok(Math.abs(elementSum - segment.TES) <= 0.01);
	assert.ok(Math.abs(segment.TES + segment.PCS_factored + segment.deductions - segment.segment_score_TSS) <= 0.01);
	}
});

test('Q7 jump shares use jump panel points over all element panel points', () => {
	const result = summarizeJumpShare(data.elements);
	assert.equal(result.length, 2);
	assert.ok(Math.abs(result.find((d) => d.segment === 'SP').share * 100 - 67.3885358) < 0.0001);
	assert.ok(Math.abs(result.find((d) => d.segment === 'FS').share * 100 - 77.0515) < 0.0001);
});

test('selected-view helpers preserve combinations, rotation totals, and protocol marks', () => {
	const combo = data.elements.find((d) => d.element_code_raw === '4F+3T');
	assert.equal(jumpRotations(combo), 7);
	assert.ok(protocolMarks(data.elements.find((d) => d.element_code_raw.includes('<'))).includes('<'));
	assert.deepEqual(protocolMarks({ element_code_raw: '4A<<', info_flag: null }), ['<<']);
	assert.equal(countJumpElements(data.elements).length, 20);
});

test('protocol marks come from jump calls only, never from the q in StSq or ChSq', () => {
	assert.deepEqual(protocolMarks({ element_code_raw: 'StSq4', info_flag: null }), []);
	assert.deepEqual(protocolMarks({ element_code_raw: 'ChSq1', info_flag: null }), []);
	assert.deepEqual(protocolMarks({ element_code_raw: '4Loq', info_flag: 'q' }), ['q']);
	assert.deepEqual(protocolMarks({ element_code_raw: '4Lz!q', info_flag: '!' }), ['q', '!']);
	assert.deepEqual(protocolMarks({ element_code_raw: '3F+3T<', info_flag: 'x' }), ['<']);
	assert.deepEqual(protocolMarks({ element_code_raw: '3Lze', info_flag: null }), ['e']);
	const marked = data.elements.filter((d) => protocolMarks(d).length);
	assert.equal(marked.length, 11, 'the official protocol has 11 elements with calls: q 5, < 3, ! 3, * 1');
	assert.ok(marked.every((d) => d.element_group === 'jump'));
	const counts = {};
	for (const mark of marked.flatMap(protocolMarks)) counts[mark] = (counts[mark] ?? 0) + 1;
	assert.deepEqual(counts, { q: 5, '<': 3, '!': 3, '*': 1 });
});

test('spin and step levels are read for every row, including reduced-value V spins', () => {
	assert.equal(elementLevel({ element_code_raw: 'CCoSp4V' }), 4);
	assert.equal(elementLevel({ element_code_raw: 'CCoSp2V' }), 2);
	assert.equal(elementLevel({ element_code_raw: 'StSq3' }), 3);
	assert.equal(elementLevel({ element_code_raw: 'ChSq1' }), 1);
	const levelled = data.elements.filter((d) => d.element_group === 'spin' || d.element_group === 'step_sequence');
	assert.equal(levelled.length, 80);
	assert.ok(levelled.every((d) => elementLevel(d) >= 1 && elementLevel(d) <= 4));
});
