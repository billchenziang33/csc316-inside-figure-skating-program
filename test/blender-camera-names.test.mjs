import assert from 'node:assert/strict';
import test from 'node:test';
import {
	findExportedNameMatch,
	findExportedNamesByPrefix,
} from '../static/movement/axel-1a-prototype/camera-name.mjs';

test('resolves glTF cameras after Blender sanitizes punctuation and adds exporter suffixes', () => {
	const cameras = [
		{ name: 'Action_side_view_·_horizontal_follow_composition_1:sr', isCamera: true },
		{ name: 'Action_front_view_1:sr', isCamera: true },
		{ name: 'Skate_inspection_·_close_view', isCamera: true },
		{ name: 'Arena_overview_·_full_60×30_rink:sr', isCamera: true },
	];
	const labels = [
		'Action side view · horizontal follow composition',
		'Action front view',
		'Skate inspection · close view',
		'Arena overview · full 60×30 rink',
	];

	assert.deepEqual(labels.map((label) => findExportedNameMatch(cameras, label)), cameras);
});

test('does not choose arbitrarily when Blender-exported names collide', () => {
	const cameras = [
		{ name: 'Action_front_view_1:sr', isCamera: true },
		{ name: 'Action_front_view_2:sr', isCamera: true },
	];
	assert.equal(findExportedNameMatch(cameras, 'Action front view'), null);
});

test('matches a decimal label when GLTFLoader removes its decimal point', () => {
	const nodes = [{ name: 'Skater_root_·_simulated_travel_and_15-turn_yaw_v8' }];

	assert.equal(
		findExportedNameMatch(nodes, 'Skater root · simulated travel and 1.5-turn yaw v8'),
		nodes[0]
	);
});

test('finds a Blender namespace after GLTFLoader replaces spaces with underscores', () => {
	const objects = [
		{ name: 'V98_trajectory_marker_·_apex_projection' },
		{ name: 'V98_vertical_marker_·_takeoff' },
		{ name: 'V980_unrelated_object' },
		{ name: 'Skater_root_·_simulated_travel' },
	];

	assert.deepEqual(
		findExportedNamesByPrefix(objects, 'V98 '),
		objects.slice(0, 2)
	);
});
