<script>
	import { onMount, tick } from 'svelte';
	import { arrive } from './lib/motion.mjs';
	import { evidenceStory } from './lib/evidence-story.mjs';
	import { scrolly, scrollToStep } from './lib/scrolly.mjs';
	import HomePage from './lib/home/HomePage.svelte';
	import ScoreComparison from './lib/charts/ScoreComparison.svelte';
	import JumpCounts from './lib/charts/JumpCounts.svelte';
	import RotationGoe from './lib/charts/RotationGoe.svelte';
	import SpinStepLevels from './lib/charts/SpinStepLevels.svelte';
	import ProtocolMatrix from './lib/charts/ProtocolMatrix.svelte';
	import BaseVsPanel from './lib/charts/BaseVsPanel.svelte';

	import MotionOverlay from './lib/MotionOverlay.svelte';
	import ElementPrimer from './lib/ElementPrimer.svelte';
	import { elementTip } from './lib/tooltip.mjs';
	import { describeElement, MARKS } from './lib/data/element-glossary.mjs';
	import { elementMarks, levelledElements } from './lib/data/derived.mjs';
	import { resolveMotion } from './lib/data/motion-reference.mjs';
	import { stages, defaultEvidenceChart, libraryHref, readRoute, routeHash } from './lib/navigation.mjs';
	let activeStage = $state('story');
	let storySteps = $state(null);
	let activeChart = $state(defaultEvidenceChart);
	let evidencePanel = $state('protocol');
	let workspaceTab = $state('sequence');
	let motionOpen = $state(false);
	function closeMotion() { motionOpen = false; }
	let stageIndex = $derived(stages.findIndex(s => s.id === (activeStage === 'chart-detail' ? 'evidence' : activeStage)));
	const chartLabels = { S12: 'Program totals', S01: 'Jump types', S02: 'Rotation & GOE', S06: 'Spin & step levels', S15: 'Base & final score' };
	const chartTitles = { S12: 'How do technical points contribute to the total?', S01: 'Which jump types do skaters perform in each program?', S02: 'How do jump rotations relate to execution?', S06: 'How do spin and step levels compare with scores?', S15: 'How does execution change the element score?' };
	let jumpElements = $derived(allElements.filter(row => row.element_group === 'jump'));
	let chartRows = $derived(activeChart === 'S12' ? segmentRows
		: activeChart === 'S06' ? levelledElements(allElements.filter(row => row.segment === selectedSegment))
		: jumpElements);
	function syncRoute() {
		const route = readRoute(location.hash);
		activeStage = route.stage;
		evidencePanel = route.panel ?? 'protocol';
		if (evidencePanel === 'compare' || activeStage === 'chart-detail') activeChart = route.chart;
		motionOpen = false;
		const elementId = route.elementId ?? history.state?.evidenceElementId;
		const element = data?.elements.find((row) => row.id === elementId);
		if (element) {
			selectedRank = element.final_rank;
			selectedSegment = element.segment;
			selectedElementId = element.id;
		}
	}
	function navigate(hash) {
		if (location.hash === hash) return;
		if ((activeStage === 'evidence' || activeStage === 'chart-detail') && !readRoute(location.hash).elementId) {
			// Legacy links have no occurrence in the URL. Remember their selection for Back.
			history.replaceState({ evidenceElementId: selectedElement?.id }, '', location.href);
		}
		history.pushState(null, '', hash);
		syncRoute();
	}

	async function go(stage, view) {
		navigate(routeHash(stage, view, selectedElement?.id));
		await tick(); document.getElementById('stage-heading')?.focus({ preventScroll: true });
		if (!revealStoryStep()) window.scrollTo({ top: 0, behavior: 'instant' });
	}
	// Links and Back/Forward that land on a Compare-scores chart also scroll its story step into place.
	function revealStoryStep() {
		if (activeStage !== 'evidence' || evidencePanel !== 'compare' || !storySteps?.isConnected) return false;
		if (activeChart === defaultEvidenceChart) window.scrollTo({ top: 0, behavior: 'instant' });
		else scrollToStep(storySteps, activeChart, { behavior: 'instant', focus: false });
		return true;
	}
	function onRouteChange() { syncRoute(); tick().then(revealStoryStep); }
	onMount(() => { syncRoute(); window.addEventListener('hashchange', onRouteChange); window.addEventListener('popstate', onRouteChange); return () => { window.removeEventListener('hashchange', onRouteChange); window.removeEventListener('popstate', onRouteChange); }; });
	let data = $state(null);
	let motionCatalog = $state(null);
	let motionLoadError = $state(false);
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
	let selectedMotion = $derived(resolveMotion(motionCatalog, selectedElement));
	let allElements = $derived(data?.elements ?? []);

	onMount(async () => {
		try {
			const response = await fetch('/data/competition.json');
			if (!response.ok) throw new Error(`Data request failed (${response.status})`);
			data = await response.json();
			syncRoute();
		} catch (error) {
			loadError = error instanceof Error ? error.message : 'Unable to load the competition data.';
		}
	});
	onMount(() => {
		const controller = new AbortController();
		fetch('/movement/beijing-2022/catalog.json', {signal: controller.signal})
			.then(response => { if (!response.ok) throw new Error('Motion catalog unavailable'); return response.json(); })
			.then(catalog => { motionCatalog = catalog; })
			.catch(error => { if (error.name !== 'AbortError') motionLoadError = true; });
		return () => controller.abort();
	});

	$effect(() => {
		if (programElements.length && !programElements.some((d) => d.id === selectedElementId)) {
			selectedElementId = programElements[0].id;
		}
	});

	function switchEvidenceView(view) {
		navigate(routeHash('evidence', view, selectedElement?.id));
		if (view !== 'protocol') tick().then(revealStoryStep);
	}

	function selectEvidenceElement(id) {
		const view = activeStage === 'evidence' && evidencePanel === 'protocol' ? 'protocol' : activeChart;
		navigate(routeHash(activeStage, view, id));
	}

	function onStoryStep(chart) {
		if (activeStage !== 'evidence' || evidencePanel !== 'compare' || activeChart === chart) return;
		activeChart = chart;
		// Scrolling is reading, not navigating: update the link without adding Back entries.
		history.replaceState(history.state, '', routeHash('evidence', chart, selectedElement?.id));
	}


	function selectWorkbenchElement(id) {
		selectedElementId = id;
		history.replaceState(null, '', routeHash('workspace', activeChart, id));
	}

</script>

{#snippet evidenceChart()}{#if activeChart === 'S12'}<ScoreComparison segments={segmentRows}/>{:else if activeChart === 'S01'}<JumpCounts elements={allElements}/>{:else if activeChart === 'S02'}<RotationGoe elements={allElements}/>{:else if activeChart === 'S06'}<p class="scope-note">{selectedSegment === 'SP' ? 'Short program' : 'Free skate'} · all ten skaters</p><SpinStepLevels elements={chartRows}/>{:else}<BaseVsPanel elements={jumpElements} selectedId={selectedElement?.id} onSelect={selectEvidenceElement}/>{/if}{/snippet}
{#snippet valuesTable()}<table><caption>{activeChart} source values · official ISU protocols</caption><thead><tr><th>Skater</th><th>Program</th>{#if activeChart === 'S12'}<th>TES</th><th>PCS</th><th>Deductions</th><th>TSS</th>{:else}<th>Element</th><th>Base value</th><th>GOE</th><th>Panel points</th>{/if}</tr></thead><tbody>{#each chartRows as row}<tr><th>{row.skater}</th><td>{row.segment}</td>{#if activeChart === 'S12'}<td>{row.TES}</td><td>{row.PCS_factored}</td><td>{row.deductions}</td><td>{row.segment_score_TSS}</td>{:else}<td>{row.element_code_raw}</td><td>{row.base_value}</td><td>{row.goe}</td><td>{row.panel_element_score}</td>{/if}</tr>{/each}</tbody></table>{/snippet}

<svelte:head><title>Inside a Figure-Skating Program · Beijing 2022</title></svelte:head>
<a class="skip-link" href="#main-content" onclick={(event) => { event.preventDefault(); document.getElementById('main-content')?.focus(); }}>Skip to content</a>
<div class="app-shell">
  {#if activeStage !== 'story'}
  <nav class="stage-nav" aria-label="Story steps">
    <button class="brand" onclick={() => go('story')}>Inside the Program <small>Beijing 2022, men’s singles</small></button>
    <ol>{#each stages as stage, i}<li><button aria-label={`${i+1} ${stage.label}`} aria-current={stageIndex === i ? 'step' : undefined} onclick={() => go(stage.id)}><span>{i+1}</span><b>{stage.label}</b></button></li>{/each}</ol>
  </nav>
  {/if}
  <p class="sr-only" aria-live="polite">Step {stageIndex + 1} of {stages.length}: {stages[stageIndex]?.label}. {selectedSkater}, {selectedSegment}.</p>
  <main id="main-content" tabindex="-1">
  {#if activeStage === 'story'}
	{#if loadError}<p class="error story-error" role="alert">Could not load program data: {loadError}</p>{/if}
	<HomePage {data} catalog={motionCatalog} onStep={(stage) => go(stage)} />

  {:else}
  <section class="stage-body" class:expanded={activeStage === 'chart-detail'}>
    {#key activeStage}<div in:arrive={{ delay: 0 }}>
    <div class="stage-heading"><div><p class="kicker">STEP {stageIndex+1} / {stages.length} · {stages[stageIndex]?.label}</p><h1 id="stage-heading" tabindex="-1">{activeStage === 'elements' ? 'Learn the jumps and spins first.' : activeStage === 'choose' ? 'Choose a program to follow.' : activeStage === 'workspace' ? 'One program, three connected views.' : activeStage === 'evidence' ? 'How did this move earn its score?' : activeStage === 'movement' ? 'See the movement.' : chartTitles[activeChart]}</h1></div>{#if activeStage !== 'choose' && activeStage !== 'elements'}<p class="selection-context">{selectedSkater} · {selectedSegment === 'SP' ? 'Short program' : 'Free skate'}<button class="text-button" onclick={() => go('choose')}>Change program</button></p>{/if}</div>
    {#if loadError}<p class="error" role="alert">Could not load program data: {loadError}</p>{:else if !data}<p class="loading" role="status">Loading official protocol data…</p>{:else}
    {#if activeStage === 'elements'}
      <ElementPrimer elements={allElements} onContinue={() => go('choose')} />
    {:else if activeStage === 'choose'}
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
      <div class="choice-summary panel"><h2>{selectedSkater}</h2><p>{selectedSegment === 'SP' ? 'Short program · 7 elements' : 'Free skate · 12 elements'} · {selectedProgram?.segment_score_TSS.toFixed(2)} total points</p><button class="primary" onclick={() => go('workspace')}>Explore this program →</button></div>
    {:else if activeStage === 'workspace'}
      <p class="stage-intro">Select an element in Sequence. Its details appear in Score; Movement opens the 3D reference.</p>
      <div class="workspace-tabs" role="group" aria-label="Workbench panel">{#each ['sequence','score','movement'] as tab}<button aria-pressed={workspaceTab === tab} onclick={() => workspaceTab = tab}>{tab === 'sequence' ? 'A · Sequence' : tab === 'score' ? 'B · Score' : 'C · Movement'}</button>{/each}</div>
			<div class="three-col">
				<section class="column panel" class:inactive-panel={workspaceTab !== 'sequence'} aria-labelledby="sequence-title">
					<div class="column-head"><span class="section-number">A · SEQUENCE</span><h3 id="sequence-title">Element order</h3></div>
					<ol class="sequence">
						{#each programElements as element (element.id)}
							<li><button class:selected={selectedElement?.id === element.id} onclick={() => selectWorkbenchElement(element.id)} aria-pressed={selectedElement?.id === element.id} use:elementTip={describeElement(element.element_code_raw, element.info_flag)}>
								<span class="order">{String(element.element_order).padStart(2,'0')}</span><span class="element-name"><b>{element.element_code_raw}</b><small>{element.element_group.replace('_',' ')}</small></span><span class="element-score">{element.panel_element_score.toFixed(2)}</span>
							</button></li>
						{/each}
					</ol>
				</section>

				<section class="column panel score-column" class:inactive-panel={workspaceTab !== 'score'} aria-labelledby="detail-title">
					<div class="column-head"><span class="section-number">B · ELEMENT SCORE</span><h3 id="detail-title">What the protocol awarded</h3></div>
					{#if selectedElement}
						<div class="selected-element"><span>ELEMENT {String(selectedElement.element_order).padStart(2,'0')}</span><h4><span class="code-help" tabindex="0" use:elementTip={describeElement(selectedElement.element_code_raw, selectedElement.info_flag)}>{selectedElement.element_code_raw}</span></h4><p>{selectedElement.element_group.replace('_',' ')} · {selectedSegment === 'SP' ? 'Short program' : 'Free skate'}</p></div>
						<div class="score-math"><div><span>Base value</span><b>{selectedElement.base_value.toFixed(2)}</b></div><div><span>GOE</span><b class:negative={selectedElement.goe < 0}>{selectedElement.goe > 0 ? '+' : ''}{selectedElement.goe.toFixed(2)}</b></div><div class="final-score"><span>Panel score</span><b>{selectedElement.panel_element_score.toFixed(2)}</b></div></div>
						{#each elementMarks(selectedElement) as { mark } (mark)}<p class="flag-note"><strong>Protocol mark: {mark} · {MARKS[mark].label}</strong> · {MARKS[mark].meaning}.</p>{/each}
						<div class="program-math"><span>PROGRAM TOTAL</span><strong>{selectedProgram?.TES.toFixed(2)} TES + {selectedProgram?.PCS_factored.toFixed(2)} PCS {selectedProgram?.deductions && selectedProgram.deductions < 0 ? `− ${Math.abs(selectedProgram.deductions).toFixed(2)} deductions` : ''}</strong><b>= {selectedProgram?.segment_score_TSS.toFixed(2)} TSS</b></div>
					{:else}<p class="loading">Choose an element from the sequence.</p>{/if}
				</section>

				<section class="column panel motion-column" class:inactive-panel={workspaceTab !== 'movement'} aria-labelledby="motion-title">
					<div class="column-head"><span class="section-number">C · 3D REFERENCE</span><h3 id="motion-title">{selectedMotion?.asset?.id === '4A' ? 'Standard 4A technique' : selectedMotion?.asset?.id ?? 'Movement reference'}</h3></div>
					{#if selectedMotion?.asset?.file}
						<figure class="movement-preview"><img src={selectedMotion.asset.poster} alt={`${selectedMotion.asset.name} · side view`}/><figcaption>{selectedMotion.asset.name} · illustrative / simulated</figcaption></figure>
						<button class="primary motion-expand" onclick={() => motionOpen = true}>Play {selectedMotion.asset.id === '4A' ? 'standard 4A' : selectedMotion.asset.id} in 3D ↗</button>
					{:else}<p role="status">{motionLoadError ? 'Movement library could not be loaded.' : motionCatalog ? 'No 3D model for this element.' : 'Loading movement library…'}</p>{/if}

				</section>
			</div>
      <div class="workspace-actions"><button class="secondary" onclick={() => go('evidence', 'protocol')}>Inspect protocol marks →</button><button class="secondary" onclick={() => go('evidence', defaultEvidenceChart)}>Compare base value and panel score →</button></div>
    {:else if activeStage === 'evidence' || activeStage === 'chart-detail'}
      {#if selectedElement}
        {@const marks = elementMarks(selectedElement)}
        <section class="evidence-selection panel" aria-label="Selected element">
          <div class="evidence-element" aria-live="polite" aria-atomic="true">
            <h2><span class="section-number">Element {String(selectedElement.element_order).padStart(2, '0')}</span> {selectedElement.element_code_raw}</h2>
            <p>{marks.length ? marks.map(({ label }) => label).join(' · ') : 'No protocol marks'}</p>
          </div>
          <dl class="evidence-points" aria-label="Score breakdown">
            <div><dt>Base value</dt><dd>{selectedElement.base_value.toFixed(2)}</dd></div>
            <div><dt>Execution (GOE)</dt><dd>{selectedElement.goe > 0 ? '+' : ''}{selectedElement.goe.toFixed(2)}</dd></div>
            <div><dt>Panel score</dt><dd>{selectedElement.panel_element_score.toFixed(2)}</dd></div>
          </dl>
          <button class="secondary" onclick={() => { workspaceTab = 'score'; go('workspace'); }}>Open in workbench →</button>
        </section>
      {/if}
      {#if activeStage === 'evidence'}
        <div class="evidence-tabs" role="group" aria-label="Scoring evidence view">
          <button aria-pressed={evidencePanel === 'compare'} onclick={() => switchEvidenceView(activeChart)}>Compare scores</button>
          <button aria-pressed={evidencePanel === 'protocol'} onclick={() => switchEvidenceView('protocol')}>Protocol marks</button>
        </div>
      {/if}
      {#if activeStage === 'evidence' && evidencePanel === 'protocol'}
        <article class="matrix-card panel">
          <div class="panel-heading"><h2>Protocol marks by element</h2></div>
          <ProtocolMatrix elements={programElements} selectedId={selectedElement?.id} onSelect={selectEvidenceElement} />
        </article>
      {:else if activeStage === 'evidence'}
        <p class="scope-note">Scroll through the scoring story to see the chart change with each section.</p>
        <div class="scrolly">
          <ol class="scrolly-steps" bind:this={storySteps} use:scrolly={{ onStep: onStoryStep, initial: activeChart }} aria-label="Scoring story">
            {#each evidenceStory as step (step.chart)}
              <li class="scrolly-step" class:is-active={activeChart === step.chart} data-step={step.chart}>
                <div class="panel">
                  <span class="section-number">{step.kicker}</span>
                  <h3 tabindex="-1">{step.title}</h3>
                  <p>{step.body}</p>
                  {#if step.chart === 'S15' && selectedElement}<p class="scrolly-focus"><b>{selectedElement.element_code_raw}</b> · {selectedElement.base_value.toFixed(2)} base {selectedElement.goe < 0 ? '−' : '+'} {Math.abs(selectedElement.goe).toFixed(2)} GOE = <b>{selectedElement.panel_element_score.toFixed(2)}</b> points</p>{/if}
                  {#if step.note}<p class="scope-note">{step.note}</p>{/if}
                  {#if step.chart === 'S12'}<button class="secondary scrolly-next" onclick={() => go('movement')}>Explore the 3D movement library →</button>{/if}
                </div>
              </li>
            {/each}
          </ol>
          <article class="scrolly-graphic analysis-card panel">
            <nav class="scrolly-progress" aria-label="Jump to a chart">
              {#each evidenceStory as step, i (step.chart)}<button aria-current={activeChart === step.chart ? 'step' : undefined} onclick={() => scrollToStep(storySteps, step.chart)}><span>{i + 1}</span>{chartLabels[step.chart]}</button>{/each}
            </nav>
            <div class="panel-heading"><div aria-live="polite"><span class="section-number">{activeChart === 'S12' ? selectedSkater : 'FINAL TOP-TEN COHORT'}</span><h2>{chartTitles[activeChart]}</h2></div><button class="secondary" onclick={() => go('chart-detail', activeChart)}>Expand chart ↗</button></div>
            {#key activeChart}<div class="chart-canvas" in:arrive={{ delay: 0 }}>{@render evidenceChart()}</div>{/key}
          </article>
        </div>
        <details class="data-values panel"><summary>Read the underlying values for {chartLabels[activeChart]} ({chartRows.length} records)</summary><div class="table-scroll">{@render valuesTable()}</div></details>
      {:else}
        <article class="analysis-card panel"><div class="panel-heading"><div><span class="section-number">{activeChart === 'S12' ? selectedSkater : 'FINAL TOP-TEN COHORT'}</span>{#if activeStage === 'evidence'}<h2>{chartTitles[activeChart]}</h2>{/if}</div><button class="secondary" onclick={() => go(activeStage === 'evidence' ? 'chart-detail' : 'evidence', activeChart)}>{activeStage === 'evidence' ? 'Expand chart ↗' : '← Return to scoring evidence'}</button></div>
        <div class="chart-canvas">{@render evidenceChart()}</div>
        {#if activeChart === 'S01'}<p class="scope-note">Each jump in a combination is counted separately. The free skate allows more jump elements than the short program.</p>
        {:else if activeChart !== 'S02'}<p class="scope-note">{evidenceStory.find((step) => step.chart === activeChart)?.note}</p>{/if}
        <details class="data-values"><summary>Read the underlying values ({chartRows.length} records)</summary><div class="table-scroll">{@render valuesTable()}</div></details>
      </article>
      {/if}
    {:else if activeStage === 'movement'}
      <div class="motion-toolbar">
        <button class="secondary" onclick={() => { workspaceTab = 'movement'; go('workspace'); }}>← Return to workbench</button>
        {#if selectedMotion?.asset?.file}
          <button class="primary" onclick={() => motionOpen = true}>Play {selectedMotion.asset.id === '4A' ? 'standard 4A' : selectedMotion.asset.id} in 3D ↗</button>
        {/if}
      </div>
      <section class="panel reference-library" aria-labelledby="movement-library-heading">
        <h2 id="movement-library-heading">50 Movement 3D Library</h2>
        <iframe class="movement-library-frame" src={libraryHref(selectedElement?.id)} title="Searchable 3D movement library"></iframe>
      </section>
    {/if}
    {/if}
    </div>{/key}
  </section>
  {/if}
  </main>
  {#if activeStage !== 'story'}
  <nav class="step-controls" aria-label="Step navigation">
    <button class="secondary" disabled={stageIndex === 0} onclick={() => go(stages[Math.max(0,stageIndex-1)].id)}>← Previous</button>
    <button class="step-current" disabled aria-current="step"><span>{stageIndex+1} / {stages.length}</span><b>{stages[stageIndex]?.label}</b></button>
    <button class="primary" onclick={() => go(stageIndex === stages.length-1 ? 'story' : stages[stageIndex+1].id)}>Next →</button>
  </nav>
  {/if}
  {#if activeStage !== 'story'}
  <details class="sources"><summary>Data, sources & scope</summary>
	<footer><div><span class="section-number">DATA & SCOPE</span><p>Beijing 2022 individual men’s singles · final top ten · 190 protocol elements · 20 segment records</p></div><div class="footer-links"><a href="https://results.isu.org/results/season2122/owg2022/CAT001RS.htm" target="_blank" rel="noreferrer">Final standings ↗</a><a href="https://www.isuresults.com/results/season2122/owg2022/owg2022_protocol.pdf" target="_blank" rel="noreferrer">Official protocol book ↗</a><a href="https://github.com/billchenziang33/csc316-inside-figure-skating-program" target="_blank" rel="noreferrer">Project source ↗</a></div></footer>
  </details>
  {/if}
</div>

{#if motionOpen && selectedMotion?.asset}<MotionOverlay onClose={closeMotion} motion={selectedMotion.asset}/>{/if}
