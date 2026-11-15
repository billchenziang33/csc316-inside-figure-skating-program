export function resolveMotion(catalog, element) {
  const occurrence = catalog?.occurrences[element?.id];
  if (!occurrence) return null;
  const variant = occurrence.variant ? catalog.assets[occurrence.variant] : null;
  return {
    ...occurrence,
    asset: variant ?? catalog.assets[occurrence.asset] ?? null,
    usesBase: !variant
  };
}
