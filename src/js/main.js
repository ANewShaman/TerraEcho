/**
 * TerraEcho — main.js
 * Responsibility: Application entry point and boot sequence.
 * Imports modules and calls their init() functions in dependency order.
 * Contains NO business logic. NO DOM manipulation beyond delegating to modules.
 *
 * Phase 1: initTheme, initTabs
 * Phase 2: + initTimelineControls, initBars, initMetricCards, initFactDisplay
 * Phase 3: + initActionCards, initImpactSummary, initMilestone
 * Phase 4: + initAudio
 */

import { initTheme }            from './themeToggle.js';
import { initTabs }             from './tabs.js';
import { initTimelineControls } from './timelineControls.js';
import { initBars }             from './modules/bars.js';
import { initMetricCards }      from './modules/metricCards.js';
import { initFactDisplay }      from './modules/factDisplay.js';

/**
 * Boot sequence — order is intentional.
 *   1. Theme     — prevents flash of wrong theme before paint
 *   2. Tabs      — wires navigation before tab-specific modules run
 *   3. Controls  — enables slider/play, publishes initial yearChanged event
 *   4. Bars      — subscribes before initial event fires (via initTimelineControls)
 *   5. Cards     — same
 *   6. Facts     — same
 *
 * Note: initTimelineControls publishes timeline:yearChanged at the end of its
 * init, so all subscriber modules (bars, metricCards, factDisplay) must be
 * initialised BEFORE initTimelineControls is called — or they will miss the
 * initial render event. Hence the order: subscribe first, then enable controls.
 */
function boot() {
  initTheme();
  initTabs();

  // Subscribers must be registered before controls fire the first event
  initBars();
  initMetricCards();
  initFactDisplay();

  // Controls init last — its final publishYearChanged() triggers all subscribers
  initTimelineControls();

  // ── Phase 3 additions ────────────────────────────────────
  // initActionCards();
  // initImpactSummary();
  // initMilestone();

  // ── Phase 4 additions ────────────────────────────────────
  // initAudio();
}

// Guard: run boot after DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  boot();
}