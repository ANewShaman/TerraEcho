/**
 * TerraEcho — state/timeline.js
 * Responsibility: Timeline state storage and typed accessors only.
 * No DOM. No events. No interpolation. No business logic.
 *
 * Consumers:
 *   timelineControls.js — reads and writes
 *   bars.js, factDisplay.js, metricCards.js — read on init
 */

const MIN_YEAR = 1900;
const MAX_YEAR = 2024;

const state = {
  year:      MIN_YEAR,
  isPlaying: false,
};

/**
 * @returns {number} Current year (integer, clamped 1900–2024)
 */
export function getYear() {
  return state.year;
}

/**
 * @param {number} year
 */
export function setYear(year) {
  state.year = Math.max(MIN_YEAR, Math.min(MAX_YEAR, Math.round(year)));
}

/**
 * @returns {boolean}
 */
export function getIsPlaying() {
  return state.isPlaying;
}

/**
 * @param {boolean} value
 */
export function setIsPlaying(value) {
  state.isPlaying = Boolean(value);
}

export { MIN_YEAR, MAX_YEAR };