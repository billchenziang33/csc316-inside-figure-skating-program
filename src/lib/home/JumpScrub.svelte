<script>
	import { onMount } from 'svelte';
	import SkaterStage from '../SkaterStage.svelte';
	import { describeElement } from '../data/element-glossary.mjs';
	import { jumpRotations } from '../data/story-facts.mjs';

	// The opening: the reader picks a skater, then scrolls to play that skater's best clean jump.
	// `jump` is the official protocol row; `asset` is its 3D model entry from the movement catalog.
	let { roster = [], skater = '', jump = null, asset = null, onPick = () => {} } = $props();

	const fmt = (n) => (n ?? 0).toFixed(2);
	const signed = (n) => `${n < 0 ? '−' : '+'}${fmt(Math.abs(n ?? 0))}`;
	const PROGRAM = { SP: 'short program', FS: 'free skate' };
	const ORDINAL = ['', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth', 'thirteenth'];

	let modelId = $derived(asset?.id ?? jump?.element_code_raw ?? '4F');
	let name = $derived(describeElement(jump?.element_code_raw ?? '').name);
	let parts = $derived(jumpRotations(jump?.element_code_raw ?? ''));
	let totalTurns = $derived(parts.reduce((sum, n) => sum + n, 0));
	let isCombo = $derived(parts.length > 1);
	let bonus = $derived(String(jump?.info_flag ?? '').includes('x'));
	let surname = $derived(skater.split(' ').at(-1));
	// "A quad flip" / "A quad toe loop + single Euler + triple Salchow combination": lower case after the
	// article, except jumps named after skaters (Axel, Salchow, Lutz, Euler).
	const lower = (text) => text.replace(/\b(?!Axel|Salchow|Lutz|Euler)[A-Z][a-z]*/g, (word) => word.toLowerCase());
	let phrase = $derived(isCombo ? `${lower(name)} combination` : lower(name));
	let article = $derived(/^[aeiou]/i.test(phrase) ? 'an' : 'a');

	// Take-off and landing frames of the model; a combination spans its first take-off to its last landing.
	let flights = $derived.by(() => {
		const events = Object.entries(asset?.event_frames ?? {});
		const at = (prefix) => events.filter(([k]) => k.startsWith(prefix)).map(([, v]) => Number(v)).sort((a, b) => a - b);
		const takeoffs = at('TAKEOFF');
		const landings = at('LANDING');
		return takeoffs.length && landings.length ? { takeoffs, landings } : { takeoffs: [166], landings: [209] };
	});

	// Scroll progress → Blender frame. The flight gets the most scroll, so each turn can be followed.
	let keys = $derived.by(() => {
		const t = flights.takeoffs[0];
		const l = flights.landings.at(-1);
		const last = asset?.frames ?? l + 60;
		const clamp = (f) => Math.max(1, Math.min(last, f));
		return [[0, clamp(t - 54)], [0.1, clamp(t - 46)], [0.3, clamp(t - 6)], [0.64, clamp(l + 3)], [0.82, clamp(l + 27)], [1, clamp(l + 43)]];
	});
	function frameAt(p) {
		for (let i = 1; i < keys.length; i++) {
			const [p1, f1] = keys[i];
			const [p0, f0] = keys[i - 1];
			if (p <= p1) return f0 + ((p - p0) / (p1 - p0)) * (f1 - f0);
		}
		return keys.at(-1)[1];
	}

	let section = $state();
	// One smoothed progress drives everything here (the 3D frame, the zoom, the captions, the counter),
	// so a mouse-wheel step glides instead of jumping and all of them stay in step with each other.
	let progress = $state(0);
	let frame = $derived(frameAt(progress));
	let segmentTurns = $state(0);
	let ready = $state(false);
	// A new jump means a new model: wait for it before showing the turn counter again.
	$effect(() => { modelId; ready = false; segmentTurns = 0; });

	// The player counts turns within one jump of a combination. Add the jumps already landed.
	let turns = $derived.by(() => {
		const index = flights.takeoffs.filter((t) => t <= frame).length - 1;
		if (index < 0) return 0;
		const before = parts.slice(0, index).reduce((sum, n) => sum + n, 0);
		return Math.min(totalTurns || 4, before + Math.max(0, segmentTurns));
	});

	onMount(() => {
		const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
		let target = 0;
		let raf = 0;
		let last = 0;
		const step = (now) => {
			// Frame-rate independent easing toward the scroll position (about 90 ms to cover two thirds).
			const dt = last ? Math.min(64, now - last) : 16;
			last = now;
			const next = reduce ? target : progress + (target - progress) * (1 - Math.exp(-dt / 90));
			progress = Math.abs(target - next) < 0.0004 ? target : next;
			if (progress === target) { raf = 0; last = 0; } else raf = requestAnimationFrame(step);
		};
		const measure = () => {
			const box = section.getBoundingClientRect();
			target = Math.min(1, Math.max(0, -box.top / Math.max(1, box.height - innerHeight)));
			if (!raf) raf = requestAnimationFrame(step);
		};
		measure();
		addEventListener('scroll', measure, { passive: true });
		addEventListener('resize', measure);
		return () => { cancelAnimationFrame(raf); removeEventListener('scroll', measure); removeEventListener('resize', measure); };
	});

	// Choosing a skater glides the page to the first caption, so the reader sees what they picked.
	function pick(name) {
		onPick(name);
		const box = section.getBoundingClientRect();
		const top = scrollY + box.top + 0.15 * Math.max(1, box.height - innerHeight);
		scrollTo({ top, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
	}

	// How visible a caption is for a window of the scroll progress.
	function shown(from, to, fade = 0.035) {
		if (progress < from - fade || progress > to + fade) return 0;
		if (progress < from) return (progress - from + fade) / fade;
		if (progress > to) return (to + fade - progress) / fade;
		return 1;
	}
	let counter = $derived(ready ? shown(0.3, 0.64, 0.025) : 0);
	// A caption fades and rises with the scroll; hidden ones leave the accessibility tree.
	const veil = (o) => `opacity:${o};transform:translateY(${(1 - o) * 18}px);visibility:${o > 0 ? 'visible' : 'hidden'}`;
	let heroOpacity = $derived(shown(-1, 0.07, 0.06));

	// The model starts small under the picker, grows to fill the stage, then steps back for the score table.
	const ease = (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));
	let place = $derived.by(() => {
		const grow = ease(progress / 0.11);
		const back = ease((progress - 0.64) / 0.08);
		const lift = 50 * (1 - grow) - 9 * back;
		const scale = 0.5 + 0.5 * grow - 0.24 * back;
		return `translateY(${lift}vh) scale(${scale})`;
	});
	let ring = $derived(Math.min(1, Math.max(0, turns) / (totalTurns || 4)));
</script>

<section class="scrub" bind:this={section} aria-labelledby="stage-heading">
	<div class="pin">
		<div class="stage" style:transform={place}>
			<SkaterStage id={modelId} view="angled" preload {frame} onReady={() => (ready = true)} label={`A 3D model of ${article} ${phrase}. Scrolling plays the jump from the approach to the landing.`} onFrame={(m) => { segmentTurns = m.turns ?? 0; }} />
		</div>
		<div class="shade" aria-hidden="true"></div>

		<header class="hero" style={veil(heroOpacity)} style:transform={`translateY(${(-progress * 220).toFixed(1)}px)`}>
			<p class="eyebrow">Beijing 2022. Men’s singles. The final top ten.</p>
			<h1 id="stage-heading" tabindex="-1">What turns a skating move into points?</h1>
			<p class="hero-sub">Pick a skater, then scroll to watch their best clean jump.</p>
			<div class="roster" role="group" aria-label="Choose a skater">
				{#each roster as entry (entry.skater)}
					<button class="press" aria-pressed={entry.skater === skater} onclick={() => pick(entry.skater)}>
						<span class="rank">{entry.rank}</span>
						<span class="who">{entry.skater}</span>
						<span class="noc">{entry.NOC}</span>
					</button>
				{/each}
			</div>
		</header>

		<div class="counter" style:opacity={counter} aria-hidden="true">
			<svg viewBox="0 0 120 120"><circle class="track" cx="60" cy="60" r="54" /><circle class="fill" cx="60" cy="60" r="54" style:stroke-dashoffset={339.3 * (1 - ring)} /></svg>
			<b>{Math.max(0, turns).toFixed(1)}</b>
			<span>turns in the air</span>
		</div>

		{#if jump}
		<div class="captions">
			<div class="caption" style={veil(shown(0.13, 0.27, 0.025))}>
				<p class="tag">{skater} · {PROGRAM[jump.segment]}, {ORDINAL[jump.element_order] ?? `#${jump.element_order}`} element</p>
				{#if isCombo}
					<h2>This is a {['', '', 'two', 'three'][parts.length] ?? parts.length}-jump combination.</h2>
					<p class="names">{name.split(' + ').map(lower).join(', then ').replace(/^./, (c) => c.toUpperCase())}, with no step in between.</p>
				{:else}
					<h2>This is {article} {phrase}.</h2>
				{/if}
				<p>Before {surname} leaves the ice, it is already worth <b>{fmt(jump.base_value)}</b> points. That is its base value, fixed by the rules{#if bonus}, plus a 10% bonus for coming in the second half of the program{/if}.</p>
			</div>
			<div class="caption" style={veil(shown(0.33, 0.58, 0.025))}>
				<h2>{totalTurns} turns in the air{isCombo ? `, over ${parts.length} jumps` : ''}.</h2>
				<p>More turns mean a higher base value. Land a quarter turn short and the technical panel marks it, and the score drops. {surname} gets every turn around.</p>
			</div>
			<div class="caption" style={veil(shown(0.66, 1.2, 0.025))}>
				<h2>{skater} lands it cleanly,</h2>
				<p>earning a total score of <b>{fmt(jump.panel_element_score)}</b>.</p>
				<table class="receipt">
					<caption class="sr-only">{skater}’s {name}, {PROGRAM[jump.segment]}</caption>
					<thead><tr><th scope="col">Element</th><th scope="col">Base value</th><th scope="col">GOE</th><th scope="col">Score</th></tr></thead>
					<tbody>
						<tr><th scope="row">{jump.element_code_raw}</th><td>{fmt(jump.base_value)}</td><td class="gain">{signed(jump.goe)}</td><td>{fmt(jump.panel_element_score)}</td></tr>
					</tbody>
				</table>
			</div>
		</div>
		{/if}
		<p class="fineprint" style:opacity={shown(0.12, 1.2)}>3D model: a simulation of the technique, not a recording of {skater}.</p>
	</div>
</section>

<style>
	.scrub { position:relative; height:560vh; }
	.pin { position:sticky; top:0; height:100vh; height:100svh; overflow:hidden; }
	.stage { position:absolute; left:0; right:0; top:0; height:74%; transform-origin:50% 50%; will-change:transform;
		-webkit-mask-image:radial-gradient(ellipse 50% 50% at 50% 50%, #000 62%, transparent 100%); mask-image:radial-gradient(ellipse 50% 50% at 50% 50%, #000 62%, transparent 100%); }
	.shade { position:absolute; inset:0; pointer-events:none; background:linear-gradient(to bottom, #000 0%, transparent 16%); }

	.hero { position:absolute; inset:0 0 auto; padding:clamp(5rem, 12vh, 8rem) 1.5rem 0; text-align:center; will-change:transform, opacity; z-index:2; }
	/* The one orchestrated moment: on arrival the title lines rise in, one after another. */
	.hero > * { animation:hero-in 900ms var(--ease-out) both; }
	.hero > :nth-child(2) { animation-delay:90ms; }
	.hero > :nth-child(3) { animation-delay:180ms; }
	.hero > :nth-child(4) { animation-delay:270ms; }
	@keyframes hero-in { from { opacity:0; transform:translateY(14px); } }
	.eyebrow { margin:0 0 1rem; color:var(--muted); font-size:clamp(1rem, 1.6vw, 1.3rem); font-weight:600; letter-spacing:-.01em; }
	h1 { text-wrap:balance; margin:0 auto; max-width:13ch; font:700 clamp(2.8rem, 7vw, 6rem)/1.02 var(--display); letter-spacing:-.045em; color:var(--ink); }
	h1:focus { outline:none; }
	.hero-sub { margin:1.2rem auto 0; max-width:34rem; color:var(--muted); font-size:clamp(1.05rem, 1.7vw, 1.35rem); line-height:1.4; font-weight:500; }

	.roster { display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:.5rem; max-width:62rem; margin:1.6rem auto 0; }
	.roster button { display:grid; grid-template-columns:auto 1fr; grid-template-rows:auto auto; column-gap:.6rem; align-items:center; text-align:left; padding:.6rem .8rem; border:1px solid var(--line); border-radius:14px; background:#161617cc; color:var(--ink); font:inherit; cursor:pointer; backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); transition:background-color var(--dur-fast) var(--ease), border-color var(--dur-fast) var(--ease), transform var(--dur-fast) var(--ease); }
	.roster button:hover { background:#1d1d1fee; border-color:#4a4a4e; }
	.roster button:active { transform:scale(.97); }
	.roster button:focus-visible { outline:2px solid var(--blue); outline-offset:2px; }
	.roster button[aria-pressed=true] { background:var(--ink); color:#000; border-color:var(--ink); }
	.roster button[aria-pressed=true] .noc, .roster button[aria-pressed=true] .rank { color:#3a3a3c; }
	.rank { grid-row:1 / 3; font:700 1.3rem/1 var(--display); color:var(--faint); min-width:1.4em; text-align:center; }
	.who { font-size:.86rem; font-weight:600; line-height:1.2; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
	.noc { font-size:.7rem; color:var(--muted); letter-spacing:.04em; }

	.counter { position:absolute; right:clamp(1.5rem, 8vw, 9rem); top:50%; width:clamp(150px, 15vw, 210px); aspect-ratio:1; transform:translateY(-60%); display:grid; place-content:center; text-align:center; border-radius:50%; background:#000000a8; backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px); }
	.counter svg { position:absolute; inset:0; transform:rotate(-90deg); }
	.counter circle { fill:none; stroke-width:5; }
	.counter .track { stroke:#ffffff1f; }
	.counter .fill { stroke:var(--ice); stroke-linecap:round; stroke-dasharray:339.3; }
	.counter b { font:600 clamp(2.6rem, 4.4vw, 3.8rem)/1 var(--display); letter-spacing:-.03em; }
	.counter span { margin-top:.35rem; font-size:.8rem; color:var(--muted); }

	.captions { position:absolute; left:0; right:0; bottom:clamp(2.5rem, 9vh, 5.5rem); display:grid; padding:0 1.5rem; }
	.caption { grid-area:1 / 1; align-self:end; justify-self:center; max-width:52rem; text-align:center; will-change:opacity, transform; }
	.caption .tag { display:inline-block; margin:0 auto .7rem; padding:.3rem .8rem; border-radius:980px; background:#000000b8; backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); color:var(--ice); font-size:clamp(.85rem, 1.2vw, 1rem); font-weight:600; }
	.caption h2 { text-wrap:balance; margin:0 0 .6rem; font:700 clamp(2rem, 4.2vw, 3.5rem)/1.06 var(--display); letter-spacing:-.035em; }
	.caption p { margin:0 auto; max-width:34rem; color:var(--muted); font-size:clamp(1.02rem, 1.5vw, 1.3rem); line-height:1.42; font-weight:500; }
	.caption p.names { margin-bottom:.5rem; color:var(--ink); }
	.caption p b { color:var(--ink); font-weight:600; }
	.gain { color:var(--gain) !important; }

	.receipt { margin:1.4rem auto 0; border-collapse:collapse; font-size:clamp(.92rem, 1.3vw, 1.08rem); }
	.receipt th, .receipt td { padding:.55rem clamp(.6rem, 1.6vw, 1.3rem); text-align:right; border-bottom:1px solid var(--line); }
	.receipt thead th { color:var(--muted); font-weight:500; font-size:.82rem; }
	.receipt th[scope=row], .receipt thead th:first-child { text-align:left; font-weight:600; }
	.receipt td:last-child { font-weight:700; font-size:1.25em; }

	.fineprint { position:absolute; left:0; right:0; bottom:1rem; margin:0; text-align:center; color:var(--faint); font-size:.75rem; }

	@media (max-width: 900px) {
		.roster { grid-template-columns:repeat(2, minmax(0, 1fr)); max-width:30rem; gap:.4rem; }
		.roster button { padding:.45rem .6rem; }
		.rank { font-size:1.05rem; }
	}
	@media (max-width: 734px) {
		.hero { padding-top:4.5rem; }
		.hero-sub { margin-top:.8rem; }
		.roster { margin-top:1rem; }
		.stage { height:66%; }
		.counter { top:5.4rem; right:1rem; width:104px; transform:none; }
		.counter b { font-size:2rem; }
		.counter span { font-size:.68rem; }
		.captions { bottom:2.6rem; }
		.receipt thead th:nth-child(2), .receipt tbody td:nth-child(2) { display:none; }
	}
</style>
