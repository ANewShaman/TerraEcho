/**
 * TerraEcho — modules/impactSummary.js
 * Responsibility: Impact total calculation and display only.
 * Subscribes to actions:incremented.
 * Recalculates totals from counts + multipliers on every update.
 * No state writes. No milestone logic. No localStorage access.
 *
 * Subscribes:
 *   actions:incremented
 *
 * Targets:
 *   #impact-co2, #impact-water, #impact-trees
 */

import eventBus         from '../eventBus.js';
import { getCounts }    from '../state/actions.js';
import { ACTION_CARDS } from '../data/actionData.js';

const MULTIPLIERS = {};
for (const card of ACTION_CARDS) {
  MULTIPLIERS[card.id] = { co2Kg: card.co2Kg, waterL: card.waterL, treeEq: card.treeEq };
}

let co2El   = null;
let waterEl = null;
let treesEl = null;

function resolveElements() {
  co2El   = document.getElementById('impact-co2');
  waterEl = document.getElementById('impact-water');
  treesEl = document.getElementById('impact-trees');
  if (!co2El || !waterEl || !treesEl) {
    console.warn('[impactSummary] Missing required DOM elements.');
    return false;
  }
  return true;
}

function calculateTotals() {
  const counts = getCounts();
  let co2Kg = 0, waterL = 0, treeEq = 0;
  for (const [actionId, count] of Object.entries(counts)) {
    const m = MULTIPLIERS[actionId];
    if (!m) continue;
    co2Kg  += m.co2Kg  * count;
    waterL += m.waterL * count;
    treeEq += m.treeEq * count;
  }
  return { co2Kg, waterL, treeEq };
}

function renderTotals(totals) {
  co2El.textContent   = totals.co2Kg.toFixed(2);
  waterEl.textContent = Math.round(totals.waterL).toLocaleString();
  treesEl.textContent = totals.treeEq.toFixed(2);
}

export function initImpactSummary() {
  if (!resolveElements()) return;
  renderTotals(calculateTotals());
  eventBus.on('actions:incremented', function() {
    renderTotals(calculateTotals());
  });
}