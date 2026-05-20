/**
 * TerraEcho — themeToggle.js
 * Responsibility: Theme detection, application, and persistence only.
 * Direct DOM manipulation. No EventBus. No external dependencies.
 *
 * Reads:  localStorage 'terraecho:theme', prefers-color-scheme
 * Writes: [data-theme] on <html>, localStorage 'terraecho:theme'
 * Targets: #theme-toggle button, .theme-toggle__icon, .theme-toggle__label
 */

const STORAGE_KEY  = 'terraecho:theme';
const DARK_VALUE   = 'dark';
const LIGHT_VALUE  = 'light';

/**
 * Returns the user's stored preference, or null if none saved.
 * @returns {'dark'|'light'|null}
 */
function getStoredTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === DARK_VALUE || stored === LIGHT_VALUE) return stored;
  } catch {
    // localStorage unavailable (private browsing, etc.)
  }
  return null;
}

/**
 * Persists a theme choice to localStorage.
 * @param {'dark'|'light'} theme
 */
function persistTheme(theme) {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Silently ignore write failures
  }
}

/**
 * Returns the OS-level color scheme preference.
 * @returns {'dark'|'light'}
 */
function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
    ? DARK_VALUE
    : LIGHT_VALUE;
}

/**
 * Applies a theme to the document root and updates the toggle button.
 * @param {'dark'|'light'} theme
 * @param {HTMLElement|null} toggleBtn - The toggle button element, if available.
 */
function applyTheme(theme, toggleBtn) {
  document.documentElement.setAttribute('data-theme', theme);

  if (!toggleBtn) return;

  const iconEl  = toggleBtn.querySelector('.theme-toggle__icon');
  const labelEl = toggleBtn.querySelector('.theme-toggle__label');

  if (theme === DARK_VALUE) {
    toggleBtn.setAttribute('aria-label', 'Switch to light mode');
    toggleBtn.setAttribute('title', 'Switch to light mode');
    if (iconEl)  iconEl.textContent  = '☀';
    if (labelEl) labelEl.textContent = 'Light';
  } else {
    toggleBtn.setAttribute('aria-label', 'Switch to dark mode');
    toggleBtn.setAttribute('title', 'Switch to dark mode');
    if (iconEl)  iconEl.textContent  = '◑';
    if (labelEl) labelEl.textContent = 'Dark';
  }
}

/**
 * Initialises the theme system.
 * Priority order:
 *   1. localStorage stored preference
 *   2. OS prefers-color-scheme
 *   3. Default to light
 *
 * Attaches click listener to #theme-toggle.
 * Called once from main.js after DOMContentLoaded.
 */
export function initTheme() {
  const toggleBtn = document.getElementById('theme-toggle');

  // Determine initial theme
  const initialTheme = getStoredTheme() ?? getSystemTheme();
  applyTheme(initialTheme, toggleBtn);

  if (!toggleBtn) {
    console.warn('[themeToggle] #theme-toggle not found.');
    return;
  }

  // Toggle on click
  toggleBtn.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next    = current === DARK_VALUE ? LIGHT_VALUE : DARK_VALUE;
    persistTheme(next);
    applyTheme(next, toggleBtn);
  });

  // React to OS-level preference changes (user switches system theme mid-session)
  // Only applies if the user hasn't made a manual choice in this session
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    // If user has a stored preference, OS changes don't override it
    if (getStoredTheme() !== null) return;
    const systemTheme = e.matches ? DARK_VALUE : LIGHT_VALUE;
    applyTheme(systemTheme, toggleBtn);
  });
}