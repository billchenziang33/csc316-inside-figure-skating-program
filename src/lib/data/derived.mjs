export function elementId(element) {
	return `${element.segment}:${element.final_rank}:${element.element_order}`;
}

export function countJumpElements(elements) {
	const groups = new Map();
	for (const element of elements.filter((item) => item.element_group === 'jump')) {
		const key = `${element.segment}:${element.final_rank}:${element.skater}`;
		const group = groups.get(key) ?? { segment: element.segment, final_rank: element.final_rank, skater: element.skater, count: 0 };
		group.count += 1;
		groups.set(key, group);
	}
	return [...groups.values()];
}

export function jumpRotations(element) {
	return [...element.element_code_raw.matchAll(/([1-4])(?=[A-Z])/g)].reduce((sum, match) => sum + Number(match[1]), 0);
}

const JUMP_TOKEN = /^[1-4](?:A|F|Lz|Lo|S|T|Eu)/;

export function protocolMarks(element) {
	const code = element.element_code_raw;
	const info = element.info_flag ?? '';
	// The letters q and e are also part of element names (StSq, ChSq), so read them only from
	// the part of each jump token that follows the jump code, e.g. the "q" in "4Loq" or "4Lz!q".
	const jumpSuffixes = code.split('+').filter((token) => JUMP_TOKEN.test(token)).map((token) => token.replace(JUMP_TOKEN, ''));
	return ['<<', '<', 'e', 'q', '!', '*'].filter((mark) => {
		if (mark === '<<') return info.includes('<<') || code.includes('<<');
		if (mark === '<') return info === '<' || (code.includes('<') && !code.includes('<<'));
		if (info.includes(mark)) return true;
		if (mark === 'e' || mark === 'q') return jumpSuffixes.some((suffix) => suffix.includes(mark));
		return code.includes(mark);
	});
}

export function elementLevel(element) {
	// Spin and step-sequence codes end in the level digit; a trailing V marks a spin whose base
	// value was reduced (CCoSp4V) but does not change its level.
	return Number(element.element_code_raw.match(/([1-4])V?$/)?.[1] ?? 0);
}

export function summarizeJumpShare(elements) {
	return ['SP', 'FS'].map((segment) => {
		const rows = elements.filter((element) => element.segment === segment);
		const totalElementPoints = rows.reduce((sum, element) => sum + element.panel_element_score, 0);
		const jumpPoints = rows
			.filter((element) => element.element_group === 'jump')
			.reduce((sum, element) => sum + element.panel_element_score, 0);
		return { segment, jumpPoints, totalElementPoints, share: jumpPoints / totalElementPoints };
	});
}

export function segmentScoreAudit({ segments, elements }) {
	return segments.map((segment) => {
		const rows = elements.filter((element) => element.skater === segment.skater && element.segment === segment.segment);
		const elementSum = rows.reduce((sum, element) => sum + element.panel_element_score, 0);
		return {
			...segment,
			calculated_element_sum: Number(elementSum.toFixed(2)),
			calculated_tss: Number((segment.TES + segment.PCS_factored + segment.deductions).toFixed(2)),
			element_count_matches: rows.length === segment.element_count,
			tes_matches: Math.abs(elementSum - segment.TES) <= 0.01,
			tss_matches: Math.abs(segment.TES + segment.PCS_factored + segment.deductions - segment.segment_score_TSS) <= 0.01
		};
	});
}
