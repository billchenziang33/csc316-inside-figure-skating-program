<script>
	import { onMount } from 'svelte';

	const base = '/movement/fs-jump3d/';
	const families = { Axel: 'Axel', Salchow: 'Salchow', Toeloop: 'Toe loop', Loop: 'Loop', Flip: 'Flip', Lutz: 'Lutz', Comb: 'Combination' };
	const rounds = { r3: 'Round 3 · Geometry and presentation', r2: 'Round 2 · Continuity and ice contact', r1: 'Round 1 · Initial retargeting' };
	let records = $state(null);
	let loadError = $state(false);
	let family = $state('all');
	let selectedId = $state('');
	let selectedRound = $state('r3');
	let generated = $derived(records?.filter(record => record.rounds.includes('r3')) ?? []);
	let ready = $derived(generated.filter(record => record.geometry_status === 'geometry_pass' && record.available !== false));
	let candidates = $derived(ready.filter(record => family === 'all' || record.family === family));
	let sample = $derived(candidates.find(record => record.id === selectedId) ?? candidates[0]);
	let round = $derived(sample?.rounds.includes(selectedRound) ? selectedRound : sample?.rounds.at(-1));
	let player = $derived(sample && `${base}player.html?${new URLSearchParams({ id: sample.id, round })}`);

	onMount(() => {
		const controller = new AbortController();
		fetch(`${base}records-manifest.json`, { signal: controller.signal })
			.then(response => {
				if (!response.ok) throw new Error('Motion catalog unavailable');
				return response.json();
			})
			.then(catalog => { records = catalog; })
			.catch(error => { if (error.name !== 'AbortError') loadError = true; });
		return () => controller.abort();
	});
</script>

<section class="panel reference-library" aria-labelledby="fs-jump-heading">
	<h2 id="fs-jump-heading">FS-Jump3D Blender Library</h2>
	<p class="scope-note">Pick an anonymous capture and compare its Blender iterations. The animations are illustrative retargetings. Phase markers are estimated.</p>
	{#if loadError}
		<p role="alert">The FS-Jump3D catalog could not be loaded. Reload the page to try again.</p>
	{:else if !records}
		<p role="status">Loading the FS-Jump3D catalog…</p>
	{:else}
		<p class="catalog-count" role="status">{records.length} source clips · {generated.length} generated through Round 3 · {ready.length} available to preview</p>
		<div class="selectors">
			<label>Jump family
				<select bind:value={family}>
					<option value="all">All families</option>
					{#each Object.entries(families) as [id, label]}<option value={id}>{label}</option>{/each}
				</select>
			</label>
			<label>Capture clip
				<select value={sample?.id} onchange={(event) => { selectedId = event.currentTarget.value; }} disabled={!sample}>
					{#if !sample}<option value="">No preview available</option>{/if}
					{#each candidates as candidate (candidate.id)}<option value={candidate.id}>{candidate.id}</option>{/each}
				</select>
			</label>
			<label>Blender iteration
				<select value={round} onchange={(event) => { selectedRound = event.currentTarget.value; }} disabled={!sample}>
					{#each Object.entries(rounds) as [id, label]}<option value={id} disabled={!sample?.rounds.includes(id)}>{label}</option>{/each}
				</select>
			</label>
		</div>
		{#if sample}
			<div class="sample-details">
				<p class="scope-note">{sample.frames} frames · {sample.fps} fps · Round 3 geometry checks passed</p>
				<a href={player} target="_blank" rel="noopener">Open player in a new tab ↗</a>
				<a href={base + sample.assets[round].path} download>Download selected GLB</a>
			</div>
			<iframe src={player} title="FS-Jump3D Blender animation player" allow="fullscreen"></iframe>
		{:else}
			<p class="scope-note" role="status">No preview is available for this jump family yet.</p>
		{/if}
	{/if}
	<p class="scope-note"><a href="https://github.com/ryota-skating/FS-Jump3D">FS-Jump3D source</a> · <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a> · <a href={base + 'README.md'}>Methods and asset credits</a></p>
</section>

<style>
	.reference-library h2 { margin: 0; }
	.catalog-count { font-size: .85rem; font-weight: 600; }
	.selectors { display: grid; grid-template-columns: 1fr 1fr 1.3fr; gap: .9rem; }
	label { display: grid; gap: .4rem; font-size: .8rem; font-weight: 600; }
	select { width: 100%; min-height: 44px; padding: .5rem; font: inherit; border: 1px solid var(--line); border-radius: 5px; background: var(--card); color: var(--navy); }
	.sample-details { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0 1rem; font-size: .8rem; margin: .6rem 0; }
	.sample-details p { margin: .35rem 0; }
	iframe { display: block; width: 100%; height: max(620px, 72dvh); border: 1px solid var(--line); border-radius: 6px; background: #142c3c; }
	@media (max-width: 700px) { .selectors { grid-template-columns: 1fr; } }
</style>
