import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const builder = await readFile(new URL('../scripts/prepare_1a_readable_blade_v148.py', import.meta.url), 'utf8');

test('V148 uses the brighter V88 satin-steel values on both V145 website blades', () => {
	assert.match(builder, /single-axel-1a-human-rink-v145\.blend/);
	assert.match(builder, /single-axel-1a-human-rink-v148\.blend/);
	assert.match(builder, /single-axel-1a-human-rink-v148-web\.glb/);
	assert.match(builder, /for side in \("Left", "Right"\)/);
	assert.match(builder, /STEEL_COLOR\s*=\s*\(0\.60, 0\.68, 0\.73, 1\.0\)/);
	assert.match(builder, /principled\.inputs\["Metallic"\]\.default_value\s*=\s*0\.35/);
	assert.match(builder, /principled\.inputs\["Roughness"\]\.default_value\s*=\s*0\.28/);
	assert.match(builder, /default_scene_objects/);
});
