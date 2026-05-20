/**
 * TerraEcho — main.js
 * Responsibility: Application entry point and boot sequence.
 * Imports modules and calls their init() functions in dependency order.
 * Contains NO business logic. NO DOM manipulation beyond delegating to modules.
 *
 * Phase 1: initTheme, initTabs
 * Phase 2: + initEventBus, initTimelineControls, initBars, initMetricCards, initFactDisplay
 * Phase 3: + initActionCards, initImpactSummary, initMilestone
 * Phase 4: + initAudio
 */

import { initTheme } from './themeToggle.js';
import { initTabs }  from './tabs.js';

/**
 * Boot sequence — runs after the DOM is fully parsed.
 * Order matters:
 *   1. Theme first — prevents flash of wrong theme.
 *   2. Tabs — wires navigation before any tab-specific modules run.
 */
function boot() {
  initTheme();
  initTabs();

  // ── Phase 2 additions (do not uncomment until Phase 2) ──
  // import('./eventBus.js').then ...
  // initTimelineControls();
  // initBars();
  // initMetricCards();
  // initFactDisplay();

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
  // DOMContentLoaded already fired (e.g. script loaded deferred)
  boot();
}