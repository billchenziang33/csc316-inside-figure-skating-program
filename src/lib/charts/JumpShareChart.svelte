<script>
	import { scaleLinear } from 'd3';
	let { data = [] } = $props();
	const x = scaleLinear().domain([0, 100]).range([0, 100]);
	const ticks = [0, 25, 50, 75, 100];
	const colors = { SP: 'var(--sp)', FS: 'var(--fs)' };
</script>

<div class="chart" role="img" aria-label="Jump panel scores made up 67.4 percent of element points in the short program and 77.1 percent in the free skate for the top ten skaters.">
	<div class="axis" aria-hidden="true">
		<span></span>
		<div class="axis-track">
			{#each ticks as tick}
				<span style={`left:${x(tick)}%`}>{tick}%</span>
			{/each}
		</div>
	</div>
	{#each data as row (row.segment)}
		<div class="bar-row">
			<div class="bar-label">{row.segment === 'SP' ? 'Short program' : 'Free skate'}</div>
			<div class="bar-track">
				<div class="bar-fill" style={`width:${x(row.share * 100)}%;background:${colors[row.segment]}`}></div>
				<span class="bar-value" style={`left:${x(row.share * 100)}%`}>{(row.share * 100).toFixed(1)}%</span>
			</div>
		</div>
	{/each}
	<div class="chart-foot">Share of all element points. Top ten skaters, official ISU score sheets.</div>
</div>

<style>
	.chart { display: grid; gap: 1.15rem; padding: 1rem 0 .25rem; }
	.axis, .bar-row { display: grid; grid-template-columns: 142px minmax(0, 1fr); gap: 1rem; align-items: center; }
	.axis-track, .bar-track { position: relative; }
	.axis-track { height: 1.4rem; border-bottom: 1px solid var(--faint); }
	.axis-track span { position: absolute; bottom: .2rem; transform: translateX(-50%); color: var(--muted); font-size: .72rem; }
	.bar-label { font-size: .9rem; color: var(--ink); }
	.bar-track { height: 2.25rem; background: var(--line); border-radius: 4px; }
	.bar-fill { height: 100%; border-radius: 4px; }
	.bar-value { position: absolute; top: 50%; transform: translate(8px,-50%); font-size: .85rem; font-weight: 700; white-space: nowrap; color: var(--ink); }
	.chart-foot { margin: .3rem 0 0 158px; color: var(--muted); font-size: .76rem; }
	@media (max-width: 540px) { .axis, .bar-row { grid-template-columns: 112px minmax(0,1fr); gap: .6rem; } .bar-label { font-size: .78rem; } .chart-foot { margin-left: 0; } }
</style>
