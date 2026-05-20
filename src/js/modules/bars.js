/**
 * TerraEcho — modules/bars.js
 * Responsibility: Bar fill rendering only.
 * Subscribes to timeline:yearChanged, calculates interpolated bar widths,
 * updates DOM. No state writes. No event publishing.
 *
 * Targets (defined in index.html):
 *   #bar-fill-forest, #bar-fill-ice, #bar-fill-co2  — fill elements
 *   #bar-value-forest, #bar-value-ice, #bar-value-co2 — value readouts
 *   [role="progressbar"]#bar-row-* — aria-valuenow updates
 */

import eventBus                          from '../eventBus.js';
import { getValuesForYear, toBarPercent } from '../data/timelineData.js';

/** DOM references — resolved once on init */
const els = {};

/**
 * Resolves and caches all bar-related DOM elements.
 * Called once from initBars().
 * @returns {boolean} false if any required element is missing
 */
function resolveElements() {
  const ids = {
    fillForest:  'bar-fill-forest',
    fillIce:     'bar-fill-ice',
    fillCo2:     'bar-fill-co2',
    valueForest: 'bar-value-forest',
    valueIce:    'bar-value-ice',
    valueCo2:    'bar-value-co2',
    trackForest: 'bar-row-forest',
    trackIce:    'bar-row-ice',
    trackCo2:    'bar-row-co2',
  };

  for (const [key, id] of Object.entries(ids)) {
    const el = document.getElementById(id);
    if (!el) {
      console.warn(`[bars] Missing element: #${id}`);
      return false;
    }
    els[key] = el;
  }

  // progressbar elements are the .bar-track inside each row
  els.progressForest = els.trackForest.querySelector('[role="progressbar"]');
  els.progressIce    = els.trackIce.querySelector('[role="progressbar"]');
  els.progressCo2    = els.trackCo2.querySelector('[role="progressbar"]');

  return true;
}

/**
 * Removes Phase 1 placeholder width classes now that JS is driving widths.
 */
function removePlaceholders() {
  els.fillForest.classList.remove('bar-fill--placeholder-forest');
  els.fillIce.classList.remove('bar-fill--placeholder-ice');
  els.fillCo2.classList.remove('bar-fill--placeholder-co2');
}

/**
 * Updates bar fills and value readouts for a given year.
 * Called on every timeline:yearChanged event.
 * @param {number} year
 */
function updateBars(year) {
  const values = getValuesForYear(year);

  const forestPct = toBarPercent('forestCover', values.forestCover);
  const icePct    = toBarPercent('arcticIce',   values.arcticIce);
  const co2Pct    = toBarPercent('co2',         values.co2);

  // Set bar widths
  els.fillForest.style.width = `${forestPct.toFixed(1)}%`;
  els.fillIce.style.width    = `${icePct.toFixed(1)}%`;
  els.fillCo2.style.width    = `${co2Pct.toFixed(1)}%`;

  // Update value readouts
  els.valueForest.textContent = `${values.forestCover.toFixed(1)}`;
  els.valueIce.textContent    = `${values.arcticIce.toFixed(1)}`;
  els.valueCo2.textContent    = `${Math.round(values.co2)}`;

  // Remove placeholder spans — replace with real text node
  els.valueForest.style.width  = '';
  els.valueForest.style.display = '';
  els.valueIce.style.width     = '';
  els.valueIce.style.display   = '';
  els.valueCo2.style.width     = '';
  els.valueCo2.style.display   = '';

  // Update ARIA progressbar values
  if (els.progressForest) {
    els.progressForest.setAttribute('aria-valuenow', Math.round(forestPct));
  }
  if (els.progressIce) {
    els.progressIce.setAttribute('aria-valuenow', Math.round(icePct));
  }
  if (els.progressCo2) {
    els.progressCo2.setAttribute('aria-valuenow', Math.round(co2Pct));
  }
}

/**
 * Initialises the bars module.
 * - Resolves DOM elements
 * - Removes Phase 1 placeholder classes
 * - Renders initial state (year 1900)
 * - Subscribes to timeline:yearChanged
 *
 * Called from main.js after DOMContentLoaded.
 */
export function initBars() {
  if (!resolveElements()) return;

  removePlaceholders();

  // Render initial state before any user interaction
  updateBars(1900);

  // Subscribe — this is the only place bars listens for external events
  eventBus.on('timeline:yearChanged', ({ year }) => {
    updateBars(year);
  });
}