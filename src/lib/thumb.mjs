// Svelte action for a segmented control (class "seg"): the light thumb slides from the old option
// to the new one, so the reader sees what changed. Pass the selected key so the thumb follows it.
// The chosen button is the child with aria-selected="true" or aria-pressed="true".
export function slidingThumb(node, key) {
	let frame = 0;

	function place(animate) {
		const chosen = node.querySelector(':scope > [aria-selected="true"], :scope > [aria-pressed="true"]');
		if (!animate) node.dataset.still = '';
		if (chosen) {
			node.style.setProperty('--thumb-x', `${chosen.offsetLeft}px`);
			node.style.setProperty('--thumb-w', `${chosen.offsetWidth}px`);
			node.style.setProperty('--thumb-on', '1');
			// In a strip that scrolls sideways (phones), bring the chosen option into view.
			if (animate && node.scrollWidth > node.clientWidth) chosen.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'smooth' });
		} else node.style.setProperty('--thumb-on', '0');
		if (!animate) requestAnimationFrame(() => requestAnimationFrame(() => delete node.dataset.still));
	}

	// Wait one frame so the buttons' aria state is already updated for the new key.
	const schedule = (animate) => { cancelAnimationFrame(frame); frame = requestAnimationFrame(() => place(animate)); };
	schedule(false);
	// A resize or a late web font moves the options: follow without animating.
	const resize = new ResizeObserver(() => schedule(false));
	resize.observe(node);
	document.fonts?.ready.then(() => schedule(false));

	return {
		update() { schedule(true); },
		destroy() { cancelAnimationFrame(frame); resize.disconnect(); }
	};
}
