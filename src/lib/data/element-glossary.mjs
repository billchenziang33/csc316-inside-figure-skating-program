// Plain-English readings of ISU element codes, for newcomers.
// Edges are described for a counter-clockwise skater, the usual direction.

export const ROTATION_NAMES = { 1: 'Single', 2: 'Double', 3: 'Triple', 4: 'Quad' };

// Ordered from lowest to highest base value. quadBase = ISU Scale of Values 2021-22.
export const JUMP_TYPES = [
  { code: 'T', name: 'Toe loop', takeoff: 'toe', edge: 'Right back outside edge, helped by the left toe pick', quadBase: 9.5 },
  { code: 'S', name: 'Salchow', takeoff: 'edge', edge: 'Left back inside edge', quadBase: 9.7 },
  { code: 'Lo', name: 'Loop', takeoff: 'edge', edge: 'Right back outside edge', quadBase: 10.5 },
  { code: 'F', name: 'Flip', takeoff: 'toe', edge: 'Left back inside edge, helped by the right toe pick', quadBase: 11 },
  { code: 'Lz', name: 'Lutz', takeoff: 'toe', edge: 'Left back outside edge, helped by the right toe pick', quadBase: 11.5 },
  { code: 'A', name: 'Axel', takeoff: 'edge', edge: 'Left forward outside edge: the only forward take-off, so it needs an extra half turn', quadBase: 12.5 },
  { code: 'Eu', name: 'Euler', takeoff: 'edge', edge: 'Right back outside edge, landing on the left foot; used only inside combinations', quadBase: null }
];

export const SPIN_POSITIONS = { U: 'upright', S: 'sit', C: 'camel', L: 'layback' };
export const SPIN_PARTS = [
  { code: 'F', meaning: 'Flying: the spin starts with a jump' },
  { code: 'C', meaning: 'Change of foot during the spin (when it comes before the position)' },
  { code: 'Co', meaning: 'Combination: the skater changes between positions' },
  { code: 'U/S/C/L', meaning: 'Position: upright, sit, camel or layback' },
  { code: 'Sp', meaning: 'Spin' },
  { code: '1–4', meaning: 'Level awarded by the technical panel; a higher level has a higher base value' },
  { code: 'V', meaning: 'A requirement was not fully met; base value reduced to 75%' }
];

export const OTHER_ELEMENTS = [
  { code: 'StSq', name: 'Step sequence', meaning: 'Footwork across the ice, levelled 1–4 like a spin' },
  { code: 'ChSq', name: 'Choreographic sequence', meaning: 'Free-skate movement passage with a fixed base value of 3.00; only GOE varies' }
];

export const MARKS = {
  '<': { label: 'Under-rotated', meaning: 'Landed between a quarter and half a turn short; base value cut to 80%' },
  '<<': { label: 'Downgraded', meaning: 'Landed half a turn or more short; scored as a jump with one fewer rotation' },
  q: { label: 'Quarter short', meaning: 'Landed exactly a quarter turn short; base value kept, execution marked down' },
  e: { label: 'Wrong edge', meaning: 'Lutz or Flip taken off from the wrong edge; base value reduced' },
  '!': { label: 'Unclear edge', meaning: 'Take-off edge not clear; base value kept, execution marked down' },
  '*': { label: 'Invalid', meaning: 'Did not count under the program rules; scores zero' },
  x: { label: 'Second-half bonus', meaning: 'Jump started in the second half of the program; base value × 1.1' }
};

const JUMP = /^([1-4])(Lz|Lo|Eu|A|F|S|T)(.*)$/;
// A C counts as change-foot only when a position or Co still follows it before Sp (FCSp = flying camel).
const SPIN = /^(F)?(C(?=(?:Co|[USCL])Sp))?(Co|[USCL])?Sp([1-4B])?(V)?$/;

function describeJump(part) {
  const [, rot, type, suffix] = part.match(JUMP);
  const jump = JUMP_TYPES.find((t) => t.code === type);
  const name = `${ROTATION_NAMES[rot]} ${jump.name}`;
  const marks = ['<<', '<', 'e', 'q', '!', '*'].filter((m) => (m === '<' ? suffix.includes('<') && !suffix.includes('<<') : suffix.includes(m)));
  return { name, marks };
}

function describeSpin(code) {
  const m = code.match(SPIN);
  if (!m) return null;
  const [, flying, change, kind, level, reduced] = m;
  const words = [flying && 'Flying', change && 'change-foot', kind === 'Co' ? 'combination' : SPIN_POSITIONS[kind]].filter(Boolean);
  const name = `${words.join(' ')} spin`.replace(/^./, (c) => c.toUpperCase());
  const notes = [];
  if (level) notes.push(level === 'B' ? 'Base level' : `Level ${level}`);
  if (reduced) notes.push('V: base value reduced to 75%');
  return { name, notes };
}

// Returns { name, notes[] } for any protocol code, or a fallback that repeats the code.
export function describeElement(code, infoFlag = '') {
  const raw = String(code ?? '');
  const notes = [];
  let name;
  const parts = raw.split('+');
  if (parts.every((p) => JUMP.test(p))) {
    const jumps = parts.map(describeJump);
    name = jumps.map((j) => j.name).join(' + ');
    if (jumps.length > 1) notes.push(`${jumps.length}-jump combination`);
    const total = parts.reduce((sum, p) => sum + Number(p[0]) + (/^\dA/.test(p) ? 0.5 : 0), 0);
    notes.push(`${total} ${total === 1 ? 'rotation' : 'rotations'}${jumps.length > 1 ? ' in total' : ' in the air'}`);
    for (const j of jumps) for (const m of j.marks) notes.push(`${MARKS[m].label} (${m}) on the ${j.name}: ${MARKS[m].meaning.split('; ')[1] ?? MARKS[m].meaning}`);
  } else if (/^StSq/.test(raw)) {
    name = 'Step sequence';
    const level = raw.match(/([1-4B])$/)?.[1];
    if (level) notes.push(level === 'B' ? 'Base level' : `Level ${level}`);
  } else if (/^ChSq/.test(raw)) {
    name = 'Choreographic sequence';
    notes.push('Fixed base value; only execution varies');
  } else {
    const spin = describeSpin(raw);
    name = spin?.name ?? raw;
    if (spin) notes.push(...spin.notes);
  }
  if (String(infoFlag).includes('x')) notes.push(`${MARKS.x.label} (x): ${MARKS.x.meaning.split('; ')[1]}`);
  return { name, notes };
}

export function describeText(code, infoFlag) {
  const { name, notes } = describeElement(code, infoFlag);
  return [name, ...notes].join('. ') + '.';
}
