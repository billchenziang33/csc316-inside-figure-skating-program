<script>
	import { JUMP_TYPES, SPIN_PARTS, OTHER_ELEMENTS, MARKS, ROTATION_NAMES, describeElement } from './data/element-glossary.mjs';
	import { protocolMarks } from './data/derived.mjs';
	import { elementTip } from './tooltip.mjs';

	let { elements = [], onContinue = () => {} } = $props();

	const JUMP_PART = /^(\d)(Lz|Lo|Eu|A|F|S|T)/;

	// How often each jump type was performed by the final top ten (every jump in a combination counts).
	let jumpRows = $derived.by(() => {
		const tally = new Map(JUMP_TYPES.map((t) => [t.code, { total: 0, quads: 0 }]));
		for (const d of elements) {
			if (d.element_group !== 'jump') continue;
			for (const part of d.element_code_raw.split('+')) {
				const m = part.match(JUMP_PART);
				if (!m) continue;
				const row = tally.get(m[2]);
				row.total += 1;
				if (m[1] === '4') row.quads += 1;
			}
		}
		return JUMP_TYPES.map((t) => ({ ...t, ...tally.get(t.code) }));
	});
	let maxBase = $derived(Math.max(...JUMP_TYPES.map((t) => t.quadBase ?? 0)));
	let maxCount = $derived(Math.max(1, ...jumpRows.map((r) => r.total)));

	let spinRows = $derived.by(() => {
		const counts = new Map();
		for (const d of elements) {
			if (d.element_group !== 'spin') continue;
			counts.set(d.element_code_raw, (counts.get(d.element_code_raw) ?? 0) + 1);
		}
		return [...counts].sort((a, b) => b[1] - a[1]).map(([code, count]) => ({ code, count, ...describeElement(code) }));
	});

	let markCounts = $derived.by(() => {
		const counts = Object.fromEntries(Object.keys(MARKS).map((m) => [m, 0]));
		for (const d of elements) {
			for (const m of protocolMarks(d)) counts[m] += 1;
			if (String(d.info_flag ?? '').includes('x')) counts.x += 1;
		}
		return counts;
	});

	const anatomy = [
		{ part: '4', label: 'Rotations', detail: '4 = quad' },
		{ part: 'Lz', label: 'Jump type', detail: 'Lutz' },
		{ part: '+', label: 'Combination', detail: 'jumps linked without a step' },
		{ part: '3', label: 'Rotations', detail: '3 = triple' },
		{ part: 'T', label: 'Jump type', detail: 'Toe loop' }
	];
	const spinAnatomy = [
		{ part: 'F', label: 'Flying', detail: 'starts with a jump' },
		{ part: 'C', label: 'Change foot', detail: 'spins on both feet' },
		{ part: 'Co', label: 'Combination', detail: 'changes position' },
		{ part: 'Sp', label: 'Spin', detail: '' },
		{ part: '4', label: 'Level', detail: '1–4, set by the panel' }
	];
</script>

<div class="primer">
	<section class="panel primer-block" aria-labelledby="read-code">
		<span class="section-number">1 · Read a code</span>
		<h2 id="read-code">Every element on a score sheet is a short code.</h2>
		<p class="lede">Official protocols list each move as a code. Once you can read the parts, any program becomes readable. Hover over a code later in the workbench to see it spelled out.</p>
		<div class="anatomy-pair">
			<figure class="anatomy">
				<figcaption>A jump combination</figcaption>
				<div class="anatomy-code" role="list">
					{#each anatomy as a}<div class="anatomy-part" role="listitem"><b>{a.part}</b><span>{a.label}</span><small>{a.detail}</small></div>{/each}
				</div>
				<p>= Quad Lutz + Triple Toe loop</p>
			</figure>
			<figure class="anatomy">
				<figcaption>A spin</figcaption>
				<div class="anatomy-code" role="list">
					{#each spinAnatomy as a}<div class="anatomy-part spin" role="listitem"><b>{a.part}</b><span>{a.label}</span><small>{a.detail}</small></div>{/each}
				</div>
				<p>= Flying change-foot combination spin, Level 4</p>
			</figure>
		</div>
		<dl class="rotations">
			{#each Object.entries(ROTATION_NAMES) as [n, name]}<div><dt>{n}</dt><dd>{name}</dd></div>{/each}
			<div class="axel-note"><dt>A</dt><dd>Axel adds ½ turn: 3A = 3½ rotations</dd></div>
		</dl>
	</section>

	<section class="panel primer-block" aria-labelledby="jump-chart">
		<span class="section-number">2 · The jumps</span>
		<h2 id="jump-chart">Six jumps, ordered by difficulty.</h2>
		<p class="lede">Jumps differ by how they leave the ice. <b class="toe">Toe jumps</b> vault off the toe pick of the free foot; <b class="edge">edge jumps</b> spring from the blade's edge alone. Harder jumps carry higher base values.</p>
		<div class="table-scroll">
			<table class="jump-table">
				<caption class="sr-only">Jump types with take-off, quad base value and how often the Beijing 2022 top ten performed them</caption>
				<thead><tr><th scope="col">Code</th><th scope="col">Jump</th><th scope="col">Take-off</th><th scope="col">Quad base value</th><th scope="col">Performed in Beijing<small>top ten · SP + FS</small></th></tr></thead>
				<tbody>
					{#each jumpRows as row (row.code)}
						<tr>
							<th scope="row"><span class="code-chip">{row.code}</span></th>
							<td><b>{row.name}</b><small>{row.edge}</small></td>
							<td><span class="badge {row.takeoff}">{row.takeoff === 'toe' ? 'Toe pick' : 'Edge'}</span></td>
							<td class="bar-cell">{#if row.quadBase}<span class="bar base" style:width={`${(row.quadBase / maxBase) * 100}%`}></span><span class="num">{row.quadBase.toFixed(2)}</span>{:else}<span class="muted">Only in combinations</span>{/if}</td>
							<td class="bar-cell"><span class="bar count" style:width={`${(row.total / maxCount) * 100}%`}></span><span class="num">{row.total}{#if row.quads}<small> · {row.quads} quad{row.quads === 1 ? '' : 's'}</small>{/if}</span></td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p class="scope-note">Base values from the ISU Scale of Values 2021–22. Take-off edges are for a skater rotating counter-clockwise. Every jump inside a combination is counted.</p>
	</section>

	<div class="primer-grid">
		<section class="panel primer-block" aria-labelledby="spin-chart">
			<span class="section-number">3 · Spins & sequences</span>
			<h2 id="spin-chart">Spins are built from parts.</h2>
			<dl class="parts">{#each SPIN_PARTS as p}<div><dt><span class="code-chip">{p.code}</span></dt><dd>{p.meaning}</dd></div>{/each}</dl>
			<h3>Spins in the Beijing top ten</h3>
			<ul class="spin-list">{#each spinRows as s (s.code)}<li><button type="button" class="code-chip" use:elementTip={{ name: s.name, notes: s.notes }}>{s.code}</button><span>{s.name}{#if s.notes.length}<em> · {s.notes.join(" · ")}</em>{/if}</span><small>{s.count}×</small></li>{/each}</ul>
			<h3>Other elements</h3>
			<dl class="parts">{#each OTHER_ELEMENTS as o}<div><dt><span class="code-chip">{o.code}</span></dt><dd><b>{o.name}.</b> {o.meaning}</dd></div>{/each}</dl>
		</section>

		<section class="panel primer-block" aria-labelledby="mark-chart">
			<span class="section-number">4 · Protocol marks</span>
			<h2 id="mark-chart">Small symbols change the score.</h2>
			<p class="lede">Officials add marks to a code when something about the element was short, unclear or bonus-worthy.</p>
			<dl class="parts marks">{#each Object.entries(MARKS) as [mark, m]}<div><dt><span class="code-chip mark">{mark}</span></dt><dd><b>{m.label}.</b> {m.meaning}<small>{markCounts[mark]} in Beijing top ten</small></dd></div>{/each}</dl>
		</section>
	</div>

	<div class="primer-actions"><button class="primary" onclick={onContinue}>Now choose a program to follow →</button></div>
</div>

<style>
	.primer { display:grid; gap:1rem; margin-top:1rem; }
	.primer-block { padding:1.35rem clamp(1rem,2.5vw,2rem); min-width:0; }
	.primer-block h2 { margin:.35rem 0 .5rem; font:700 clamp(1.2rem,2vw,1.55rem)/1.25 var(--serif); color:var(--navy); }
	.primer-block h3 { margin:1.4rem 0 .5rem; font-size:.85rem; color:var(--ink); }
	.lede { color:var(--muted); max-width:760px; line-height:1.65; font-size:.9rem; margin:0 0 1rem; }
	.lede .toe { color:var(--rust); } .lede .edge { color:var(--teal); }
	.primer-grid { display:grid; grid-template-columns:1fr 1fr; gap:1rem; }

	.anatomy-pair { display:grid; grid-template-columns:1fr 1fr; gap:1rem; }
	.anatomy { margin:0; padding:1rem; background:var(--paper); border-radius:6px; }
	.anatomy figcaption { font:.68rem var(--mono); text-transform:uppercase; letter-spacing:.1em; color:var(--muted); margin-bottom:.7rem; }
	.anatomy-code { display:flex; flex-wrap:wrap; gap:.35rem; }
	.anatomy-part { display:grid; justify-items:center; gap:.15rem; min-width:62px; padding:.5rem .4rem; background:var(--card); border:1px solid var(--line); border-top:3px solid var(--rust); border-radius:4px; text-align:center; }
	.anatomy-part.spin { border-top-color:var(--teal); }
	.anatomy-part b { font:600 1.35rem var(--mono); color:var(--navy); }
	.anatomy-part span { font-size:.68rem; font-weight:600; }
	.anatomy-part small { font-size:.62rem; color:var(--muted); max-width:86px; line-height:1.3; }
	.anatomy p { margin:.8rem 0 0; font-size:.85rem; font-weight:600; }

	.rotations { display:flex; flex-wrap:wrap; gap:.5rem; margin:1rem 0 0; }
	.rotations div { display:flex; align-items:center; gap:.45rem; padding:.35rem .65rem; border:1px solid var(--line); border-radius:999px; font-size:.78rem; }
	.rotations dt { font:600 .85rem var(--mono); color:var(--navy); }
	.rotations dd { margin:0; }

	.table-scroll { overflow-x:auto; max-height:none; }
	.jump-table { width:100%; border-collapse:collapse; font-size:.82rem; min-width:640px; }
	.jump-table th, .jump-table td { padding:.65rem .6rem; border-bottom:1px solid var(--line); text-align:left; vertical-align:middle; }
	.jump-table thead th { font:500 .66rem var(--mono); text-transform:uppercase; letter-spacing:.08em; color:var(--muted); }
	.jump-table thead small { display:block; text-transform:none; letter-spacing:0; }
	.jump-table td b { display:block; }
	.jump-table td small { display:block; color:var(--muted); font-size:.72rem; line-height:1.4; margin-top:.15rem; max-width:300px; }
	.jump-table tbody tr:last-child { color:var(--muted); }
	.badge { display:inline-block; padding:.2rem .5rem; border-radius:999px; font-size:.7rem; font-weight:600; white-space:nowrap; }
	.badge.toe { background:#f6e3da; color:#8f3f22; } .badge.edge { background:#dceae7; color:#245b55; }
	.bar-cell { position:relative; width:22%; }
	.bar { display:block; height:8px; border-radius:2px; margin-bottom:.3rem; min-width:3px; }
	.bar.base { background:var(--navy); } .bar.count { background:var(--teal); }
	.num { font:.75rem var(--mono); } .num small { display:inline; font-family:inherit; }
	.muted { color:var(--muted); font-size:.72rem; }

	.code-chip { display:inline-block; min-width:2.2rem; padding:.15rem .45rem; background:var(--paper); border:1px solid var(--line); border-radius:4px; font:600 .78rem var(--mono); color:var(--navy); text-align:center; white-space:nowrap; }
	button.code-chip { cursor:help; }
	button.code-chip:focus-visible { outline:2px solid var(--navy); outline-offset:2px; }
	.code-chip.mark { color:var(--rust); }
	.parts { display:grid; gap:.55rem; margin:0; }
	.parts div { display:grid; grid-template-columns:5.5rem 1fr; gap:.6rem; align-items:baseline; font-size:.82rem; line-height:1.5; }
	.parts dd { margin:0; }
	.parts dd small { display:block; color:var(--muted); font-size:.7rem; }
	.spin-list { list-style:none; margin:0; padding:0; display:grid; gap:.35rem; }
	.spin-list li { display:grid; grid-template-columns:6.5rem 1fr auto; gap:.6rem; align-items:center; font-size:.8rem; }
	.spin-list small { font:.72rem var(--mono); color:var(--muted); }
	.spin-list em { font-style:normal; color:var(--muted); }
	.primer-actions { display:flex; justify-content:center; padding:.5rem 0 1rem; }

	@media (max-width: 900px) { .primer-grid, .anatomy-pair { grid-template-columns:1fr; } }
</style>
