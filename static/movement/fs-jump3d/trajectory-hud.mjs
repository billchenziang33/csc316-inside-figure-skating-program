const EVENT_MARKER_PATTERN = /^V102[_\s]+EVENT[_\s]+(TAKEOFF|APEX|LANDING)[_\s]+FRAME[_\s]+(\d+)$/i;

export function readAxelEventFrames(objects) {
	const events = {};
	for (const object of objects) {
		const match = EVENT_MARKER_PATTERN.exec(object.name ?? '');
		if (!match) continue;
		const key = match[1].toLowerCase();
		if (events[key] !== undefined) throw new Error(`Duplicate ${key} event marker in the V102 GLB.`);
		const frame = Number(match[2]);
		if (!Number.isSafeInteger(frame) || frame < 1) throw new Error(`Invalid ${key} event frame in the V102 GLB.`);
		events[key] = frame;
	}
	for (const key of ['takeoff', 'apex', 'landing']) {
		if (events[key] === undefined) throw new Error(`Missing ${key} event marker in the V102 GLB.`);
	}
	if (!(events.takeoff < events.apex && events.apex < events.landing)) {
		throw new Error('V102 event markers are out of order; expected take-off < apex < landing.');
	}
	return events;
}

export function phaseAt(frame, events) {
	const blenderFrame = frame + 1;
	if (blenderFrame < events.takeoff) return 'Approach · simulated';
	if (blenderFrame === events.takeoff) return 'Take-off · simulated';
	if (blenderFrame < events.apex) return 'Ascent · simulated';
	if (blenderFrame === events.apex) return 'Apex · simulated';
	if (blenderFrame < events.landing) return 'Descent · simulated';
	if (blenderFrame === events.landing) return 'Landing · simulated';
	return 'Exit glide · simulated';
}

export function timeAtAnimationFrame(frame, duration, frameCount) {
	if (!Number.isFinite(duration) || duration <= 0 || !Number.isInteger(frameCount) || frameCount < 2) {
		throw new RangeError('Animation duration and frame count must be valid.');
	}
	const clampedFrame = Math.max(1, Math.min(frameCount, frame));
	return ((clampedFrame - 1) / (frameCount - 1)) * duration;
}

export function measureFlightMetrics(current, takeoff, apex, landing) {
	const horizontalDistance = (from, to) => Math.hypot(to.x - from.x, to.z - from.z);
	return {
		heightFromTakeoff: current.y - takeoff.y,
		horizontalDistanceFromTakeoff: horizontalDistance(takeoff, current),
		peakRise: apex.y - takeoff.y,
		totalHorizontalTravel: horizontalDistance(takeoff, landing),
	};
}

export function formatMeters(value, signed = false) {
	const prefix = signed && value > 0 ? '+' : '';
	return `${prefix}${value.toFixed(2)} m`;
}
