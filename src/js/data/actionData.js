/**
 * TerraEcho — data/actionData.js
 * Responsibility: Action system data definitions only.
 * Card config · Impact multipliers · Milestone thresholds · Donation URL
 * No DOM. No events. No calculations. No side effects.
 */

/**
 * Action card definitions.
 * id must match the data-action attribute in index.html
 * and the counts object keys in state/actions.js.
 *
 * Impact multipliers per single logged action:
 *   co2Kg    — kilograms of CO2 equivalent saved
 *   waterL   — litres of water saved
 *   treeEq   — tree-year equivalents (1 tree absorbs ~21kg CO2/yr)
 *
 * Sources (approximate, for narrative accuracy):
 *   Bottle    — lifecycle analysis, reusable vs single-use plastic
 *   Plastic   — avoided production emissions per item
 *   Tree      — IPCC / Project Drawdown tree sequestration estimates
 *   Cycling   — per average 5km trip vs car (DEFRA emission factors)
 *   Meal      — Oxford University food emissions study (Poore & Nemecek)
 *   Shower    — 8min to 4min reduction, avg 10L/min showerhead
 */
export const ACTION_CARDS = [
  {
    id:       'bottle',
    label:    'Reusable Bottle',
    emoji:    '🍶',
    hintText: '~0.08 kg CO2 saved',
    co2Kg:    0.08,
    waterL:   0,
    treeEq:   0.08 / 21,
  },
  {
    id:       'plastic',
    label:    'Avoided Plastic',
    emoji:    '🚫',
    hintText: '~0.03 kg CO2 saved',
    co2Kg:    0.03,
    waterL:   2,
    treeEq:   0.03 / 21,
  },
  {
    id:       'tree',
    label:    'Planted Tree',
    emoji:    '🌱',
    hintText: '~21 kg CO2/yr absorbed',
    co2Kg:    21,
    waterL:   0,
    treeEq:   1,
  },
  {
    id:       'cycled',
    label:    'Cycled',
    emoji:    '🚲',
    hintText: '~1.05 kg CO2 saved',
    co2Kg:    1.05,
    waterL:   0,
    treeEq:   1.05 / 21,
  },
  {
    id:       'meal',
    label:    'Plant-Based Meal',
    emoji:    '🥗',
    hintText: '~1.5 kg CO2 saved vs beef',
    co2Kg:    1.5,
    waterL:   450,
    treeEq:   1.5 / 21,
  },
  {
    id:       'shower',
    label:    'Short Shower',
    emoji:    '🚿',
    hintText: '~50 L water saved',
    co2Kg:    0.02,
    waterL:   50,
    treeEq:   0.02 / 21,
  },
];

/**
 * Milestone threshold definitions.
 * id is stored in dismissedMilestones[] in localStorage.
 * totalActions is the cumulative count that triggers this milestone.
 */
export const MILESTONES = [
  {
    id:           'milestone-3',
    totalActions: 3,
    message:      'Small actions echo.',
    subtext:      'Every choice you make sends a signal — to yourself, to the people watching, to the systems around you.',
    emoji:        '🌿',
  },
  {
    id:           'milestone-10',
    totalActions: 10,
    message:      'Your choices already changed more than a habit.',
    subtext:      'Ten logged actions means ten moments where you chose differently. That is how identity shifts.',
    emoji:        '🌱',
  },
  {
    id:           'milestone-25',
    totalActions: 25,
    message:      'Tiny actions repeated become systems.',
    subtext:      'What started as individual choices is becoming a pattern. Patterns outlast motivation.',
    emoji:        '🌲',
  },
  {
    id:           'milestone-50',
    totalActions: 50,
    message:      'Imagine if a city moved like this.',
    subtext:      'Fifty actions. Now multiply that by a neighbourhood, a district, a million people choosing the same.',
    emoji:        '🌍',
  },
  {
    id:           'milestone-100',
    totalActions: 100,
    message:      'Change compounds.',
    subtext:      'One hundred actions logged. The CO2 you have not put into the atmosphere does not disappear — it stays out.',
    emoji:        '🌏',
  },
];

/** Donation URL — opened in new tab from milestone card */
export const DONATION_URL = 'https://www.cooleffect.org';

/** localStorage key — single key for entire actions state */
export const STORAGE_KEY = 'terraecho:actions';