<script module>
	// Each model is about 8 MB and its set-up runs on the page's main thread, so models load one after another.
	let queue = Promise.resolve();

	// The part of a model worth looping: the flight for jumps, the whole move for spins and sequences.
	export function loopOf(asset) {
		const events = Object.entries(asset?.event_frames ?? {});
		const at = (prefix) => events.filter(([k]) => k.startsWith(prefix)).map(([, v]) => Number(v));
		const takeoffs = at('TAKEOFF');
		const landings = at('LANDING');
		if ((asset.kind === 'jump' || asset.kind === 'combination') && takeoffs.length && landings.length) {
			return [Math.max(1, Math.min(...takeoffs) - 40), Math.min(asset.frames, Math.max(...landings) + 30)];
		}
		const start = Number(asset.event_frames?.APPROACH ?? asset.event_frames?.ENTRY ?? 1);
		return [Math.max(1, start), asset.frames];
	}
</script>

<script>
	import { onMount, untrack } from 'svelte';
	import { reducedMotion } from './motion.mjs';

	// One model from the 3D movement library, drawn as a picture with no controls.
	// Either it loops a range of Blender frames (`loop`), or the page drives it (`frame`).
	let {
		id,
		view = null,
		loop = null,
		frame = null,
		interactive = false,
		preload = false,
		spot = false,
		bg = '000000',
		label = '',
		onFrame = () => {},
		onReady = () => {}
	} = $props();

	let host = $state();
	let iframe = $state();
	let near = $state(false);
	let visible = $state(false);
	let readySrc = $state('');
	let failedSrc = $state('');
	// The model in the iframe can lag behind the one asked for: the old one fades out first.
	let shownSrc = $state('');
	let shownId = $state('');
	let leaving = $state(false);

	let src = $derived(
		`/movement/beijing-2022/player.html?id=${encodeURIComponent(id)}&mode=stage` +
			(view ? `&view=${view}` : '') +
			(bg !== '000000' ? `&bg=${bg}` : '') +
			(loop ? `&loop=${Math.round(loop[0])}-${Math.round(loop[1])}` : '')
	);
	let ready = $derived(!leaving && readySrc === shownSrc && shownSrc !== '');
	let failed = $derived(failedSrc === shownSrc && shownSrc !== '');

	// A new model was asked for: let the current one fade out (180 ms), then load the next.
	// Asking again during the fade only changes which model comes next.
	let swapTimer = 0;
	$effect(() => {
		const next = src;
		const nextId = id;
		untrack(() => {
			clearTimeout(swapTimer);
			const showing = readySrc === shownSrc && shownSrc !== '';
			if (next === shownSrc) { leaving = false; return; }
			if (!showing || reducedMotion()) { shownSrc = next; shownId = nextId; leaving = false; return; }
			leaving = true;
			swapTimer = setTimeout(() => { shownSrc = next; shownId = nextId; leaving = false; }, 180);
		});
	});

	function post(message) {
		iframe?.contentWindow?.postMessage({ type: 'stage', ...message }, location.origin);
	}

	onMount(() => {
		// Load the model a screen ahead; loop only while it is on screen.
		let settle = () => {};
		const turn = () => new Promise((resolve) => { settle = resolve; near = true; setTimeout(resolve, 15000); });
		let joined = false;
		const join = () => { if (joined) return; joined = true; mount.disconnect(); queue = queue.then(turn); };
		const mount = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) join(); }, { rootMargin: '120% 0px' });
		if (preload) join();
		const watch = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; });
		mount.observe(host);
		watch.observe(host);
		const listen = (event) => {
			if (event.origin !== location.origin || !iframe || event.source !== iframe.contentWindow) return;
			const message = event.data ?? {};
			if (message.id !== shownId) return; // a message from the model that was just swapped out
			if (message.type === 'stage-ready') { readySrc = shownSrc; settle(); onReady(message); }
			else if (message.type === 'stage-frame') onFrame(message);
			else if (message.type === 'stage-error') { failedSrc = shownSrc; settle(); }
		};
		addEventListener('message', listen);
		return () => { clearTimeout(swapTimer); mount.disconnect(); watch.disconnect(); removeEventListener('message', listen); };
	});

	$effect(() => { if (ready && loop) post({ action: visible ? 'play' : 'pause' }); });
	$effect(() => { if (ready && frame != null) post({ action: 'seek', frame }); });
</script>

<div class="stage" class:ready class:interactive class:spot style:--stage-bg={`#${bg}`} bind:this={host}>
	{#if near}
		<iframe bind:this={iframe} src={shownSrc} title={label} tabindex="-1" aria-hidden="true"></iframe>
	{/if}
	<span class="sr-only">{label}</span>
	{#if failed}
		<p class="note">The 3D model did not load. Check your connection, then reload the page.</p>
	{:else if !ready && !leaving}
		<span class="loading" aria-hidden="true"></span>
	{/if}
</div>

<style>
	.stage { position:relative; width:100%; height:100%; background:var(--stage-bg); overflow:hidden; }
	iframe { position:absolute; inset:0; width:100%; height:100%; border:0; background:var(--stage-bg); opacity:0; pointer-events:none; transition:opacity 180ms var(--ease-in); }
	.ready iframe { opacity:1; transition:opacity 700ms var(--ease-out); }
	.interactive.ready iframe { pointer-events:auto; }
	/* A pool of light: the rink fades out to the page instead of ending in a hard line. */
	.spot { -webkit-mask-image:radial-gradient(ellipse 50% 50% at 50% 52%, #000 58%, transparent 100%); mask-image:radial-gradient(ellipse 50% 50% at 50% 52%, #000 58%, transparent 100%); }
	.note { position:absolute; inset:auto 0 50%; margin:0; padding:0 1.5rem; text-align:center; color:var(--muted); font-size:.94rem; }
	.loading { position:absolute; left:50%; top:50%; width:28px; height:28px; margin:-14px; border-radius:50%; border:2px solid #ffffff22; border-top-color:#ffffffaa; opacity:0; animation:spin 1s linear infinite, appear var(--dur) var(--ease-out) 400ms forwards; }
	/* Only show the spinner when loading takes long enough to notice. */
	@keyframes spin { to { transform:rotate(360deg); } }
	@keyframes appear { to { opacity:1; } }
</style>
