<script>
	import { onMount, tick } from 'svelte';
	import JumpScrub from './JumpScrub.svelte';
	import JumpCompare from './JumpCompare.svelte';
	import MoveLibrary from './MoveLibrary.svelte';
	import ScoreCharts from './ScoreCharts.svelte';
	import ProgramReader from './ProgramReader.svelte';
	import ScoreStory from '../ScoreStory.svelte';
	import ElementPrimer from '../ElementPrimer.svelte';
	import MotionOverlay from '../MotionOverlay.svelte';
	import { CHARACTERS, bestCleanJump, skaterRoster, storyFacts } from '../data/story-facts.mjs';
	import { resolveMotion } from '../data/motion-reference.mjs';

	// The whole project on one page: the jump, all 190 elements, the codes, the 3D library,
	// the charts and one program at a time.
	let { data = null, catalog = null, onStep = () => {} } = $props();

	let elements = $derived(data?.elements ?? []);
	let segments = $derived(data?.segments ?? []);
	let byId = $derived(new Map(elements.map((e) => [e.id, e])));
	let facts = $derived(storyFacts(elements, segments));

	// The program read in "Read one program"; dots and charts elsewhere on the page can choose it.
	// It starts on the opening skater's best clean jump, and follows whoever the reader picks there.
	let rank = $state(1);
	let segment = $state('FS');
	let elementId = $state(null);
	let skater = $derived(segments.find((s) => s.final_rank === rank)?.skater ?? '');
	let overlay = $state(null);

	// The opening: the reader's chosen skater (the gold medallist until they pick) and that skater's best clean jump.
	let roster = $derived(skaterRoster(segments));
	let pickedSkater = $state('');
	let openingSkater = $derived(pickedSkater || roster[0]?.skater || '');
	let openingJump = $derived(bestCleanJump(elements, openingSkater));
	let openingAsset = $derived(resolveMotion(catalog, openingJump)?.asset ?? null);
	// Picking a skater also opens their program, with the same jump selected, in "Read one program".
	function pickSkater(name) {
		pickedSkater = name;
		const jump = bestCleanJump(elements, name);
		if (!jump) return;
		rank = jump.final_rank;
		segment = jump.segment;
		elementId = jump.id;
	}
	$effect(() => { if (elementId === null && openingJump) pickSkater(openingJump.skater); });
	// Counts arrivals in "Read one program" from a dot or a chart, so the chosen element can greet the reader.
	let arrival = $state(0);

	async function read(id) {
		const row = byId.get(id);
		if (!row) return;
		rank = row.final_rank;
		segment = row.segment;
		elementId = row.id;
		await tick();
		document.getElementById('program')?.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
		arrival += 1;
	}

	const LINKS = [
		{ id: 'top', label: 'The jump' },
		{ id: 'all', label: 'All 190' },
		{ id: 'codes', label: 'The codes' },
		{ id: 'moves', label: '3D library' },
		{ id: 'scores', label: 'Scores' },
		{ id: 'program', label: 'One program' }
	];
	let active = $state('top');
	let menuOpen = $state(false);
	let nav = $state();
	let menuButton = $state();
	// The phone menu closes with Escape or a tap anywhere else, and gives focus back to its button.
	function closeMenu(event) {
		if (!menuOpen) return;
		if (event.type === 'keydown') { if (event.key !== 'Escape') return; menuButton?.focus(); }
		else if (nav?.contains(event.target)) return;
		menuOpen = false;
	}
	onMount(() => {
		const observer = new IntersectionObserver((entries) => {
			for (const entry of entries) if (entry.isIntersecting) active = entry.target.id;
		}, { rootMargin: '-45% 0px -50% 0px' });
		for (const { id } of LINKS) { const node = document.getElementById(id); if (node) observer.observe(node); }
		return () => observer.disconnect();
	});
</script>

<svelte:window onkeydown={closeMenu} onpointerdown={closeMenu} />

<nav class="localnav" aria-label="Sections" bind:this={nav}>
	<a class="title" href="#top" onclick={() => (menuOpen = false)}>Inside the Program</a>
	<button class="menu" bind:this={menuButton} aria-expanded={menuOpen} aria-controls="localnav-links" aria-label="Sections" onclick={() => (menuOpen = !menuOpen)}>
		<svg viewBox="0 0 12 8" aria-hidden="true"><path d="M1 1.5l5 5 5-5" /></svg>
	</button>
	<ul id="localnav-links" class="links" class:open={menuOpen}>
		{#each LINKS as link (link.id)}
			<li><a href={`#${link.id}`} aria-current={active === link.id ? 'location' : undefined} onclick={() => (menuOpen = false)}>{link.label}</a></li>
		{/each}
	</ul>
	<a class="pill press" href="#moves">Watch in 3D</a>
</nav>

<div id="top">
	<JumpScrub {roster} skater={openingSkater} jump={openingJump} asset={openingAsset} onPick={pickSkater} />
</div>

<JumpCompare uno={byId.get(CHARACTERS.unoFree)} brown={byId.get(CHARACTERS.brownFree)} />

<section id="all" class="chapter" aria-labelledby="all-heading">
	<div class="lead">
		<h2 id="all-heading">Now look at all {facts.elements}.</h2>
		<p>Uno and Brown are two dots. Here are the other {facts.elements - 2}: every element the top ten skated in Beijing, from the official score sheets.</p>
	</div>
	<ScoreStory {elements} {segments} onOpen={read} />
</section>

<section id="codes" class="chapter boxed" aria-labelledby="codes-heading">
	<div class="lead">
		<h2 id="codes-heading">Learn to read a score sheet.</h2>
	</div>
	<ElementPrimer {elements} />
</section>

<MoveLibrary {catalog} {elements} onPlay={(asset) => (overlay = asset)} onBrowse={() => onStep('movement')} />

<ScoreCharts {elements} {segments} {skater} {segment} selectedId={elementId} onSelect={read} />

<ProgramReader {segments} {elements} {catalog} {arrival} bind:rank bind:segment bind:elementId onPlay={(asset) => (overlay = asset)} />

<section class="takeaway" aria-labelledby="takeaway-heading">
	<h2 id="takeaway-heading">Difficulty sets the ceiling.<br /><span>Execution decides how much of it you keep.</span></h2>
	<p>{facts.gained} of {facts.elements} elements gained points from the judges. But {facts.quadsLost} of {facts.quads} quad jumps lost points, and in {facts.upsets.toLocaleString('en')} of {facts.pairs.toLocaleString('en')} pairs of jumps, the easier jump scored more.</p>
</section>

<footer class="colophon">
	<div class="cols">
		<div>
			<h3>Data and scope</h3>
			<p>ISU score sheets for the Beijing 2022 men’s singles top ten. The data covers {facts.programs} programs and {facts.elements} scored elements.</p>
			<p>Quad counts include combinations that start with a quad, such as 4T+3T.</p>
		</div>
		<div>
			<h3>Sources</h3>
			<ul>
				<li><a href="https://results.isu.org/results/season2122/owg2022/CAT001RS.htm" target="_blank" rel="noreferrer">Final standings (ISU)</a></li>
				<li><a href="https://www.isuresults.com/results/season2122/owg2022/owg2022_protocol.pdf" target="_blank" rel="noreferrer">Official score sheets, PDF</a></li>
				<li><a href="https://github.com/billchenziang33/csc316-inside-figure-skating-program" target="_blank" rel="noreferrer">Project source code</a></li>
			</ul>
			<button class="link" onclick={() => onStep('elements')}>Open the step-by-step version</button>
		</div>
	</div>
	<p class="credit">By Bill Chen, Cindy Liu and Liam Li. CSC316, University of Toronto.</p>
</footer>

{#if overlay}<MotionOverlay motion={overlay} onClose={() => (overlay = null)} />{/if}

<style>
	.localnav { position:sticky; top:0; z-index:20; height:52px; display:flex; align-items:center; gap:1.5rem; padding:0 max(1rem, calc((100vw - 1240px) / 2 + 1rem)); background:#000000b8; border-bottom:1px solid #ffffff1f; backdrop-filter:saturate(180%) blur(20px); -webkit-backdrop-filter:saturate(180%) blur(20px); margin-bottom:-52px; }
	.title { color:var(--ink); font:600 1.3rem var(--display); letter-spacing:-.02em; white-space:nowrap; }
	.title:hover { text-decoration:none; }
	.links { display:flex; gap:1.4rem; list-style:none; margin:0 0 0 auto; padding:0; }
	.links a { color:var(--muted); font-size:.75rem; letter-spacing:-.01em; white-space:nowrap; transition:color var(--dur) var(--ease); }
	.links a:hover { color:var(--ink); text-decoration:none; }
	.links a[aria-current] { color:var(--ink); }
	.pill { padding:.3rem .8rem; border-radius:980px; background:var(--button); color:#fff; font-size:.75rem; white-space:nowrap; transition:background-color var(--dur-fast) var(--ease), transform var(--dur-fast) var(--ease); }
	.pill:hover { background:#0077ed; text-decoration:none; }
	.menu { display:none; margin-left:auto; width:36px; height:36px; border:0; background:none; cursor:pointer; padding:0; }
	.menu svg { width:12px; fill:none; stroke:var(--ink); stroke-width:1.6; transition:transform var(--dur) var(--ease); }
	.menu[aria-expanded=true] svg { transform:rotate(180deg); }

	.chapter { scroll-margin-top:52px; }
	.lead { text-align:center; max-width:46rem; margin:0 auto; padding:clamp(6rem, 16vh, 10rem) clamp(1rem, 4vw, 2rem) clamp(1rem, 4vh, 2rem); }
	.lead h2 { margin:0 0 1rem; font:700 clamp(2.5rem, 5.6vw, 4.5rem)/1.04 var(--display); letter-spacing:-.04em; }
	.lead p { margin:0; color:var(--muted); font-size:clamp(1.1rem, 1.6vw, 1.32rem); line-height:1.42; font-weight:500; }
	.boxed { max-width:1240px; margin:0 auto; padding:0 clamp(1rem, 4vw, 2rem); }
	.boxed .lead { padding-bottom:2.25rem; }

	.takeaway { max-width:1000px; margin:0 auto; padding:clamp(8rem, 24vh, 14rem) clamp(1rem, 4vw, 2rem); text-align:center; }
	.takeaway h2 { margin:0 0 2rem; font:700 clamp(2.6rem, 6.4vw, 5.5rem)/1.04 var(--display); letter-spacing:-.045em; }
	.takeaway h2 span { color:var(--muted); }
	.takeaway p { margin:0 auto; max-width:40rem; color:var(--muted); font-size:clamp(1.05rem, 1.5vw, 1.25rem); line-height:1.5; }

	.colophon { display:block; max-width:1240px; margin:0 auto; padding:2.5rem clamp(1rem, 4vw, 2rem) 3rem; border-top:1px solid var(--line); color:var(--muted); font-size:.8rem; line-height:1.6; }
	.cols { display:grid; grid-template-columns:2fr 1fr; gap:2rem 4rem; }
	.colophon h3 { margin:0 0 .5rem; color:var(--ink); font-size:.85rem; font-weight:600; }
	.colophon p { margin:0 0 .9rem; max-width:44rem; }
	.colophon ul { list-style:none; padding:0; display:grid; gap:.4rem; margin:0 0 1.5rem; }
	.colophon ul a { color:var(--blue); font-size:.8rem; }
	.link { border:0; background:none; padding:0; color:var(--blue); font:inherit; cursor:pointer; text-underline-offset:3px; }
	.link:hover { text-decoration:underline; }
	.credit { margin-top:1.5rem !important; padding-top:1rem; border-top:1px solid var(--line); }

	@media (max-width: 900px) {
		.localnav { gap:.75rem; }
		.title { font-size:1.1rem; }
		.menu { display:grid; place-items:center; }
		/* The menu drops down from under the bar; its links follow a beat later, top to bottom. */
		.links { display:flex; position:absolute; top:52px; left:0; right:0; flex-direction:column; gap:0; padding:.5rem 1.25rem 1.25rem; background:#000000f2; border-bottom:1px solid #ffffff1f;
			opacity:0; visibility:hidden; transform:translateY(-8px); transition:opacity var(--dur-fast) var(--ease-in), transform var(--dur-fast) var(--ease-in), visibility 0s var(--dur-fast); }
		.links.open { opacity:1; visibility:visible; transform:none; transition:opacity var(--dur) var(--ease-out), transform var(--dur) var(--ease-out), visibility 0s; }
		.links li { opacity:0; transform:translateY(-4px); transition:opacity var(--dur-fast) var(--ease-in), transform var(--dur-fast) var(--ease-in); }
		.links.open li { opacity:1; transform:none; transition:opacity var(--dur) var(--ease-out), transform var(--dur) var(--ease-out); }
		.links.open li:nth-child(2) { transition-delay:25ms; } .links.open li:nth-child(3) { transition-delay:50ms; } .links.open li:nth-child(4) { transition-delay:75ms; } .links.open li:nth-child(5) { transition-delay:100ms; } .links.open li:nth-child(6) { transition-delay:125ms; }
		.links a { display:block; padding:.85rem 0; font-size:1.05rem; border-bottom:1px solid #ffffff14; }
		.cols { grid-template-columns:1fr; }
	}
</style>
