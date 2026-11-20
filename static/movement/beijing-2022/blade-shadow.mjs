export function createBodyShadow(THREE, texture) {
	const plane = new THREE.PlaneGeometry(1.8, 1.1).rotateX(-Math.PI / 2);
	const shadow = new THREE.Mesh(plane, new THREE.MeshBasicMaterial({
		map: texture, color: 0x263c4c, transparent: true, opacity: 0, depthWrite: false,
	}));
	shadow.visible = false;
	shadow.renderOrder = 1;
	return shadow;
}

// The lower blade stays on the surface throughout both grounded phases.
export function updateBodyShadow(shadow, clearance, position, iceHeight) {
	const t = Math.max(0, Math.min(1, (clearance - .003) / .18));
	const fade = t * t * (3 - 2 * t);
	shadow.material.opacity = .23 * fade * Math.exp(-1.15 * clearance);
	shadow.scale.setScalar(.78 + .55 * Math.min(clearance, 1.5));
	shadow.position.set(position.x, iceHeight + .001, position.z);
	shadow.visible = fade > 0;
}
