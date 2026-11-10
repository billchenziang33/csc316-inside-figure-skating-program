import { cpSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { build } from 'vite';
import viteConfig from '../vite.config.js';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output = path.join(root, 'dist');

await build({
	...viteConfig,
	configFile: false,
	root,
	publicDir: false,
	build: {
		...viteConfig.build,
		outDir: output,
		emptyOutDir: true
	}
});

const publicFiles = [
	'data/competition.json',
	'movement-reference.png',
	'movement/index.html',
	'movement/LICENSE.MOTIONEXPERT.txt',
	'movement/LICENSE.THREE.txt',
	'movement/THIRD_PARTY_NOTICES.md',
	'movement/axel-1a-prototype/README.md',
	'movement/axel-1a-prototype/blender-player.js',
	'movement/axel-1a-prototype/camera-name.mjs',
	'movement/axel-1a-prototype/playback-clock.mjs',
	'movement/axel-1a-prototype/trajectory-hud.mjs',
	'movement/axel-1a-prototype/index.html',
	'movement/axel-1a-prototype/joint-reference.json',
	'movement/axel-1a-prototype/player.html',
	'movement/axel-1a-prototype/vendor/GLTFLoader.js',
	'movement/axel-1a-prototype/vendor/three.umd.js',
	...[
		'single-axel-1a-human-rink-v107-takeoff-side.png',
		'single-axel-1a-human-rink-v107-apex-side.png',
		'single-axel-1a-human-rink-v107-landing-side.png',
		'single-axel-1a-human-rink-v107-skate-closeup.png',
		'single-axel-1a-human-rink-v107-takeoff-front.png',
		'single-axel-1a-human-rink-v107-apex-front.png',
		'single-axel-1a-human-rink-v107-landing-front.png',
		'single-axel-1a-human-rink-v107.blend',
		'single-axel-1a-human-rink-v107-web.glb'
	].map((name) => `movement/axel-1a-prototype/${name}`)
];

for (const relative of publicFiles) {
	const source = path.join(root, 'static', relative);
	const destination = path.join(output, relative);
	mkdirSync(path.dirname(destination), { recursive: true });
	cpSync(source, destination);
}

console.log(`Prepared ${publicFiles.length} curated static files in dist; full historical Blender assets stay out of the public build.`);
