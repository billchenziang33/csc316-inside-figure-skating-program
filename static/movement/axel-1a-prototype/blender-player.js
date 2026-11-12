import { findExportedNameMatch, findExportedNamesByPrefix } from './camera-name.mjs';
import { fitBoundingSphereDistance, fitOrbitCameraDistance } from './camera-fit.mjs';
import { toggleFullscreen } from './fullscreen-control.js';
import { advancePlaybackTime, elapsedPlaybackSeconds, playbackSpeedFromControl, seekAnimationActions } from './playback-clock.mjs?v=100';
import { formatMeters, measureFlightMetrics, phaseAt, readAxelEventFrames, timeAtAnimationFrame } from './trajectory-hud.mjs?v=102';

const THREE = globalThis.THREE;
const GLTFLoader = THREE?.GLTFLoader;

const FILE = '/movement/axel-1a-prototype/single-axel-1a-human-rink-v178-web.glb';
const CAMERA_NAMES = [
	'Action side view · horizontal follow composition',
	'Action front view',
	'Skate inspection · close view',
	'Arena overview · full 60×30 rink',
	'Action skater-facing follow view v121',
	'Action skater side profile full-body v124',
];
const canvas = document.querySelector('#blender-stage');
const shell = document.querySelector('#stage-shell');
const message = document.querySelector('#stage-message');
const playButton = document.querySelector('#blender-play');
const resetButton = document.querySelector('#blender-reset');
const frameSlider = document.querySelector('#blender-frame');
const counter = document.querySelector('#blender-counter');
const speedSelect = document.querySelector('#blender-speed');
const fullscreenButton = document.querySelector('#blender-fullscreen');
const cameraResetButton = document.querySelector('#blender-camera-reset');
const cameraButtons = [...document.querySelectorAll('[data-camera]')];
const phaseHud = document.querySelector('#flight-phase');
const heightHud = document.querySelector('#flight-height');
const distanceHud = document.querySelector('#flight-distance');
const peakHud = document.querySelector('#flight-peak');
const totalHud = document.querySelector('#flight-total');

let renderer;
let modelScene;
let sceneObjects = [];
let activeCamera;
let sourceCamera;
let viewerCamera;
let mixer;
let clipActions = [];
let animationTrackCount = 0;
let duration = 0;
let animationStartTime = 0;
let frameCount = 160;
let playbackTime = 0;
let playing = false;
let lastTick = 0;
let inspectionSkates;
let skaterSideCamera;
let inspectionCamera;
let arenaCamera;
let followInspection = false;
let orbitEnabled = false;
let orbitYaw = 0;
let orbitPitch = 0;
let orbitZoom = 1;
const orbitPan = new THREE.Vector3();
let dragPointerId = null;
let dragMode = 'orbit';
let lastPointerX = 0;
let lastPointerY = 0;
let trajectoryRoot;
let trajectoryEventFrames;
let trajectoryPoints;
let trajectoryGuides = [];
const inspectionDirection = new THREE.Vector3();
const inspectionOrientation = new THREE.Quaternion();
const inspectionTarget = new THREE.Vector3();
const inspectionCameraPosition = new THREE.Vector3();
const inspectionBox = new THREE.Box3();
const trajectoryPosition = new THREE.Vector3();
const cameraWorldPosition = new THREE.Vector3();
const cameraWorldQuaternion = new THREE.Quaternion();
const orbitTarget = new THREE.Vector3();
const orbitOffset = new THREE.Vector3();
const orbitFitBounds = new THREE.Box3();
const orbitFitSphere = new THREE.Sphere();
const cameraRight = new THREE.Vector3();
const cameraUp = new THREE.Vector3();
const arenaBounds = new THREE.Box3();
const arenaTarget = new THREE.Vector3();
let arenaObject;
let iceHeight;
let skateShadows = [];
const shadowDirection = new THREE.Vector3();
const shadowCenter = new THREE.Vector3();
const shadowBounds = new THREE.Box3();

function createSkateShadows() {
	const textureCanvas = document.createElement('canvas');
	textureCanvas.width = textureCanvas.height = 64;
	const context = textureCanvas.getContext('2d');
	const falloff = context.createRadialGradient(32, 32, 0, 32, 32, 32);
	falloff.addColorStop(0, 'rgba(255,255,255,1)');
	falloff.addColorStop(0.45, 'rgba(255,255,255,.75)');
	falloff.addColorStop(1, 'rgba(255,255,255,0)');
	context.fillStyle = falloff;
	context.fillRect(0, 0, 64, 64);
	const texture = new THREE.CanvasTexture(textureCanvas);
	const geometry = new THREE.PlaneGeometry(.57, .21).rotateX(-Math.PI / 2);
	iceHeight = shadowBounds.setFromObject(arenaObject).max.y;
	skateShadows = [inspectionSkates[1], inspectionSkates[3]].map((runner) => {
		const surfaces = [];
		runner.traverse((part) => {
			const positions = part.geometry?.getAttribute('position');
			if (positions) surfaces.push({ part, positions });
		});
		const material = new THREE.MeshBasicMaterial({
			map: texture, color: 0x223646, transparent: true, depthWrite: false,
		});
		const shadow = new THREE.Mesh(geometry, material);
		shadow.renderOrder = 2;
		modelScene.add(shadow);
		return { runner, surfaces, shadow };
	});
}

function updateSkateShadows() {
	for (const { runner, surfaces, shadow } of skateShadows) {
		let lowest = Infinity;
		for (const { part, positions } of surfaces) {
			const matrix = part.matrixWorld.elements;
			for (let i = 0; i < positions.count; i++) {
				const y = matrix[1] * positions.getX(i) + matrix[5] * positions.getY(i) +
					matrix[9] * positions.getZ(i) + matrix[13];
				lowest = Math.min(lowest, y);
			}
		}
		const gap = Math.max(0, lowest - iceHeight);
		shadow.visible = gap < .26;
		if (!shadow.visible) continue;
		shadowBounds.setFromObject(runner).getCenter(shadowCenter);
		shadow.position.set(shadowCenter.x, iceHeight + .002, shadowCenter.z);
		shadowDirection.set(0, 0, 1).transformDirection(runner.matrixWorld);
		shadow.rotation.y = Math.atan2(-shadowDirection.z, shadowDirection.x);
		shadow.scale.setScalar(1 + 1.5 * gap);
		shadow.material.opacity = .53 * Math.exp(-16 * gap);
	}
}

function frameFromTime(time) {
	return Math.min(frameCount - 1, Math.max(0, Math.round(time / duration * (frameCount - 1))));
}

function updateInspectionCamera() {
	if (!followInspection || !activeCamera) return;
	modelScene.updateMatrixWorld(true);
	inspectionBox.makeEmpty();
	for (const skatePart of inspectionSkates) inspectionBox.expandByObject(skatePart);
	inspectionBox.getCenter(inspectionTarget);
	skaterSideCamera.getWorldQuaternion(inspectionOrientation);
	inspectionDirection.set(0.27, 0.04, 1).applyQuaternion(inspectionOrientation).normalize();
	const aspect = viewerCamera?.aspect || inspectionCamera.aspect || 1.5;
	const sphere = inspectionBox.getBoundingSphere(new THREE.Sphere());
	const fitDistance = fitBoundingSphereDistance({
		radius: sphere.radius,
		verticalFovDegrees: inspectionCamera.fov,
		aspect,
		margin: 1.18,
	});
	inspectionCameraPosition.copy(inspectionTarget).addScaledVector(inspectionDirection, fitDistance);
	if (activeCamera.parent) {
		activeCamera.parent.updateWorldMatrix(true, false);
		activeCamera.position.copy(activeCamera.parent.worldToLocal(inspectionCameraPosition.clone()));
	} else {
		activeCamera.position.copy(inspectionCameraPosition);
	}
	activeCamera.up.set(0, 1, 0);
	activeCamera.lookAt(inspectionTarget);
	activeCamera.updateMatrixWorld(true);
}

function resize() {
	if (!renderer || !activeCamera) return;
	const width = Math.max(1, shell.clientWidth);
	const height = Math.max(1, shell.clientHeight);
	renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
	renderer.setSize(width, height, false);
	if (activeCamera.isPerspectiveCamera) {
		activeCamera.aspect = width / height;
		activeCamera.updateProjectionMatrix();
	}
	if (followInspection) {
		updateInspectionCamera();
		updateViewerCamera();
	}
	renderer.render(modelScene, activeCamera);
}

function phaseLabel(frame) {
	if (frame + 1 === trajectoryEventFrames.takeoff) return 'Take-off · skater’s left foot';
	if (frame + 1 === trajectoryEventFrames.landing) return 'Landing · skater’s right foot';
	return phaseAt(frame, trajectoryEventFrames);
}

function setPlaybackTime(time, updateSlider = true) {
	if (!activeCamera) throw new Error('The v178 GLB camera was not resolved.');
	playbackTime = Math.max(0, Math.min(duration, time));
	seekAnimationActions(mixer, clipActions, animationStartTime + playbackTime);
	modelScene.updateMatrixWorld(true);
	updateSkateShadows();
	updateInspectionCamera();
	updateViewerCamera();
	const frame = frameFromTime(playbackTime);
	if (updateSlider) frameSlider.value = String(frame);
	counter.textContent = `Frame ${frame + 1} / ${frameCount} · ${phaseLabel(frame)}`;
	updateFlightHud(frame);
	renderer.render(modelScene, activeCamera);
}

function updateFlightHud(frame) {
	if (!trajectoryRoot || !trajectoryPoints) return;
	trajectoryRoot.getWorldPosition(trajectoryPosition);
	const current = { x: trajectoryPosition.x, y: trajectoryPosition.y, z: trajectoryPosition.z };
	const { takeoff, apex, landing } = trajectoryPoints;
	const metrics = measureFlightMetrics(current, takeoff, apex, landing);
	phaseHud.textContent = phaseLabel(frame);
	heightHud.textContent = formatMeters(metrics.heightFromTakeoff, true);
	distanceHud.textContent = formatMeters(metrics.horizontalDistanceFromTakeoff);
	peakHud.textContent = formatMeters(metrics.peakRise);
	totalHud.textContent = formatMeters(metrics.totalHorizontalTravel);
}

function sampleTrajectoryEvents() {
	const restoreTime = playbackTime;
	const sample = (frame) => {
		seekAnimationActions(mixer, clipActions,
			animationStartTime + timeAtAnimationFrame(frame, duration, frameCount));
		modelScene.updateMatrixWorld(true);
		trajectoryRoot.getWorldPosition(trajectoryPosition);
		return { x: trajectoryPosition.x, y: trajectoryPosition.y, z: trajectoryPosition.z };
	};
	trajectoryPoints = {
		takeoff: sample(trajectoryEventFrames.takeoff),
		apex: sample(trajectoryEventFrames.apex),
		landing: sample(trajectoryEventFrames.landing),
	};
	seekAnimationActions(mixer, clipActions, animationStartTime + restoreTime);
	modelScene.updateMatrixWorld(true);
}

function updateViewerCamera() {
	if (!sourceCamera || !viewerCamera) return;
	modelScene.updateMatrixWorld(true);
	if (followInspection) {
		cameraWorldPosition.copy(inspectionCameraPosition);
	} else {
		sourceCamera.getWorldPosition(cameraWorldPosition);
		sourceCamera.getWorldQuaternion(cameraWorldQuaternion);
	}
	if (!orbitEnabled) {
		if (!followInspection) {
			viewerCamera.position.copy(cameraWorldPosition);
			viewerCamera.quaternion.copy(cameraWorldQuaternion);
		}
	} else {
		let orbitFitRadius = 0;
		if (followInspection) {
			orbitTarget.copy(inspectionTarget);
			inspectionBox.getBoundingSphere(orbitFitSphere);
			orbitFitRadius = orbitFitSphere.radius;
		} else if (sourceCamera === arenaCamera && arenaObject) {
			arenaBounds.setFromObject(arenaObject);
			arenaBounds.getBoundingSphere(orbitFitSphere);
			arenaTarget.copy(orbitFitSphere.center);
			orbitTarget.copy(arenaTarget);
			orbitFitRadius = orbitFitSphere.radius;
		} else {
			orbitFitBounds.setFromObject(trajectoryRoot);
			orbitFitBounds.getBoundingSphere(orbitFitSphere);
			orbitTarget.copy(orbitFitSphere.center);
			orbitFitRadius = orbitFitSphere.radius;
		}
		orbitOffset.copy(cameraWorldPosition).sub(orbitTarget);
		const baseRadius = Math.max(0.25, cameraWorldPosition.distanceTo(orbitTarget));
		const radius = fitOrbitCameraDistance({
			cameraDistance: baseRadius,
			boundingRadius: orbitFitRadius,
			verticalFovDegrees: sourceCamera.fov,
			aspect: viewerCamera.aspect || 1,
			zoom: orbitZoom,
		});
		const theta = Math.atan2(orbitOffset.x, orbitOffset.z) + orbitYaw;
		const phi = THREE.MathUtils.clamp(Math.acos(THREE.MathUtils.clamp(orbitOffset.y / baseRadius, -1, 1)) + orbitPitch, 0.08, Math.PI - 0.08);
		orbitTarget.add(orbitPan);
		viewerCamera.position.set(
			orbitTarget.x + radius * Math.sin(phi) * Math.sin(theta),
			orbitTarget.y + radius * Math.cos(phi),
			orbitTarget.z + radius * Math.sin(phi) * Math.cos(theta),
		);
		viewerCamera.up.set(0, 1, 0);
		viewerCamera.lookAt(orbitTarget);
	}
	viewerCamera.near = sourceCamera.near;
	viewerCamera.far = sourceCamera.far;
	viewerCamera.fov = sourceCamera.fov;
	viewerCamera.zoom = sourceCamera.zoom;
	viewerCamera.updateProjectionMatrix();
	viewerCamera.updateMatrixWorld(true);
}

function resetView() {
	orbitEnabled = false;
	orbitYaw = 0;
	orbitPitch = 0;
	orbitZoom = 1;
	orbitPan.set(0, 0, 0);
	updateViewerCamera();
	resize();
}

function chooseCamera(name) {
	const selectedCamera = findExportedNameMatch(sceneObjects, name);
	if (!selectedCamera?.isCamera) {
		const available = [];
		modelScene.traverse((object) => { if (object.isCamera) available.push(`${object.name}:${object.constructor.name}`); });
		throw new Error(`Camera not found: ${name}; available cameras: ${available.join(', ') || '(none)'}`);
	}
	selectedCamera.updateWorldMatrix(true, false);
	sourceCamera = selectedCamera;
	activeCamera = viewerCamera;
	followInspection = sourceCamera === inspectionCamera;
	orbitEnabled = false;
	orbitYaw = 0;
	orbitPitch = 0;
	orbitZoom = 1;
	orbitPan.set(0, 0, 0);
	for (const guide of trajectoryGuides) guide.visible = !followInspection;
	updateInspectionCamera();
	updateViewerCamera();
	for (const button of cameraButtons) {
		button.setAttribute('aria-pressed', String(button.dataset.camera === name));
	}
	cameraResetButton.disabled = false;
	resize();
}

function animate(now) {
	requestAnimationFrame(animate);
	if (!renderer || !activeCamera) return;
	const elapsed = elapsedPlaybackSeconds(now, lastTick, document.visibilityState === 'visible');
	lastTick = now;
	if (playing && document.visibilityState === 'visible') {
		const next = advancePlaybackTime(playbackTime, elapsed, playbackSpeedFromControl(speedSelect.value), duration);
		setPlaybackTime(next);
		if (next >= duration) {
			playing = false;
			playButton.textContent = 'Play';
		}
	}
	updateViewerCamera();
	renderer.render(modelScene, activeCamera);
}

async function start() {
	try {
		if (!THREE || !GLTFLoader) throw new Error('The bundled Three.js runtime did not load.');
		renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
		renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
		renderer.outputColorSpace = THREE.SRGBColorSpace;
		renderer.toneMapping = THREE.ACESFilmicToneMapping;
		renderer.toneMappingExposure = 1.05;
		modelScene = new THREE.Scene();
		modelScene.background = new THREE.Color('#c9dce1');
		modelScene.add(new THREE.HemisphereLight(0xeaf7ff, 0x415667, 1.5));
		const key = new THREE.DirectionalLight(0xfff6e9, 2.3);
		key.position.set(-8, 12, 10);
		modelScene.add(key);
		const fill = new THREE.DirectionalLight(0xc4e8ff, 1.0);
		fill.position.set(10, 7, -8);
		modelScene.add(fill);
		viewerCamera = new THREE.PerspectiveCamera(50, 1, 0.01, 200);
		viewerCamera.name = 'Interactive orbit camera';
		modelScene.add(viewerCamera);

		const loader = new GLTFLoader();
		const gltf = await loader.loadAsync(FILE);
		modelScene.add(gltf.scene);
		modelScene.traverse((object) => sceneObjects.push(object));
		trajectoryGuides = findExportedNamesByPrefix(sceneObjects, 'V102');
		trajectoryRoot = findExportedNameMatch(sceneObjects, 'Skater root · simulated travel and 1.5-turn yaw v8');
		inspectionSkates = ['Left', 'Right'].flatMap((side) => ['boot', 'blade'].map((part) =>
			findExportedNameMatch(sceneObjects, `${side} skate · website ${part} v64`)));
		inspectionCamera = findExportedNameMatch(sceneObjects, CAMERA_NAMES[2]);
		arenaCamera = findExportedNameMatch(sceneObjects, CAMERA_NAMES[3]);
		const skaterFollowCamera = findExportedNameMatch(sceneObjects, CAMERA_NAMES[4]);
		skaterSideCamera = findExportedNameMatch(sceneObjects, CAMERA_NAMES[5]);
		arenaObject = findExportedNameMatch(sceneObjects, 'V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)');
		if (inspectionSkates.some((part) => !part) || !inspectionCamera?.isCamera || !arenaCamera?.isCamera || !skaterFollowCamera?.isCamera || !skaterSideCamera?.isCamera || !arenaObject) {
			throw new Error('The v178 skate inspection, arena, skater-follow or side-profile camera is missing.');
		}
		createSkateShadows();
		const clips = gltf.animations;
		animationTrackCount = clips.reduce((count, clip) => count + clip.tracks.length, 0);
		if (!clips.length || animationTrackCount < 80) {
			throw new Error('The v178 GLB did not contain the expected articulated 3D action.');
		}
		const rootPositionTrack = clips.flatMap((clip) => clip.tracks).find((track) =>
			track.name.startsWith(trajectoryRoot.name) && track.name.endsWith('.position'));
		if (!rootPositionTrack || rootPositionTrack.times.length !== frameCount) {
			throw new Error('The v178 root track does not contain the expected frame samples.');
		}
		animationStartTime = rootPositionTrack.times[0];
		duration = rootPositionTrack.times.at(-1) - animationStartTime;
		if (!Number.isFinite(duration) || duration <= 0) throw new Error('The v178 animation has no usable duration.');
		mixer = new THREE.AnimationMixer(gltf.scene);
		clipActions = clips.map((clip) => {
			const action = mixer.clipAction(clip);
			action.setLoop(THREE.LoopOnce, 1);
			action.clampWhenFinished = true;
			action.play();
			return action;
		});
		if (!trajectoryRoot) throw new Error('The v178 GLB is missing its animated skater root track.');
		trajectoryEventFrames = readAxelEventFrames(sceneObjects);
		if (Object.values(trajectoryEventFrames).some((frame) => frame > frameCount)) {
			throw new Error('A V102 inherited trajectory event is outside the exported animation frame range.');
		}
		sampleTrajectoryEvents();
		inspectionCamera.zoom = 1.0;
		inspectionCamera.near = 0.01;
		inspectionCamera.updateProjectionMatrix();
		mixer.setTime(animationStartTime);
		modelScene.updateMatrixWorld(true);
		chooseCamera(CAMERA_NAMES[5]);
		frameSlider.disabled = false;
		playButton.disabled = false;
		resetButton.disabled = false;
		fullscreenButton.disabled = false;
		cameraResetButton.disabled = false;
		setPlaybackTime(0);
		message.textContent = `Ready · Blender v178 · ${(duration).toFixed(2)} s · ${animationTrackCount} animated channels · ${renderer.info.render.calls} draw calls`;
		requestAnimationFrame(animate);
	} catch (error) {
		console.error('Blender v178 player failed to load:', error);
		message.textContent = `3D playback failed: ${error.message}. Open README for the .blend and fallback previews.`;
		message.setAttribute('data-error', 'true');
	}
}

playButton.addEventListener('click', () => {
	if (!duration) return;
	if (!playing && playbackTime >= duration) setPlaybackTime(0);
	playing = !playing;
	lastTick = 0;
	playButton.textContent = playing ? 'Pause' : 'Play';
});

resetButton.addEventListener('click', () => {
	playing = false;
	playButton.textContent = 'Play';
	setPlaybackTime(0);
});

document.addEventListener('visibilitychange', () => {
	lastTick = 0;
	if (document.hidden && playing) {
		playing = false;
		playButton.textContent = 'Play';
	}
});

frameSlider.addEventListener('input', () => {
	playing = false;
	playButton.textContent = 'Play';
	setPlaybackTime((Number(frameSlider.value) / (frameCount - 1)) * duration, false);
});

cameraButtons.forEach((button) => button.addEventListener('click', () => chooseCamera(button.dataset.camera)));
cameraResetButton.addEventListener('click', resetView);
canvas.addEventListener('pointerdown', (event) => {
	if ((event.button !== 0 && event.button !== 2) || !activeCamera) return;
	dragPointerId = event.pointerId;
	dragMode = event.button === 2 || event.shiftKey ? 'pan' : 'orbit';
	lastPointerX = event.clientX;
	lastPointerY = event.clientY;
	canvas.setPointerCapture(event.pointerId);
	canvas.classList.toggle('is-panning', dragMode === 'pan');
	canvas.classList.toggle('is-dragging', dragMode === 'orbit');
	event.preventDefault();
});
canvas.addEventListener('pointermove', (event) => {
	if (dragPointerId !== event.pointerId) return;
	const dx = event.clientX - lastPointerX;
	const dy = event.clientY - lastPointerY;
	lastPointerX = event.clientX;
	lastPointerY = event.clientY;
	orbitEnabled = true;
	if (dragMode === 'pan') {
		updateViewerCamera();
		cameraRight.set(1, 0, 0).applyQuaternion(viewerCamera.quaternion).normalize();
		cameraUp.set(0, 1, 0).applyQuaternion(viewerCamera.quaternion).normalize();
		const radius = viewerCamera.position.distanceTo(orbitTarget);
		const worldUnitsPerPixel = 2 * radius * Math.tan(THREE.MathUtils.degToRad(viewerCamera.fov) / 2) / Math.max(1, canvas.clientHeight);
		orbitPan.addScaledVector(cameraRight, -dx * worldUnitsPerPixel);
		orbitPan.addScaledVector(cameraUp, dy * worldUnitsPerPixel);
	} else {
		orbitYaw -= dx * 0.003;
		orbitPitch += dy * 0.003;
	}
	updateViewerCamera();
	renderer.render(modelScene, activeCamera);
});
const endOrbitDrag = (event) => {
	if (dragPointerId !== event.pointerId) return;
	if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
	dragPointerId = null;
	canvas.classList.remove('is-panning');
	canvas.classList.remove('is-dragging');
};
canvas.addEventListener('pointerup', endOrbitDrag);
canvas.addEventListener('pointercancel', endOrbitDrag);
canvas.addEventListener('contextmenu', (event) => event.preventDefault());
canvas.addEventListener('wheel', (event) => {
	if (!activeCamera) return;
	event.preventDefault();
	orbitEnabled = true;
	orbitZoom = THREE.MathUtils.clamp(orbitZoom * Math.exp(event.deltaY * 0.001), 0.35, 3.5);
	updateViewerCamera();
	renderer.render(modelScene, activeCamera);
}, { passive: false });
fullscreenButton.addEventListener('click', async () => {
	const fallback = {
		get active() { return document.body.classList.contains('css-fullscreen'); },
		enter() { document.body.classList.add('css-fullscreen'); },
		exit() { document.body.classList.remove('css-fullscreen'); },
	};
	await toggleFullscreen({ element: shell, documentRef: document, fallback });
	fullscreenButton.textContent = document.fullscreenElement || fallback.active ? 'Exit fullscreen' : 'Fullscreen';
	resize();
});
document.addEventListener('fullscreenchange', () => {
	fullscreenButton.textContent = document.fullscreenElement ? 'Exit fullscreen' : 'Fullscreen';
	resize();
});
document.addEventListener('keydown', (event) => {
	if (event.key !== 'Escape' || !document.body.classList.contains('css-fullscreen')) return;
	event.preventDefault();
	event.stopPropagation();
	document.body.classList.remove('css-fullscreen');
	fullscreenButton.textContent = 'Fullscreen';
	resize();
});
window.addEventListener('resize', resize);
new ResizeObserver(resize).observe(shell);
start();
window.addEventListener('keydown', (event) => {
	if (event.key !== 'Escape' || window.parent === window || document.body.classList.contains('css-fullscreen')) return;
	window.parent.postMessage({ type: 'motion-escape' }, location.origin);
});
