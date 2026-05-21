/**
 * TerraEcho — main.js
 * Responsibility: Application entry point and boot sequence only.
 * Imports modules and calls init() in dependency order.
 * No business logic. No DOM manipulation.
 *
 * Boot order rules:
 *   1. Theme          — before first paint, prevents flash
 *   2. Tabs           — before any tab-specific module runs
 *   3. ActionsState   — before any action module reads state
 *   4. Bars/Cards/Facts — subscribers registered before controls fire
 *   5. TimelineControls — fires initial yearChanged after subscribers ready
 *   6. ActionCards/Impact/Milestone — read state, subscribe to events
 */

import { initTheme }            from './themeToggle.js';
import { initTabs }             from './tabs.js';
import { initActionsState }     from './state/actions.js';
import { initBars }             from './modules/bars.js';
import { initMetricCards }      from './modules/metricCards.js';
import { initFactDisplay }      from './modules/factDisplay.js';
import { initTimelineControls } from './timelineControls.js';
import { initActionCards }      from './modules/actionCards.js';
import { initImpactSummary }    from './modules/impactSummary.js';
import { initMilestone }        from './modules/milestone.js';

function boot() {
  // Phase 1
  initTheme();
  initTabs();

  // Phase 3 state — must load before any action module reads it
  initActionsState();

  // Phase 2 subscribers — registered before controls publish first event
  initBars();
  initMetricCards();
  initFactDisplay();

  // Phase 2 controls — publishes initial timeline:yearChanged
  initTimelineControls();

  // Phase 3 modules — all read from initActionsState on init
  initActionCards();
  initImpactSummary();
  initMilestone();

  // Phase 4: initAudio();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  boot();
}