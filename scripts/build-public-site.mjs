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
	'movement/axel-1a-prototype/fullscreen-control.js',
	'movement/axel-1a-prototype/camera-name.mjs',
	'movement/axel-1a-prototype/camera-fit.mjs',
	'movement/axel-1a-prototype/playback-clock.mjs',
	'movement/axel-1a-prototype/trajectory-hud.mjs',
	'movement/axel-1a-prototype/index.html',
	'movement/axel-1a-prototype/joint-reference.json',
	'movement/axel-1a-prototype/player.html',
	'movement/axel-1a-prototype/vendor/GLTFLoader.js',
	'movement/axel-1a-prototype/vendor/three.umd.js',
	...[
		'single-axel-1a-human-rink-v118-frame060-side.png',
		'single-axel-1a-human-rink-v118-frame076-side.png',
		'single-axel-1a-human-rink-v118-frame082-side.png',
		'single-axel-1a-human-rink-v118-frame090-side.png',
		'single-axel-1a-human-rink-v118-frame060-front.png',
		'single-axel-1a-human-rink-v118-frame076-front.png',
		'single-axel-1a-human-rink-v118-frame090-front.png',
		'single-axel-1a-human-rink-v118-frame087-skate-closeup-web.png',
		'single-axel-1a-human-rink-v118.blend',
		'single-axel-1a-human-rink-v118-web.glb',
		'single-axel-1a-human-rink-v124-frame060-side.png',
		'single-axel-1a-human-rink-v124-frame076-side.png',
		'single-axel-1a-human-rink-v124-frame090-side.png',
		'single-axel-1a-human-rink-v124-frame060-front.png',
		'single-axel-1a-human-rink-v124-frame076-front.png',
		'single-axel-1a-human-rink-v124-frame090-front.png',
		'single-axel-1a-human-rink-v124-frame087-skate-closeup.png',
		'single-axel-1a-human-rink-v124.blend',
		'single-axel-1a-human-rink-v124-web.glb',
		'single-axel-1a-human-rink-v128-frame060-side.png',
		'single-axel-1a-human-rink-v128-frame076-side.png',
		'single-axel-1a-human-rink-v128-frame090-side.png',
		'single-axel-1a-human-rink-v128-frame060-front.png',
		'single-axel-1a-human-rink-v128-frame076-front.png',
		'single-axel-1a-human-rink-v128-frame090-front.png',
		'single-axel-1a-human-rink-v128-frame087-skate-closeup.png',
		'single-axel-1a-human-rink-v128.blend',
		'single-axel-1a-human-rink-v128-web.glb',
		'single-axel-1a-human-rink-v145-frame090-side.png',
		'single-axel-1a-human-rink-v145-frame090-front.png',
		'single-axel-1a-human-rink-v145-frame087-side.png',
		'single-axel-1a-human-rink-v145-frame090-skate-closeup.png',
		'single-axel-1a-human-rink-v145-frame060-side.png',
		'single-axel-1a-human-rink-v145-frame060-front.png',
		'single-axel-1a-human-rink-v145.blend',
		'single-axel-1a-human-rink-v145-web.glb',
		'single-axel-1a-human-rink-v153-frame060-side.png',
		'single-axel-1a-human-rink-v153-frame060-front.png',
		'single-axel-1a-human-rink-v153-frame076-side.png',
		'single-axel-1a-human-rink-v153-frame076-front.png',
		'single-axel-1a-human-rink-v153-frame087-side.png',
		'single-axel-1a-human-rink-v153-frame090-side.png',
		'single-axel-1a-human-rink-v153-frame092-side.png',
		'single-axel-1a-human-rink-v153-frame092-front.png',
		'single-axel-1a-human-rink-v153-frame092-skate-closeup.png',
		'single-axel-1a-human-rink-v153.blend',
		'single-axel-1a-human-rink-v153-web.glb',
		'single-axel-1a-human-rink-v155-frame080-side.png',
		'single-axel-1a-human-rink-v155-frame081-side.png',
		'single-axel-1a-human-rink-v155-frame081-front.png',
		'single-axel-1a-human-rink-v155-frame084-side.png',
		'single-axel-1a-human-rink-v155-frame087-side.png',
		'single-axel-1a-human-rink-v155-frame092-side.png',
		'single-axel-1a-human-rink-v155-frame092-front.png',
		'single-axel-1a-human-rink-v155-frame092-skate-closeup.png',
		'single-axel-1a-human-rink-v155.blend',
		'single-axel-1a-human-rink-v155-web.glb',
		'single-axel-1a-human-rink-v156-frame046-side.png',
		'single-axel-1a-human-rink-v156-frame046-front.png',
		'single-axel-1a-human-rink-v156-frame070-side.png',
		'single-axel-1a-human-rink-v156-frame087-side.png',
		'single-axel-1a-human-rink-v156-frame092-side.png',
		'single-axel-1a-human-rink-v156-frame092-front.png',
		'single-axel-1a-human-rink-v156-frame092-skate-closeup.png',
		'single-axel-1a-human-rink-v156.blend',
		'single-axel-1a-human-rink-v156-web.glb',
		'single-axel-1a-human-rink-v159-frame079-front.png',
		'single-axel-1a-human-rink-v159-frame079-skate-closeup.png',
		'single-axel-1a-human-rink-v159-frame092-side.png',
		'single-axel-1a-human-rink-v159-frame092-front.png',
		'single-axel-1a-human-rink-v159-frame136-front.png',
		'single-axel-1a-human-rink-v159.blend',
		'single-axel-1a-human-rink-v159-web.glb',
		'single-axel-1a-human-rink-v167-frame047-side.png',
		'single-axel-1a-human-rink-v167-frame050-front.png',
		'single-axel-1a-human-rink-v167-frame050-side.png',
		'single-axel-1a-human-rink-v167-frame051-side.png',
		'single-axel-1a-human-rink-v167-frame055-side.png',
		'single-axel-1a-human-rink-v167.blend',
		'single-axel-1a-human-rink-v167-web.glb'
	].map((name) => `movement/axel-1a-prototype/${name}`)
];

for (const relative of publicFiles) {
	const source = path.join(root, 'static', relative);
	const destination = path.join(output, relative);
	mkdirSync(path.dirname(destination), { recursive: true });
	cpSync(source, destination);
}

console.log(`Prepared ${publicFiles.length} curated static files in dist; full historical Blender assets stay out of the public build.`);
