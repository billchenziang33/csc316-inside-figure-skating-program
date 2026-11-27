<script>
	import SkaterStage from '../SkaterStage.svelte';

	// Uno's quad flip (fall) next to Brown's triple flip (clean), each with its 3D model looping.
	let { uno = null, brown = null } = $props();
	const fmt = (n) => (n ?? 0).toFixed(2);
	const signed = (n) => `${n < 0 ? '−' : '+'}${fmt(Math.abs(n ?? 0))}`;

	let cards = $derived([
		{ row: uno, model: '4F', loop: [150, 226], jump: 'Quad flip', who: 'Shoma Uno', how: 'Fell on the landing' },
		{ row: brown, model: '3F', loop: [150, 220], jump: 'Triple flip', who: 'Jason Brown', how: 'Landed cleanly' }
	]);
</script>

<section class="compare" aria-labelledby="compare-heading">
	<div class="intro">
		<h2 id="compare-heading">An easier jump can score more.</h2>
		<p>Jason Brown did not try a single quad in Beijing. His triple flip is worth less than half of Uno’s quad flip. In the free skate, it still earned more.</p>
	</div>

	<div class="pair">
		{#each cards as card (card.model)}
			<article>
				<div class="screen">
					<SkaterStage id={card.model} view="angled" preload spot bg="161617" loop={card.loop} label={`3D model of a ${card.jump.toLowerCase()}, looping.`} />
				</div>
				<div class="facts">
					<h3>{card.jump}</h3>
					<p class="who">{card.who}, free skate. {card.how}.</p>
					<dl>
						<div><dt>Base value</dt><dd>{fmt(card.row?.base_value)}</dd></div>
						<div><dt>Judges</dt><dd class:gain={card.row?.goe > 0} class:loss={card.row?.goe < 0}>{signed(card.row?.goe)}</dd></div>
						<div class="score"><dt>Score</dt><dd>{fmt(card.row?.panel_element_score)}</dd></div>
					</dl>
				</div>
			</article>
		{/each}
	</div>
	<p class="fineprint">3D technique simulations.</p>
</section>

<style>
	.compare { padding:clamp(6rem, 16vh, 10rem) clamp(1rem, 4vw, 2rem) clamp(4rem, 10vh, 6rem); max-width:1100px; margin:0 auto; }
	.intro { text-align:center; max-width:44rem; margin:0 auto clamp(2.5rem, 6vh, 4rem); }
	h2 { margin:0 0 1rem; font:700 clamp(2.5rem, 5.6vw, 4.5rem)/1.04 var(--display); letter-spacing:-.04em; }
	.intro p { margin:0; color:var(--muted); font-size:clamp(1.1rem, 1.6vw, 1.32rem); line-height:1.42; font-weight:500; }
	.pair { display:grid; grid-template-columns:1fr 1fr; gap:clamp(.75rem, 2vw, 1.25rem); }
	article { background:var(--card); border-radius:28px; overflow:hidden; display:flex; flex-direction:column; }
	.screen { aspect-ratio:4 / 3.4; position:relative; }
	.facts { padding:1.6rem clamp(1.25rem, 3vw, 2.25rem) 2rem; text-align:center; }
	h3 { margin:0; font:700 clamp(1.6rem, 2.6vw, 2.2rem)/1.1 var(--display); letter-spacing:-.03em; }
	.who { margin:.4rem 0 1.5rem; color:var(--muted); }
	dl { margin:0; display:grid; grid-template-columns:1fr 1fr 1fr; gap:.5rem; }
	dl div { display:grid; gap:.2rem; }
	dt { color:var(--muted); font-size:.82rem; }
	dd { margin:0; font:600 1.5rem/1.1 var(--display); letter-spacing:-.02em; }
	.score dd { font-size:2.4rem; font-weight:700; }
	.gain { color:var(--gain); }
	.loss { color:var(--loss); }
	.fineprint { margin:1.25rem 0 0; text-align:center; color:var(--faint); font-size:.8rem; }
	@media (max-width: 734px) {
		.pair { grid-template-columns:1fr; }
		.score dd { font-size:2rem; }
	}
</style>
