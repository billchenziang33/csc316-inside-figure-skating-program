import test from 'node:test';
import assert from 'node:assert/strict';
import { advancePlaybackTime, elapsedPlaybackSeconds, playbackSpeedFromControl, seekAnimationActions } from '../static/movement/axel-1a-prototype/playback-clock.mjs';

test('visible playback advances by the full elapsed interval', () => {
	assert.equal(elapsedPlaybackSeconds(2_000, 1_000, true), 1);
	assert.equal(advancePlaybackTime(1, 1, 1, 13.33), 2);
});

test('hidden playback contributes no elapsed time', () => {
	assert.equal(elapsedPlaybackSeconds(15_000, 1_000, false), 0);
	assert.equal(advancePlaybackTime(1, elapsedPlaybackSeconds(15_000, 1_000, false), 1, 13.33), 1);
});

test('elapsed intervals never move the clock backward', () => {
	assert.equal(elapsedPlaybackSeconds(900, 1_000, true), 0);
});

test('playback speed always comes from the current UI control value', () => {
	assert.equal(playbackSpeedFromControl('0.35'), 0.35);
	assert.equal(playbackSpeedFromControl('1'), 1);
	assert.equal(playbackSpeedFromControl('invalid'), 1);
	assert.equal(advancePlaybackTime(2, 4, playbackSpeedFromControl('0.35'), 13.33), 3.4);
});

test('seeking after a clamped animation end re-enables actions before updating mixer time', () => {
	const actions = [{ enabled: true, paused: true }, { enabled: false, paused: true }];
	let observedAtSetTime;
	const mixer = {
		setTime(time) {
			observedAtSetTime = { time, actions: actions.map(({ enabled, paused }) => ({ enabled, paused })) };
		},
	};

	seekAnimationActions(mixer, actions, 7.25);

	assert.deepEqual(observedAtSetTime, {
		time: 7.25,
		actions: [{ enabled: true, paused: false }, { enabled: true, paused: false }],
	});
});
