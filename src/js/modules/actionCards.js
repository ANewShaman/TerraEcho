/**
 * TerraEcho — modules/actionCards.js
 * Responsibility: Action card click handling and count display only.
 * Reads initial counts from state on load.
 * Increments count on click, updates DOM, publishes actions:incremented.
 * No impact calculations. No milestone logic.
 *
 * Publishes:
 *   actions:incremented → { actionId: string, count: number, totalCount: number }
 *
 * Targets (defined in index.html):
 *   [data-action]         — clickable card buttons
 *   #count-{actionId}     — count badge on each card
 */

import eventBus                          from '../eventBus.js';
import { incrementCount, getCount,
         getTotalCount }                 from '../state/actions.js';

function updateCountBadge(actionId, count) {
  const badgeEl = document.getElementById('count-' + actionId);
  if (!badgeEl) return;

  badgeEl.textContent = count;

  if (count > 0) {
    badgeEl.classList.add('action-card__count--visible');
  } else {
    badgeEl.classList.remove('action-card__count--visible');
  }
}

function handleCardClick(actionId) {
  incrementCount(actionId);

  const newCount   = getCount(actionId);
  const totalCount = getTotalCount();

  updateCountBadge(actionId, newCount);

  const badgeEl = document.getElementById('count-' + actionId);
  if (badgeEl) {
    badgeEl.style.transform = 'scale(1.35)';
    setTimeout(function() { badgeEl.style.transform = ''; }, 180);
  }

  eventBus.emit('actions:incremented', { actionId, count: newCount, totalCount });
}

export function initActionCards() {
  const cards = document.querySelectorAll('[data-action]');

  if (cards.length === 0) {
    console.warn('[actionCards] No action cards found.');
    return;
  }

  cards.forEach(function(card) {
    const actionId = card.dataset.action;

    const existingCount = getCount(actionId);
    if (existingCount > 0) {
      updateCountBadge(actionId, existingCount);
    }

    card.addEventListener('click', function() { handleCardClick(actionId); });
  });
}