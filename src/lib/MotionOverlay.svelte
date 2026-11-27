<script>
  import { onMount } from 'svelte';
  import { describeElement } from './data/element-glossary.mjs';
  import { rise, leave } from './motion.mjs';
  let { onClose, motion = null } = $props();
  // The overlay draws its own title bar, so the player hides its own and takes the site's dark look.
  let src = $derived(motion?.player ? `${motion.player}${motion.player.includes('?') ? '&' : '?'}chrome=overlay` : '');
  let dialog;
  let frame = $state(null);
  let demoHtml = $state('');
  let loadError = $state('');
  onMount(() => {
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    dialog.showModal();
    const controller = new AbortController();
    if (!motion) fetch('/movement/axel-1a-prototype/player.html', { signal: controller.signal })
      .then(response => { if (!response.ok) throw new Error(`Demo request failed (${response.status})`); return response.text(); })
      .then(html => { demoHtml = html; })
      .catch(error => { if (error.name !== 'AbortError') loadError = error.message; });
    const closeFromFrame = (event) => {
      if (event.origin === location.origin && event.source === frame?.contentWindow && event.data?.type === 'motion-escape') onClose();
    };
    window.addEventListener('message', closeFromFrame);
    return () => { controller.abort(); window.removeEventListener('message', closeFromFrame); document.body.style.overflow = previousOverflow; previousFocus?.focus?.({ preventScroll: true }); };
  });
</script>

<dialog bind:this={dialog} in:rise|global out:leave|global={{ duration: 200 }} class="motion-overlay" aria-labelledby="motion-overlay-title" oncancel={(event) => { event.preventDefault(); onClose(); }}>
  <header><div><h2 id="motion-overlay-title">{motion ? `${describeElement(motion.id).name} (${motion.id})` : 'Single Axel, Blender v178 3D reference'}</h2><p>A 3D simulation of the technique, not a recording of a skater.</p></div><button onclick={onClose}>Done</button></header>
  {#if motion}<iframe bind:this={frame} {src} allow="fullscreen" title={`${motion.id} Blender animation`}></iframe>{:else if demoHtml}<iframe bind:this={frame} srcdoc={demoHtml} allow="fullscreen" title="Blender v178 Single Axel animation with play, scrub and side/front cameras"></iframe>{:else if loadError}<p role="alert">{loadError}</p>{:else}<p role="status">Loading the Blender v178 animation…</p>{/if}
</dialog>

<style>
  .motion-overlay{position:fixed;inset:0;margin:0;padding:0;width:100vw;max-width:none;height:100dvh;max-height:none;border:0;background:#000;color:#f5f5f7;overflow:hidden}
  .motion-overlay[open]{display:flex;flex-direction:column}.motion-overlay::backdrop{background:#000}
  header{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.6rem 1.2rem;background:#000;border-bottom:1px solid #ffffff1f;flex-shrink:0}
  h2{font:600 1.05rem var(--display);letter-spacing:-.02em;margin:0 0 .15rem}p{font-size:.78rem;color:#a1a1a6;margin:0;line-height:1.4}
  button{font:500 .9rem var(--sans);background:#0071e3;border:0;border-radius:980px;color:#fff;padding:.5rem 1.2rem;min-height:36px;cursor:pointer;flex-shrink:0;transition:background-color var(--dur-fast) var(--ease),transform var(--dur-fast) var(--ease)}button:hover{background:#0077ed}button:active{transform:scale(.97);transition-duration:60ms}button:focus-visible{outline:2px solid #2997ff;outline-offset:3px}
  iframe{width:100%;flex:1;min-height:0;border:0;background:#000}
  @media(max-width:600px){header{padding:.5rem .7rem;gap:.5rem}h2{font-size:.8rem}p{font-size:.62rem}button{font-size:.68rem;padding:.5rem;max-width:145px}}
</style>
