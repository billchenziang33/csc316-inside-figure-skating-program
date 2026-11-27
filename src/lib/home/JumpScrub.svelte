<script>
	import { onMount } from 'svelte';
	import SkaterStage from '../SkaterStage.svelte';

	// The opening: Uno's quad flip, played by the reader's scrolling.
	let { short = null, free = null } = $props();

	const fmt = (n) => (n ?? 0).toFixed(2);
	const signed = (n) => `${n < 0 ? '−' : '+'}${fmt(Math.abs(n))}`;

	// Scroll progress → Blender frame of the 4F model (take-off 166, landing 209).
	// The flight gets the most scroll, so each turn can be followed.
	const KEYS = [[0, 112], [0.1, 120], [0.3, 160], [0.64, 212], [0.82, 236], [1, 252]];
	function frameAt(p) {
		for (let i = 1; i < KEYS.length; i++) {
			const [p1, f1] = KEYS[i];
			const [p0, f0] = KEYS[i - 1];
			if (p <= p1) return f0 + ((p - p0) / (p1 - p0)) * (f1 - f0);
		}
		return KEYS.at(-1)[1];
	}

	let section = $state();
	// One smoothed progress drives everything here (the 3D frame, the zoom, the captions, the counter),
	// so a mouse-wheel step glides instead of jumping and all of them stay in step with each other.
	let progress = $state(0);
	let frame = $derived(frameAt(progress));
	let turns = $state(0);
	let ready = $state(false);

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

	// The model starts small under the title, grows to fill the stage, then steps back for the score table.
	const ease = (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));
	let place = $derived.by(() => {
		const grow = ease(progress / 0.11);
		const back = ease((progress - 0.82) / 0.06);
		const lift = 46 * (1 - grow) - 9 * back;
		const scale = 0.58 + 0.42 * grow - 0.2 * back;
		return `translateY(${lift}vh) scale(${scale})`;
	});
	let ring = $derived(Math.min(1, Math.max(0, turns) / 4));
</script>

<section class="scrub" bind:this={section} aria-labelledby="stage-heading">
	<div class="pin">
		<div class="stage" style:transform={place}>
			<SkaterStage id="4F" view="angled" preload {frame} onReady={() => (ready = true)} label="A 3D model of a quad flip. Scrolling plays the jump from the approach to the landing." onFrame={(m) => { turns = m.turns ?? 0; }} />
		</div>
		<div class="shade" aria-hidden="true"></div>

		<header class="hero" style:opacity={shown(-1, 0.07, 0.06)} style:transform={`translateY(${(-progress * 220).toFixed(1)}px)`}>
			<p class="eyebrow">Beijing 2022. Men’s singles. The final top ten.</p>
			<h1 id="stage-heading" tabindex="-1">What turns a skating move into points?</h1>
			<p class="hero-sub">Ten skaters. Twenty programs. 190 scored elements.<br />Scroll to watch one jump, then all of them.</p>
		</header>

		<div class="counter" style:opacity={counter} aria-hidden="true">
			<svg viewBox="0 0 120 120"><circle class="track" cx="60" cy="60" r="54" /><circle class="fill" cx="60" cy="60" r="54" style:stroke-dashoffset={339.3 * (1 - ring)} /></svg>
			<b>{Math.max(0, turns).toFixed(1)}</b>
			<span>turns in the air</span>
		</div>

		<div class="captions">
			<div class="caption" style={veil(shown(0.13, 0.27, 0.025))}>
				<h2>This is a quad flip.</h2>
				<p>Shoma Uno opened his short program with it. Before he leaves the ice, the jump is already worth <b>{fmt(short?.base_value ?? 11)}</b> points. That is its base value, fixed by the rules.</p>
			</div>
			<div class="caption" style={veil(shown(0.33, 0.58, 0.025))}>
				<h2>Four turns in the air.</h2>
				<p>He pulls his arms in tight to turn fast enough. If he lands a quarter turn short, the technical panel marks it and the score drops.</p>
			</div>
			<div class="caption" style={veil(shown(0.66, 0.8, 0.025))}>
				<h2>In the short program, he lands it.</h2>
				<p>Nine judges grade how well it was done. Their grades add <b class="gain">{signed(short?.goe ?? 3.77)}</b> points. The jump earns <b>{fmt(short?.panel_element_score ?? 14.77)}</b>.</p>
			</div>
			<div class="caption" style={veil(shown(0.86, 1.2, 0.025))}>
				<h2>Two days later, he falls on it.</h2>
				<p>Same jump, same base value. This time the judges take points away.</p>
				<table class="receipt">
					<caption class="sr-only">Shoma Uno’s quad flip in both programs</caption>
					<thead><tr><th scope="col">Program</th><th scope="col">Base value</th><th scope="col">Judges</th><th scope="col">Score</th></tr></thead>
					<tbody>
						<tr><th scope="row">Short program</th><td>{fmt(short?.base_value)}</td><td class="gain">{signed(short?.goe ?? 0)}</td><td>{fmt(short?.panel_element_score)}</td></tr>
						<tr><th scope="row">Free skate</th><td>{fmt(free?.base_value)}</td><td class="loss">{signed(free?.goe ?? 0)}</td><td>{fmt(free?.panel_element_score)}</td></tr>
					</tbody>
				</table>
			</div>
		</div>
		<p class="fineprint" style:opacity={shown(0.12, 1.2)}>3D model: a simulation of the technique, not a recording of Uno.</p>
	</div>
</section>

<style>
	.scrub { position:relative; height:560vh; }
	.pin { position:sticky; top:0; height:100vh; height:100svh; overflow:hidden; }
	.stage { position:absolute; left:0; right:0; top:0; height:74%; transform-origin:50% 50%; will-change:transform;
		-webkit-mask-image:radial-gradient(ellipse 50% 50% at 50% 50%, #000 62%, transparent 100%); mask-image:radial-gradient(ellipse 50% 50% at 50% 50%, #000 62%, transparent 100%); }
	.shade { position:absolute; inset:0; pointer-events:none; background:linear-gradient(to bottom, #000 0%, transparent 16%); }

	.hero { position:absolute; inset:0 0 auto; padding:clamp(5.5rem, 15vh, 9rem) 1.5rem 0; text-align:center; will-change:transform, opacity; }
	/* The one orchestrated moment: on arrival the title lines rise in, one after another. */
	.hero > * { animation:hero-in 900ms var(--ease-out) both; }
	.hero > :nth-child(2) { animation-delay:90ms; }
	.hero > :nth-child(3) { animation-delay:180ms; }
	@keyframes hero-in { from { opacity:0; transform:translateY(14px); } }
	.eyebrow { margin:0 0 1rem; color:var(--muted); font-size:clamp(1rem, 1.6vw, 1.3rem); font-weight:600; letter-spacing:-.01em; }
	h1 { text-wrap:balance; margin:0 auto; max-width:13ch; font:700 clamp(3rem, 8.4vw, 7.25rem)/1.02 var(--display); letter-spacing:-.045em; color:var(--ink); }
	h1:focus { outline:none; }
	.hero-sub { margin:1.4rem auto 0; max-width:34rem; color:var(--muted); font-size:clamp(1.05rem, 1.7vw, 1.4rem); line-height:1.4; font-weight:500; }

	.counter { position:absolute; right:clamp(1.5rem, 8vw, 9rem); top:50%; width:clamp(150px, 15vw, 210px); aspect-ratio:1; transform:translateY(-60%); display:grid; place-content:center; text-align:center; border-radius:50%; background:#000000a8; backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px); }
	.counter svg { position:absolute; inset:0; transform:rotate(-90deg); }
	.counter circle { fill:none; stroke-width:5; }
	.counter .track { stroke:#ffffff1f; }
	.counter .fill { stroke:var(--ice); stroke-linecap:round; stroke-dasharray:339.3; }
	.counter b { font:600 clamp(2.6rem, 4.4vw, 3.8rem)/1 var(--display); letter-spacing:-.03em; }
	.counter span { margin-top:.35rem; font-size:.8rem; color:var(--muted); }

	.captions { position:absolute; left:0; right:0; bottom:clamp(2.5rem, 9vh, 5.5rem); display:grid; padding:0 1.5rem; }
	.caption { grid-area:1 / 1; align-self:end; justify-self:center; max-width:52rem; text-align:center; will-change:opacity, transform; }
	.caption h2 { text-wrap:balance; margin:0 0 .6rem; font:700 clamp(2rem, 4.2vw, 3.5rem)/1.06 var(--display); letter-spacing:-.035em; }
	.caption p { margin:0 auto; max-width:34rem; color:var(--muted); font-size:clamp(1.02rem, 1.5vw, 1.3rem); line-height:1.42; font-weight:500; }
	.caption p b { color:var(--ink); font-weight:600; }
	.gain { color:var(--gain) !important; }
	.loss { color:var(--loss) !important; }

	.receipt { margin:1.4rem auto 0; border-collapse:collapse; font-size:clamp(.92rem, 1.3vw, 1.08rem); }
	.receipt th, .receipt td { padding:.55rem clamp(.6rem, 1.6vw, 1.3rem); text-align:right; border-bottom:1px solid var(--line); }
	.receipt thead th { color:var(--muted); font-weight:500; font-size:.82rem; }
	.receipt th[scope=row], .receipt thead th:first-child { text-align:left; font-weight:600; }
	.receipt td:last-child { font-weight:700; font-size:1.25em; }

	.fineprint { position:absolute; left:0; right:0; bottom:1rem; margin:0; text-align:center; color:var(--faint); font-size:.75rem; }

	@media (max-width: 734px) {
		.stage { height:66%; }
		.counter { top:5.4rem; right:1rem; width:104px; transform:none; }
		.counter b { font-size:2rem; }
		.counter span { font-size:.68rem; }
		.captions { bottom:2.6rem; }
		.receipt thead th:nth-child(2), .receipt tbody td:nth-child(2) { display:none; }
	}
</style>
