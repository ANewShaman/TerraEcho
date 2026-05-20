/**
 * TerraEcho — timelineControls.js
 * Responsibility: Timeline user interaction and playback only.
 *
 * Owns:
 *   - Slider input → year update → publish timeline:yearChanged
 *   - --pct CSS property for track fill
 *   - Play/pause button state
 *   - requestAnimationFrame autoplay loop (1900→2024, ~30s total)
 *   - Pause on drag during playback
 *
 * Publishes:
 *   timeline:yearChanged  → { year: number }
 *   timeline:playStarted  → {}
 *   timeline:playStopped  → {}
 *
 * Does NOT: read DOM beyond its own elements, touch bars/facts/cards.
 *
 * Targets (defined in index.html):
 *   #timeline-slider — range input
 *   #year-number     — hero year display
 *   #play-btn        — play/pause button
 *   .play-btn__icon  — SVG path inside play button
 */

import eventBus                    from './eventBus.js';
import { getYear, setYear,
         getIsPlaying, setIsPlaying,
         MIN_YEAR, MAX_YEAR }       from './state/timeline.js';

/* ── Playback config ─────────────────────────────────────── */
/** Total duration of one full play-through in milliseconds */
const PLAY_DURATION_MS  = 30_000;
/** Years spanned across full play-through */
const YEAR_SPAN         = MAX_YEAR - MIN_YEAR; // 124
/** Years advanced per millisecond during playback */
const YEARS_PER_MS      = YEAR_SPAN / PLAY_DURATION_MS;

/* ── SVG icon paths ──────────────────────────────────────── */
const ICON_PLAY  = 'M4 2.5l9 5.5-9 5.5V2.5z';
const ICON_PAUSE = 'M4 2h3v12H4V2zm5 0h3v12H9V2z';

/* ── DOM references ──────────────────────────────────────── */
let sliderEl   = null;
let yearNumEl  = null;
let playBtnEl  = null;
let playIconEl = null;

/* ── RAF state ───────────────────────────────────────────── */
let rafId         = null;   // current requestAnimationFrame handle
let lastTimestamp = null;   // timestamp from previous RAF frame

/* ─────────────────────────────────────────────────────────── */

/**
 * Resolves and caches DOM elements.
 * @returns {boolean}
 */
function resolveElements() {
  sliderEl   = document.getElementById('timeline-slider');
  yearNumEl  = document.getElementById('year-number');
  playBtnEl  = document.getElementById('play-btn');
  playIconEl = playBtnEl?.querySelector('.play-btn__icon path');

  if (!sliderEl || !yearNumEl || !playBtnEl) {
    console.warn('[timelineControls] Missing required DOM elements.');
    return false;
  }
  return true;
}

/**
 * Updates the slider's --pct custom property for the track fill gradient.
 * CSS in timeline.css uses var(--pct) on the range input.
 * @param {number} year
 */
function updateSliderFill(year) {
  const pct = ((year - MIN_YEAR) / YEAR_SPAN) * 100;
  sliderEl.style.setProperty('--pct', `${pct.toFixed(2)}%`);
}

/**
 * Updates all display elements to reflect the given year.
 * Does NOT publish any event — callers are responsible for that.
 * @param {number} year
 */
function syncDisplayToYear(year) {
  const rounded = Math.round(year);

  sliderEl.value = rounded;
  sliderEl.setAttribute('aria-valuenow',  rounded);
  sliderEl.setAttribute('aria-valuetext', `Year ${rounded}`);

  yearNumEl.textContent = rounded;

  updateSliderFill(rounded);
}

/**
 * Publishes timeline:yearChanged with the current state year.
 */
function publishYearChanged() {
  eventBus.emit('timeline:yearChanged', { year: getYear() });
}

/* ── Play / Pause ─────────────────────────────────────────── */

/**
 * Sets the play button visual state.
 * @param {boolean} playing
 */
function setPlayButtonState(playing) {
  if (!playBtnEl) return;

  if (playIconEl) {
    playIconEl.setAttribute('d', playing ? ICON_PAUSE : ICON_PLAY);
  }

  playBtnEl.setAttribute('aria-label', playing ? 'Pause timeline' : 'Play timeline animation');
  playBtnEl.querySelector('.play-btn span') &&
    (playBtnEl.querySelector('span:not(.play-btn__icon)')
      ? (playBtnEl.querySelector('span:not(.play-btn__icon)').textContent = playing ? 'Pause' : 'Play')
      : null);

  // Update text node directly — the button contains SVG + text node "Play"
  // Walk child nodes to find and update the text node
  playBtnEl.childNodes.forEach((node) => {
    if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
      node.textContent = playing ? ' Pause' : ' Play';
    }
  });
}

/**
 * Stops playback — cancels RAF, updates state and button.
 * Does NOT reset year.
 */
function stopPlayback() {
  if (rafId !== null) {
    cancelAnimationFrame(rafId);
    rafId = null;
  }
  lastTimestamp = null;
  setIsPlaying(false);
  setPlayButtonState(false);
  eventBus.emit('timeline:playStopped', {});
}

/**
 * The RAF loop. Advances year proportionally to elapsed time.
 * @param {DOMHighResTimeStamp} timestamp
 */
function rafLoop(timestamp) {
  if (!getIsPlaying()) return;

  if (lastTimestamp === null) {
    lastTimestamp = timestamp;
  }

  const elapsed  = timestamp - lastTimestamp;
  lastTimestamp  = timestamp;

  const newYear = getYear() + elapsed * YEARS_PER_MS;

  if (newYear >= MAX_YEAR) {
    // Reached 2024 — snap to end and stop
    setYear(MAX_YEAR);
    syncDisplayToYear(MAX_YEAR);
    publishYearChanged();
    stopPlayback();
    return;
  }

  setYear(newYear);
  syncDisplayToYear(newYear);
  publishYearChanged();

  rafId = requestAnimationFrame(rafLoop);
}

/**
 * Starts playback from the current year.
 * If already at 2024, resets to 1900 first.
 */
function startPlayback() {
  if (getYear() >= MAX_YEAR) {
    setYear(MIN_YEAR);
    syncDisplayToYear(MIN_YEAR);
    publishYearChanged();
  }

  setIsPlaying(true);
  setPlayButtonState(true);
  lastTimestamp = null;
  eventBus.emit('timeline:playStarted', {});
  rafId = requestAnimationFrame(rafLoop);
}

/* ── Event listeners ──────────────────────────────────────── */

/**
 * Handles slider input events (fires continuously while dragging).
 */
function onSliderInput() {
  const year = parseInt(sliderEl.value, 10);

  // Dragging during playback pauses it
  if (getIsPlaying()) {
    stopPlayback();
  }

  setYear(year);
  syncDisplayToYear(year);
  publishYearChanged();
}

/**
 * Handles play button clicks.
 */
function onPlayClick() {
  if (getIsPlaying()) {
    stopPlayback();
  } else {
    startPlayback();
  }
}

/* ── Init ────────────────────────────────────────────────── */

/**
 * Initialises timeline controls.
 * - Resolves DOM elements
 * - Enables disabled controls from Phase 1
 * - Sets initial display state
 * - Attaches event listeners
 *
 * Called from main.js after DOMContentLoaded.
 */
export function initTimelineControls() {
  if (!resolveElements()) return;

  // Enable controls — they were disabled in Phase 1 HTML
  sliderEl.removeAttribute('disabled');
  playBtnEl.removeAttribute('disabled');

  // Set initial display
  syncDisplayToYear(MIN_YEAR);

  // Attach listeners
  sliderEl.addEventListener('input', onSliderInput);
  playBtnEl.addEventListener('click', onPlayClick);

  // Publish initial state so all subscribers render year 1900 on load
  publishYearChanged();
}