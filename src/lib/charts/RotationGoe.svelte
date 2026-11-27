<script>
	import { scaleLinear } from 'd3';
	import { jumpRotations } from '../data/derived.mjs';
	let { elements = [] } = $props();
	let points = $derived(elements.filter((d) => d.element_group === 'jump').map((d) => ({...d, rotations: jumpRotations(d), combo: d.element_code_raw.includes('+')})));
	const x = scaleLinear().domain([0, 11]).range([58, 730]);
	const y = scaleLinear().domain([-6, 6]).range([245, 32]);
	const xTicks = [0, 2, 4, 6, 8, 10];
	const yTicks = [-6, -3, 0, 3, 6];
</script>

<div class="viz" role="img" aria-label="Scatterplot of jump rotation total and official element GOE for top-ten short-program and free-skate jump elements. Combinations retain one element-level GOE score.">
	<div class="legend"><span><i class="sp"></i>Short program</span><span><i class="fs"></i>Free skate</span><span>□ In a combination</span><span>○ On its own</span></div>
	<svg viewBox="0 0 770 300" role="presentation">
		{#each yTicks as t}<line x1="58" x2="730" y1={y(t)} y2={y(t)} style:stroke={t===0?'var(--faint)':'var(--line)'} stroke-dasharray={t===0?'':'3 4'}/><text x="48" y={y(t)+4} text-anchor="end">{t}</text>{/each}
		{#each xTicks as t}<line x1={x(t)} x2={x(t)} y1="32" y2="245" style="stroke:var(--line)"/><text x={x(t)} y="263" text-anchor="middle">{t}</text>{/each}
		<line x1="58" x2="730" y1="245" y2="245" style="stroke:var(--faint)"/><line x1="58" x2="58" y1="32" y2="245" style="stroke:var(--faint)"/>
		{#each points as point (point.id)}
			{#if point.combo}<rect x={x(point.rotations)-4} y={y(point.goe)-4} width="8" height="8" class:fs-mark={point.segment==='FS'} class:sp-mark={point.segment==='SP'}><title>{point.skater} · {point.segment} · {point.element_code_raw} · {point.rotations} jump rotations · element GOE {point.goe > 0 ? '+' : ''}{point.goe.toFixed(2)}</title></rect>
			{:else}<circle cx={x(point.rotations)} cy={y(point.goe)} r="4" class:fs-mark={point.segment==='FS'} class:sp-mark={point.segment==='SP'}><title>{point.skater} · {point.segment} · {point.element_code_raw} · {point.rotations} jump rotations · element GOE {point.goe > 0 ? '+' : ''}{point.goe.toFixed(2)}</title></circle>{/if}
		{/each}
		<text x="394" y="293" text-anchor="middle">Total rotations encoded in protocol element</text><text transform="translate(15 140) rotate(-90)" text-anchor="middle">Official element GOE (points)</text>
	</svg>
	<p class="foot">Combination rows show total listed rotations on x and the single official element GOE on y; GOE is not divided among component jumps. n = {points.length} scored jump elements.</p>
</div>

<style>
	.viz{display:grid;gap:.2rem}.legend{display:flex;gap:1rem;justify-content:flex-end;align-items:center;flex-wrap:wrap;font-size:.7rem;color:var(--muted)}.legend i{display:inline-block;width:.65rem;height:.65rem;border-radius:50%;margin-right:.25rem}.sp{background:var(--sp)}.fs{background:var(--fs)}svg{width:100%;height:auto;overflow:visible}svg text{font:10px 'DM Sans',Arial,sans-serif;fill:var(--muted)}.fs-mark{fill:var(--fs);fill-opacity:.72;stroke:var(--bg)}.sp-mark{fill:var(--sp);fill-opacity:.72;stroke:var(--bg)}.foot{margin:.2rem 0 0;color:var(--muted);font-size:.69rem;line-height:1.5}
</style>
