// Svelte action: a plain-English tooltip for an element code.
// One shared, fixed-position tip is used so scrolling lists (overflow:auto) cannot clip it.
// Usage: <button use:elementTip={{ name, notes }}>
const TIP_ID = 'element-tip';

function tipNode() {
  let tip = document.getElementById(TIP_ID);
  if (!tip) {
    tip = document.createElement('div');
    tip.id = TIP_ID;
    tip.className = 'element-tip';
    tip.setAttribute('role', 'tooltip');
    document.body.append(tip);
    void tip.offsetWidth; // settle its hidden state first, so even the first showing fades in
  }
  return tip;
}

export function elementTip(node, content) {
  let current = content;
  let owner = false;

  function show() {
    if (!current?.name) return;
    const tip = tipNode();
    const title = document.createElement('strong');
    title.textContent = current.name;
    const list = document.createElement('ul');
    for (const note of current.notes ?? []) {
      const item = document.createElement('li');
      item.textContent = note;
      list.append(item);
    }
    tip.replaceChildren(title, ...(list.children.length ? [list] : []));
    // Already showing for another code: move it without fading out and in again.
    tip.classList.add('on');
    owner = true;
    node.setAttribute('aria-describedby', TIP_ID);

    // Prefer the right of the element; fall back to below it on narrow screens.
    const r = node.getBoundingClientRect();
    const { width, height } = tip.getBoundingClientRect();
    const gap = 10;
    let left = r.right + gap;
    let top = r.top + r.height / 2 - height / 2;
    if (left + width > innerWidth - 8) {
      left = Math.min(Math.max(8, r.left), innerWidth - width - 8);
      top = r.bottom + gap;
      if (top + height > innerHeight - 8) top = r.top - height - gap;
    }
    tip.style.left = `${Math.round(left)}px`;
    tip.style.top = `${Math.round(Math.max(8, Math.min(top, innerHeight - height - 8)))}px`;
  }

  function hide() {
    if (!owner) return;
    owner = false;
    node.removeAttribute('aria-describedby');
    const tip = document.getElementById(TIP_ID);
    if (tip) tip.classList.remove('on');
  }

  const onKey = (event) => { if (event.key === 'Escape') hide(); };
  const onPointerEnter = (event) => { if (event.pointerType === 'mouse') show(); };
  const onPointerLeave = (event) => { if (event.pointerType === 'mouse') hide(); };
  // On touch screens a tap selects the element and shows its tip; tapping elsewhere hides it.
  const onPointerUp = (event) => { if (event.pointerType !== 'mouse') show(); };
  const onOutside = (event) => { if (owner && !node.contains(event.target)) hide(); };

  node.addEventListener('pointerenter', onPointerEnter);
  node.addEventListener('pointerleave', onPointerLeave);
  node.addEventListener('pointerup', onPointerUp);
  node.addEventListener('focusin', show);
  node.addEventListener('focusout', hide);
  node.addEventListener('keydown', onKey);
  document.addEventListener('pointerdown', onOutside);
  window.addEventListener('scroll', hide, { passive: true, capture: true });

  return {
    update(next) { current = next; if (owner) show(); },
    destroy() {
      hide();
      node.removeEventListener('pointerenter', onPointerEnter);
      node.removeEventListener('pointerleave', onPointerLeave);
      node.removeEventListener('pointerup', onPointerUp);
      node.removeEventListener('focusin', show);
      node.removeEventListener('focusout', hide);
      node.removeEventListener('keydown', onKey);
      document.removeEventListener('pointerdown', onOutside);
      window.removeEventListener('scroll', hide, { capture: true });
    }
  };
}
