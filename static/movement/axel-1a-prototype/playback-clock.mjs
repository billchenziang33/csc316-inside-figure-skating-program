export function elapsedPlaybackSeconds(now, lastTick, visible = true) {
	if (!visible || !lastTick) return 0;
	return Math.max(0, (now - lastTick) / 1000);
}

export function advancePlaybackTime(currentTime, elapsedSeconds, speed, duration) {
	return Math.min(duration, currentTime + Math.max(0, elapsedSeconds) * speed);
}

export function playbackSpeedFromControl(value) {
	const speed = Number(value);
	return Number.isFinite(speed) && speed > 0 ? speed : 1;
}

export function seekAnimationActions(mixer, actions, time) {
	for (const action of actions) {
		action.enabled = true;
		action.paused = false;
	}
	mixer.setTime(time);
}
