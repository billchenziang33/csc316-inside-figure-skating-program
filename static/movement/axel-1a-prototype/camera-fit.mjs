/** Return a conservative camera distance that keeps a bounding sphere inside a perspective frustum. */
export function fitBoundingSphereDistance({ radius, verticalFovDegrees, aspect, margin = 1.18 }) {
	if (!Number.isFinite(radius) || radius < 0) throw new RangeError('radius must be finite and non-negative');
	if (!Number.isFinite(verticalFovDegrees) || verticalFovDegrees <= 0 || verticalFovDegrees >= 180) {
		throw new RangeError('verticalFovDegrees must be between 0 and 180');
	}
	if (!Number.isFinite(aspect) || aspect <= 0) throw new RangeError('aspect must be positive');
	if (!Number.isFinite(margin) || margin < 1) throw new RangeError('margin must be at least 1');
	if (radius === 0) return 0;

	const halfVertical = verticalFovDegrees * Math.PI / 360;
	const halfHorizontal = Math.atan(Math.tan(halfVertical) * aspect);
	const limitingHalfAngle = Math.min(halfVertical, halfHorizontal);
	return radius * margin / Math.sin(limitingHalfAngle);
}
