/**
 * TerraEcho — state/actions.js
 * Responsibility: Action state storage and localStorage persistence only.
 * Exposes typed accessors. Owns all localStorage read/write for actions.
 * No DOM. No events. No impact calculations.
 *
 * Schema stored in localStorage (key: 'terraecho:actions'):
 * {
 *   counts: { bottle: 0, plastic: 0, tree: 0, cycled: 0, meal: 0, shower: 0 },
 *   dismissedMilestones: []
 * }
 *
 * Derived values (CO2, water, tree equivalents) are NOT stored.
 * They are recalculated from counts at runtime by impactSummary.js.
 */

import { STORAGE_KEY } from '../data/actionData.js';

const DEFAULT_STATE = {
  counts: {
    bottle:  0,
    plastic: 0,
    tree:    0,
    cycled:  0,
    meal:    0,
    shower:  0,
  },
  dismissedMilestones: [],
};

let state = null;

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return structuredClone(DEFAULT_STATE);

    const parsed = JSON.parse(raw);

    if (
      typeof parsed.counts !== 'object' ||
      !Array.isArray(parsed.dismissedMilestones)
    ) {
      return structuredClone(DEFAULT_STATE);
    }

    const counts = { ...DEFAULT_STATE.counts };
    for (const key of Object.keys(DEFAULT_STATE.counts)) {
      if (typeof parsed.counts[key] === 'number') {
        counts[key] = Math.max(0, Math.round(parsed.counts[key]));
      }
    }

    return {
      counts,
      dismissedMilestones: parsed.dismissedMilestones.filter(
        (id) => typeof id === 'string'
      ),
    };
  } catch {
    return structuredClone(DEFAULT_STATE);
  }
}

function saveToStorage() {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        counts:              state.counts,
        dismissedMilestones: state.dismissedMilestones,
      })
    );
  } catch {
    // Silently ignore write failures
  }
}

export function initActionsState() {
  state = loadFromStorage();
}

export function getCounts() {
  return { ...state.counts };
}

export function getCount(actionId) {
  return state.counts[actionId] ?? 0;
}

export function incrementCount(actionId) {
  if (!(actionId in state.counts)) {
    console.warn('[actions] Unknown action id: ' + actionId);
    return;
  }
  state.counts[actionId] += 1;
  saveToStorage();
}

export function getTotalCount() {
  return Object.values(state.counts).reduce((sum, n) => sum + n, 0);
}

export function getDismissedMilestones() {
  return [...state.dismissedMilestones];
}

export function dismissMilestone(milestoneId) {
  if (!state.dismissedMilestones.includes(milestoneId)) {
    state.dismissedMilestones.push(milestoneId);
    saveToStorage();
  }
}

export function isMilestoneDismissed(milestoneId) {
  return state.dismissedMilestones.includes(milestoneId);
}