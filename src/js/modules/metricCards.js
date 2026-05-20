/**
 * TerraEcho — modules/metricCards.js
 * Responsibility: Metric card DOM updates only.
 * Subscribes to timeline:yearChanged.
 * Updates species at risk, temperature anomaly, sea level rise cards.
 * No state writes. No event publishing.
 *
 * Targets (defined in index.html):
 *   #metric-species  — species at risk value
 *   #metric-temp     — temperature anomaly value
 *   #metric-sea      — sea level rise value
 */

import eventBus            from '../eventBus.js';
import { getValuesForYear } from '../data/timelineData.js';

/** DOM references */
let speciesEl = null;
let tempEl    = null;
let seaEl     = null;

/**
 * Resolves and caches DOM elements.
 * @returns {boolean}
 */
function resolveElements() {
  speciesEl = document.getElementById('metric-species');
  tempEl    = document.getElementById('metric-temp');
  seaEl     = document.getElementById('metric-sea');

  if (!speciesEl || !tempEl || !seaEl) {
    console.warn('[metricCards] Missing required DOM elements.');
    return false;
  }
  return true;
}

/**
 * Formats species count from raw thousands value.
 * e.g. 9.0 → "9,000"  |  11.5 → "11,500"
 * @param {number} thousands
 * @returns {string}
 */
function formatSpecies(thousands) {
  return Math.round(thousands * 1000).toLocaleString();
}

/**
 * Formats temperature anomaly with sign.
 * e.g. 0.72 → "+0.72°C"  |  -0.1 → "−0.10°C"
 * @param {number} val
 * @returns {string}
 */
function formatTemp(val) {
  const sign = val >= 0 ? '+' : '−';
  return `${sign}${Math.abs(val).toFixed(2)}`;
}

/**
 * Formats sea level rise in mm.
 * e.g. 130 → "+130 mm"
 * @param {number} val
 * @returns {string}
 */
function formatSea(val) {
  return `+${Math.round(val)}`;
}

/**
 * Updates all three metric cards for a given year.
 * @param {number} year
 */
function updateMetricCards(year) {
  const values = getValuesForYear(year);

  speciesEl.textContent = formatSpecies(values.species);
  tempEl.textContent    = formatTemp(values.tempAnomaly);
  seaEl.textContent     = formatSea(values.seaLevel);
}

/**
 * Initialises the metric cards module.
 * - Resolves DOM elements
 * - Renders initial state (year 1900)
 * - Subscribes to timeline:yearChanged
 *
 * Called from main.js after DOMContentLoaded.
 */
export function initMetricCards() {
  if (!resolveElements()) return;

  // Render initial state
  updateMetricCards(1900);

  // Subscribe
  eventBus.on('timeline:yearChanged', ({ year }) => {
    updateMetricCards(year);
  });
}