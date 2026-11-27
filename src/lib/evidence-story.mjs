// Scrollytelling order for Step 5 · Compare scores.
// The story zooms out: one element → all jumps → jump allowance → spins & steps → whole program.
export const evidenceStory = [
  {
    chart: 'S15',
    kicker: '1 · One element',
    title: 'Every element starts from a fixed base value.',
    body: 'The ISU Scale of Values sets a base value for each element. The judging panel then adds or subtracts Grade of Execution (GOE). Points sitting above the diagonal gained from execution; points below it lost.',
    note: 'Select a dot to see that jump’s score above.'
  },
  {
    chart: 'S02',
    kicker: '2 · Rotation and risk',
    title: 'More rotations raise the ceiling, not the guarantee.',
    body: 'Quadruple jumps carry the highest base values. In these programs, 11 of the 47 jump elements that started with a quad received negative GOE, compared with 4 of the other 53.'
  },
  {
    chart: 'S01',
    kicker: '3 · Choosing the jumps',
    title: 'Same number of jumps, different choices.',
    body: 'ISU rules fix how many jump elements a program may contain, so skaters compete on which jumps they choose. The toe loop dominates with 46 jumps, 20 of them quads. It is also the usual add-on: 26 of the 49 jumps performed second or third in a combination were toe loops. The Axel is required in the short program, and all ten skaters performed one.',
    note: 'Counts cover all ten skaters; the free skate allows more jump elements than the short program.'
  },
  {
    chart: 'S06',
    kicker: '4 · Beyond the jumps',
    title: 'Spins and step sequences are scored by level.',
    body: 'A technical panel assigns Level 1 to 4, and the level sets the base value. Across the top ten, jumps earned about 74% of all element points; spins, steps and the choreographic sequence shared the rest.',
    note: 'Elements at the same level can earn different scores because of GOE.'
  },
  {
    chart: 'S12',
    kicker: '5 · The whole program',
    title: 'Element points are only half the total.',
    body: 'All element scores add up to the Technical Element Score (TES). Program components (PCS) are added and deductions such as falls are subtracted to reach the segment total. For the final top ten, TES made up about 53% of the combined total.',
    note: 'The free skate is longer and includes more elements than the short program.'
  }
];

export const storyCharts = evidenceStory.map((step) => step.chart);
