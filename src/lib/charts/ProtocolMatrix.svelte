<script>
	import { protocolMarks, protocolMarkLabels } from '../data/derived.mjs';
	let { elements = [], selectedId = null, onSelect = () => {} } = $props();
	const flags = ['!', 'e', 'q', '<', '<<', '*'];
</script>

<div class="matrix-wrap">
	<table class="matrix">
		<thead><tr><th scope="col">Order / element</th>{#each flags as flag (flag)}<th scope="col" title={protocolMarkLabels[flag]}>{flag}</th>{/each}</tr></thead>
		<tbody>
			{#each elements as element (element.id)}
				{@const marks = protocolMarks(element)}
				<tr class:chosen={selectedId === element.id}>
					<th scope="row"><button class="row-button" onclick={() => onSelect(element.id)} aria-pressed={selectedId === element.id}><span>{String(element.element_order).padStart(2,'0')}</span><b>{element.element_code_raw}</b><small>{element.panel_element_score.toFixed(2)}</small></button></th>
					{#each flags as flag (flag)}
						<td>{#if marks.includes(flag)}
							<button class="cell" aria-label={`${element.element_code_raw}, ${flag} · ${protocolMarkLabels[flag]}`} aria-pressed={selectedId === element.id} onclick={() => onSelect(element.id)}>●</button>
						{:else}<span class="empty" aria-hidden="true">·</span>{/if}</td>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>
</div>
<details class="mark-legend">
	<summary>What do these marks mean?</summary>
	<dl>{#each flags as flag (flag)}<div><dt>{flag}</dt><dd>{protocolMarkLabels[flag]}</dd></div>{/each}</dl>
</details>

<style>
	.matrix-wrap{overflow:auto;border:1px solid #e6e8e2;border-radius:4px}
	.matrix{border-collapse:collapse;width:100%;font-size:.72rem}
	.matrix th,.matrix td{border-bottom:1px solid #eceee9;padding:.12rem .18rem;text-align:center}
	.matrix thead th{background:#f4f5f0;color:#59665f;height:29px;font:500 .68rem var(--mono)}
	.matrix thead th:not(:first-child){width:8%}
	.matrix th:first-child{text-align:left;padding-inline:.4rem}
	.matrix tbody th{padding:0}
	.row-button{border:0;background:transparent;color:var(--ink);width:100%;min-height:40px;display:flex;align-items:center;gap:.4rem;text-align:left;padding:.2rem .4rem;cursor:pointer}
	.row-button span,.row-button small{color:#59665f;font:.62rem var(--mono)}
	.row-button b{font-size:.7rem;overflow-wrap:anywhere}
	.row-button small{margin-left:auto}
	.matrix tr.chosen{background:#edf2ed}
	.cell{border:0;background:transparent;color:#9e442f;min-width:24px;min-height:32px;padding:0;cursor:pointer}
	.cell:hover,.cell[aria-pressed=true]{background:#f4e8df;border-radius:4px}
	.empty{color:#747f78}
	.mark-legend{margin-top:.75rem;color:#59665f;font-size:.8rem}
	.mark-legend summary{cursor:pointer}
	.mark-legend dl{display:flex;flex-wrap:wrap;gap:.5rem 1rem;margin-bottom:0}
	.mark-legend dl div{display:flex;align-items:baseline;gap:.3rem}
	.mark-legend dt{color:var(--ink);font:700 .85rem var(--mono)}
	.mark-legend dd{margin:0}
</style>
