<script>
	import { scaleLinear } from 'd3';
	let { segments = [] } = $props();
	const scale = scaleLinear().domain([0, 250]).range([0, 74]);
	const tickValues = [0, 50, 100, 150, 200, 250];
	let rows = $derived(['SP', 'FS'].map((program) => segments.find((d) => d.segment === program)).filter(Boolean));
</script>

<div class="chart" role="img" aria-label="For the selected skater, compare technical element score with total segment score in the short program and free skate. Total segment score includes technical score, component score, and deductions.">
	<div class="axis">
		<span></span><div class="axis-track">
			{#each tickValues as tick}<span style={`left:${scale(tick)}%`}>{tick}</span>{/each}
		</div>
	</div>
	{#each rows as row (row.segment)}
		<div class="row">
			<div class="label"><b>{row.segment}</b><small>{row.segment === 'SP' ? 'Short program' : 'Free skate'}</small></div>
			<div class="bars">
				<div class="bar-line"><span class="bar tes" style={`width:${scale(row.TES)}%`}></span><span class="number" style={`left:calc(${scale(row.TES)}% + 6px)`}>TES {row.TES.toFixed(2)}</span></div>
				<div class="bar-line"><span class="bar tss" style={`width:${scale(row.segment_score_TSS)}%`}></span><span class="number" style={`left:calc(${scale(row.segment_score_TSS)}% + 6px)`}>TSS {row.segment_score_TSS.toFixed(2)}</span></div>
			</div>
		</div>
	{/each}
	<div class="legend"><span><i class="tes-key"></i>Technical element score (TES)</span><span><i class="tss-key"></i>Total segment score (TSS)</span></div>
	<p class="note">TSS includes TES, program components, and deductions; it is not an independent score.</p>
</div>

<style>
	.chart { display:grid; gap:.95rem; }
	.axis,.row { display:grid; grid-template-columns:108px minmax(0,1fr); gap:.85rem; align-items:center; }
	.axis-track { height:1.3rem; position:relative; }
	.axis-track::after { content:''; position:absolute; left:0; bottom:0; width:74%; height:1px; background:var(--faint); }
	.axis-track span { position:absolute; bottom:.2rem; transform:translateX(-50%); color:var(--muted); font-size:.7rem; }
	.label b,.label small { display:block; }.label small { color:var(--muted); font-size:.72rem; margin-top:.15rem; }
	.bars { display:grid; gap:.38rem; }
	.bar-line { height:1.2rem; position:relative; }
	.bar { display:block; height:100%; border-radius:3px; min-width:1px; }
	.tes { background:var(--sp); }.tss { background:var(--fs); }
	.number { position:absolute; top:50%; transform:translateY(-50%); font-size:.73rem; font-weight:700; white-space:nowrap; color:var(--ink); }
	.legend { display:flex; gap:1rem; flex-wrap:wrap; margin-left:116px; font-size:.72rem; color:var(--muted); }
	.legend span { display:inline-flex; align-items:center; gap:.35rem; }.legend i { width:.7rem; height:.7rem; border-radius:2px; }.tes-key { background:var(--sp); }.tss-key { background:var(--fs); }
	.note { margin:0 0 0 116px; color:var(--muted); font-size:.76rem; line-height:1.45; }
	@media(max-width:540px) { .axis,.row { grid-template-columns:78px minmax(0,1fr); gap:.5rem; }.legend,.note { margin-left:0; }.number { font-size:.66rem; } }
</style>
