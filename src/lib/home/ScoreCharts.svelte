<script>
	import { arrive, leave, fitHeight } from '../motion.mjs';
	import { evidenceStory } from '../evidence-story.mjs';
	import { levelledElements } from '../data/derived.mjs';
	import BaseVsPanel from '../charts/BaseVsPanel.svelte';
	import RotationGoe from '../charts/RotationGoe.svelte';
	import JumpCounts from '../charts/JumpCounts.svelte';
	import SpinStepLevels from '../charts/SpinStepLevels.svelte';
	import ScoreComparison from '../charts/ScoreComparison.svelte';
	import { slidingThumb } from '../thumb.mjs';

	// The five scoring charts, one at a time, behind a segmented control.
	let { elements = [], segments = [], skater = '', segment = 'SP', selectedId = null, onSelect = () => {} } = $props();

	const NAMES = { S15: 'Base value and score', S02: 'Rotations', S01: 'Jump choices', S06: 'Spins and steps', S12: 'Program totals' };
	let chart = $state('S15');
	let story = $derived(evidenceStory.find((s) => s.chart === chart));
	let jumps = $derived(elements.filter((e) => e.element_group === 'jump'));
	let levelled = $derived(levelledElements(elements.filter((e) => e.segment === segment)));
	let programs = $derived(segments.filter((s) => s.skater === skater));
</script>

<section class="charts" id="scores" aria-labelledby="scores-heading">
	<div class="intro">
		<h2 id="scores-heading">The scores, side by side.</h2>
		<p>Five charts, each built from the official score sheets. Choose one.</p>
	</div>

	<div class="tabs seg" role="tablist" aria-label="Chart" use:slidingThumb={chart}>
		{#each evidenceStory as s (s.chart)}
			<button role="tab" aria-selected={chart === s.chart} onclick={() => (chart = s.chart)}>{NAMES[s.chart]}</button>
		{/each}
	</div>

	<div class="board">
		<div class="text stack" aria-live="polite" use:fitHeight>
			{#key chart}
				<div in:arrive out:leave>
					<h3>{story.title}</h3>
					<p>{story.body}</p>
					{#if chart === 'S12'}<p class="scope">Shown for {skater}. Pick another skater below in “Read one program”.</p>
					{:else if chart === 'S06'}<p class="scope">Shown for the {segment === 'SP' ? 'short program' : 'free skate'}, all ten skaters.</p>
					{:else if chart === 'S15'}<p class="scope">Click a dot to read that jump in “Read one program”.</p>{/if}
					<p class="note">{story.note}</p>
				</div>
			{/key}
		</div>
		<div class="canvas stack" use:fitHeight>
		{#key chart}
			<div in:arrive={{ delay: 80, duration: 320 }} out:leave>
				{#if chart === 'S15'}<BaseVsPanel elements={jumps} {selectedId} {onSelect} />
				{:else if chart === 'S02'}<RotationGoe {elements} />
				{:else if chart === 'S01'}<JumpCounts {elements} />
				{:else if chart === 'S06'}<SpinStepLevels elements={levelled} />
				{:else}<ScoreComparison segments={programs} />{/if}
			</div>
		{/key}
		</div>
	</div>
</section>

<style>
	.charts { padding:clamp(6rem, 16vh, 10rem) clamp(1rem, 4vw, 2rem) clamp(4rem, 10vh, 6rem); max-width:1240px; margin:0 auto; scroll-margin-top:52px; }
	.intro { text-align:center; max-width:46rem; margin:0 auto 2.25rem; }
	h2 { margin:0 0 1rem; font:700 clamp(2.5rem, 5.6vw, 4.5rem)/1.04 var(--display); letter-spacing:-.04em; }
	.intro p { margin:0; color:var(--muted); font-size:clamp(1.1rem, 1.6vw, 1.32rem); line-height:1.42; font-weight:500; }
	.tabs { display:flex; width:max-content; max-width:100%; margin:0 auto 1.5rem; padding:4px; gap:2px; background:var(--card-strong); border-radius:980px; overflow-x:auto; scrollbar-width:none; }
.tabs button { border:0; background:transparent; color:var(--muted); padding:.55rem 1.1rem; border-radius:980px; font-size:.94rem; font-weight:500; cursor:pointer; white-space:nowrap; min-height:40px; transition:color var(--dur) var(--ease); }
	.tabs button:hover { color:var(--ink); }
	.tabs button[aria-selected=true] { color:#1d1d1f; }
	.board { display:grid; grid-template-columns:minmax(260px, .8fr) minmax(0, 2fr); gap:clamp(1.25rem, 3vw, 2.5rem); padding:clamp(1.5rem, 3vw, 2.75rem); background:var(--card); border-radius:28px; }
	h3 { margin:0 0 .8rem; font:700 clamp(1.45rem, 2.2vw, 1.9rem)/1.12 var(--display); letter-spacing:-.03em; }
	.text { overflow:hidden; transition:height var(--dur-slow) var(--ease); }
	.text p { margin:0 0 1rem; color:var(--muted); line-height:1.55; }
	.text .scope { color:var(--ink); font-size:.92rem; }
	.text .note { font-size:.82rem; color:var(--faint); }
	.canvas { min-width:0; overflow-x:auto; overflow-y:hidden; transition:height var(--dur-slow) var(--ease); }
	@media (max-width: 900px) {
		.tabs button { padding:.5rem .8rem; font-size:.88rem; }
		.board { grid-template-columns:1fr; }
		.tabs { justify-content:flex-start; }
		.canvas > :global(* > *) { min-width:520px; }
	}
</style>
