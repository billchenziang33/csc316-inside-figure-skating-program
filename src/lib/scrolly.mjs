// Svelte action: reports which [data-step] child is crossing the middle of the viewport.
// Usage: <ol use:scrolly={{ onStep: (key) => ..., initial: 'S02' }}> <li data-step="S02"> …
export function scrolly(node, options) {
  let { onStep, initial } = options;
  let observer;

  const steps = () => [...node.querySelectorAll('[data-step]')];
  const observeSteps = () => {
    observer?.disconnect();
    const { top, bottom, height } = triggerBand();
    observer = new IntersectionObserver((entries) => {
      if (!node.isConnected) return;
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const key = entry.target.dataset.step;
        if (key) onStep?.(key);
      }
    }, { rootMargin: `-${top}px 0px -${height - bottom}px 0px` });
    steps().forEach((step) => observer.observe(step));
  };
  observeSteps();
  window.addEventListener('resize', observeSteps);

  // A direct link to a later step scrolls it into place once the page has settled.
  const frame = requestAnimationFrame(() => {
    const target = steps().find((step) => step.dataset.step === initial);
    if (target && target !== steps()[0]) scrollToStep(node, initial, { behavior: 'instant', focus: false });
  });

  return {
    update(next) { ({ onStep } = next); },
    destroy() {
      cancelAnimationFrame(frame);
      window.removeEventListener('resize', observeSteps);
      observer.disconnect();
    }
  };
}

// Below 1040px the chart is pinned on top, so steps activate in the band beneath it.
function triggerBand() {
  const height = window.innerHeight;
  const stacked = matchMedia('(max-width: 1040px)').matches;
  return { top: height * (stacked ? 0.72 : 0.45), bottom: height * (stacked ? 0.82 : 0.55), height };
}

export function scrollToStep(container, key, { behavior, focus = true } = {}) {
  const step = container?.querySelector(`[data-step="${key}"]`);
  if (!step) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const { top, bottom } = triggerBand();
  const bounds = step.getBoundingClientRect();
  window.scrollTo({
    top: window.scrollY + bounds.top + bounds.height / 2 - (top + bottom) / 2,
    behavior: behavior ?? (reduce ? 'instant' : 'smooth')
  });
  if (focus) step.querySelector('h3')?.focus({ preventScroll: true });
}
