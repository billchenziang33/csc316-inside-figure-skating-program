<script>
	import { onMount, tick } from 'svelte';
	import JumpShareChart from './lib/charts/JumpShareChart.svelte';
	import ScoreComparison from './lib/charts/ScoreComparison.svelte';
	import JumpCounts from './lib/charts/JumpCounts.svelte';
	import RotationGoe from './lib/charts/RotationGoe.svelte';
	import SpinStepLevels from './lib/charts/SpinStepLevels.svelte';
	import ProtocolMatrix from './lib/charts/ProtocolMatrix.svelte';
	import BaseVsPanel from './lib/charts/BaseVsPanel.svelte';

	import MotionOverlay from './lib/MotionOverlay.svelte';
	import { stages, chartIds, readRoute, routeHash } from './lib/navigation.mjs';
	let activeStage = $state('story');
	let activeChart = $state('S12');
	let workspaceTab = $state('sequence');
	let motionOpen = $state(false);
	function closeMotion() { motionOpen = false; }
	let stageIndex = $derived(activeStage === 'chart-detail' ? 4 : stages.findIndex(s => s.id === activeStage));
	const chartTitles = { S12: 'How do technical points contribute to the total?', S01: 'How many scored jump elements appear in each program?', S02: 'How do jump rotations relate to execution?', S06: 'How do spin and step levels compare with scores?', S15: 'How does execution change the element score?' };
	let chartRows = $derived(activeChart === 'S12' ? segmentRows : allElements.filter(d => activeChart === 'S06' ? d.segment === selectedSegment && d.element_group !== 'jump' : activeChart === 'S02' || activeChart === 'S15' || activeChart === 'S01' ? d.element_group === 'jump' : true));
	function syncRoute() { const r = readRoute(location.hash); activeStage = r.stage; activeChart = r.chart; }
	async function go(stage, chart = activeChart) {
		history.pushState(null, '', routeHash(stage, chart)); syncRoute();
		await tick(); document.getElementById('stage-heading')?.focus({ preventScroll: true }); window.scrollTo({ top: 0, behavior: 'instant' });
	}
	onMount(() => { syncRoute(); window.addEventListener('hashchange', syncRoute); window.addEventListener('popstate', syncRoute); return () => { window.removeEventListener('hashchange', syncRoute); window.removeEventListener('popstate', syncRoute); }; });
	let data = $state(null);
	let loadError = $state('');
	let selectedRank = $state(1);
	let selectedSegment = $state('SP');
	let selectedElementId = $state(null);
	let selectedSkater = $derived(data?.segments.find((d) => d.final_rank === selectedRank)?.skater ?? '');
	let segmentRows = $derived(data?.segments.filter((d) => d.skater === selectedSkater) ?? []);
	let selectedProgram = $derived(segmentRows.find((d) => d.segment === selectedSegment));
	let programElements = $derived((data?.elements ?? [])
		.filter((d) => d.skater === selectedSkater && d.segment === selectedSegment)
		.sort((a, b) => a.element_order - b.element_order));
	let selectedElement = $derived(programElements.find((d) => d.id === selectedElementId) ?? programElements[0] ?? null);
	let jumpShare = $derived(data?.jumpShare ?? []);
	let allElements = $derived(data?.elements ?? []);

	onMount(async () => {
		try {
			const response = await fetch('/data/competition.json');
			if (!response.ok) throw new Error(`Data request failed (${response.status})`);
			data = await response.json();
		} catch (error) {
			loadError = error instanceof Error ? error.message : 'Unable to load the competition data.';
		}
	});

	$effect(() => {
		if (programElements.length && !programElements.some((d) => d.id === selectedElementId)) {
			selectedElementId = programElements[0].id;
		}
	});

	function selectFromChart(element) {
		selectedRank = element.final_rank;
		selectedSegment = element.segment;
		selectedElementId = element.id;
		workspaceTab = 'score'; go('workspace');
	}

</script>

<svelte:head><title>Inside a Figure-Skating Program · Beijing 2022</title></svelte:head>
<a class="skip-link" href="#main-content" onclick={(event) => { event.preventDefault(); document.getElementById('main-content')?.focus(); }}>Skip to content</a>
<div class="app-shell">
  <nav class="stage-nav" aria-label="Story steps">
    <button class="brand" onclick={() => go('story')}>INSIDE THE PROGRAM <small>BEIJING 2022 · MEN’S SINGLES</small></button>
    <ol>{#each stages as stage, i}<li><button aria-label={`${i+1} ${stage.label}`} aria-current={stageIndex === i ? 'step' : undefined} onclick={() => go(stage.id)}><span>{i+1}</span><b>{stage.label}</b></button></li>{/each}</ol>
  </nav>
  <p class="sr-only" aria-live="polite">Step {stageIndex + 1} of 6: {stages[stageIndex]?.label}. {selectedSkater}, {selectedSegment}.</p>
  <main id="main-content" tabindex="-1">
  {#if activeStage === 'story'}
	<header class="hero">
		<div class="hero-top"><span class="eyebrow">CSC316 · Beijing 2022 · Men’s singles</span><span class="issue">THE SCORE, DECODED</span></div>
		<div class="hero-copy">
			<p class="kicker">Inside a figure-skating program</p>
			<h1 id="stage-heading" tabindex="-1">Jumps carry most of the technical score.<br /><em>And more in the free skate.</em></h1>
			<p class="deck">Across the event’s top ten, jump elements account for 67.4% of technical element points in the short program and 77.1% in the free skate.</p>
			<div class="hero-actions"><button class="primary" onclick={() => go('choose')}>Explore a program →</button><button class="quiet" onclick={() => go('charts')}>Skip to charts</button></div>
		</div>
		<div class="hero-chart panel">
			<div class="panel-heading"><div><span class="section-number">01 / THE PATTERN</span><h2>Jump points take a larger share in the free skate</h2></div><span class="delta">+9.7 pp</span></div>
			{#if loadError}<p class="error" role="alert">{loadError}</p>{:else if jumpShare.length}<JumpShareChart data={jumpShare} />{:else}<p class="loading">Loading official protocol data…</p>{/if}
		</div>
		<div class="source-line">A top-ten cohort analysis · 10 skaters · official ISU element panel scores · <a href="https://results.isu.org/results/season2122/owg2022/" target="_blank" rel="noreferrer">Source: ISU results</a></div>
	</header>

  {:else}
  <section class="stage-body" class:expanded={activeStage === 'chart-detail'}>
    <div class="stage-heading"><div><p class="kicker">STEP {stageIndex+1} / 6 · {activeStage === 'chart-detail' ? activeChart : stages[stageIndex]?.label}</p><h1 id="stage-heading" tabindex="-1">{activeStage === 'choose' ? 'Choose a program to follow.' : activeStage === 'workspace' ? 'One program, three connected views.' : activeStage === 'protocol' ? 'Read the protocol marks.' : activeStage === 'movement' ? 'See the movement.' : chartTitles[activeChart]}</h1></div>{#if activeStage !== 'choose'}<p class="selection-context">{selectedSkater} · {selectedSegment === 'SP' ? 'Short program' : 'Free skate'}<button class="text-button" onclick={() => go('choose')}>Change program</button></p>{/if}</div>
    {#if loadError}<p class="error" role="alert">Could not load program data: {loadError}</p>{:else if !data}<p class="loading" role="status">Loading official protocol data…</p>{:else}
    {#if activeStage === 'choose'}
      <p class="stage-intro">Follow one of the final top ten through the official element sequence and scoring breakdown.</p>
			<div class="controls panel">
				<label>Skater
					<select bind:value={selectedRank}>
						{#each data.segments.filter((d) => d.segment === 'SP').sort((a,b) => a.final_rank - b.final_rank) as skater (skater.final_rank)}
							<option value={skater.final_rank}>#{skater.final_rank} · {skater.skater} ({skater.NOC})</option>
						{/each}
					</select>
				</label>
				<div class="segment-control" role="group" aria-label="Choose skating program">
					<button class:active={selectedSegment === 'SP'} onclick={() => selectedSegment = 'SP'}>Short program <small>7 elements</small></button>
					<button class:active={selectedSegment === 'FS'} onclick={() => selectedSegment = 'FS'}>Free skate <small>12 elements</small></button>
				</div>
				<div class="program-score"><span>Program total · TSS</span><strong>{selectedProgram?.segment_score_TSS.toFixed(2) ?? '—'}</strong></div>
			</div>
      <div class="choice-summary panel"><span class="section-number">YOUR PROGRAM</span><h2>{selectedSkater}</h2><p>{selectedSegment === 'SP' ? 'Short program · 7 elements' : 'Free skate · 12 elements'} · {selectedProgram?.segment_score_TSS.toFixed(2)} total points</p><p>Choose an element in the next screen to compare its base value, execution and final score.</p><button class="primary" onclick={() => go('workspace')}>Open the three-column workbench →</button></div>
    {:else if activeStage === 'workspace'}
      <p class="stage-intro">Select an element in Sequence. Its details appear in Score; Movement opens the 3D reference.</p>
      <div class="workspace-tabs" role="group" aria-label="Workbench panel">{#each ['sequence','score','movement'] as tab}<button aria-pressed={workspaceTab === tab} onclick={() => workspaceTab = tab}>{tab === 'sequence' ? 'A · Sequence' : tab === 'score' ? 'B · Score' : 'C · Movement'}</button>{/each}</div>
			<div class="three-col">
				<section class="column panel" class:inactive-panel={workspaceTab !== 'sequence'} aria-labelledby="sequence-title">
					<div class="column-head"><span class="section-number">A · SEQUENCE</span><h3 id="sequence-title">Element order</h3><p>Official protocol order; not a timeline or rink map.</p></div>
					<ol class="sequence">
						{#each programElements as element (element.id)}
							<li><button class:selected={selectedElement?.id === element.id} onclick={() => selectedElementId = element.id} aria-pressed={selectedElement?.id === element.id}>
								<span class="order">{String(element.element_order).padStart(2,'0')}</span><span class="element-name"><b>{element.element_code_raw}</b><small>{element.element_group.replace('_',' ')}</small></span><span class="element-score">{element.panel_element_score.toFixed(2)}</span>
							</button></li>
						{/each}
					</ol>
				</section>

				<section class="column panel score-column" class:inactive-panel={workspaceTab !== 'score'} aria-labelledby="detail-title">
					<div class="column-head"><span class="section-number">B · ELEMENT SCORE</span><h3 id="detail-title">What the protocol awarded</h3><p>Official panel values for the selected element.</p></div>
					{#if selectedElement}
						<div class="selected-element"><span>ELEMENT {String(selectedElement.element_order).padStart(2,'0')}</span><h4>{selectedElement.element_code_raw}</h4><p>{selectedElement.element_group.replace('_',' ')} · {selectedSegment === 'SP' ? 'Short program' : 'Free skate'}</p></div>
						<div class="score-math"><div><span>Base value</span><b>{selectedElement.base_value.toFixed(2)}</b></div><div><span>GOE</span><b class:negative={selectedElement.goe < 0}>{selectedElement.goe > 0 ? '+' : ''}{selectedElement.goe.toFixed(2)}</b></div><div class="final-score"><span>Panel score</span><b>{selectedElement.panel_element_score.toFixed(2)}</b></div></div>
						{#if selectedElement.info_flag}<p class="flag-note"><strong>Protocol mark: {selectedElement.info_flag}</strong> · Check the official notation key for this call.</p>{/if}
						<div class="program-math"><span>PROGRAM TOTAL</span><strong>{selectedProgram?.TES.toFixed(2)} TES + {selectedProgram?.PCS_factored.toFixed(2)} PCS {selectedProgram?.deductions && selectedProgram.deductions < 0 ? `− ${Math.abs(selectedProgram.deductions).toFixed(2)} deductions` : ''}</strong><b>= {selectedProgram?.segment_score_TSS.toFixed(2)} TSS</b></div>
					{:else}<p class="loading">Choose an element from the sequence.</p>{/if}
					<p class="score-caveat">An element score combines base value and Grade of Execution (GOE). It does not measure the full artistic or athletic performance.</p>
				</section>

				<section class="column panel motion-column" class:inactive-panel={workspaceTab !== 'movement'} aria-labelledby="motion-title">
					<div class="column-head"><span class="section-number">C · 3D REFERENCE</span><h3 id="motion-title">A movement example</h3><p>Open the interactive Single Axel reference in a full-screen view.</p></div>
					<figure class="movement-preview"><img src="/movement/axel-1a-prototype/single-axel-1a-human-rink-v108-landing-side.png" alt="Blender v108 full-body side view of the illustrative Single Axel landing with visible skates"/><figcaption>Blender v108 · simulated landing · side view</figcaption></figure><button class="primary motion-expand" onclick={() => motionOpen = true}>Play Blender v108 in 3D ↗</button>
					<p class="motion-caveat">This is a generic reference demo, not motion capture of {selectedSkater || 'the selected skater'} or a Beijing 2022 performance.</p>

				</section>
			</div>
      <div class="workspace-actions"><button class="secondary" onclick={() => go('protocol')}>Inspect protocol marks →</button><button class="secondary" onclick={() => go('charts','S15')}>Compare base value and panel score →</button></div>
    {:else if activeStage === 'protocol'}
      <p class="stage-intro">S11 · Select an element row or marked cell. The same selection is retained in the workbench.</p>
			<div class="matrix-card panel">
				<div class="panel-heading"><div><span class="section-number">S11 · NOVEL VIEW</span><h2>Protocol marks in {selectedSkater || 'the selected program'}’s {selectedSegment === 'SP' ? 'short program' : 'free skate'}</h2></div><span class="selected-label">Select a marked cell to link the element</span></div>
				{#if programElements.length}<ProtocolMatrix elements={programElements} selectedId={selectedElement?.id} onSelect={(id) => { selectedElementId = id; workspaceTab = 'score'; }} />{/if}
			</div>
      <button class="secondary" onclick={() => { workspaceTab = 'score'; go('workspace'); }}>Inspect {selectedElement?.element_code_raw} in the workbench →</button>
    {:else if activeStage === 'charts' || activeStage === 'chart-detail'}
      {#if activeStage === 'charts'}<div class="chart-tabs" role="group" aria-label="Choose evidence chart">{#each chartIds as chart}<button aria-pressed={activeChart === chart} onclick={() => go('charts',chart)}>{chart} · {chart === 'S12' ? 'Program totals' : chart === 'S01' ? 'Jump counts' : chart === 'S02' ? 'Rotation & GOE' : chart === 'S06' ? 'Spin & step levels' : 'Base & final score'}</button>{/each}</div>{/if}
      <article class="analysis-card panel"><div class="panel-heading"><div><span class="section-number">{activeChart} · {activeChart === 'S12' ? selectedSkater : 'FINAL TOP-TEN COHORT'}</span><h2>{chartTitles[activeChart]}</h2></div><button class="secondary" onclick={() => go(activeStage === 'charts' ? 'chart-detail' : 'charts')}>{activeStage === 'charts' ? 'Expand chart ↗' : '← Return to charts'}</button></div>
        <div class="chart-canvas">{#if activeChart === 'S12'}<ScoreComparison segments={segmentRows}/>{:else if activeChart === 'S01'}<JumpCounts elements={allElements}/>{:else if activeChart === 'S02'}<RotationGoe elements={allElements}/>{:else if activeChart === 'S06'}<p class="scope-note">{selectedSegment === 'SP' ? 'Short program' : 'Free skate'} · all ten skaters</p><SpinStepLevels elements={allElements.filter(d => d.segment === selectedSegment)}/>{:else}<BaseVsPanel elements={allElements.filter(d => d.element_group === 'jump')} onSelect={selectFromChart}/>{/if}</div>
        <p class="scope-note">{activeChart === 'S12' ? 'TES + PCS + deductions = TSS. Points in SP and FS belong to different program lengths.' : activeChart === 'S01' ? 'A combination is counted as one scored jump element, not as separate jumps.' : activeChart === 'S02' ? 'Rotations and GOE describe different aspects of a jump. This comparison does not establish causation.' : activeChart === 'S06' ? 'Level is a technical classification; the panel score also includes execution.' : 'Choose a point to open that athlete, program and element in the workbench.'}</p>
        <details class="data-values"><summary>Read the underlying values ({chartRows.length} records)</summary><div class="table-scroll"><table><caption>{activeChart} source values · official ISU protocols</caption><thead><tr><th>Skater</th><th>Program</th>{#if activeChart === 'S12'}<th>TES</th><th>PCS</th><th>Deductions</th><th>TSS</th>{:else}<th>Element</th><th>Base value</th><th>GOE</th><th>Panel points</th>{/if}</tr></thead><tbody>{#each chartRows as row}<tr><th>{row.skater}</th><td>{row.segment}</td>{#if activeChart === 'S12'}<td>{row.TES}</td><td>{row.PCS_factored}</td><td>{row.deductions}</td><td>{row.segment_score_TSS}</td>{:else}<td>{row.element_code_raw}</td><td>{row.base_value}</td><td>{row.goe}</td><td>{row.panel_element_score}</td>{/if}</tr>{/each}</tbody></table></div></details>
      </article>
    {:else if activeStage === 'movement'}
      <p class="stage-intro">Single Axel · a generic movement reference. This is not motion capture of {selectedSkater} or a Beijing 2022 performance.</p>
      <div class="motion-toolbar"><button class="secondary" onclick={() => { workspaceTab = 'movement'; go('workspace'); }}>← Return to workbench</button><button class="primary" onclick={() => motionOpen = true}>Enter full-screen 3D reference ↗</button><a class="secondary" href="/movement/axel-1a-prototype/">Open 1A illustrative pose study ↗</a></div>
      <figure class="motion-poster"><button class="poster-launch" onclick={() => motionOpen = true} aria-label="Enter the Blender v108 Single Axel animation in full screen"><img src="/movement/axel-1a-prototype/single-axel-1a-human-rink-v108-takeoff-side.png" alt="Blender v108 simulated skater at take-off in the horizontal side view"/></button><figcaption>Blender v108 take-off preview · Enter full screen to play, scrub, and switch side/front, skate-close-up, and arena views.</figcaption></figure>
      <p class="scope-note">The full-screen view keeps your selected program and element. It uses the same Blender v108 motion as the standalone prototype. Use Play, Front, Side and skate close-up; all phases remain illustrative / simulated.</p>
    {/if}
    {/if}
  </section>
  {/if}
  </main>
  <nav class="step-controls" aria-label="Step navigation"><button class="secondary" disabled={stageIndex === 0} onclick={() => go(stages[Math.max(0,stageIndex-1)].id)}>← Previous</button><span>{stageIndex+1} / {stages.length} <b>{stages[stageIndex]?.label}</b></span><button class="primary" onclick={() => go(stageIndex === stages.length-1 ? 'story' : stages[stageIndex+1].id)}>{stageIndex === stages.length-1 ? 'Back to the finding ↺' : 'Next →'}</button></nav>
  <details class="sources"><summary>Data, sources & scope</summary>
	<footer><div><span class="section-number">DATA & SCOPE</span><p>Beijing 2022 individual men’s singles · final top ten · 190 protocol elements · 20 segment records</p></div><div class="footer-links"><a href="https://results.isu.org/results/season2122/owg2022/CAT001RS.htm" target="_blank" rel="noreferrer">Final standings ↗</a><a href="https://www.isuresults.com/results/season2122/owg2022/owg2022_protocol.pdf" target="_blank" rel="noreferrer">Official protocol book ↗</a><a href="https://github.com/billchenziang33/csc316-inside-figure-skating-program" target="_blank" rel="noreferrer">Project source ↗</a></div></footer>
  </details>
</div>

{#if motionOpen}<MotionOverlay onClose={closeMotion} skater={selectedSkater}/>{/if}
