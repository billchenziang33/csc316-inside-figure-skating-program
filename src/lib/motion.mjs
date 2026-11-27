// One motion language for the whole site. The CSS twins of these values live in app.css (--ease, --dur-*).
// Moves use the standard curve; things that arrive use ease-out; things that leave are shorter and use ease-in.

function bezier(x1, y1, x2, y2) {
	const at = (a, b, t) => ((1 - 3 * b + 3 * a) * t + (3 * b - 6 * a)) * t * t + 3 * a * t;
	const slope = (a, b, t) => 3 * (1 - 3 * b + 3 * a) * t * t + 2 * (3 * b - 6 * a) * t + 3 * a;
	return (x) => {
		if (x <= 0) return 0;
		if (x >= 1) return 1;
		let t = x;
		for (let i = 0; i < 6; i++) {
			const d = slope(x1, x2, t);
			if (Math.abs(d) < 1e-6) break;
			t -= (at(x1, x2, t) - x) / d;
		}
		return at(y1, y2, Math.min(1, Math.max(0, t)));
	};
}

export const EASE = bezier(0.28, 0.11, 0.32, 1);
export const EASE_OUT = bezier(0.2, 0.8, 0.2, 1);
export const EASE_IN = bezier(0.4, 0, 1, 1);
export const DUR = { fast: 150, base: 250, slow: 500 };

export function reducedMotion() {
	return typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
}

// Content that replaces other content in the same place: a short fade with a small rise.
// Pair `in:arrive` and `out:leave` on children stacked in one grid cell (class "swap"), so the old
// content fades out while the new fades in, without the two pushing each other around.
export function arrive(node, { delay = 60, duration = DUR.base, y = 6 } = {}) {
	if (reducedMotion()) return { duration: 0 };
	return { delay, duration, easing: EASE_OUT, css: (t, u) => `opacity:${t};transform:translateY(${u * y}px)` };
}

export function leave(node, { duration = DUR.fast } = {}) {
	if (reducedMotion()) return { duration: 0 };
	return { duration, easing: EASE_IN, css: (t) => `opacity:${t}` };
}

// A panel that opens over the page: fades in and settles from slightly smaller.
export function rise(node, { duration = 320, scale = 0.985 } = {}) {
	if (reducedMotion()) return { duration: 0 };
	return { duration, easing: EASE_OUT, css: (t, u) => `opacity:${t};transform:scale(${1 - u * (1 - scale)})` };
}

// A note that joins or leaves a list: it opens its own space, so the list grows instead of jumping.
export function grow(node, { duration = DUR.base } = {}) {
	if (reducedMotion()) return { duration: 0 };
	const height = node.offsetHeight;
	const style = getComputedStyle(node);
	const pt = parseFloat(style.paddingTop), pb = parseFloat(style.paddingBottom), mb = parseFloat(style.marginBottom);
	return {
		duration,
		easing: EASE,
		css: (t) => `overflow:hidden;opacity:${Math.min(1, t * 1.6)};height:${t * height}px;padding-top:${t * pt}px;padding-bottom:${t * pb}px;margin-bottom:${t * mb}px`
	};
}

// Tween length for a number that changes because the reader chose something.
export function numberTween() {
	return { duration: reducedMotion() ? 0 : 320, easing: EASE_OUT };
}

// Svelte action for a crossfading container (class "stack"): its height glides to the height of the
// newest child, so content below moves smoothly instead of jumping when the swap finishes.
export function fitHeight(node) {
	let watched = null;
	const fit = () => {
		const last = node.lastElementChild;
		if (last) node.style.height = `${last.offsetHeight}px`;
	};
	const size = new ResizeObserver(fit);
	const follow = () => {
		const last = node.lastElementChild;
		if (last === watched) return;
		if (watched) size.unobserve(watched);
		watched = last;
		if (last) size.observe(last);
		fit();
	};
	const children = new MutationObserver(follow);
	children.observe(node, { childList: true });
	node.style.transition = 'none';
	follow();
	requestAnimationFrame(() => { node.style.transition = ''; });
	return { destroy() { size.disconnect(); children.disconnect(); } };
}
