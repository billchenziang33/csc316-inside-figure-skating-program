<script>
	import SkaterStage, { loopOf } from '../SkaterStage.svelte';
	import { describeElement } from '../data/element-glossary.mjs';
	import { slidingThumb } from '../thumb.mjs';
	import { arrive, leave } from '../motion.mjs';

	// The 3D movement library, inline: pick an element type and its model plays on the big screen.
	let { catalog = null, elements = [], onPlay = () => {}, onBrowse = () => {} } = $props();

	const KINDS = [
		{ key: 'jump', label: 'Jumps' },
		{ key: 'combination', label: 'Combinations' },
		{ key: 'spin', label: 'Spins' },
		{ key: 'sequence', label: 'Sequences' }
	];
	const fmt = (n) => n.toFixed(2);

	let kind = $state('jump');
	let picked = $state({ jump: '4F', combination: '4T+3T', spin: 'FCSp', sequence: 'StSq' });

	// Every performed element that uses each model.
	let uses = $derived.by(() => {
		const byId = new Map(elements.map((e) => [e.id, e]));
		const map = new Map();
		for (const [id, occurrence] of Object.entries(catalog?.occurrences ?? {})) {
			const row = byId.get(id);
			if (!row) continue;
			if (!map.has(occurrence.asset)) map.set(occurrence.asset, []);
			map.get(occurrence.asset).push(row);
		}
		return map;
	});
	let models = $derived(Object.values(catalog?.assets ?? {})
		.filter((asset) => asset.kind === kind)
		.map((asset) => ({ asset, rows: uses.get(asset.id) ?? [] }))
		.sort((a, b) => b.rows.length - a.rows.length || a.asset.id.localeCompare(b.asset.id)));
	let current = $derived(models.find((m) => m.asset.id === picked[kind]) ?? models[0]);
	let name = $derived(current ? describeElement(current.asset.id).name : '');
	let best = $derived(current?.rows.length ? current.rows.reduce((a, b) => (b.panel_element_score > a.panel_element_score ? b : a)) : null);
	let mean = $derived(current?.rows.length ? current.rows.reduce((s, r) => s + r.panel_element_score, 0) / current.rows.length : null);
	// The catalog note opens with the element's name, which the heading already shows.
	let about = $derived((current?.asset.note ?? '').split(/(?<=\.)\s+/).slice(1).filter((s) => !/simulated|motion capture/i.test(s)).slice(0, 2).join(' '));

</script>

<section class="library" id="moves" aria-labelledby="moves-heading">
	<div class="intro">
		<h2 id="moves-heading">Every element, in 3D.</h2>
		<p>We built a 3D model for each of the 50 element types the top ten performed. Choose one to watch it. Drag the picture to look from another side.</p>
	</div>

	<div class="tabs seg" role="tablist" aria-label="Kind of element" use:slidingThumb={kind}>
		{#each KINDS as k (k.key)}
			<button role="tab" aria-selected={kind === k.key} onclick={() => (kind = k.key)}>{k.label}</button>
		{/each}
	</div>

	{#if catalog && current}
		<div class="viewer">
			<div class="screen">
				<SkaterStage id={current.asset.id} loop={loopOf(current.asset)} interactive spot bg="161617" label={`3D model of ${name}, looping.`} />
			</div>
			<div class="info" aria-live="polite">
				<div class="stack">
					{#key current.asset.id}
						<div in:arrive out:leave>
							<p class="code">{current.asset.id}</p>
							<h3>{name}</h3>
							<p class="about">{about}</p>
							{#if current.rows.length}
								<dl>
									<div><dt>Done in Beijing</dt><dd>{current.rows.length}×</dd></div>
									<div><dt>Average score</dt><dd>{fmt(mean)}</dd></div>
									<div><dt>Best score</dt><dd>{fmt(best.panel_element_score)}</dd></div>
								</dl>
								<p class="best">Best: {best.skater}, {best.segment === 'SP' ? 'short program' : 'free skate'}.</p>
							{:else}
								<p class="best">Not done on its own in Beijing. It appears inside combinations.</p>
							{/if}
						</div>
					{/key}
				</div>
				<button class="secondary" onclick={() => onPlay(current.asset)}>Open the full player</button>
			</div>
		</div>

		<ul class="picker" aria-label={`${KINDS.find((k) => k.key === kind).label} with a 3D model`}>
			{#each models as m, i (m.asset.id)}
				<li in:arrive={{ delay: Math.min(i, 10) * 12, y: 4 }}>
					<button aria-pressed={m.asset.id === current.asset.id} onclick={() => (picked = { ...picked, [kind]: m.asset.id })}>
						<b>{m.asset.id}</b>{#if m.rows.length}<span>{m.rows.length}×</span>{/if}
					</button>
				</li>
			{/each}
		</ul>
		<p class="more"><button class="link" onclick={onBrowse}>Browse all 50 models in the full library</button></p>
	{:else}
		<p class="wait">Loading the 3D library…</p>
	{/if}
</section>

<style>
	.library { padding:clamp(6rem, 16vh, 10rem) clamp(1rem, 4vw, 2rem) clamp(4rem, 10vh, 6rem); max-width:1240px; margin:0 auto; scroll-margin-top:52px; }
	.intro { text-align:center; max-width:46rem; margin:0 auto 2.25rem; }
	h2 { margin:0 0 1rem; font:700 clamp(2.5rem, 5.6vw, 4.5rem)/1.04 var(--display); letter-spacing:-.04em; }
	.intro p { margin:0; color:var(--muted); font-size:clamp(1.1rem, 1.6vw, 1.32rem); line-height:1.42; font-weight:500; }

	.tabs { display:flex; width:max-content; max-width:100%; margin:0 auto 1.5rem; padding:4px; gap:2px; background:var(--card-strong); border-radius:980px; overflow-x:auto; }
	.tabs button { border:0; background:transparent; color:var(--muted); padding:.55rem 1.15rem; border-radius:980px; font-size:.94rem; font-weight:500; cursor:pointer; white-space:nowrap; min-height:40px; transition:color var(--dur) var(--ease); }
	.tabs button:hover { color:var(--ink); }
	.tabs button[aria-selected=true] { color:#1d1d1f; }

	.viewer { display:grid; grid-template-columns:minmax(0, 1.75fr) minmax(280px, 1fr); background:var(--card); border-radius:28px; overflow:hidden; }
	.screen { position:relative; min-height:clamp(340px, 52vh, 560px); }
	.info { padding:clamp(1.5rem, 3vw, 2.5rem); display:flex; flex-direction:column; align-items:flex-start; gap:.25rem; }
	.code { margin:0; color:var(--ice); font-size:1rem; font-weight:600; }
	h3 { margin:0 0 .5rem; font:700 clamp(1.7rem, 2.6vw, 2.3rem)/1.08 var(--display); letter-spacing:-.03em; }
	.about { margin:0 0 1.25rem; color:var(--muted); font-size:.98rem; line-height:1.5; }
	dl { margin:0 0 .5rem; display:grid; grid-template-columns:repeat(3, auto); gap:1.25rem; }
	dl div { display:grid; gap:.15rem; }
	dt { color:var(--muted); font-size:.78rem; }
	dd { margin:0; font:600 1.45rem var(--display); letter-spacing:-.02em; }
	.best { margin:0 0 1.5rem; color:var(--muted); font-size:.88rem; }
	.info .secondary { margin-top:auto; }

	.picker { list-style:none; margin:1.25rem 0 0; padding:0; display:flex; flex-wrap:wrap; justify-content:center; gap:.5rem; }
	.picker button { display:inline-flex; align-items:baseline; gap:.4rem; min-height:40px; padding:.45rem .95rem; border-radius:980px; border:1px solid var(--line); background:transparent; color:var(--ink); cursor:pointer; font-size:.94rem; transition:border-color var(--dur-fast) var(--ease), background-color var(--dur) var(--ease), color var(--dur) var(--ease), transform var(--dur-fast) var(--ease); }
	.picker button:active { transform:scale(.96); transition-duration:60ms; }
	.picker button:hover { border-color:var(--muted); }
	.picker button[aria-pressed=true] { background:var(--ink); color:#000; border-color:var(--ink); }
	.picker b { font-weight:600; }
	.picker span { font-size:.78rem; color:var(--muted); transition:color var(--dur) var(--ease); }
	.picker button[aria-pressed=true] span { color:#555; }
	.more { text-align:center; margin:1.75rem 0 0; }
	.link { border:0; background:none; color:var(--blue); font-size:1.05rem; cursor:pointer; padding:.5rem; text-underline-offset:3px; }
	.link:hover { text-decoration:underline; }
	.wait { text-align:center; color:var(--muted); }

	@media (max-width: 900px) {
		.tabs button { padding:.5rem .8rem; font-size:.88rem; }
		.viewer { grid-template-columns:1fr; }
		.screen { min-height:min(70vw, 420px); }
	}
</style>
