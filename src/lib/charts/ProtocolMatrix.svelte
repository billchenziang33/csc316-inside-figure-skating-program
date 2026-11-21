<script>
	import { protocolMarks, protocolMarkLabels } from '../data/derived.mjs';
	let { elements = [], selectedId = null, onSelect = () => {} } = $props();
	const flags = Object.entries(protocolMarkLabels);
	let rows = $derived(elements.map((element) => ({ element, marks: protocolMarks(element) })));
	let markedCount = $derived(rows.filter(({ marks }) => marks.length > 0).length);
</script>

<p class="marks-summary">
	{#if markedCount === 0}
		This program has no protocol marks.
	{:else}
		This program has protocol marks on <strong>{markedCount} of {rows.length}</strong> elements.
	{/if}
</p>

<div class="protocol-table-wrap">
	<table class="protocol-table" aria-label="Element codes, protocol marks, and panel scores">
		<thead>
			<tr><th scope="col">Element</th><th scope="col">Protocol marks</th><th scope="col" class="panel-score">Panel score</th></tr>
		</thead>
		<tbody>
			{#each rows as { element, marks } (element.id)}
				<tr class:chosen={selectedId === element.id}>
					<th scope="row">
						<button class="element-button" onclick={() => onSelect(element.id)} aria-pressed={selectedId === element.id}>
							<span class="order">{String(element.element_order).padStart(2, '0')}</span>
							<span class="code">{element.element_code_raw}</span>
						</button>
					</th>
					<td>
						{#if marks.length}
							<div class="mark-list">
								{#each marks as mark (mark)}
									<button class="mark-button" aria-label={`${element.element_code_raw}, ${mark} · ${protocolMarkLabels[mark]}`} aria-pressed={selectedId === element.id} onclick={() => onSelect(element.id)}>
										<span class="mark-symbol">{mark}</span>
										<span>{protocolMarkLabels[mark]}</span>
									</button>
								{/each}
							</div>
						{:else}
							<span class="no-marks">None</span>
						{/if}
					</td>
					<td class="panel-score">{element.panel_element_score.toFixed(2)}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>
<details class="mark-legend">
	<summary>What do these marks mean?</summary>
	<dl>{#each flags as [flag, label] (flag)}<div><dt>{flag}</dt><dd>{label}</dd></div>{/each}</dl>
</details>

<style>
	.marks-summary { margin:.5rem 0 1rem; color:#42544b; font-size:.95rem; }
	.protocol-table-wrap { border:1px solid var(--line); border-radius:6px; }
	.protocol-table { border-collapse:collapse; width:100%; }
	.protocol-table th, .protocol-table td {
		padding:.45rem clamp(.45rem, 1.4vw, 1.1rem);
		border-bottom:1px solid var(--line);
		text-align:left;
	}
	.protocol-table thead th { background:#eef1ed; color:var(--navy); font-size:.88rem; font-weight:700; }
	.protocol-table thead th:first-child { width:28%; border-top-left-radius:5px; }
	.protocol-table thead th:last-child { width:16%; border-top-right-radius:5px; }
	.protocol-table tbody th { padding:0; box-shadow:inset 3px 0 transparent; }
	.protocol-table tr:last-child > td, .protocol-table tbody tr:last-child > th { border-bottom:0; }
	.protocol-table .panel-score { text-align:right; }
	.protocol-table td.panel-score { font-family:var(--mono); font-size:1rem; font-weight:500; }
	.protocol-table .chosen { background:#e5f0ea; }
	.protocol-table .chosen th { box-shadow:inset 3px 0 var(--teal); }
	.element-button {
		display:flex;
		align-items:baseline;
		gap:clamp(.35rem, 1vw, .85rem);
		width:100%;
		min-height:48px;
		padding:.65rem clamp(.45rem, 1.4vw, 1.1rem);
		border:0;
		background:transparent;
		color:var(--navy);
		text-align:left;
		cursor:pointer;
	}
	.element-button:hover .code { text-decoration:underline; text-underline-offset:.2em; }
	.element-button:focus-visible, .mark-button:focus-visible { outline-color:var(--navy); }
	.element-button:focus-visible { outline-offset:-4px; }
	.order { color:#4d6057; font:.77rem var(--mono); }
	.code { font-size:1rem; font-weight:700; overflow-wrap:anywhere; }
	.no-marks { color:#4d6057; font-size:.88rem; }
	.mark-list { display:flex; flex-wrap:wrap; gap:.35rem .5rem; }
	.mark-button {
		display:inline-flex;
		align-items:center;
		gap:.45rem;
		min-height:44px;
		max-width:100%;
		padding:.2rem .55rem;
		border:1px solid #d3a488;
		border-radius:5px;
		background:#fff2e8;
		color:#773a28;
		font-size:.88rem;
		font-weight:600;
		text-align:left;
		cursor:pointer;
	}
	.mark-button:hover { border-color:#773a28; }
	.mark-symbol {
		flex:none;
		min-width:1.6rem;
		padding:.14rem .2rem;
		border-radius:3px;
		background:#793d2d;
		color:white;
		font:500 .9rem var(--mono);
		text-align:center;
	}
	.mark-legend { margin-top:.85rem; color:#42544b; font-size:.88rem; }
	.mark-legend summary { width:fit-content; cursor:pointer; font-weight:600; }
	.mark-legend dl { display:flex; flex-wrap:wrap; gap:.55rem 1.15rem; margin-bottom:0; }
	.mark-legend dl div { display:flex; align-items:baseline; gap:.4rem; }
	.mark-legend dt { color:var(--ink); font:500 .95rem var(--mono); }
	.mark-legend dd { margin:0; }
	@media (max-width:480px) {
		.protocol-table thead th:first-child { width:32%; }
		.protocol-table thead th:last-child { width:23%; }
		.protocol-table td.panel-score { font-size:.9rem; }
		.mark-button { gap:.3rem; padding-inline:.3rem; }
	}
</style>
