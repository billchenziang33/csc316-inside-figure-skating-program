// Numbers quoted by the opening scroll story. Every sentence that cites a count reads it from here,
// so the text cannot drift away from the official protocol data.

/** Element occurrences the story follows by name. */
export const CHARACTERS = {
	unoShort: 'SP:3:1', // Shoma Uno, short program, 4F
	unoFree: 'FS:3:3', // Shoma Uno, free skate, 4F (fall)
	brownFree: 'FS:6:1', // Jason Brown, free skate, 3F
	hanyuFree: 'FS:4:1' // Yuzuru Hanyu, free skate, 4A<
};

export const ELEMENT_GROUPS = [
	{ key: 'jump', label: 'Jumps', short: 'Jumps' },
	{ key: 'spin', label: 'Spins', short: 'Spins' },
	{ key: 'step_sequence', label: 'Step sequences', short: 'Steps' },
	{ key: 'choreographic_sequence', label: 'Choreo sequences', short: 'Choreo' }
];

/** A jump element that opens with a quadruple jump, e.g. 4F or 4T+3T. */
export const opensWithQuad = (element) => element.element_group === 'jump' && /^4/.test(element.element_code_raw);

export function storyFacts(elements = [], segments = []) {
	const jumps = elements.filter((element) => element.element_group === 'jump');
	const quads = jumps.filter(opensWithQuad);
	const others = jumps.filter((element) => !opensWithQuad(element));

	// Every pair of jumps with different base values: how often did the easier one score more?
	let pairs = 0;
	let upsets = 0;
	for (let i = 0; i < jumps.length; i++) {
		for (let j = i + 1; j < jumps.length; j++) {
			const [a, b] = [jumps[i], jumps[j]];
			if (a.base_value === b.base_value) continue;
			pairs += 1;
			const [harder, easier] = a.base_value > b.base_value ? [a, b] : [b, a];
			if (easier.panel_element_score > harder.panel_element_score) upsets += 1;
		}
	}

	const tes = segments.reduce((sum, segment) => sum + segment.TES, 0);
	const total = segments.reduce((sum, segment) => sum + segment.segment_score_TSS, 0);

	return {
		elements: elements.length,
		programs: segments.length,
		skaters: new Set(elements.map((element) => element.skater)).size,
		groups: Object.fromEntries(ELEMENT_GROUPS.map(({ key }) => [key, elements.filter((element) => element.element_group === key).length])),
		gained: elements.filter((element) => element.goe > 0).length,
		lost: elements.filter((element) => element.goe < 0).length,
		level: elements.filter((element) => element.goe === 0).length,
		quads: quads.length,
		quadsLost: quads.filter((element) => element.goe < 0).length,
		otherJumps: others.length,
		otherJumpsLost: others.filter((element) => element.goe < 0).length,
		pairs,
		upsets,
		tesShare: total ? tes / total : 0
	};
}
