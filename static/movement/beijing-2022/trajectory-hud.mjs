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

export function readEventSegments(eventFrames) {
	const takeoffs = Object.entries(eventFrames ?? {})
		.filter(([name, frame]) => /^TAKEOFF_.+/.test(name) && Number.isSafeInteger(Number(frame)))
		.map(([name, takeoff]) => {
			const suffix = name.slice('TAKEOFF_'.length);
			const apex = Number(eventFrames[`APEX_${suffix}`]);
			const landing = Number(eventFrames[`LANDING_${suffix}`]);
			if (!Number.isSafeInteger(apex) || !Number.isSafeInteger(landing) ||
				!(Number(takeoff) < apex && apex < landing)) {
				throw new Error(`Invalid event triplet for ${suffix}.`);
			}
			return { name: suffix, takeoff: Number(takeoff), apex, landing };
		})
		.sort((a, b) => a.takeoff - b.takeoff);

	for (let index = 1; index < takeoffs.length; index++) {
		if (takeoffs[index - 1].landing >= takeoffs[index].takeoff) {
			throw new Error('Jump event segments must be ordered without overlapping flight intervals.');
		}
	}
	return takeoffs;
}

export function selectEventSegment(frame, segments) {
	if (!Array.isArray(segments) || segments.length === 0) return null;
	const blenderFrame = frame + 1;
	const active = segments.find((segment) =>
		blenderFrame >= segment.takeoff && blenderFrame <= segment.landing);
	if (active) return active;
	const previous = segments.filter((segment) => segment.takeoff < blenderFrame).at(-1);
	return previous ?? segments[0];
}

export function phaseAt(frame, events) {
	const blenderFrame = frame + 1;
	const segments = Array.isArray(events?.segments) ? events.segments : null;
	if (segments?.length) {
		if (blenderFrame < segments[0].takeoff) return 'Approach · simulated';
		const active = segments.find((segment) => blenderFrame >= segment.takeoff && blenderFrame <= segment.landing);
		if (active) return `${active.name} · ${phaseAt(frame, active)}`;
		const afterAnyJump = segments.some((segment) => blenderFrame > segment.landing);
		const beforeAnotherJump = segments.some((segment) => blenderFrame < segment.takeoff);
		if (afterAnyJump && beforeAnotherJump) return 'Transition · simulated';
		if (blenderFrame > segments.at(-1).landing) return 'Exit glide · simulated';
		return 'Approach · simulated';
	}
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

/** Cumulative turns from a list of yaw angles (radians) sampled every frame from take-off to landing. */
export function cumulativeTurns(yaws) {
	const turns = [0];
	for (let i = 1; i < yaws.length; i++) {
		let delta = yaws[i] - yaws[i - 1];
		delta -= Math.round(delta / (2 * Math.PI)) * 2 * Math.PI;
		turns.push(turns[i - 1] + Math.abs(delta) / (2 * Math.PI));
	}
	return turns;
}

/** Turns completed in the air at a 0-based player frame for one take-off/landing segment. */
export function turnsAt(frame, segment, turns) {
	const blenderFrame = frame + 1;
	if (!turns?.length || blenderFrame <= segment.takeoff) return 0;
	if (blenderFrame >= segment.landing) return turns.at(-1);
	return turns[Math.min(turns.length - 1, blenderFrame - segment.takeoff)];
}

export function formatTurns(current, total) {
	return `${current.toFixed(1)} / ${total.toFixed(1)}`;
}

/**
 * Smooth a per-frame track of {x, y, z} points with a centred moving average.
 * `half` frames on each side for x and z, `halfY` for y. A step longer than `cut` metres is a camera cut,
 * and the average never reaches across one. A centred window adds no lag to steady travel.
 */
export function smoothTrack(points, half, halfY = half, cut = 1) {
	const breaks = [0];
	for (let i = 1; i < points.length; i++) {
		if (Math.hypot(points[i].x - points[i - 1].x, points[i].y - points[i - 1].y, points[i].z - points[i - 1].z) > cut) breaks.push(i);
	}
	breaks.push(points.length);
	const mean = (key, i, lo, hi, reach) => {
		const from = Math.max(lo, i - reach), to = Math.min(hi - 1, i + reach);
		let sum = 0;
		for (let j = from; j <= to; j++) sum += points[j][key];
		return sum / (to - from + 1);
	};
	const out = [];
	for (let b = 0; b + 1 < breaks.length; b++) {
		const lo = breaks[b], hi = breaks[b + 1];
		for (let i = lo; i < hi; i++) out.push({ x: mean('x', i, lo, hi, half), y: mean('y', i, lo, hi, halfY), z: mean('z', i, lo, hi, half) });
	}
	return out;
}
