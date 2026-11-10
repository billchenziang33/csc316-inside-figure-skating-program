import { findExportedNameMatch, findExportedNamesByPrefix } from './camera-name.mjs';
import { fitBoundingSphereDistance } from './camera-fit.mjs';
import { advancePlaybackTime, elapsedPlaybackSeconds, playbackSpeedFromControl, seekAnimationActions } from './playback-clock.mjs?v=100';
import { formatMeters, measureFlightMetrics, phaseAt, readAxelEventFrames, timeAtAnimationFrame } from './trajectory-hud.mjs?v=102';

const THREE = globalThis.THREE;
const GLTFLoader = THREE?.GLTFLoader;

const FILE = '/movement/axel-1a-prototype/single-axel-1a-human-rink-v121-web.glb';
const CAMERA_NAMES = [
	'Action side view · horizontal follow composition',
	'Action front view',
	'Skate inspection · close view',
	'Arena overview · full 60×30 rink',
	'Action skater-facing follow view v121',
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
let inspectionRunner;
let inspectionBoot;
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
const inspectionTarget = new THREE.Vector3();
const inspectionCameraPosition = new THREE.Vector3();
const inspectionBox = new THREE.Box3();
const trajectoryPosition = new THREE.Vector3();
const cameraWorldPosition = new THREE.Vector3();
const cameraWorldQuaternion = new THREE.Quaternion();
const orbitTarget = new THREE.Vector3();
const orbitOffset = new THREE.Vector3();
const cameraRight = new THREE.Vector3();
const cameraUp = new THREE.Vector3();
const arenaBounds = new THREE.Box3();
const arenaTarget = new THREE.Vector3();
let arenaObject;

function frameFromTime(time) {
	return Math.min(frameCount - 1, Math.max(0, Math.round(time / duration * (frameCount - 1))));
}

function updateInspectionCamera() {
	if (!followInspection || !inspectionRunner || !activeCamera) return;
	modelScene.updateMatrixWorld(true);
	inspectionBox.setFromObject(inspectionRunner);
	if (inspectionBoot) inspectionBox.union(new THREE.Box3().setFromObject(inspectionBoot));
	inspectionBox.getCenter(inspectionTarget);
	inspectionTarget.y += 0.04;
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
	renderer.render(modelScene, activeCamera);
}

function setPlaybackTime(time, updateSlider = true) {
	if (!activeCamera) throw new Error('The v121 GLB camera was not resolved.');
	playbackTime = Math.max(0, Math.min(duration, time));
	seekAnimationActions(mixer, clipActions, animationStartTime + playbackTime);
	modelScene.updateMatrixWorld(true);
	updateInspectionCamera();
	updateViewerCamera();
	const frame = frameFromTime(playbackTime);
	if (updateSlider) frameSlider.value = String(frame);
	counter.textContent = `Frame ${frame + 1} / ${frameCount} · ${phaseAt(frame, trajectoryEventFrames)}`;
	updateFlightHud(frame);
	renderer.render(modelScene, activeCamera);
}

function updateFlightHud(frame) {
	if (!trajectoryRoot || !trajectoryPoints) return;
	trajectoryRoot.getWorldPosition(trajectoryPosition);
	const current = { x: trajectoryPosition.x, y: trajectoryPosition.y, z: trajectoryPosition.z };
	const { takeoff, apex, landing } = trajectoryPoints;
	const metrics = measureFlightMetrics(current, takeoff, apex, landing);
	phaseHud.textContent = phaseAt(frame, trajectoryEventFrames);
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
		if (followInspection) {
			orbitTarget.copy(inspectionTarget);
		} else if (sourceCamera === arenaCamera && arenaObject) {
			arenaBounds.setFromObject(arenaObject);
			arenaBounds.getCenter(arenaTarget);
			orbitTarget.copy(arenaTarget);
		} else {
			trajectoryRoot.getWorldPosition(orbitTarget);
			orbitTarget.y += 0.82;
		}
		orbitOffset.copy(cameraWorldPosition).sub(orbitTarget);
		let radius = Math.max(0.25, orbitOffset.length() * orbitZoom);
		const baseRadius = Math.max(0.25, cameraWorldPosition.distanceTo(orbitTarget));
		const theta = Math.atan2(orbitOffset.x, orbitOffset.z) + orbitYaw;
		const phi = THREE.MathUtils.clamp(Math.acos(THREE.MathUtils.clamp(orbitOffset.y / baseRadius, -1, 1)) + orbitPitch, 0.08, Math.PI - 0.08);
		radius = THREE.MathUtils.clamp(radius, 0.25, 120);
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
		inspectionRunner = findExportedNameMatch(sceneObjects, 'Right skate · website blade v64');
		inspectionBoot = findExportedNameMatch(sceneObjects, 'Right skate · website boot v64');
		inspectionCamera = findExportedNameMatch(sceneObjects, CAMERA_NAMES[2]);
		arenaCamera = findExportedNameMatch(sceneObjects, CAMERA_NAMES[3]);
		const skaterFollowCamera = findExportedNameMatch(sceneObjects, CAMERA_NAMES[4]);
		arenaObject = findExportedNameMatch(sceneObjects, 'V23 capsule ice · 60 m × 30 m (30 m straights + semicircles)');
		if (!inspectionRunner || !inspectionBoot || !inspectionCamera?.isCamera || !arenaCamera?.isCamera || !skaterFollowCamera?.isCamera || !arenaObject) {
			throw new Error('The v121 skate inspection, arena or skater-follow camera target is missing.');
		}
		const clips = gltf.animations;
		animationTrackCount = clips.reduce((count, clip) => count + clip.tracks.length, 0);
		if (!clips.length || animationTrackCount < 80) {
			throw new Error('The v121 GLB did not contain the expected articulated 3D action.');
		}
		const rootPositionTrack = clips.flatMap((clip) => clip.tracks).find((track) =>
			track.name.startsWith(trajectoryRoot.name) && track.name.endsWith('.position'));
		if (!rootPositionTrack || rootPositionTrack.times.length !== frameCount) {
			throw new Error('The v121 root track does not contain the expected frame samples.');
		}
		animationStartTime = rootPositionTrack.times[0];
		duration = rootPositionTrack.times.at(-1) - animationStartTime;
		if (!Number.isFinite(duration) || duration <= 0) throw new Error('The v121 animation has no usable duration.');
		mixer = new THREE.AnimationMixer(gltf.scene);
		clipActions = clips.map((clip) => {
			const action = mixer.clipAction(clip);
			action.setLoop(THREE.LoopOnce, 1);
			action.clampWhenFinished = true;
			action.play();
			return action;
		});
		if (!trajectoryRoot) throw new Error('The v121 GLB is missing its animated skater root track.');
		trajectoryEventFrames = readAxelEventFrames(sceneObjects);
		if (Object.values(trajectoryEventFrames).some((frame) => frame > frameCount)) {
			throw new Error('A V102 inherited trajectory event is outside the exported animation frame range.');
		}
		sampleTrajectoryEvents();
		mixer.setTime(animationStartTime + duration * (94 - 1) / (frameCount - 1));
		modelScene.updateMatrixWorld(true);
		inspectionBox.setFromObject(inspectionRunner);
		inspectionBox.union(new THREE.Box3().setFromObject(inspectionBoot));
		inspectionBox.getCenter(inspectionTarget);
		inspectionCamera.getWorldPosition(inspectionCameraPosition);
		inspectionDirection.copy(inspectionCameraPosition).sub(inspectionTarget).normalize();
		inspectionCamera.zoom = 1.0;
		inspectionCamera.near = 0.01;
		inspectionCamera.updateProjectionMatrix();
		mixer.setTime(animationStartTime);
		modelScene.updateMatrixWorld(true);
		chooseCamera(CAMERA_NAMES[4]);
		frameSlider.disabled = false;
		playButton.disabled = false;
		resetButton.disabled = false;
		fullscreenButton.disabled = false;
		cameraResetButton.disabled = false;
		setPlaybackTime(0);
		message.textContent = `Ready · Blender v121 · ${(duration).toFixed(2)} s · ${animationTrackCount} animated channels · ${renderer.info.render.calls} draw calls`;
		requestAnimationFrame(animate);
	} catch (error) {
		console.error('Blender v121 player failed to load:', error);
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
	if (!document.fullscreenElement) await shell.requestFullscreen();
	else await document.exitFullscreen();
	resize();
});
window.addEventListener('resize', resize);
new ResizeObserver(resize).observe(shell);
start();
window.addEventListener('keydown', (event) => {
	if (event.key !== 'Escape' || window.parent === window) return;
	window.parent.postMessage({ type: 'motion-escape' }, location.origin);
});
