import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const builder = await readFile(new URL('../scripts/prepare_1a_right_leg_body_alignment_v149.py', import.meta.url), 'utf8');

test('V149 corrects right foot heading as a rigid ankle-connected leg chain from V148', () => {
	assert.match(builder, /single-axel-1a-human-rink-v148\.blend/);
	assert.match(builder, /single-axel-1a-human-rink-v149\.blend/);
	assert.match(builder, /single-axel-1a-human-rink-v149-web\.glb/);
	assert.match(builder, /YAW_LIMIT_DEGREES\s*=\s*20\.0/);
	assert.match(builder, /Human · right leg volume 3/);
	assert.match(builder, /Human · right leg volume 4/);
	assert.match(builder, /Right skate · exact website fit v64/);
	assert.match(builder, /pivot.*hip/i);
	assert.match(builder, /illustrative\/simulated/i);
});
