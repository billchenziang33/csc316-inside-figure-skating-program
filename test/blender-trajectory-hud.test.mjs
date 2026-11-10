import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import * as trajectoryHud from '../static/movement/axel-1a-prototype/trajectory-hud.mjs';
const { measureFlightMetrics, timeAtAnimationFrame } = trajectoryHud;

test('flight HUD measures height on Y and travel on the GLB horizontal XZ plane', () => {
	const takeoff = { x: 1, y: 2, z: 3 };
	const apex = { x: 2, y: 2.44, z: 3.3 };
	const landing = { x: 3, y: 2, z: 3.6 };
	const current = { x: 2.2, y: 2.3, z: 3.4 };
	const metrics = measureFlightMetrics(current, takeoff, apex, landing);
	assert.ok(Math.abs(metrics.heightFromTakeoff - 0.3) < 1e-12);
	assert.ok(Math.abs(metrics.horizontalDistanceFromTakeoff - Math.hypot(1.2, 0.4)) < 1e-12);
	assert.ok(Math.abs(metrics.peakRise - 0.44) < 1e-12);
	assert.ok(Math.abs(metrics.totalHorizontalTravel - Math.hypot(2, 0.6)) < 1e-12);
});

test('flight HUD maps 1-based Blender frames onto exported GLB clip time', () => {
	assert.equal(timeAtAnimationFrame(1, 13.25, 160), 0);
	assert.equal(timeAtAnimationFrame(160, 13.25, 160), 13.25);
	assert.equal(timeAtAnimationFrame(73, 13.25, 160), 6);
	assert.equal(timeAtAnimationFrame(73, 13.25, 160), 13.25 * 72 / 159);
});

test('event frames are parsed from normalized Blender marker names', () => {
	assert.equal(typeof trajectoryHud.readAxelEventFrames, 'function');
	const objects = [
		{ name: 'V102_EVENT_TAKEOFF_FRAME_60' },
		{ name: 'V102_EVENT_APEX_FRAME_76' },
		{ name: 'V102_EVENT_LANDING_FRAME_90' },
	];
	assert.deepEqual(trajectoryHud.readAxelEventFrames(objects), { takeoff: 60, apex: 76, landing: 90 });
});

test('exported V102 GLB contains the audited event frame markers', async () => {
	const path = new URL('../static/movement/axel-1a-prototype/single-axel-1a-human-rink-v102-web.glb', import.meta.url);
	const binary = await readFile(path);
	assert.equal(binary.toString('ascii', 0, 4), 'glTF');
	const jsonLength = binary.readUInt32LE(12);
	const document = JSON.parse(binary.toString('utf8', 20, 20 + jsonLength));
	assert.deepEqual(trajectoryHud.readAxelEventFrames(document.nodes), { takeoff: 60, apex: 76, landing: 90 });
});

test('event parser rejects incomplete or non-monotonic marker metadata', () => {
	assert.equal(typeof trajectoryHud.readAxelEventFrames, 'function');
	assert.throws(() => trajectoryHud.readAxelEventFrames([
		{ name: 'V102_EVENT_TAKEOFF_FRAME_60' },
		{ name: 'V102_EVENT_APEX_FRAME_76' },
	]), /landing/i);
	assert.throws(() => trajectoryHud.readAxelEventFrames([
		{ name: 'V102_EVENT_TAKEOFF_FRAME_60' },
		{ name: 'V102_EVENT_APEX_FRAME_59' },
		{ name: 'V102_EVENT_LANDING_FRAME_90' },
	]), /order/i);
});

test('simulated phase boundaries follow the exported event frames', () => {
	assert.equal(typeof trajectoryHud.phaseAt, 'function');
	const events = { takeoff: 60, apex: 76, landing: 90 };
	assert.equal(trajectoryHud.phaseAt(58, events), 'Approach · simulated');
	assert.equal(trajectoryHud.phaseAt(59, events), 'Take-off · simulated');
	assert.equal(trajectoryHud.phaseAt(60, events), 'Ascent · simulated');
	assert.equal(trajectoryHud.phaseAt(75, events), 'Apex · simulated');
	assert.equal(trajectoryHud.phaseAt(76, events), 'Descent · simulated');
	assert.equal(trajectoryHud.phaseAt(89, events), 'Landing · simulated');
	assert.equal(trajectoryHud.phaseAt(90, events), 'Exit glide · simulated');
});
