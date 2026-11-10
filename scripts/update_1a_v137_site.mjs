import { readFileSync, writeFileSync } from 'node:fs';

const indexPath = new URL('../static/movement/axel-1a-prototype/index.html', import.meta.url);
let index = readFileSync(indexPath, 'utf8');
const historicalPreviewPattern = /single-axel-1a-human-rink-v137-(frame060-side|frame076-side|frame060-front|frame076-front|frame090-front)\.png/g;
index = index.replace(historicalPreviewPattern, 'single-axel-1a-human-rink-v128-$1.png');

const oldCollisionParagraph = /<p>The HUD reads the animated Blender\/GLB root path\..*?These sampled results do not prove continuous collision freedom or blade contact\.<\/p>/s;
const updatedCollisionParagraph = '<p>The HUD reads the animated Blender/GLB root path. Simulated take-off/apex/landing events remain frames 60 / 76 / 90; root rise is 0.300 m and take-off-to-landing travel is 0.993 m. Blade clearance was sampled at 1/16-frame intervals against the measured ice top Z=+0.012 m; minimum gap remains +1.929 mm right and +1.956 mm left. A 0.5-frame BVH audit found no boot-to-boot overlap and no new landing-boot overlap. At f81, free-boot/opposite-calf contact is back to the V128 baseline (37 triangle pairs); the existing thigh/calf contacts remain. Discrete geometry samples do not prove continuous collision freedom or blade contact.</p>';
if (!oldCollisionParagraph.test(index)) {
	throw new Error('Could not find the existing flight and collision audit paragraph.');
}
index = index.replace(oldCollisionParagraph, updatedCollisionParagraph);
writeFileSync(indexPath, index);
