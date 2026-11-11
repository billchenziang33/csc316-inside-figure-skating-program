import assert from 'node:assert/strict';
import test from 'node:test';
import { fitBoundingSphereDistance, fitOrbitCameraDistance } from '../static/movement/axel-1a-prototype/camera-fit.mjs';

test('fits the whole boot sphere with margin in desktop and portrait viewports', () => {
	for (const aspect of [2.6, 1.5, 0.72]) {
		const radius = 0.24;
		const fov = 37.849;
		const margin = 1.18;
		const distance = fitBoundingSphereDistance({ radius, verticalFovDegrees: fov, aspect, margin });
		const halfVertical = fov * Math.PI / 360;
		const halfHorizontal = Math.atan(Math.tan(halfVertical) * aspect);
		assert.ok(distance * Math.sin(halfVertical) >= radius * margin);
		assert.ok(distance * Math.sin(halfHorizontal) >= radius * margin);
	}
});

test('orbit keeps the full skater in frame when the original camera is too close', () => {
	const distance = fitOrbitCameraDistance({
		cameraDistance: 2.5,
		boundingRadius: 1.25,
		verticalFovDegrees: 50,
		aspect: 0.48,
	});
	const halfHorizontal = Math.atan(Math.tan(50 * Math.PI / 360) * 0.48);
	assert.ok(distance * Math.sin(halfHorizontal) >= 1.25 * 1.18);
});

test('rejects degenerate camera and viewport values', () => {
	for (const input of [
		{ radius: -1, verticalFovDegrees: 40, aspect: 1 },
		{ radius: 1, verticalFovDegrees: 180, aspect: 1 },
		{ radius: 1, verticalFovDegrees: 40, aspect: 0 },
		{ radius: 1, verticalFovDegrees: 40, aspect: 1, margin: 0.9 },
	]) assert.throws(() => fitBoundingSphereDistance(input), RangeError);
});
