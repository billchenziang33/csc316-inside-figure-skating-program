<script>
  import { onMount } from 'svelte';
  let { onClose, skater = '' } = $props();
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
    fetch('/movement/axel-1a-prototype/player.html', { signal: controller.signal })
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

<dialog bind:this={dialog} class="motion-overlay" aria-labelledby="motion-overlay-title" oncancel={(event) => { event.preventDefault(); onClose(); }}>
  <header><div><h2 id="motion-overlay-title">Single Axel · Blender v128 3D reference</h2><p>Illustrative / simulated action · not motion capture of {skater || 'the selected athlete'}</p></div><button onclick={onClose}>Return to the main page ↙</button></header>
  {#if demoHtml}<iframe bind:this={frame} srcdoc={demoHtml} allow="fullscreen" title="Blender v128 Single Axel animation with play, scrub and side/front cameras"></iframe>{:else if loadError}<p role="alert">{loadError}</p>{:else}<p role="status">Loading the Blender v128 animation…</p>{/if}
</dialog>

<style>
  .motion-overlay{position:fixed;inset:0;margin:0;padding:0;width:100vw;max-width:none;height:100dvh;max-height:none;border:0;background:#142c3c;color:#edf4f7;overflow:hidden}
  .motion-overlay[open]{display:flex;flex-direction:column}.motion-overlay::backdrop{background:#101b2c}
  header{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.7rem 1.2rem;background:#101b2c;flex-shrink:0}
  h2{font-size:1rem;margin:0 0 .25rem}p{font-size:.72rem;color:#c7d6d8;margin:0;line-height:1.4}
  button{font:600 .82rem 'DM Sans',Arial,sans-serif;background:#fffefa;border:1px solid #aebfba;border-radius:5px;color:#18382f;padding:.7rem 1rem;min-height:44px;cursor:pointer;flex-shrink:0}button:focus-visible{outline:3px solid #e9ab55;outline-offset:3px}
  iframe{width:100%;flex:1;min-height:0;border:0;background:#142c3c}
  @media(max-width:600px){header{padding:.5rem .7rem;gap:.5rem}h2{font-size:.8rem}p{font-size:.62rem}button{font-size:.68rem;padding:.5rem;max-width:145px}}
</style>
