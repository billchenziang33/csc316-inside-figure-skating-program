<script>
	import ProtocolMatrix from '../charts/ProtocolMatrix.svelte';
	import SkaterStage, { loopOf } from '../SkaterStage.svelte';
	import { describeElement, MARKS } from '../data/element-glossary.mjs';
	import { elementMarks } from '../data/derived.mjs';
	import { resolveMotion } from '../data/motion-reference.mjs';
	import { elementTip } from '../tooltip.mjs';
	import { slidingThumb } from '../thumb.mjs';
	import { Tween } from 'svelte/motion';
	import { arrive, leave, grow, numberTween } from '../motion.mjs';

	// One program, element by element: the order, the score sum, the nine judges, the officials' marks.
	let {
		segments = [],
		elements = [],
		catalog = null,
		rank = $bindable(1),
		segment = $bindable('SP'),
		elementId = $bindable(null),
		arrival = 0,
		onPlay = () => {}
	} = $props();

	const fmt = (n) => (n ?? 0).toFixed(2);
	const signed = (n) => `${n < 0 ? '−' : '+'}${fmt(Math.abs(n ?? 0))}`;
	const GROUP = { jump: 'Jump', spin: 'Spin', step_sequence: 'Step sequence', choreographic_sequence: 'Choreographic sequence' };

	let skaters = $derived(segments.filter((s) => s.segment === 'SP').sort((a, b) => a.final_rank - b.final_rank));
	let skater = $derived(skaters.find((s) => s.final_rank === rank)?.skater ?? '');
	let program = $derived(segments.find((s) => s.skater === skater && s.segment === segment));
	let rows = $derived(elements.filter((e) => e.skater === skater && e.segment === segment).sort((a, b) => a.element_order - b.element_order));
	let row = $derived(rows.find((e) => e.id === elementId) ?? rows[0] ?? null);
	let info = $derived(row ? describeElement(row.element_code_raw, row.info_flag) : null);
	let judges = $derived(row ? Array.from({ length: 9 }, (_, i) => row[`J${i + 1}`]) : []);
	let motion = $derived(resolveMotion(catalog, row));
	let marks = $derived(row ? elementMarks(row) : []);

	// Numbers count to their new value, so a change of element or program reads as a change.
	const total = Tween.of(() => program?.segment_score_TSS ?? 0, numberTween());
	const base = Tween.of(() => row?.base_value ?? 0, numberTween());
	const goe = Tween.of(() => Math.abs(row?.goe ?? 0), numberTween());
	const score = Tween.of(() => row?.panel_element_score ?? 0, numberTween());

	// Arriving from a dot or a chart point: once the page stops scrolling, the chosen row glows once.
	let flashId = $state(null);
	$effect(() => {
		if (!arrival) return;
		const id = elementId;
		let timer = 0;
		const glow = () => { flashId = id; timer = setTimeout(() => (flashId = null), 1400); };
		const wait = setTimeout(glow, 900);
		const done = () => { clearTimeout(wait); glow(); };
		if ('onscrollend' in window) addEventListener('scrollend', done, { once: true });
		return () => { clearTimeout(wait); clearTimeout(timer); removeEventListener('scrollend', done); };
	});
</script>

<section class="reader" id="program" aria-labelledby="program-heading">
	<div class="intro">
		<h2 id="program-heading">Read one program.</h2>
		<p>Pick a skater, then choose an element to see how it scored.</p>
	</div>

	<div class="controls">
		<label class="who"><span>Skater</span>
			<select bind:value={rank}>
				{#each skaters as s (s.final_rank)}<option value={s.final_rank}>{s.final_rank}. {s.skater} ({s.NOC})</option>{/each}
			</select>
		</label>
		<div class="segmented seg" role="group" aria-label="Program" use:slidingThumb={segment}>
			<button aria-pressed={segment === 'SP'} onclick={() => (segment = 'SP')}>Short program</button>
			<button aria-pressed={segment === 'FS'} onclick={() => (segment = 'FS')}>Free skate</button>
		</div>
		{#if program}
			<p class="total"><span>Program total</span><b>{fmt(total.current)}</b></p>
		{/if}
	</div>

	<div class="grid">
		<ol class="order-list" aria-label="Elements in skating order">
			{#each rows as e, i (e.id)}
				<li in:arrive={{ delay: 40 + Math.min(i, 8) * 18 }}>
					<button class:flash={flashId === e.id} aria-pressed={row?.id === e.id} onclick={() => (elementId = e.id)}>
						<span class="n">{e.element_order}</span>
						<span class="name"><b use:elementTip={describeElement(e.element_code_raw, e.info_flag)}>{e.element_code_raw}</b><small>{GROUP[e.element_group]}</small></span>
						<span class="pts" class:loss={e.goe < 0}>{fmt(e.panel_element_score)}</span>
					</button>
				</li>
			{/each}
		</ol>

		{#if row}
			<article class="detail" class:has-model={motion?.asset}>
				<div class="head" aria-live="polite">
					<div class="stack">
						{#key row.id}
							<div in:arrive out:leave>
								<p class="code">{row.element_code_raw}</p>
								<h3>{info.name}</h3>
								<p class="sub">{GROUP[row.element_group]}, element {row.element_order} of {rows.length}{info.notes.length ? `. ${info.notes.join('. ')}` : ''}.</p>
							</div>
						{/key}
					</div>

					<div class="sum" aria-label="Score">
						<div><span>Base value</span><b>{fmt(base.current)}</b></div>
						<i aria-hidden="true">{row.goe < 0 ? '−' : '+'}</i>
						<div><span>Judges</span><b class:gain={row.goe > 0} class:loss={row.goe < 0}>{fmt(goe.current)}</b></div>
						<i aria-hidden="true">=</i>
						<div class="final"><span>Score</span><b>{fmt(score.current)}</b></div>
					</div>
				</div>

				{#if motion?.asset}
					<figure class="model">
						<SkaterStage id={motion.asset.id} loop={loopOf(motion.asset)} spot bg="161617" label={`3D model of ${describeElement(motion.asset.id).name}, looping.`} />
						<figcaption>
							<span>3D model of {motion.asset.id}</span>
							<button class="link" onclick={() => onPlay(motion.asset)}>Open the player</button>
						</figcaption>
					</figure>
				{/if}

				<div class="rest">
					<div class="judges">
						<p>Nine judges’ grades, from −5 to +5. The panel drops the highest and the lowest, then averages the rest.</p>
						<ol aria-label="Grades from judges 1 to 9">
							{#each judges as g, i (i)}<li class:plus={g > 0} class:minus={g < 0} style:--i={i} title={`Judge ${i + 1}`}>{g > 0 ? `+${g}` : g}</li>{/each}
						</ol>
					</div>

					{#each marks as { mark } (mark)}
						<p class="mark" transition:grow><b>{MARKS[mark].label} ({mark}).</b> {MARKS[mark].meaning}.</p>
					{/each}
				</div>
			</article>
		{/if}
	</div>

	{#if program}
		<p class="math">All element scores add up to <b>{fmt(program.TES)}</b>. Program components add <b>{fmt(program.PCS_factored)}</b>{program.deductions ? `, deductions take away ${fmt(Math.abs(program.deductions))}` : ''}. Total: <b>{fmt(program.segment_score_TSS)}</b>.</p>
	{/if}

	<div class="matrix">
		<h3>What the officials marked</h3>
		<p>Protocol marks flag details such as an under-rotation, a wrong edge or a second-half bonus. Select a row to see that element’s score above.</p>
		<ProtocolMatrix elements={rows} selectedId={row?.id} onSelect={(id) => (elementId = id)} />
	</div>
</section>

<style>
	.reader { padding:clamp(6rem, 16vh, 10rem) clamp(1rem, 4vw, 2rem) clamp(4rem, 10vh, 6rem); max-width:1240px; margin:0 auto; scroll-margin-top:52px; }
	.intro { text-align:center; max-width:46rem; margin:0 auto 2.25rem; }
	h2 { margin:0 0 1rem; font:700 clamp(2.5rem, 5.6vw, 4.5rem)/1.04 var(--display); letter-spacing:-.04em; }
	.intro p { margin:0; color:var(--muted); font-size:clamp(1.1rem, 1.6vw, 1.32rem); line-height:1.42; font-weight:500; }

	.controls { display:flex; flex-wrap:wrap; align-items:end; justify-content:center; gap:1rem 1.5rem; margin-bottom:1.5rem; }
	.who { display:grid; gap:.4rem; min-width:min(100%, 300px); color:var(--muted); font-size:.85rem; }
	.segmented { display:flex; padding:4px; gap:2px; background:var(--card-strong); border-radius:980px; }
	.segmented button { border:0; background:transparent; color:var(--muted); padding:.55rem 1.15rem; border-radius:980px; font-size:.94rem; font-weight:500; cursor:pointer; min-height:40px; transition:color var(--dur) var(--ease); }
	.segmented button:hover { color:var(--ink); }
	.segmented button[aria-pressed=true] { color:#1d1d1f; }
	.total { margin:0; display:grid; text-align:right; }
	.total span { color:var(--muted); font-size:.85rem; }
	.total b { font:700 2rem/1 var(--display); letter-spacing:-.03em; }

	.grid { display:grid; grid-template-columns:minmax(260px, .9fr) minmax(0, 1.6fr); gap:clamp(.75rem, 2vw, 1.25rem); align-items:start; }
	.order-list { list-style:none; margin:0; padding:.5rem; background:var(--card); border-radius:28px; }
	.order-list button { width:100%; display:grid; grid-template-columns:1.6rem 1fr auto; align-items:center; gap:.75rem; padding:.7rem .9rem; border:0; border-radius:16px; background:transparent; color:var(--ink); text-align:left; cursor:pointer; min-height:52px; transition:background-color var(--dur-fast) var(--ease); }
	.order-list button:hover { background:#ffffff0d; }
	.order-list button:active { background:#ffffff17; transition-duration:60ms; }
	/* Arrived here from a dot or a chart: the chosen row glows once. */
	.order-list button.flash { animation:arrive-glow 1.4s var(--ease-out); }
	@keyframes arrive-glow { 0% { box-shadow:0 0 0 0 #64d2ff00; } 25% { box-shadow:0 0 0 3px #64d2ffaa; } 100% { box-shadow:0 0 0 0 #64d2ff00; } }
	.order-list button[aria-pressed=true] { background:var(--chosen); }
	.n { color:var(--faint); font-size:.85rem; }
	.name b { display:block; font-weight:600; font-size:1rem; }
	.name small { color:var(--muted); font-size:.8rem; }
	.pts { font-weight:600; }
	.pts.loss { color:var(--loss); }

	.detail { padding:clamp(1.5rem, 3vw, 2.5rem); background:var(--card); border-radius:28px; position:sticky; top:64px; display:grid; grid-template-columns:minmax(0, 1fr); column-gap:1.25rem; }
	.detail.has-model { grid-template-columns:minmax(0, 1fr) clamp(180px, 36%, 290px); grid-template-areas:'head model' 'rest rest'; }
	.has-model .head { grid-area:head; }
	.has-model .rest { grid-area:rest; }
	.model { grid-area:model; margin:-.75rem -.75rem 1rem 0; display:grid; grid-template-rows:auto auto; }
	.model :global(.stage) { aspect-ratio:1; height:auto; }
	.model figcaption { display:flex; justify-content:center; align-items:baseline; gap:.6rem; margin-top:-.4rem; font-size:.8rem; color:var(--faint); }
	.link { border:0; background:none; padding:.4rem 0; color:var(--blue); font-size:.84rem; cursor:pointer; }
	.link:hover { text-decoration:underline; }
	.has-model .sum b { font-size:clamp(1.55rem, 2.3vw, 2.1rem); }
	.has-model .sum .final b { font-size:clamp(2rem, 3.1vw, 2.75rem); }
	.code { margin:0; color:var(--ice); font-weight:600; font-size:1.05rem; }
	h3 { margin:.1rem 0 .4rem; font:700 clamp(1.8rem, 3vw, 2.6rem)/1.06 var(--display); letter-spacing:-.035em; }
	.sub { margin:0 0 1.75rem; color:var(--muted); line-height:1.5; }
	.sum { display:flex; align-items:end; flex-wrap:wrap; gap:.4rem 1rem; margin-bottom:1.75rem; }
	.sum div { display:grid; gap:.15rem; }
	.sum span { color:var(--muted); font-size:.8rem; }
	.sum b { font:600 clamp(1.8rem, 3vw, 2.4rem)/1 var(--display); letter-spacing:-.03em; }
	.sum i { font-style:normal; font-size:1.8rem; color:var(--faint); line-height:1.1; }
	.sum .final b { font-weight:700; font-size:clamp(2.4rem, 4vw, 3.2rem); }
	.gain { color:var(--gain); }
	.loss { color:var(--loss); }

	.judges p { margin:0 0 .6rem; color:var(--muted); font-size:.88rem; line-height:1.5; }
	.judges ol { list-style:none; margin:0 0 1.5rem; padding:0; display:grid; grid-template-columns:repeat(9, minmax(0, 1fr)); gap:.35rem; max-width:460px; }
	.judges li { display:grid; place-items:center; aspect-ratio:1; border-radius:12px; background:var(--card-strong); font-weight:600; font-size:1rem; transition:background-color var(--dur) var(--ease) calc(var(--i) * 15ms), color var(--dur) var(--ease) calc(var(--i) * 15ms); }
	.judges li.plus { background:#0c2633; color:var(--gain); }
	.judges li.minus { background:#33100e; color:var(--loss); }
	.mark { margin:0 0 .75rem; padding:.8rem 1rem; border-radius:14px; background:var(--loss-bg); color:var(--loss-ink); font-size:.9rem; line-height:1.5; }

	.math { margin:1.5rem auto 0; max-width:46rem; text-align:center; color:var(--muted); line-height:1.5; }
	.math b { color:var(--ink); }
	.matrix { margin-top:clamp(3rem, 8vh, 5rem); padding:clamp(1.5rem, 3vw, 2.5rem); background:var(--card); border-radius:28px; }
	.matrix h3 { font-size:clamp(1.5rem, 2.4vw, 2rem); }
	.matrix > p { margin:0 0 1.5rem; color:var(--muted); max-width:44rem; line-height:1.5; }

	@media (max-width: 900px) {
		.grid { grid-template-columns:1fr; }
		.detail { position:static; }
		.detail.has-model { grid-template-columns:minmax(0, 1fr); grid-template-areas:'model' 'head' 'rest'; }
		.model { margin:-.5rem 0 .75rem; }
		.model :global(.stage) { aspect-ratio:16 / 11; }
		.controls { display:grid; justify-items:center; }
		.total { text-align:center; }
		.matrix { overflow-x:auto; }
	}
</style>
