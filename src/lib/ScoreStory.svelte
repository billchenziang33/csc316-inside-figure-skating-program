<script>
	import { onMount } from 'svelte';
	import { scaleLinear } from 'd3';
	import { CHARACTERS, ELEMENT_GROUPS, opensWithQuad, storyFacts } from './data/story-facts.mjs';
	import { arrive, leave } from './motion.mjs';

	let { elements = [], segments = [], onOpen = () => {} } = $props();

	const { unoShort, unoFree, brownFree, hanyuFree } = CHARACTERS;
	const facts = $derived(storyFacts(elements, segments));
	const byId = $derived(new Map(elements.map((element) => [element.id, element])));
	const fmt = (n) => n.toFixed(2);
	const programName = (segment) => (segment === 'SP' ? 'Short program' : 'Free skate');

	// ── Steps ────────────────────────────────────────────────────────────────
	// layout: where the dots go · show: which dots are lit · color: what the colour means
	// base: dots drawn at their base value (before the judges' GOE) · notes: annotated dots
	const steps = $derived([
		{
			key: 'units', layout: 'units', show: 'all', color: 'type',
			label: 'Every scored element, Beijing 2022 top ten',
			text: `<p>Each dot is one element the top ten performed in Beijing: <b>${facts.elements}</b> in all, sorted by kind and by score.</p><p><span class="chip jump">${facts.groups.jump} jumps</span> <span class="chip spin">${facts.groups.spin} spins</span> <span class="chip step">${facts.groups.step_sequence} step sequences</span> <span class="chip choreo">${facts.groups.choreographic_sequence} choreographic sequences</span></p>`
		},
		{
			key: 'scatter', layout: 'scatter', show: 'all', color: 'type', notes: [unoFree, brownFree],
			label: 'Base value and final score, all elements',
			text: `<p>Now every dot moves to its <b>base value</b> (across) and its <b>final score</b> (up).</p><p>On the dashed line, the judges added nothing. Above it, they added points. Below it, they took points away.</p>`
		},
		{
			key: 'gains', layout: 'scatter', show: 'all', color: 'goe',
			label: 'Did execution add or take away points?',
			text: `<p>Most moves gain. <span class="chip gain">${facts.gained} of ${facts.elements}</span> scored above their base value.</p><p>Only <span class="chip loss">${facts.lost}</span> lost points.</p>`
		},
		{
			key: 'quads', layout: 'scatter', show: 'quads', color: 'goe',
			label: 'Jumps that start with a quad',
			text: `<p>But the losses are not spread evenly. They pile up on the hardest jumps.</p><p><span class="chip loss">${facts.quadsLost} of ${facts.quads}</span> jumps that start with a quad lost points. For all other jumps, it was ${facts.otherJumpsLost} of ${facts.otherJumps}.</p>`
		},
		{
			key: 'hanyu', layout: 'scatter', show: 'quads', color: 'goe', notes: [hanyuFree],
			label: 'Jumps that start with a quad',
			text: `<p>One of them: <span class="chip char">Yuzuru Hanyu</span> tried a <b>quad Axel</b>, a jump no skater had ever landed in competition.</p><p>The judges ruled it short of four and a half turns. It earned <b>5.00</b>.</p>`
		},
		{
			key: 'upsets', layout: 'scatter', show: 'jumps', color: 'goe', notes: [unoFree, brownFree],
			label: 'All 100 jumps',
			text: `<p>Uno and Brown are not a rare case.</p><p>Take any two jumps with different base values. In <b>${facts.upsets.toLocaleString('en')} of ${facts.pairs.toLocaleString('en')}</b> pairs, about 1 in 6, the easier jump scored more.</p>`
		},
		{
			key: 'program', layout: 'scatter', show: 'all', color: 'type',
			label: 'Base value and final score, all elements',
			text: `<p>And these moves are only part of the story. Across the 20 programs, element points made up about <b>${Math.round(facts.tesShare * 100)}%</b> of the total.</p><p>The rest comes from <b>program components</b>: the judges’ marks for the skating as a whole.</p>`
		},
		{
			key: 'end', layout: 'scatter', show: 'all', color: 'goe',
			label: 'Hover a dot for details. Click to read it.',
			text: `<p>Every dot is now yours to explore.</p><p>Hover over a dot to see the move. Click it to read that element in its program, further down this page.</p>`
		}
	]);

	let activeKey = $state('units');
	let step = $derived(steps.find((s) => s.key === activeKey) ?? steps[0]);

	// ── Geometry ─────────────────────────────────────────────────────────────
	let W = $state(1200);
	let H = $state(800);
	let wide = $derived(W >= 900);
	let plot = $derived(wide
		? { left: Math.min(Math.max(W * 0.42, 470), W - 420), right: W - 60, top: 120, bottom: H - 90 }
		: { left: 52, right: W - 22, top: 176, bottom: Math.max(330, H * 0.6) });
	let x = $derived(scaleLinear().domain([0, 18]).range([plot.left, plot.right]));
	let y = $derived(scaleLinear().domain([0, 22]).range([plot.bottom, plot.top]));
	const xTicks = [0, 5, 10, 15];
	const yTicks = [0, 5, 10, 15, 20];

	const noise = (i, k) => { const s = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return s - Math.floor(s); };

	// Unit chart: one block of dots per element group, ten to a row.
	let units = $derived.by(() => {
		const perRow = 10;
		const gap = 2;
		const cols = ELEMENT_GROUPS.length * perRow + (ELEMENT_GROUPS.length - 1) * gap;
		const d = Math.min(wide ? 17 : 12, (plot.right - plot.left) / cols);
		const width = cols * d;
		const left = (plot.left + plot.right) / 2 - width / 2;
		const top = (plot.top + plot.bottom) / 2 - (10 * d) / 2;
		const spots = new Map();
		const labels = [];
		ELEMENT_GROUPS.forEach((group, g) => {
			const rows = elements.filter((e) => e.element_group === group.key).sort((a, b) => b.panel_element_score - a.panel_element_score);
			const x0 = left + g * (perRow + gap) * d;
			rows.forEach((e, i) => spots.set(e.id, { x: x0 + (i % perRow) * d + d / 2, y: top + Math.floor(i / perRow) * d + d / 2 }));
			labels.push({ key: group.key, x: x0, y: top + 10 * d + 22, text: wide ? `${group.label} ${rows.length}` : `${group.short} ${rows.length}` });
		});
		return { spots, labels, d };
	});

	function isLit(e, s) {
		if (s.show === 'all') return true;
		if (s.show === 'quads') return opensWithQuad(e);
		if (s.show === 'jumps') return e.element_group === 'jump';
		return s.show.includes(e.id);
	}

	const GROUP_CLASS = { jump: 'jump', spin: 'spin', step_sequence: 'step', choreographic_sequence: 'choreo' };
	function tone(e, s) {
		if (s.color === 'faint') return 'faint';
		if (s.color === 'char') return 'char';
		if (s.color === 'goe') return e.goe > 0 ? 'gain' : e.goe < 0 ? 'loss' : 'level';
		return GROUP_CLASS[e.element_group];
	}

	let dots = $derived(elements.map((e, i) => {
		const lit = isLit(e, step);
		let px; let py;
		if (step.layout === 'field') {
			px = 20 + noise(i, 1) * (W - 40);
			py = 20 + noise(i, 2) * (H - 40);
		} else if (step.layout === 'units') {
			({ x: px, y: py } = units.spots.get(e.id) ?? { x: 0, y: 0 });
		} else {
			px = x(e.base_value);
			py = y(step.base?.includes(e.id) ? e.base_value : e.panel_element_score);
		}
		const featured = (step.notes ?? []).includes(e.id) || (step.color === 'char' && lit);
		const r = step.layout === 'units' ? Math.max(3, units.d * 0.36) : featured ? (wide ? 8 : 6.5) : wide ? 5 : 4;
		return { e, px, py, r, lit, tone: tone(e, step), featured, delay: (i % 20) * 10 };
	}));

	// Short labels next to the dots the story names.
	const NAMES = { [unoShort]: 'Uno 4F, short program', [unoFree]: 'Uno 4F, free skate', [brownFree]: 'Brown 3F, free skate', [hanyuFree]: 'Hanyu 4A<, free skate' };
	let notes = $derived((step.notes ?? []).map((id) => {
		const e = byId.get(id);
		if (!e) return null;
		const onBase = step.base?.includes(id);
		const score = onBase ? e.base_value : e.panel_element_score;
		const right = x(e.base_value) < (plot.left + plot.right) / 2 + 80 || !wide;
		return { id, x: x(e.base_value) + (right ? 14 : -14), y: y(score) + 4, anchor: right ? 'start' : 'end', name: NAMES[id], value: onBase ? `${fmt(e.base_value)} base` : fmt(e.panel_element_score) };
	}).filter(Boolean));
	let arrows = $derived((step.arrows ?? []).map((id) => {
		const e = byId.get(id);
		return e && { id, x: x(e.base_value), y1: y(e.base_value), y2: y(e.panel_element_score), gain: e.goe >= 0 };
	}).filter(Boolean));

	// ── Scroll → active step ─────────────────────────────────────────────────
	let stepList = $state();
	onMount(() => {
		const observer = new IntersectionObserver((entries) => {
			for (const entry of entries) if (entry.isIntersecting) activeKey = entry.target.dataset.step;
		}, { rootMargin: '-50% 0px -50% 0px' });
		stepList?.querySelectorAll('[data-step]').forEach((node) => observer.observe(node));
		return () => observer.disconnect();
	});

	// ── Hover details ────────────────────────────────────────────────────────
	let hovered = $state(null);
	let hoverDot = $derived(hovered ? dots.find((d) => d.e.id === hovered && d.lit) : null);
	let unhover = 0;
	function enter(d) { if (!d.lit || step.layout === 'field') return; clearTimeout(unhover); hovered = d.e.id; }
	function exit(d) { clearTimeout(unhover); unhover = setTimeout(() => { if (hovered === d.e.id) hovered = null; }, 120); }
</script>

<div class="story">
	<div class="graphic" bind:clientWidth={W} bind:clientHeight={H}>
		<svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Each dot is one of the 190 elements the Beijing 2022 men’s singles top ten performed. The dots move as the story is read.">
			<g class="axes" class:shown={step.layout === 'scatter'} aria-hidden="true">
				{#each yTicks as t}<line class="grid" x1={plot.left} x2={plot.right} y1={y(t)} y2={y(t)} /><text class="tick" x={plot.left - 10} y={y(t) + 4} text-anchor="end">{t}</text>{/each}
				{#each xTicks as t}<text class="tick" x={x(t)} y={plot.bottom + 22} text-anchor="middle">{t}</text>{/each}
				<line class="parity" x1={x(0)} y1={y(0)} x2={x(18)} y2={y(18)} />
				<text class="parity-label" x={x(17.6)} y={y(18) - 8} text-anchor="end">judges added nothing</text>
				<text class="axis-title" x={plot.right} y={plot.bottom + 46} text-anchor="end">Base value (difficulty)</text>
				<text class="axis-title" x={plot.left - 10} y={plot.top - 22}>Final score (points)</text>
			</g>
			<g class="unit-labels" class:shown={step.layout === 'units'} aria-hidden="true">
				{#each units.labels as label (label.key)}<text class="tick" x={label.x} y={label.y}>{label.text}</text>{/each}
			</g>
			{#each arrows as a (a.id)}
				<line class="goe-arrow" class:gain={a.gain} class:loss={!a.gain} x1={a.x} x2={a.x} y1={a.y1} y2={a.y2} />
			{/each}
			<g class="dots">
				{#each dots as d (d.e.id)}
					<circle
						class="dot {d.tone}"
						class:lit={d.lit}
						class:featured={d.featured}
						r={d.r}
						style:r={`${d.r}px`}
						style:transform={`translate(${d.px}px, ${d.py}px)`}
						style:transition-delay={`${d.delay}ms`}
						role="presentation"
						onpointerenter={() => enter(d)}
						onpointerleave={() => exit(d)}
						onclick={() => { if (d.lit && step.layout !== 'field') onOpen(d.e.id); }}
					/>
				{/each}
			</g>
			{#each notes as n (n.id + activeKey)}
				<g in:arrive={{ delay: 650, duration: 300, y: 0 }} out:leave>
					<text class="note-name" x={n.x} y={n.y - 8} text-anchor={n.anchor}>{n.name}</text>
					<text class="note-value" x={n.x} y={n.y + 12} text-anchor={n.anchor}>{n.value}</text>
				</g>
			{/each}
		</svg>
		<div class="graphic-label" aria-hidden="true">
			<div class="stack">
				{#key step.label}<span in:arrive out:leave>{step.label}</span>{/key}
			</div>
			<div class="stack">
				{#key step.color}
					<div class="legend" in:arrive out:leave>
						{#if step.color === 'type'}<i class="chip jump">Jump</i><i class="chip spin">Spin</i><i class="chip step">Step sequence</i><i class="chip choreo">Choreographic sequence</i>
						{:else if step.color === 'goe'}<i class="chip gain">Judges added points</i><i class="chip loss">Judges took points away</i>{/if}
					</div>
				{/key}
			</div>
		</div>
		{#if hoverDot}
			<div class="tip" class:flip={hoverDot.px > W - 260} style:--x={`${hoverDot.px}px`} style:--y={`${hoverDot.py}px`} in:arrive={{ delay: 0, duration: 150, y: 4 }} out:leave={{ duration: 100 }}>
				<b>{hoverDot.e.skater}</b>
				<span><code>{hoverDot.e.element_code_raw}</code>, {programName(hoverDot.e.segment).toLowerCase()}</span>
				<span>{fmt(hoverDot.e.base_value)} base {hoverDot.e.goe < 0 ? '−' : '+'} {fmt(Math.abs(hoverDot.e.goe))} GOE = <b>{fmt(hoverDot.e.panel_element_score)}</b></span>
				<small>Click to read it in its program</small>
			</div>
		{/if}
	</div>

	<ol class="steps" bind:this={stepList}>
		{#each steps as s (s.key)}
			<li data-step={s.key} class:current={s.key === activeKey}>
				<div class="card">{@html s.text}</div>
			</li>
		{/each}
	</ol>
</div>


<style>
	.story { position:relative; scroll-margin-top:52px; }
	.graphic { position:sticky; top:0; height:100vh; height:100svh; overflow:hidden; }
	svg { display:block; }

	/* One gesture per step: every dot moves on the same curve; colour and size settle a little sooner. */
	.dot { fill:var(--faint); opacity:.08; cursor:default; transition:transform 900ms var(--ease), opacity var(--dur-slow) var(--ease), fill var(--dur-slow) var(--ease), r var(--dur-slow) var(--ease), stroke-width var(--dur-fast) var(--ease); }
	.dot.lit { opacity:.9; }
	.dot.jump.lit { fill:var(--c-jump); }
	.dot.spin.lit { fill:var(--c-spin); }
	.dot.step.lit { fill:var(--c-step); }
	.dot.choreo.lit { fill:var(--c-choreo); }
	.dot.gain.lit { fill:var(--gain); }
	.dot.loss.lit { fill:var(--loss); opacity:1; }
	.dot.level.lit { fill:var(--muted); }
	.dot.char.lit { fill:var(--ink); opacity:1; }
	.dot.featured { stroke:var(--bg); stroke-width:2; opacity:1; }
	.dot.lit { cursor:pointer; }
	.dot.lit:hover { stroke:var(--ink); stroke-width:2; }

	.axes, .unit-labels { opacity:0; transition:opacity var(--dur-slow) var(--ease); }
	.axes.shown, .unit-labels.shown { opacity:1; }
	.grid { stroke:#ffffff17; }
	.tick { fill:var(--muted); font:500 12px var(--sans); }
	.axis-title { fill:var(--muted); font:500 13px var(--sans); }
	.parity { stroke:var(--muted); stroke-dasharray:4 5; opacity:.6; }
	.parity-label { fill:var(--muted); font:500 12px var(--sans); }
	.goe-arrow { stroke-width:3; stroke-linecap:round; }
	.goe-arrow.gain { stroke:var(--gain); }
	.goe-arrow.loss { stroke:var(--loss); }
	.note-name { fill:var(--ink); font:600 14px var(--sans); paint-order:stroke; stroke:var(--bg); stroke-width:5px; stroke-linejoin:round; }
	.note-value { fill:var(--muted); font:500 13px var(--sans); paint-order:stroke; stroke:var(--bg); stroke-width:5px; stroke-linejoin:round; }

	.graphic-label { position:absolute; top:4.5rem; left:clamp(1rem, 4vw, 3rem); right:1rem; display:grid; gap:.5rem; pointer-events:none; }
	.graphic-label span { font:600 1rem var(--display); letter-spacing:-.015em; color:var(--ink); }
	.legend { display:flex; flex-wrap:wrap; gap:.35rem 1rem; }

	/* The tip glides from dot to dot instead of jumping. */
	.tip { position:absolute; left:0; top:0; z-index:3; transform:translate(calc(var(--x) + 16px), calc(var(--y) - 50%)); transition:transform var(--dur) var(--ease-out); display:grid; gap:.2rem; width:max-content; max-width:260px; padding:.75rem .9rem; background:#1d1d1fee; border-radius:14px; box-shadow:0 12px 40px #000c; font-size:.86rem; line-height:1.4; pointer-events:none; backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px); }
	.tip.flip { transform:translate(calc(var(--x) - 100% - 16px), calc(var(--y) - 50%)); }
	.tip small { color:var(--muted); font-size:.75rem; }
	.tip code { font:inherit; font-weight:600; color:var(--ice); }

	.steps { position:relative; z-index:2; list-style:none; margin:-100vh 0 0; margin-top:-100svh; padding:0 0 40vh; pointer-events:none; }
	.steps li { min-height:100vh; display:flex; align-items:center; padding:0 clamp(1rem, 4vw, 3rem); }
	.card { pointer-events:auto; width:min(390px, 100%); padding:1.4rem 1.5rem; background:#1d1d1fd9; border-radius:22px; backdrop-filter:saturate(180%) blur(20px); -webkit-backdrop-filter:saturate(180%) blur(20px);font-size:1.12rem; line-height:1.45; font-weight:500; color:var(--muted); opacity:.35; transition:opacity var(--dur-slow) var(--ease); }
	li.current .card { opacity:1; }
	.card :global(p) { margin:0; }
	.card :global(p + p) { margin-top:.8rem; }
	.card :global(b) { color:var(--ink); font-weight:600; }
	.card :global(.chip) { margin-right:.7em; }
	.card :global(code) { font:inherit; font-weight:600; color:var(--ice); }

	@media (max-width: 899px) {
		.steps li { align-items:flex-end; padding-bottom:6vh; justify-content:center; }
		.card { font-size:1rem; }
		.graphic-label { top:3.75rem; }
	}
</style>
