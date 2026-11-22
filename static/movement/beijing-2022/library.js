
const progress = document.querySelector('#progress');
const container = document.querySelector('#actions');
const search = document.querySelector('#search');
const filter = document.querySelector('#filter');
const from = new URLSearchParams(location.search).get('from');

async function loadLibrary() {
  const response = await fetch('./catalog.json', { cache: 'no-cache' });
  if (!response.ok) throw new Error(`Motion catalog returned HTTP ${response.status}`);
  const catalog = await response.json();
  const motions = Object.values(catalog.assets);
  const returnToOccurrence = Object.hasOwn(catalog.occurrences, from);
  if (returnToOccurrence) document.querySelector('#workbench').href = `/#workspace/${from}`;

  function cardFor(motion) {
    const card = document.createElement('a');
    card.className = 'card';
    const target = new URL(motion.player, location.origin);
    if (returnToOccurrence) target.searchParams.set('from', from);
    card.href = target.href;
    const image = document.createElement('img');
    image.src = motion.poster;
    image.alt = '';
    image.loading = 'lazy';
    const details = document.createElement('div');
    const title = document.createElement('strong');
    title.textContent = motion.name;
    const play = document.createElement('span');
    play.textContent = 'Play in 3D →';
    details.append(title, play);
    card.append(image, details);
    return card;
  }

  function render() {
    const query = search.value.trim().toLocaleLowerCase();
    const visible = motions.filter((motion) =>
      (!filter.value || motion.kind === filter.value) &&
      (!query || `${motion.id} ${motion.name}`.toLocaleLowerCase().includes(query)));
    container.replaceChildren(...visible.map(cardFor));
    progress.textContent = `${visible.length} of ${catalog.plannedBaseActions} movements shown · ${motions.filter((motion) => motion.file).length} 3D models available`;
  }

  search.addEventListener('input', render);
  filter.addEventListener('change', render);
  render();
}

loadLibrary().catch((error) => {
  console.error(error);
  progress.textContent = 'The movement catalog could not be loaded. Refresh to try again.';
});
