import { readFile, writeFile } from 'node:fs/promises';

const [mediaIndex, ...extraArgs] = process.argv.slice(2);
if (!mediaIndex || extraArgs.length) throw new Error('Usage: node scripts/import-motion-catalog.mjs <media-index.json>');

const staticDir = new URL('../static/movement/beijing-2022/', import.meta.url);
const catalogPath = new URL('catalog.json', staticDir);
const readJson = async (path) => JSON.parse(await readFile(path, 'utf8'));
const catalog = await readJson(catalogPath);
const media = await readJson(mediaIndex);
const origin = 'https://billchenziang33.github.io/figure-skate-database-3d/';
const player = '/movement/beijing-2022/player.html';
const isDigest = (value) => /^[0-9a-f]{64}$/.test(value);

function mediaUrl(filename, digest) {
  const url = new URL(encodeURIComponent(filename), origin);
  if (digest) url.searchParams.set('v', digest.slice(0, 12));
  return url.href;
}

function playerAsset(entry) {
  const { id, name, kind, file, frames, sha256, poster, poster_sha256 } = entry;
  if (!id || !name || !kind || !/^[^/\\]+\.glb$/.test(file) || !isDigest(sha256)
    || !/^[^/\\]+\.(png|jpg|webp)$/.test(poster) || !Number.isSafeInteger(frames) || frames < 2) {
    throw new Error(`Incomplete or invalid motion data for ${id}`);
  }
  const result = {
    id, name, kind, file, frames, sha256,
    model: mediaUrl(file, sha256),
    player: `${player}?id=${encodeURIComponent(id)}`,
    poster: mediaUrl(poster, poster_sha256),
    archived_rounds: entry.archived_rounds ?? entry.rounds?.length ?? 0,
    blender_geometry_reviewed: entry.blender_geometry_reviewed === true,
    blender_technique_reviewed: entry.blender_technique_reviewed === true,
    public_side_view: entry.public_side_view ?? 'pending',
    event_frames: entry.event_frames ?? null,
    motion_label: 'illustrative / simulated',
    note: entry.note ?? '',
  };
  if (entry.source) result.source = entry.source;
  return result;
}

if (!Array.isArray(media) || media.length !== 50 || new Set(media.map(({ id }) => id)).size !== 50) {
  throw new Error('Expected the 50 distinct base actions');
}

catalog.assets = Object.fromEntries(media.map((entry) => [entry.id, playerAsset(entry)]));
catalog.plannedBaseActions = 50;
for (const occurrence of Object.values(catalog.occurrences)) {
  if (!catalog.assets[occurrence.asset]) throw new Error(`No base match for ${occurrence.code}`);
  delete occurrence.variant;
}

await writeFile(catalogPath, `${JSON.stringify(catalog, null, 2)}\n`);
console.log(`Imported ${media.length} base actions for ${Object.keys(catalog.occurrences).length} occurrences.`);
