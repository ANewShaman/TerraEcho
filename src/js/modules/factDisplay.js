/**
 * TerraEcho — modules/factDisplay.js
 * Responsibility: Fact card DOM updates only.
 * Subscribes to timeline:yearChanged.
 * Snaps to correct milestone fact. Fades text on change.
 * No interpolation. No state writes. No event publishing.
 *
 * Targets (defined in index.html):
 *   #fact-text        — narrative paragraph
 *   #fact-year-badge  — year badge above the text
 *   #fact-source      — source attribution (added below)
 */

import eventBus              from '../eventBus.js';
import { FACTS, getFactYearFor } from '../data/facts.js';

/** Currently displayed milestone year — prevents redundant DOM updates */
let currentFactYear = null;

/** DOM references */
let factTextEl   = null;
let yearBadgeEl  = null;
let factSourceEl = null;

/**
 * Resolves and caches DOM elements.
 * @returns {boolean}
 */
function resolveElements() {
  factTextEl   = document.getElementById('fact-text');
  yearBadgeEl  = document.getElementById('fact-year-badge');
  factSourceEl = document.querySelector('.fact-card__source');

  if (!factTextEl || !yearBadgeEl) {
    console.warn('[factDisplay] Missing required DOM elements.');
    return false;
  }
  return true;
}

/**
 * Updates the fact card for a given milestone year.
 * Applies a brief opacity fade when the fact changes.
 * If the fact year hasn't changed, does nothing.
 *
 * @param {number} milestoneYear - One of the six milestone years
 */
function displayFact(milestoneYear) {
  if (milestoneYear === currentFactYear) return;
  currentFactYear = milestoneYear;

  const fact = FACTS[milestoneYear];
  if (!fact) return;

  // Fade out
  factTextEl.style.opacity = '0';

  // Swap content after a short delay matching the fade duration
  setTimeout(() => {
    // Normalise whitespace from template literal indentation
    factTextEl.textContent = fact.text.replace(/\s+/g, ' ').trim();
    yearBadgeEl.textContent = String(milestoneYear);

    if (factSourceEl) {
      factSourceEl.textContent = fact.source;
    }

    // Fade back in
    factTextEl.style.opacity = '1';
  }, 150);
}

/**
 * Initialises the fact display module.
 * - Resolves DOM elements
 * - Sets CSS transition on fact text
 * - Renders initial fact (1900)
 * - Subscribes to timeline:yearChanged
 *
 * Called from main.js after DOMContentLoaded.
 */
export function initFactDisplay() {
  if (!resolveElements()) return;

  // Set transition once via JS so CSS file stays clean
  factTextEl.style.transition = 'opacity 0.15s ease';

  // Render initial state
  displayFact(1900);

  // Subscribe
  eventBus.on('timeline:yearChanged', ({ year }) => {
    const milestoneYear = getFactYearFor(year);
    displayFact(milestoneYear);
  });
}