<script>
	import { max, scaleLinear } from 'd3';
	let { elements = [] } = $props();

	// Jump types in protocol notation, ordered from the Axel down to the Toe loop; the Euler appears only inside combinations.
	const TYPES = [
		{ code: 'A', label: 'Axel' },
		{ code: 'Lz', label: 'Lutz' },
		{ code: 'F', label: 'Flip' },
		{ code: 'Lo', label: 'Loop' },
		{ code: 'S', label: 'Salchow' },
		{ code: 'T', label: 'Toe loop' },
		{ code: 'Eu', label: 'Euler' }
	];
	const SEGMENTS = ['SP', 'FS'];
	const JUMP_PART = /^\d(Lz|Lo|Eu|A|F|S|T)/;

	// Split each jump element into its individual jumps ("4F+3T" -> F, T) and count them per segment and type.
	let counts = $derived.by(() => {
		const tally = new Map();
		for (const d of elements) {
			if (d.element_group !== 'jump') continue;
			for (const part of String(d.element_code_raw).split('+')) {
				const type = part.match(JUMP_PART)?.[1];
				if (!type) continue;
				const key = `${d.segment}:${type}`;
				tally.set(key, (tally.get(key) ?? 0) + 1);
			}
		}
		return TYPES.map((t) => ({ ...t, SP: tally.get(`SP:${t.code}`) ?? 0, FS: tally.get(`FS:${t.code}`) ?? 0 }));
	});
	let x = $derived(scaleLinear().domain([0, max(counts, (d) => Math.max(d.SP, d.FS)) || 1]).nice().range([0, 92]));
	let ticks = $derived(x.ticks(5));
	let summary = $derived(counts.map((d) => `${d.label}: ${d.SP} in short program, ${d.FS} in free skate`).join('; '));
</script>

<div class="viz" role="img" aria-label={`Number of jumps by jump type across the final top ten, short program versus free skate. Each jump inside a combination counts separately. ${summary}.`}>
	<div class="legend"><span><i class="sp"></i>Short program</span><span><i class="fs"></i>Free skate</span></div>
	<div class="axis"><span>Jump type</span><div>{#each ticks as t}<small style={`left:${x(t)}%`}>{t}</small>{/each}<b>Jumps performed (all ten skaters)</b></div></div>
	{#each counts as d (d.code)}
		<div class="row"><span class="type">{d.label} <em>{d.code}</em></span><div class="plot">
			{#each ticks as t}<i class="grid" style={`left:${x(t)}%`}></i>{/each}
			{#each SEGMENTS as segment (segment)}
				<div class:sp-bar={segment === 'SP'} class:fs-bar={segment === 'FS'} class="bar" style={`width:${x(d[segment])}%`}><span>{d[segment]}</span></div>
			{/each}
		</div></div>
	{/each}
	<p class="foot">Each jump inside a combination counts separately: 4F+3T adds one Flip and one Toe loop. Under-rotated, edge-called and invalid (*) jumps still count as performed. The Euler (Eu) appears only as a link inside three-jump combinations.</p>
</div>

<style>
	.viz{display:grid;gap:.3rem}.legend{display:flex;gap:1rem;justify-content:flex-end;font-size:.72rem;color:#58645f}.legend span{display:flex;align-items:center;gap:.35rem}.legend i{width:.65rem;height:.65rem;border-radius:2px}.sp{background:#d46b47}.fs{background:#397a74}.axis,.row{display:grid;grid-template-columns:92px minmax(0,1fr);gap:.7rem;align-items:center}.axis>span{font-size:.68rem;color:#77827d}.axis>div{position:relative;height:1.55rem;border-bottom:1px solid #cfd6d0}.axis small{position:absolute;bottom:.2rem;transform:translateX(-50%);font-size:.65rem;color:#77827d}.axis b{position:absolute;right:0;top:-.2rem;font-size:.62rem;color:#77827d;background:#fffefa;padding-left:.25rem}.row{height:31px}.type{font-size:.72rem;color:#41504a;text-align:right;white-space:nowrap}.type em{font: normal .62rem var(--mono);color:#77827d}.plot{position:relative;display:grid;gap:3px}.grid{position:absolute;top:0;bottom:0;width:1px;background:#e6e9e4;pointer-events:none}.bar{height:11px;min-width:2px;border-radius:2px;position:relative}.sp-bar{background:#d46b47}.fs-bar{background:#397a74}.bar span{position:absolute;left:calc(100% + 5px);top:50%;transform:translateY(-50%);font: .65rem var(--mono);color:#41504a}.foot{margin:.55rem 0 0;color:#707c75;font-size:.69rem;line-height:1.5}
</style>
