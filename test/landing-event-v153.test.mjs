import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const read = (path) => readFile(new URL(path, import.meta.url), 'utf8');
const [builder, audit, player, runtime] = await Promise.all([
	read('../scripts/prepare_1a_landing_event_v153.py'),
	read('../scripts/audit_1a_v153_touchdown.py'),
	read('../static/movement/axel-1a-prototype/player.html'),
	read('../static/movement/axel-1a-prototype/blender-player.js')
]);

test('V153 touchdown marker remains wired into the V169 toe-aligned action', () => {
	assert.match(builder, /single-axel-1a-human-rink-v152\.blend/);
	assert.match(builder, /LANDING_FRAME = 92/);
	assert.match(builder, /V102_EVENT_LANDING_FRAME_92/);
	assert.match(builder, /landing_event_alignment_v153/);
	assert.doesNotMatch(builder, /keyframe_insert/);
	assert.match(audit, /first_contact_whole_frame/);
	assert.match(audit, /0\.001 <= landing_sample\["support_gap_m"\] <= 0\.003/);
	assert.match(player, /Blender v169/);
	assert.match(player, /blender-player\.js\?v=168/);
	assert.match(runtime, /single-axel-1a-human-rink-v169-web\.glb/);
	assert.match(runtime, /readAxelEventFrames\(sceneObjects\)/);
});
