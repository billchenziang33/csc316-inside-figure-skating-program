import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const builder = await readFile(new URL('../scripts/prepare_1a_landing_free_skate_alignment_v151.py', import.meta.url), 'utf8');
const audit = await readFile(new URL('../scripts/audit_1a_v151_free_skate_heading.py', import.meta.url), 'utf8');

test('V151 aligns the viewer-right free skate during descent as a connected leg chain', () => {
	assert.match(builder, /single-axel-1a-human-rink-v149\.blend/);
	assert.match(builder, /single-axel-1a-human-rink-v151\.blend/);
	assert.match(builder, /single-axel-1a-human-rink-v151-web\.glb/);
	assert.match(builder, /Human · left leg volume 3/);
	assert.match(builder, /Human · left leg volume 4/);
	assert.match(builder, /Left skate · exact website fit v64/);
	assert.match(builder, /frame - 85\.0/);
	assert.match(builder, /frame - 87\.0/);
	assert.match(builder, /illustrative\/simulated/i);
	assert.match(audit, /landing_window_max_face_to_boot_abs_deg/);
	assert.match(audit, /max_boot_to_blade_abs_deg/);
});
