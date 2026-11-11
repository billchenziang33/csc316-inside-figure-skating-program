import test from 'node:test';
import assert from 'node:assert/strict';
import { toggleFullscreen } from '../static/movement/axel-1a-prototype/fullscreen-control.js';

test('denied native fullscreen enters and exits the expanded-view fallback', async () => {
	let fallbackActive = false;
	let nativeRequests = 0;
	const fallback = {
		get active() { return fallbackActive; },
		enter() { fallbackActive = true; },
		exit() { fallbackActive = false; }
	};
	const documentRef = { fullscreenElement: null, exitFullscreen: async () => {} };
	const element = { requestFullscreen: async () => { nativeRequests++; throw new TypeError('not granted'); } };

	assert.equal(await toggleFullscreen({ element, documentRef, fallback }), 'fallback-entered');
	assert.equal(fallback.active, true);
	assert.equal(await toggleFullscreen({ element, documentRef, fallback }), 'fallback-exited');
	assert.equal(fallback.active, false);
	assert.equal(nativeRequests, 1);
});

test('granted native fullscreen continues to use the browser fullscreen API', async () => {
	let requested = false;
	const documentRef = {
		fullscreenElement: null,
		exitFullscreen: async () => { documentRef.fullscreenElement = null; }
	};
	const element = {
		requestFullscreen: async () => {
			requested = true;
			documentRef.fullscreenElement = element;
		}
	};
	const fallback = { active: false, enter() { throw new Error('unexpected fallback'); }, exit() {} };

	assert.equal(await toggleFullscreen({ element, documentRef, fallback }), 'native-entered');
	assert.equal(requested, true);
	assert.equal(await toggleFullscreen({ element, documentRef, fallback }), 'native-exited');
	assert.equal(documentRef.fullscreenElement, null);
});
