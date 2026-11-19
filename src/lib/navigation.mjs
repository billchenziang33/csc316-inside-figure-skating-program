export const stages = [
  { id: 'story', label: 'The finding' },
  { id: 'choose', label: 'Choose a program' },
  { id: 'workspace', label: 'Program workbench' },
  { id: 'protocol', label: 'Protocol marks' },
  { id: 'charts', label: 'Compare the evidence' },
  { id: 'movement', label: 'Movement reference' }
];
export const chartIds = ['S12', 'S01', 'S02', 'S06', 'S15'];
const validOccurrence = /^(?:SP|FS):(?:[1-9]|10):(?:[1-9]|1[0-2])$/;

export function readRoute(hash) {
  const [requested, chart] = String(hash).replace(/^#\/?/, '').split('/');
  const stage = stages.some(s => s.id === requested) || requested === 'chart-detail' ? requested : 'story';
  const route = { stage, chart: chartIds.includes(chart) ? chart : 'S12' };
  if (stage === 'workspace' && validOccurrence.test(chart)) route.elementId = chart;
  return route;
}
export function routeHash(stage, chart = 'S12', elementId) {
  const safe = readRoute(`#${stage}/${stage === 'workspace' ? elementId : chart}`);
  const detail = ['charts', 'chart-detail'].includes(safe.stage) ? safe.chart : safe.elementId;
  return `#${safe.stage}${detail ? `/${detail}` : ''}`;
}
export function libraryHref(elementId) {
  return '/movement/beijing-2022/' + (validOccurrence.test(elementId) ? `?from=${encodeURIComponent(elementId)}` : '');
}
