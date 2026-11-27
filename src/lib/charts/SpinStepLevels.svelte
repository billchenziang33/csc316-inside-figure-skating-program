<script>
	import { scaleBand, scaleLinear } from 'd3';
	let { elements = [] } = $props();
	let points = $derived(elements.map((d, i) => ({
		...d, jitter: ((d.final_rank * 17 + d.element_order * 13 + i) % 11 - 5) * 2.1
	})));
	const x = scaleBand().domain([1,2,3,4]).range([78, 725]).padding(.3);
	const y = scaleLinear().domain([0, 12]).range([252, 32]);
	const yTicks = [0,3,6,9,12];
</script>

<div class="viz" role="img" aria-label="Spin and step sequence panel scores by protocol level across the top-ten cohort, with separate marks for spins and step sequences.">
	<div class="legend"><span><i class="spin"></i>Spin</span><span><i class="step"></i>Step sequence</span></div>
	<svg viewBox="0 0 770 300" role="presentation">
		{#each yTicks as t}<line x1="78" x2="725" y1={y(t)} y2={y(t)} style="stroke:var(--line)"/><text x="67" y={y(t)+4} text-anchor="end">{t}</text>{/each}
		{#each [1,2,3,4] as level}<line x1={x(level)+x.bandwidth()/2} x2={x(level)+x.bandwidth()/2} y1="32" y2="252" style="stroke:var(--line)"/><text x={x(level)+x.bandwidth()/2} y="271" text-anchor="middle">Level {level}</text>{/each}
		<line x1="78" x2="725" y1="252" y2="252" style="stroke:var(--faint)"/><line x1="78" x2="78" y1="32" y2="252" style="stroke:var(--faint)"/>
		{#each points as point (point.id)}
			{#if point.element_group === 'spin'}<circle cx={x(point.level)+x.bandwidth()/2+point.jitter} cy={y(point.panel_element_score)} r="4" class="spin-dot"><title>{point.skater} · {point.segment} · {point.element_code_raw} · {point.panel_element_score.toFixed(2)} points</title></circle>
			{:else}<rect x={x(point.level)+x.bandwidth()/2+point.jitter-3.5} y={y(point.panel_element_score)-3.5} width="7" height="7" class="step-dot"><title>{point.skater} · {point.segment} · {point.element_code_raw} · {point.panel_element_score.toFixed(2)} points</title></rect>{/if}
		{/each}
		<text x="400" y="296" text-anchor="middle">Protocol level</text><text transform="translate(18 140) rotate(-90)" text-anchor="middle">Element panel score (points)</text>
	</svg>
	<p class="foot">Top ten skaters. Each mark is one element from the official score sheets. The level is read from the element code. {points.length} elements.</p>
</div>

<style>
	.viz{display:grid;gap:.15rem}.legend{display:flex;gap:1rem;justify-content:flex-end;font-size:.7rem;color:var(--muted)}.legend i{display:inline-block;width:.62rem;height:.62rem;margin-right:.25rem}.spin{border-radius:50%;background:var(--sp)}.step{background:var(--fs)}.spin-dot{fill:var(--sp);fill-opacity:.75;stroke:var(--bg)}.step-dot{fill:var(--fs);fill-opacity:.75;stroke:var(--bg)}svg{width:100%;height:auto}svg text{font:10px 'DM Sans',Arial,sans-serif;fill:var(--muted)}.foot{margin:.1rem 0 0;color:var(--muted);font-size:.69rem;line-height:1.5}
</style>
