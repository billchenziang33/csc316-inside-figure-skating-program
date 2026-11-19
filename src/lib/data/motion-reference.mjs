export function resolveMotion(catalog, element) {
  const occurrence = catalog?.occurrences[element?.id];
  if (!occurrence) return null;
  return { ...occurrence, asset: catalog.assets[occurrence.asset] ?? null };
}
