// Svelte action: reports which [data-step] child is crossing the middle of the viewport.
// Usage: <ol use:scrolly={{ onStep: (key) => ..., initial: 'S02' }}> <li data-step="S02"> …
export function scrolly(node, options) {
  let { onStep, initial } = options;
  let current = null;

  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      const key = entry.target.dataset.step;
      if (key && key !== current) { current = key; onStep?.(key); }
    }
  }, { rootMargin: isStacked() ? '-72% 0px -18% 0px' : '-45% 0px -45% 0px' });

  const steps = () => [...node.querySelectorAll('[data-step]')];
  steps().forEach((step) => observer.observe(step));

  // A direct link to a later step scrolls it into place once the page has settled.
  const frame = requestAnimationFrame(() => {
    const target = steps().find((step) => step.dataset.step === initial);
    if (target && target !== steps()[0]) scrollToStep(node, initial, { behavior: 'instant', focus: false });
  });

  return {
    update(next) { ({ onStep } = next); },
    destroy() { cancelAnimationFrame(frame); observer.disconnect(); }
  };
}

// Below 1040px the chart is pinned on top, so steps activate in the band beneath it.
const isStacked = () => matchMedia('(max-width: 1040px)').matches;

export function scrollToStep(container, key, { behavior, focus = true } = {}) {
  const step = container?.querySelector(`[data-step="${key}"]`);
  if (!step) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  step.scrollIntoView({ block: isStacked() ? 'end' : 'center', behavior: behavior ?? (reduce ? 'instant' : 'smooth') });
  if (focus) step.querySelector('h3')?.focus({ preventScroll: true });
}
