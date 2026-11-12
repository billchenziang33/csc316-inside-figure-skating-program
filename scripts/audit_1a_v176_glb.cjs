const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const parse = file => {
  const bytes = readFileSync(file);
  assert.equal(bytes.toString('ascii', 0, 4), 'glTF');
  const chunk = bytes.readUInt32LE(12);
  return [JSON.parse(bytes.toString('utf8', 20, 20+chunk)), bytes.subarray(28+chunk)];
};
function readTracks(file) {
  const [doc, bin] = parse(file);
  const root = doc.nodes.findIndex(n => n.name.includes('Skater root · simulated travel and 1.5-turn yaw v8'));
  assert.notEqual(root, -1);
  const markers = doc.nodes.filter(n => /^V102[_\s]+EVENT[_\s]+/.test(n.name))
      .map(n => [n.name,n.translation]).sort();
  assert.equal(markers.length, 3);
  const track = {};
  for (const anim of doc.animations) for (const channel of anim.channels) {
    if (channel.target.node !== root) continue;
    const sample = anim.samplers[channel.sampler];
    track[channel.target.path] = [sample.input, sample.output].map(index => {
      const a = doc.accessors[index], view = doc.bufferViews[a.bufferView];
      assert.equal(a.componentType, 5126);
      const start = (view.byteOffset ?? 0) + (a.byteOffset ?? 0);
      const comps = {SCALAR:1,VEC3:3,VEC4:4}[a.type];
      return [...new Float32Array(bin.buffer, bin.byteOffset + start, a.count * comps)];
    });
  }
  assert.ok(track.translation);
  assert.ok(track.rotation);
  return {markers, track};
}
const [, , sourcePath, candidatePath, auditYaw] = process.argv;
const [source, candidate] = [sourcePath, candidatePath].map(readTracks);
assert.deepEqual(candidate.markers, source.markers);
assert.deepEqual(candidate.track.translation, source.track.translation);
if (auditYaw !== '--verify-axel-yaw') assert.deepEqual(candidate, source);
const q = candidate.track.rotation[1];
const yaw = [];
for (let i = 0; i < q.length; i += 4) {
  const [x,y,z,w] = q.slice(i,i+4);
  yaw.push(Math.atan2(2*(w*y+x*z),1-2*(y*y+z*z)));
}
const rotation = (from, to) => {
  let result = 0;
  for (let i=from; i<to; i++) {
    const d = yaw[i]-yaw[i-1];
    result += Math.atan2(Math.sin(d),Math.cos(d));
  }
  return result/(2*Math.PI);
};
const turns = rotation(60,92);
if (auditYaw === '--verify-axel-yaw') assert.ok(Math.abs(Math.abs(turns) - 1.5) < .005, 'Wrong f60–f92 airborne yaw');
console.log(JSON.stringify({ markers: candidate.markers.map(m=>m[0]),
  rootTrackSamples: candidate.track.translation[0].length,
  transformChannels: Object.keys(candidate.track), f60to92RootYawTurns:turns }));
