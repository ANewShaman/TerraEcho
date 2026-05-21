/**
 * TerraEcho — modules/milestone.js
 * Responsibility: Milestone threshold evaluation and card rendering only.
 * Subscribes to actions:incremented.
 * Shows the highest reached, non-dismissed milestone.
 * Handles dismiss — persists to state, hides card.
 * No impact calculations. No count incrementing.
 *
 * Subscribes:
 *   actions:incremented
 *
 * Targets:
 *   #milestone-card, #milestone-title, #milestone-text,
 *   #milestone-impact, #milestone-donate-btn, #milestone-dismiss
 */

import eventBus                              from '../eventBus.js';
import { getTotalCount, isMilestoneDismissed,
         dismissMilestone }                  from '../state/actions.js';
import { MILESTONES, DONATION_URL }          from '../data/actionData.js';

let cardEl    = null;
let titleEl   = null;
let textEl    = null;
let impactEl  = null;
let donateEl  = null;
let dismissEl = null;

let visibleMilestoneId = null;

function resolveElements() {
  cardEl    = document.getElementById('milestone-card');
  titleEl   = document.getElementById('milestone-title');
  textEl    = document.getElementById('milestone-text');
  impactEl  = document.getElementById('milestone-impact');
  donateEl  = document.getElementById('milestone-donate-btn');
  dismissEl = document.getElementById('milestone-dismiss');

  if (!cardEl || !titleEl || !textEl || !donateEl || !dismissEl) {
    console.warn('[milestone] Missing required DOM elements.');
    return false;
  }
  return true;
}

function getActiveMilestone(totalCount) {
  let active = null;
  for (const milestone of MILESTONES) {
    if (totalCount >= milestone.totalActions && !isMilestoneDismissed(milestone.id)) {
      active = milestone;
    }
  }
  return active;
}

function showMilestone(milestone) {
  visibleMilestoneId = milestone.id;

  titleEl.textContent = milestone.message;
  textEl.textContent  = milestone.subtext;

  const iconEl = cardEl.querySelector('.milestone-card__icon');
  if (iconEl) iconEl.textContent = milestone.emoji;

  const badgeEl = cardEl.querySelector('.milestone-card__badge');
  if (badgeEl) badgeEl.textContent = milestone.totalActions + ' actions';

  donateEl.href = DONATION_URL;

  if (impactEl) {
    impactEl.textContent = milestone.totalActions + ' actions logged and counting.';
  }

  cardEl.classList.remove('milestone-card--hidden');
}

function hideCard() {
  cardEl.classList.add('milestone-card--hidden');
  visibleMilestoneId = null;
}

function evaluate() {
  const total  = getTotalCount();
  const active = getActiveMilestone(total);

  if (!active) {
    if (visibleMilestoneId !== null) hideCard();
    return;
  }

  if (active.id !== visibleMilestoneId) {
    showMilestone(active);
  }
}

function handleDismiss() {
  if (!visibleMilestoneId) return;
  dismissMilestone(visibleMilestoneId);
  hideCard();
  evaluate();
}

export function initMilestone() {
  if (!resolveElements()) return;
  dismissEl.addEventListener('click', handleDismiss);
  evaluate();
  eventBus.on('actions:incremented', evaluate);
}