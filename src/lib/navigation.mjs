export const stages = [
  { id: 'story', label: 'The finding' },
  { id: 'elements', label: 'Jumps & spins' },
  { id: 'choose', label: 'Choose a program' },
  { id: 'workspace', label: 'Program workbench' },
  { id: 'evidence', label: 'Scoring evidence' },
  { id: 'movement', label: 'Movement reference' }
];
export const chartIds = ['S12', 'S01', 'S02', 'S06', 'S15'];
export const defaultEvidenceChart = 'S15';
const validOccurrence = /^(?:SP|FS):(?:[1-9]|10):(?:[1-9]|1[0-2])$/;

export function readRoute(hash) {
  const [requested, view, occurrence] = String(hash).replace(/^#\/?/, '').split('/');
  if (requested === 'evidence' || requested === 'protocol' || requested === 'charts') {
    const compare = requested === 'charts' || (requested === 'evidence' && (!view || chartIds.includes(view)));
    const route = {
      stage: 'evidence',
      chart: chartIds.includes(view) ? view : requested === 'charts' ? 'S12' : defaultEvidenceChart,
      panel: compare ? 'compare' : 'protocol'
    };
    const id = requested === 'protocol' ? view : occurrence;
    if (validOccurrence.test(id)) route.elementId = id;
    return route;
  }
  const stage = stages.some(s => s.id === requested) || requested === 'chart-detail' ? requested : 'story';
  const route = { stage, chart: chartIds.includes(view) ? view : 'S12' };
  const id = stage === 'chart-detail' ? occurrence : view;
  if (['workspace', 'movement', 'chart-detail'].includes(stage) && validOccurrence.test(id)) route.elementId = id;
  return route;
}
export function routeHash(stage, view, elementId) {
  const path = ['workspace', 'movement'].includes(stage) ? [stage, elementId] : [stage, view, elementId];
  const safe = readRoute(`#${path.join('/')}`);
  const detail = safe.panel === 'protocol' ? 'protocol' : safe.chart;
  const parts = [safe.stage];
  if (safe.stage === 'evidence' || safe.stage === 'chart-detail') parts.push(detail);
  if (safe.elementId) parts.push(safe.elementId);
  return `#${parts.join('/')}`;
}
export function libraryHref(elementId) {
  return '/movement/beijing-2022/' + (validOccurrence.test(elementId) ? `?from=${encodeURIComponent(elementId)}` : '');
}
